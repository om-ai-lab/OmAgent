from pathlib import Path
from omagent_core.utils.registry import registry
from omagent_core.utils.general import read_image
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.models.llms.vstar import VStarLLM
import copy
import torch
import heapq
from .utils import *

# Set the current path to the directory of this file
CURRENT_PATH = Path(__file__).parents[0]

@registry.register_worker()
class VQA_LLM_Preprocess(BaseWorker):
    """
    Preprocessing worker for Visual Question Answering (VQA) tasks.
    This class prepares the input data for the VQA LLM by reading the image
    and storing it in the state management system (STM).
    """

    def _run(self, qid: str, query: str, image_path: str):
        """
        Main execution method for preprocessing VQA input.
        
        Args:
            qid (str): The question ID.
            query (str): The text query from the user.
            image_path (str): The path to the input image.
        """
        # Clear the state management for the current workflow instance
        self.stm.clear(self.workflow_instance_id)
        
        # Read the image from the specified path
        img = read_image(input_source=image_path)
        
        # Store the image and query in the state management
        self.stm(self.workflow_instance_id)['image_cache'] = {'<image_0>': img}
        self.stm(self.workflow_instance_id)['prompt'] = query
        self.stm(self.workflow_instance_id)['id'] = qid
        return

@registry.register_worker()
class VQA_LLM(BaseWorker, VStarLLM):
    """
    Worker for executing the Visual Question Answering (VQA) LLM.
    This class interacts with the VStar LLM to get answers based on the input image and query.
    """

    llm: VStarLLM

    def _run(self, *args, **kwargs):
        """
        Main execution method for the VQA LLM.
        
        This method retrieves the image and prompt from the state management,
        calls the VStar LLM to get a response, and processes the result.
        """
        # Retrieve the cached image and prompt from the state management
        img = self.stm(self.workflow_instance_id)['image_cache']['<image_0>']
        prompt = self.stm(self.workflow_instance_id)['prompt']
        
        # Call the VStar LLM to get a response for the VQA task
        response = self.llm.vqa(prompt, img)
        res = response['choices'][0]['message']['content']
        
        # Log the response for debugging purposes
        self.callback.info(self.workflow_instance_id, progress='VQA LLM', message=f'response: {response}')
        
        # Determine if the VQA LLM succeeded based on the response content
        vqa_llm_succeed = 0 if MISSING_INFO in res else 1
        
        if vqa_llm_succeed == 1:
            # Store the answer in the state management if successful
            self.stm(self.workflow_instance_id)['answer'] = res
        else:
            # Process missing objects from the response
            missing_objects = res.split(MISSING_INFO)[-1]
            if missing_objects.endswith('.'):
                missing_objects = missing_objects[:-1]
            missing_objects = [obj.strip() for obj in missing_objects.split(',')]
            self.stm(self.workflow_instance_id)['missing_objects'] = missing_objects
            self.stm(self.workflow_instance_id)['all_missing_objects'] = missing_objects
            
        return {"vqa_llm_succeed": vqa_llm_succeed}
    
@registry.register_worker()
class VstarSearchPreprocess(BaseWorker):
    """
    Preprocessing worker for the VStar search task.
    This class prepares the search parameters based on the missing objects.
    """

    def _run(self, *args, **kwargs):
        """
        Main execution method for preprocessing the VStar search.
        
        This method initializes the search parameters and updates the state management.
        """
        # Retrieve the cached image and missing objects from the state management
        image = self.stm(self.workflow_instance_id)['image_cache']['<image_0>']
        missing_objects = self.stm(self.workflow_instance_id)['missing_objects']
        
        print("missing_objects", missing_objects)
        
        # Get the target object name for the search
        target_object_name = missing_objects.pop(0)
        
        # Initialize the search parameters
        init_patch = dict()
        init_patch['bbox'] = [0, 0, image.width, image.height]
        init_patch['scale_level'] = 1
        init_patch['score'] = None
        init_patch['parent_index'] = -1
        
        # Initialize the search path with the initial patch
        search_path = [init_patch]
        print("missing_objects_after_pop", missing_objects)
        
        # Update the state management with the initialized values
        self.stm(self.workflow_instance_id)['missing_objects'] = missing_objects
        self.stm(self.workflow_instance_id)['target_object_name'] = target_object_name
        self.stm(self.workflow_instance_id)['search_path'] = search_path
        self.stm(self.workflow_instance_id)['all_valid_boxes'] = []
        self.stm(self.workflow_instance_id)['search_result'] = None
        self.stm(self.workflow_instance_id)['queue'] = []
        self.stm(self.workflow_instance_id)['search_step'] = 0

        return 
    
@registry.register_worker()
class VstarLoopCheck(BaseWorker):
    """
    Worker to check if there are any missing objects in the search process.
    This class determines if the search can be completed based on the missing objects.
    """

    def _run(self, *args, **kwargs):
        """
        Main execution method for checking the loop condition.
        
        This method checks if there are any missing objects and returns the status.
        """
        missing_objects = self.stm(self.workflow_instance_id)['missing_objects']

        if len(missing_objects) == 0:
            print("missing_objects is empty")
            return {"finish": True}
        else:
            print("missing_objects is not empty")
            return {"finish": False}

    

@registry.register_worker()
class VstarSearch(BaseWorker, VStarLLM):
    """
    Worker for executing the VStar search task.
    This class interacts with the VStar LLM to perform visual searches based on the input image and target object.
    """

    llm: VStarLLM

    def _normalize_score(self, score_heatmap):
        """
        Normalize the score heatmap to a range of [0, 1].
        
        Args:
            score_heatmap (torch.Tensor): The heatmap scores to normalize.
        
        Returns:
            torch.Tensor: The normalized heatmap scores.
        """
        max_score = score_heatmap.max()
        min_score = score_heatmap.min()
        if max_score != min_score:
            score_heatmap = (score_heatmap - min_score) / (max_score - min_score)
        else:
            score_heatmap = score_heatmap * 0
        return score_heatmap



    def _run(self, *args, **kwargs):
        """
        Main execution method for the VStar search.
        
        This method retrieves the current patch, performs the search, and updates the state management with results.
        """
        # Retrieve the cached image and search parameters from the state management
        image = self.stm(self.workflow_instance_id)['image_cache']['<image_0>']
        search_path = self.stm(self.workflow_instance_id)['search_path']
        current_patch = search_path[-1]
        target_object_name = self.stm(self.workflow_instance_id)['target_object_name']
        current_patch_bbox = current_patch['bbox']
        current_patch_scale_level = current_patch['scale_level']
        queue = self.stm(self.workflow_instance_id)['queue']

        # Crop the image based on the current patch's bounding box
        image_patch = image.crop((int(current_patch_bbox[0]), int(current_patch_bbox[1]), 
                                   int(current_patch_bbox[0] + current_patch_bbox[2]), 
                                   int(current_patch_bbox[1] + current_patch_bbox[3])))
        
        # Call the VStar LLM to perform a visual search
        response = self.llm.visual_search(target_object_name, copy.deepcopy(image_patch), mode='detection')
        res = response['choices'][0]['message']['content']
        
        # Parse the response for bounding boxes, logits, and heatmaps
        pred_bboxes, pred_logits, target_cue_heatmap = res
        pred_bboxes = torch.tensor(pred_bboxes, dtype=torch.float32)
        self.callback.info(self.workflow_instance_id, progress='VstarSearch', message=f'bbox: {pred_bboxes}')
        pred_logits = torch.tensor(pred_logits, dtype=torch.float32)
        target_cue_heatmap = torch.tensor(target_cue_heatmap, dtype=torch.bool)

        # Process the predicted logits to find the best bounding box
        if len(pred_logits) > 0:
            top_index = pred_logits.view(-1).argmax()
            top_logit = pred_logits.view(-1).max()
            final_bbox = pred_bboxes[top_index].view(4)
            final_bbox = final_bbox * torch.Tensor([image_patch.width, image_patch.height, image_patch.width, image_patch.height])
            final_bbox[:2] -= final_bbox[2:] / 2
            
            if top_logit > CONFIDENCE_HIGH:
                # Store the detection result if confidence is high
                search_path[-1]['detection_result'] = final_bbox
                if len(search_path) == 1:
                    all_valid_boxes = pred_bboxes[pred_logits.view(-1) > 0.5].view(-1, 4)
                    all_valid_boxes = all_valid_boxes * torch.Tensor([[image_patch.width, image_patch.height, image_patch.width, image_patch.height]])
                    all_valid_boxes[:, :2] -= all_valid_boxes[:, 2:] / 2
                    self.stm(self.workflow_instance_id)['search_result'] = (True, search_path, all_valid_boxes)
                    return 
                self.stm(self.workflow_instance_id)['search_result'] = (True, search_path, None)
                return
            else:
                # Store temporary detection result if confidence is low
                search_path[-1]['temp_detection_result'] = (top_logit, final_bbox)
        
        # Check if the current patch size is below the minimum size
        if min(current_patch_bbox[2], current_patch_bbox[3]) <= SMALLEST_SIZE:
            self.stm(self.workflow_instance_id)['search_result'] = (False, search_path, None)
            return
        
        # Process the target cue heatmap
        target_cue_heatmap = target_cue_heatmap.view(current_patch_bbox[3], current_patch_bbox[2], 1)
        score_max = target_cue_heatmap.max().item()
        threshold = max(TARGET_CUE_THRESHOLD_MINIMUM, TARGET_CUE_THRESHOLD * (TARGET_CUE_THRESHOLD_DECAY) ** (current_patch_scale_level - 1))
        
        if score_max > threshold:
            target_cue_heatmap = self._normalize_score(target_cue_heatmap)
            final_heatmap = target_cue_heatmap
        else:
            # If the score is below the threshold, perform a VQA search
            response = self.llm.visual_search(target_object_name, copy.deepcopy(image_patch), mode='vqa')
            vqa_results = response['choices'][0]['message']['content']
            self.callback.info(self.workflow_instance_id, progress='VstarSearch-vqa', message=f'response: {vqa_results}')
            possible_location_phrase = vqa_results.split('most likely to appear')[-1].strip()
            if possible_location_phrase.endswith('.'):
                possible_location_phrase = possible_location_phrase[:-1]
            possible_location_phrase = possible_location_phrase.split(target_object_name)[-1]
            noun_chunks = extract_noun_chunks(possible_location_phrase)
            if len(noun_chunks) == 1:
                possible_location_phrase = noun_chunks[0]
            else:
                possible_location_phrase = "region {}".format(possible_location_phrase)
                
            # Perform segmentation search based on the possible location
            response = self.llm.visual_search(possible_location_phrase, copy.deepcopy(image_patch), mode='segmentation')
            res = response['choices'][0]['message']['content']
            res = torch.tensor(res, dtype=torch.int32)
            context_cue_heatmap = res.view(current_patch_bbox[3], current_patch_bbox[2], 1)
            context_cue_heatmap = self._normalize_score(context_cue_heatmap)
            final_heatmap = context_cue_heatmap
        
        current_patch_index = len(search_path) - 1

        if score_max <= threshold:
            # Store context cue if the score is below the threshold
            search_path[current_patch_index]['context_cue'] = vqa_results + "#" + possible_location_phrase
        search_path[current_patch_index]['final_heatmap'] = final_heatmap.cpu().numpy()
        
        # Get sub-patches for further processing
        basic_sub_patches, sub_patch_width, sub_patch_height = get_sub_patches(current_patch_bbox, *split_4subpatches(current_patch_bbox))

        tmp_patch = current_patch
        basic_sub_scores = [0] * len(basic_sub_patches)

        # Calculate scores for each sub-patch
        while True:
            tmp_score_heatmap = tmp_patch['final_heatmap']
            tmp_sub_scores = get_subpatch_scores(tmp_score_heatmap, tmp_patch['bbox'], basic_sub_patches)
            basic_sub_scores = [basic_sub_scores[patch_i] + tmp_sub_scores[patch_i] / (4 ** tmp_patch['scale_level']) for patch_i in range(len(basic_sub_scores))]
            if tmp_patch['parent_index'] == -1:
                break
            else:
                tmp_patch = search_path[tmp_patch['parent_index']]
        
        sub_patches = basic_sub_patches
        sub_scores = basic_sub_scores

        # Log the sub-scores for debugging
        self.callback.info(self.workflow_instance_id, progress='VstarSearch', message=f"sub_scores: {sub_scores}")
        
        # Push new patches into the queue for further processing
        for sub_patch, sub_score in zip(sub_patches, sub_scores):
            new_patch_info = dict()
            new_patch_info['bbox'] = sub_patch
            new_patch_info['scale_level'] = current_patch_scale_level + 1
            new_patch_info['score'] = sub_score
            new_patch_info['parent_index'] = current_patch_index
            heapq.heappush(queue, Prioritize(-new_patch_info['score'], new_patch_info))

        # Update the state management with the new queue and search result
        self.stm(self.workflow_instance_id)['queue'] = queue
        self.stm(self.workflow_instance_id)['search_result'] = False, search_path, None
        search_step = self.stm(self.workflow_instance_id)['search_step']
        search_step += 1
        self.stm(self.workflow_instance_id)['search_step'] = search_step

        return 

@registry.register_worker()
class VstarSearchCheck(BaseWorker):
    """
    Worker to check the status of the VStar search process.
    This class determines if the search has completed or if more steps are needed.
    """

    def _run(self, *args, **kwargs):
        """
        Main execution method for checking the search status.
        
        This method checks the current search step and updates the state management accordingly.
        """
        search_step = self.stm(self.workflow_instance_id)['search_step']
        
        # Check if the maximum search step has been exceeded
        if search_step > MAX_SEARCH_STEP:
            self.stm(self.workflow_instance_id)['search_result'] = False, None, None
            return {"finish": True}
        
        # Retrieve the search result from the state management
        success, search_path, all_valid_boxes = self.stm(self.workflow_instance_id)['search_result']
        self.callback.info(self.workflow_instance_id, progress='VstarSearchCheck', message=f'\nsuccess: {success}\nall_valid_boxes:{all_valid_boxes}')
        
        if success:
            # If the search was successful, update the all_search_result in the state management
            target_object_name = self.stm(self.workflow_instance_id)['target_object_name']
            if self.stm(self.workflow_instance_id).get('all_search_result', None) is None:
                self.stm(self.workflow_instance_id)['all_search_result'] = {}
            result_this_step = {target_object_name: self.stm(self.workflow_instance_id)['search_result']}
            result_origin = self.stm(self.workflow_instance_id)['all_search_result']
            self.stm(self.workflow_instance_id)['all_search_result'] = {**result_origin, **result_this_step}

            # Uncomment the following lines to save the detected crop image
            # image = self.stm(self.workflow_instance_id)['image_cache']['<image_0>']
            # bbox = search_path[-1]['bbox']
            # x, y, w, h = bbox
            # os.makedirs(f"./images", exist_ok=True)
            # image.crop([x, y, x + w, y + h]).save(f"./images/crop_{target_object_name}.jpg")
            # self.callback.info(self.workflow_instance_id, progress='VstarSearchCheck', message=f'The detected crop image has been saved in "images/crop_{target_object_name}.jpg".')
            return {"finish": True}
        
        # Check if the queue is empty
        queue = self.stm(self.workflow_instance_id)['queue']
        if len(queue) == 0:
            self.stm(self.workflow_instance_id)['search_result'] = False, None, None
            return {"finish": True}
        
        # Choose the next patch to process from the queue
        patch_chosen = heapq.heappop(queue).item
        self.callback.info(self.workflow_instance_id, progress='VstarSearchCheck', message=f'\npatch_chosen: {patch_chosen}')
        
        # Update the state management with the chosen patch
        self.stm(self.workflow_instance_id)['search_path'] = search_path + [patch_chosen]
        self.stm(self.workflow_instance_id)['queue'] = queue
        self.stm(self.workflow_instance_id)['current_patch'] = patch_chosen
        current_patch_bbox = patch_chosen['bbox']
        
        # Check if the current patch size is below the minimum size
        if min(current_patch_bbox[2], current_patch_bbox[3]) <= SMALLEST_SIZE:
            self.stm(self.workflow_instance_id)['search_result'] = False, search_path, None
            return {"finish": True}
        
        return {"finish": False}

@registry.register_worker()
class VQA_LLM_Post(BaseWorker, VStarLLM):
    """
    Worker for handling the post-processing of the Visual Question Answering (VQA) task.
    This class processes the results and prepares the final output for the user.
    """

    llm: VStarLLM

    def _run(self, *args, **kwargs):
        """
        Main execution method for post-processing the VQA results.
        
        This method retrieves the results from the state management and sends the final answer to the user.
        """
        # Prepare the result dictionary with relevant information
        result = {
            "id": self.stm(self.workflow_instance_id).get('id', None),
            "query": self.stm(self.workflow_instance_id).get('prompt', None),
            "last_output": self.stm(self.workflow_instance_id).get('answer', None),
            "missing_objects": self.stm(self.workflow_instance_id).get('all_missing_objects', None),
        }
        
        # Retrieve the cached image and prompt from the state management
        img = self.stm(self.workflow_instance_id)['image_cache']['<image_0>']
        prompt = self.stm(self.workflow_instance_id)['prompt']
        all_missing_objects = self.stm(self.workflow_instance_id).get('all_missing_objects', None)
        all_search_result = self.stm(self.workflow_instance_id).get('all_search_result', None)
        
        # Check if there are no missing objects
        if not all_missing_objects or len(all_missing_objects) == 0:
            self.callback.send_answer(self.workflow_instance_id, progress="VQA LLM Post", msg=self.stm(self.workflow_instance_id)['answer'])
            return {"result": result}
        
        # Check if there were any search results
        if all_search_result is None:
            self.callback.send_answer(self.workflow_instance_id, progress="VQA LLM Post", msg="Sorry, there are some mistakes in the search process.")
            result['last_output'] = "Sorry, there are some mistakes in the search process. No search result."
            return {"result": result}

        # Process each missing object to find its search result
        searched_infos = []
        for object_name in all_missing_objects:
            if object_name not in all_search_result:
                self.callback.send_answer(self.workflow_instance_id, progress="VQA LLM Post", msg=f"Sorry, I can not find the object {object_name} in the image.")
                continue
                
            success, search_path, all_valid_boxes = all_search_result[object_name] 
            if success:
                searched_infos.append({'bbox': search_path[-1]['bbox'], 'name': object_name})
                
        # Check if no objects were found
        if not searched_infos:
            self.callback.send_answer(self.workflow_instance_id, progress="VQA LLM Post", msg="Sorry, I can not find the object in the image.")
            result['last_output'] = "Sorry, I can not find all objects in the image. No success"
            return {"result": result}
            
        # Prepare the object names and bounding boxes for the final VQA call
        object_names = [info['name'] for info in searched_infos]
        bboxes = [info['bbox'] for info in searched_infos]
        
        # Call the VStar LLM for the final VQA post-processing
        response = self.llm.vqa_post(prompt, img, object_names=object_names, bboxes=bboxes)
        response = response['choices'][0]['message']['content']
        
        # Send the final answer to the user
        self.callback.send_answer(self.workflow_instance_id, msg=response)
        result['last_output'] = response
        return {"result": result}

