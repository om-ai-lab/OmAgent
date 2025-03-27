from pathlib import Path
from typing import List, Tuple
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.utils.registry import registry
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.advanced_components.workflow.ZoomEye.schemas.tree import *
from omagent_core.advanced_components.workflow.ZoomEye.schemas.utils import *

@registry.register_worker()
class ZoomEyeSearch(BaseWorker, BaseLLMBackend):
    """
    Worker class that implements the core search algorithm of ZoomEye.
    Performs a confidence-guided tree traversal to locate visual elements in images,
    using a language model to evaluate confidence scores for image regions.
    """

    llm: OpenaiGPTLLM
    
    def get_confidence_weight(self, node: Node, max_depth: int):
        """
        Calculate a weighted bias based on node depth in the image tree.
        Deeper nodes get progressively more weight in confidence calculations.
        
        Args:
            node (Node): The image tree node being evaluated
            max_depth (int): Maximum depth of the image tree
            
        Returns:
            float: Weighted confidence value between 0.6 and 1.0
        """
        bias_value = 0.6  # Minimum weight value
        coeff = (1 - bias_value) / (max_depth ** 2)
        return coeff * (node.depth**2) + bias_value


    def stopping_criterion(self, cur_node: Node, question: str, threshold: float) -> bool:
        """
        Determine if the current node satisfies the search criteria sufficiently
        to stop the search process.
        
        Args:
            cur_node (Node): Current node being evaluated
            question (str): The query that guides the search
            threshold (float): Confidence threshold for accepting a node
            
        Returns:
            bool: True if node exceeds confidence threshold, False otherwise
        """
        try:
            # Generate a conversation to evaluate the node's answering confidence
            conversation = get_confidence_conversation(cur_node, cur_node.state.original_image_pil, 
                                                    confidence_type='answering', input_ele=question)
            
            # Enable logprobs for confidence calculation
            if not self.llm.logprobs:
                self.llm.logprobs = True
                self.llm.top_logprobs = 5
            
            # Get LLM response with confidence information
            llm_response = self.llm.generate(conversation)
            
            # Safely retrieve token usage data from STM
            stm_data = self.stm(self.workflow_instance_id) or {}
            prompt_tokens = stm_data.get('prompt_tokens', 0)
            completion_tokens = stm_data.get('completion_tokens', 0)
            
            # Update token usage counts
            self.stm(self.workflow_instance_id)['prompt_tokens'] = prompt_tokens + llm_response['usage']['prompt_tokens']
            self.stm(self.workflow_instance_id)['completion_tokens'] = completion_tokens + llm_response['usage']['completion_tokens']
            
            # Calculate confidence score and store it in the node
            cur_answering_confidence = calculate_confidence_from_logprobs(llm_response)
            cur_node.answering_confidence = cur_answering_confidence
            
            # Return whether the node exceeds the acceptance threshold
            return cur_answering_confidence >= threshold
        except Exception as e:
            print(f"Error in stopping_criterion: {e}")
            return False

    def get_priority(self, node: Node, image_pil, max_depth: int, visual_cue: str) -> float:
        """
        Calculate a priority score for a node to determine the traversal order.
        Uses a weighted combination of existence confidence and latent confidence.
        
        Args:
            node (Node): The node to calculate priority for
            image_pil: The original PIL image
            max_depth (int): Maximum depth of the image tree
            visual_cue (str): The visual element being searched for
            
        Returns:
            float: Priority score between 0.0 and 1.0
        """
        try:
            # Only calculate confidence if not already done
            if node.fast_confidence is None:
                if not self.llm.logprobs:
                    self.llm.logprobs = True
                    self.llm.top_logprobs = 5
                
                # Get existence confidence (is the object visible in this region?)
                existence_confidence = self._get_confidence(node, image_pil, 'existence', visual_cue)
                
                # Get latent confidence (could the object be in this region?)
                latent_confidence = self._get_confidence(node, image_pil, 'latent', visual_cue)
                
                # Calculate weighted combination based on node depth
                w = self.get_confidence_weight(node, max_depth)
                node.fast_confidence = existence_confidence * w + latent_confidence * (1 - w)
                
                # Store detailed confidence information for debugging
                node.fast_confidence_details = {
                    'existence': existence_confidence,
                    'latent': latent_confidence,
                    'weight': w
                }
            return node.fast_confidence
        except Exception as e:
            print(f"Error in get_priority: {e}")
            return 0.0

    def _get_confidence(self, node: Node, image_pil, confidence_type: str, visual_cue: str) -> float:
        """
        Helper method to get specific confidence scores from the language model.
        
        Args:
            node (Node): The node to evaluate
            image_pil: The original PIL image
            confidence_type (str): Type of confidence to evaluate ('existence' or 'latent')
            visual_cue (str): The visual element being searched for
            
        Returns:
            float: Confidence score between 0.0 and 1.0
        """
        # Generate appropriate conversation for confidence evaluation
        conversation = get_confidence_conversation(node, image_pil, confidence_type=confidence_type, 
                                                input_ele=visual_cue)
        response = self.llm.generate(conversation)
        
        # Safely update token usage counts
        stm_data = self.stm(self.workflow_instance_id) or {}
        prompt_tokens = stm_data.get('prompt_tokens', 0)
        completion_tokens = stm_data.get('completion_tokens', 0)
        
        self.stm(self.workflow_instance_id)['prompt_tokens'] = prompt_tokens + response['usage']['prompt_tokens']
        self.stm(self.workflow_instance_id)['completion_tokens'] = completion_tokens + response['usage']['completion_tokens']
        
        # Calculate and return confidence score
        return calculate_confidence_from_logprobs(response)

    def update_candidates(
        self,
        new_answering_threshold: float,
        pop_trace: List[Tuple[int, Node]],
        candidates: List[Node],
        num_candidates = 1,
    ):
        """
        Update the list of candidate nodes based on new threshold.
        
        Args:
            new_answering_threshold (float): New confidence threshold for candidates
            pop_trace (List[Tuple[int, Node]]): History of nodes processed
            candidates (List[Node]): Current list of candidate nodes
            num_candidates (int): Maximum number of candidates to keep
        """
        # Add nodes that meet the new threshold
        for _, node in pop_trace:
            if node.answering_confidence >= new_answering_threshold and node not in candidates:
                candidates.append(node)
                
        # Keep only the top candidates if we have too many
        if len(candidates) > num_candidates:
            candidates.sort(key=lambda x: x.answering_confidence, reverse=True)
            while len(candidates) > num_candidates:
                candidates.pop()

    def _run(self, *args, **kwargs):
        """
        Main execution method for the search process.
        Performs one step of the search algorithm, processing a single node.
        
        Args:
            *args: Variable length argument list (not used)
            **kwargs: Arbitrary keyword arguments (not used)
            
        Returns:
            None: Updates are made directly to shared memory
        """
        # Retrieve search state from shared memory
        visual_cues = self.stm(self.workflow_instance_id).get('visual_cues', None)
        visual_cue = self.stm(self.workflow_instance_id).get('current_visual_cue', None)
        
        # If no visual cues to search for, mark as finished
        if visual_cues is None and visual_cue is None:
            self.stm(self.workflow_instance_id)['finish'] = True
            return
            
        # Retrieve search parameters and state variables
        candidates = self.stm(self.workflow_instance_id)['candidates']
        num_pop = self.stm(self.workflow_instance_id)['num_pop']
        pop_num_limit = self.stm(self.workflow_instance_id)['pop_num_limit']
        temp_threshold_descrease = self.stm(self.workflow_instance_id)['temp_threshold_descrease']
        answering_confidence_threshold_upper = self.stm(self.workflow_instance_id)['answering_confidence_threshold_upper']
        pop_trace = self.stm(self.workflow_instance_id)['pop_trace']
        max_depth = self.stm(self.workflow_instance_id)['max_depth']
        image_pil = self.stm(self.workflow_instance_id)['image_cache']['<image_0>']
        question = self.stm(self.workflow_instance_id)['prompt']
        Q = self.stm(self.workflow_instance_id)['Q']
        
        # If queue is empty, mark search as finished
        if len(Q) == 0:
            self.stm(self.workflow_instance_id)['finish'] = True
            return
            
        # Get the next node to process
        cur_node = Q.pop(0)
        cur_node: Node  # Type hint for clarity
        
        # Update processing counters and history
        num_pop += 1
        pop_trace.append((num_pop, cur_node))
        self.stm(self.workflow_instance_id)['num_pop'] = num_pop
        self.stm(self.workflow_instance_id)['pop_trace'] = pop_trace

        # Check if current node satisfies search criteria
        if self.stopping_criterion(cur_node, question, answering_confidence_threshold_upper):
            candidates.append(cur_node)
            self.stm(self.workflow_instance_id)['candidates'] = candidates
            self.stm(self.workflow_instance_id)['finish'] = True
            return 
            
        # Check if we've reached node processing limit
        if num_pop >= pop_num_limit:
            # Lower confidence threshold to find more candidates
            answering_confidence_threshold_upper -= temp_threshold_descrease[0]
            self.stm(self.workflow_instance_id)['answering_confidence_threshold_upper'] = answering_confidence_threshold_upper
            
            # Update threshold decrease steps if there are more
            if len(temp_threshold_descrease) > 1:
                _ = temp_threshold_descrease.pop(0)
                print("temp_threshold_descrease:", temp_threshold_descrease)
                self.stm(self.workflow_instance_id)['temp_threshold_descrease'] = temp_threshold_descrease
                
            # Increase processing limit for next round
            pop_num_limit += NUM_INTERVEL
            
            # Update candidates with new threshold
            self.update_candidates(answering_confidence_threshold_upper, pop_trace, candidates)
            
            # If we found candidates with reduced threshold, finish search
            if len(candidates) > 0:
                self.stm(self.workflow_instance_id)['candidates'] = candidates
                self.stm(self.workflow_instance_id)['finish'] = True
                return
                
            # If threshold is too low, stop search to avoid low quality results
            if answering_confidence_threshold_upper < ANSWERING_CONFIDENCE_THRESHOLD_LOWER:
                self.stm(self.workflow_instance_id)['finish'] = True
                return
                
        # Add child nodes to the queue
        for child in cur_node.children:
            Q.append(child)
            
        # Sort queue by priority to process most promising nodes first
        Q.sort(key=lambda x: self.get_priority(x, image_pil, max_depth, visual_cue), reverse=True)
        
        # Update queue in shared memory
        self.stm(self.workflow_instance_id)['Q'] = Q

        return 