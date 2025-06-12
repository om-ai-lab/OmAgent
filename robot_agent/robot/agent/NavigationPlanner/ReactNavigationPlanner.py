from omagent_core.omagent4agent import *
from omagent_core.utils.general import read_image
import json
import base64
from io import BytesIO
from datetime import datetime

@registry.register_worker()
class ReactNavigationPlanner(BaseWorker, BaseLLMBackend):
    """
    ReAct-based Navigation Planner that uses reasoning and acting methodology
    to improve navigation decision-making for robot navigation tasks.
    """
    llm: OpenaiGPTLLM
    tool_manager: ToolManager
    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_template(
                "You are an advanced robotic navigation planning expert using ReAct methodology. "
                "Follow these steps:\n"
                "1. THINK: Analyze the current situation, target, and environment\n"
                "2. ACT: Use tools to gather necessary information (environment analysis, memory search, etc.)\n"
                "3. OBSERVE: Evaluate tool results and incorporate into reasoning\n"
                "4. REASON: Based on all information, generate optimal navigation proposals\n\n"
                "Always structure your response with clear reasoning before taking actions.\n"
                "Generate navigation proposals EXACTLY as:\n"
                "Navigation Action Proposals:\n"
                "Action 1: Distance X.Xm, Angle Y.Y°, Minimum Width Z.Zpx\n"
                "Action 2: ...\n"
                "Include 2-3 proposals maximum, prioritizing safety and efficiency.",
                role="system"
            ),
            PromptTemplate.from_template(
                "Current Task: Navigate to {{target_info}}\n"
                "Previous Context: {{context}}\n"
                "Available Tools: {{tool_schema}}\n\n"
                "Please reason step by step about the navigation challenge and use tools when necessary.",
                role="user"
            )
        ]
    )
    
    max_reasoning_steps: int = Field(default=5, description="Maximum reasoning steps")
    
    def _run(self, *args, **kwargs):
        self.callback.info(agent_id=self.workflow_instance_id, progress='🧠 ReAct Navigation Planning', message="Starting intelligent navigation planning")
        
        try:
            # Get target information
            target_object = self.stm(self.workflow_instance_id).get("target_object", "")
            target_location = self.stm(self.workflow_instance_id).get("target_location", "")
            target_info = f"Find {target_object} at {target_location}" if target_object else "Explore environment"
            
            # Initialize context with previous navigation history
            context = self._build_initial_context()
            
            # Execute ReAct planning cycle
            planning_result = self._react_planning_cycle(target_info, context)
            
            # Store final navigation proposals
            self.stm(self.workflow_instance_id)["navigation_proposals"] = planning_result["proposals"]
            self.stm(self.workflow_instance_id)["planning_reasoning"] = planning_result["reasoning_history"]
            
            self.callback.info(agent_id=self.workflow_instance_id, progress='✅ ReAct Planning Complete', 
                             message=f"Generated {len(planning_result['reasoning_history'])} reasoning steps")
            
        except Exception as e:
            self.callback.info(agent_id=self.workflow_instance_id, progress='❌ Planning Error', 
                             message=f"ReAct planning failed: {str(e)}")
            # Fallback to basic proposals
            self.stm(self.workflow_instance_id)["navigation_proposals"] = "Navigation Action Proposals:\nAction 1: Distance 1.0m, Angle 0.0°, Minimum Width 100px"
    
    def _react_planning_cycle(self, target_info: str, initial_context: str) -> dict:
        """Execute the ReAct planning cycle with reasoning, acting, and observing."""
        
        reasoning_history = []
        context = initial_context
        tools_used = []
        
        for step in range(self.max_reasoning_steps):
            self.callback.info(agent_id=self.workflow_instance_id, progress=f'🤔 Reasoning Step {step+1}', 
                             message="Analyzing situation and planning actions")
            
            # THINK: Generate reasoning about current situation
            reasoning_result = self._think_step(target_info, context, step + 1)
            reasoning_history.append(reasoning_result)
            
            # Check if we have enough information to generate proposals
            if self._should_generate_proposals(reasoning_result["reasoning"]):
                self.callback.info(agent_id=self.workflow_instance_id, progress='📋 Generating Proposals', 
                                 message="Sufficient information gathered, creating navigation plan")
                break
            
            # ACT: Execute tools based on reasoning
            if self._should_use_tools(reasoning_result["reasoning"]):
                tool_results = self._act_step(reasoning_result["reasoning"], target_info, context)
                tools_used.extend(tool_results)
                
                # OBSERVE: Update context with tool results
                context = self._observe_and_update_context(context, reasoning_result["reasoning"], tool_results)
            else:
                # Update context with reasoning only
                context += f"\n\nStep {step+1} Reasoning: {reasoning_result['reasoning']}\n"
        
        # Generate final navigation proposals
        final_proposals = self._generate_navigation_proposals(target_info, reasoning_history, tools_used, context)
        
        return {
            "proposals": final_proposals,
            "reasoning_history": reasoning_history,
            "tools_used": tools_used,
            "final_context": context
        }
    
    def _think_step(self, target_info: str, context: str, step_num: int) -> dict:
        """Execute a thinking/reasoning step."""
        
        try:
            # Create reasoning prompt
            reasoning_prompt = f"""Step {step_num} - Analyze the current navigation situation:

            Target: {target_info}
            Current Context: {context}

            Think about:
            1. What information do I have about the environment?
            2. What information do I still need?
            3. What are the potential navigation challenges?
            4. What tools should I use to gather missing information?
            5. Am I ready to generate navigation proposals?

            Provide clear reasoning about the next steps."""

            response = self.llm.generate([
                {"role": "user", "content": reasoning_prompt}
            ])
            
            reasoning = response["choices"][0]["message"].get("content", "")
            
            self.callback.info(agent_id=self.workflow_instance_id, progress=f'💭 Step {step_num} Reasoning', 
                             message=reasoning[:200] + "..." if len(reasoning) > 200 else reasoning)
            
            return {
                "step": step_num,
                "reasoning": reasoning,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "step": step_num,
                "reasoning": f"Error in reasoning step: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def _act_step(self, reasoning: str, target_info: str, context: str) -> list:
        """Execute tools based on reasoning."""
        tool_results = []
        try:
            # Determine which tools to use based on reasoning
            if "environment" in reasoning.lower() or "current observation" in reasoning.lower():
                # Get environment state
                self.callback.info(agent_id=self.workflow_instance_id, progress='📡 Environment Analysis', 
                                 message="Analyzing current environment state")
                
                env_result = self._analyze_environment()
                tool_results.append({
                    "tool": "environment_analysis",
                    "result": env_result,
                    "timestamp": datetime.now().isoformat()
                })
            
            if "memory" in reasoning.lower() or "previous" in reasoning.lower() or "history" in reasoning.lower():
                # Search memory for relevant information
                self.callback.info(agent_id=self.workflow_instance_id, progress='🧠 Memory Search', 
                                 message="Searching memory for relevant navigation history")
                
                memory_result = self._search_memory(target_info)
                tool_results.append({
                    "tool": "memory_search",
                    "result": memory_result,
                    "timestamp": datetime.now().isoformat()
                })
            
            if "map" in reasoning.lower() or "spatial" in reasoning.lower():
                # Analyze map data
                self.callback.info(agent_id=self.workflow_instance_id, progress='🗺️ Map Analysis', 
                                 message="Analyzing spatial layout and navigation paths")
                
                map_result = self._analyze_map()
                tool_results.append({
                    "tool": "map_analysis",
                    "result": map_result,
                    "timestamp": datetime.now().isoformat()
                })
                
        except Exception as e:
            tool_results.append({
                "tool": "error",
                "result": f"Tool execution error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
        
        return tool_results
    
    def _analyze_environment(self) -> str:
        """Analyze current environment using VLM."""
        try:
            env_state_json = self.tool_manager.execute(
                tool_name="mcp_ut-dog_get_environment_state",
                args={}
            )
            env_state = json.loads(env_state_json)
            rgb_data = env_state.get("observation", {}).get("rgb", "")
            
            if rgb_data:
                # Display current observation
                self.callback.info_image(self.workflow_instance_id, progress="Current RGB", image=rgb_data)
                
                analysis_json = self.tool_manager.execute(
                    tool_name="mcp_vlm-r1_analyze_image",
                    args={
                        "image_path": rgb_data,
                        "question": "Analyze navigable spaces, obstacles, doorways, and potential movement directions. Estimate distances and identify safe paths."
                    }
                )
                analysis_data = json.loads(analysis_json)
                return analysis_data.get("result", "No environment analysis available")
            else:
                return "No visual data available for environment analysis"
                
        except Exception as e:
            return f"Environment analysis failed: {str(e)}"
    
    def _analyze_map(self) -> str:
        """Analyze map data for spatial understanding."""
        try:
            env_state_json = self.tool_manager.execute(
                tool_name="mcp_ut-dog_get_environment_state",
                args={}
            )
            env_state = json.loads(env_state_json)
            map_data = env_state.get("map", "")
            
            if map_data:
                # Display current map
                self.callback.info_image(self.workflow_instance_id, progress="Navigation Map", image=map_data)
                
                map_analysis_json = self.tool_manager.execute(
                    tool_name="mcp_vlm-r1_analyze_image",
                    args={
                        "image_path": map_data,
                        "question": "Analyze the map for optimal navigation routes, identify blocked paths, open areas, and strategic movement directions."
                    }
                )
                map_analysis_data = json.loads(map_analysis_json)
                return map_analysis_data.get("result", "No map analysis available")
            else:
                return "No map data available for analysis"
                
        except Exception as e:
            return f"Map analysis failed: {str(e)}"
    
    def _search_memory(self, target_info: str) -> str:
        """Search memory for relevant navigation information."""
        try:
            memory_result = self.tool_manager.execute(
                tool_name="mcp_mem0_search_robot_observations",
                args={"query": f"{target_info} navigation obstacles spatial relationships"}
            )
            return memory_result if memory_result else "No relevant memory found"
            
        except Exception as e:
            return f"Memory search failed: {str(e)}"
    
    def _should_use_tools(self, reasoning: str) -> bool:
        """Determine if tools should be used based on reasoning."""
        tool_indicators = [
            "need to analyze", "need to check", "should examine", "need information",
            "analyze environment", "check memory", "look at map", "get data",
            "need to understand", "should investigate", "need visual", "examine current"
        ]
        
        reasoning_lower = reasoning.lower()
        return any(indicator in reasoning_lower for indicator in tool_indicators)
    
    def _should_generate_proposals(self, reasoning: str) -> bool:
        """Determine if enough information is available to generate proposals."""
        completion_indicators = [
            "ready to generate", "sufficient information", "can now create",
            "enough data", "ready to plan", "can generate proposals",
            "have all needed", "sufficient analysis", "ready for navigation"
        ]
        
        reasoning_lower = reasoning.lower()
        return any(indicator in reasoning_lower for indicator in completion_indicators)
    
    def _observe_and_update_context(self, context: str, reasoning: str, tool_results: list) -> str:
        """Update context with reasoning and tool results."""
        
        updated_context = context + f"\n\nReasoning: {reasoning}\n"
        
        for result in tool_results:
            updated_context += f"\n{result['tool'].title()} Result: {result['result']}\n"
        
        return updated_context
    
    def _generate_navigation_proposals(self, target_info: str, reasoning_history: list, 
                                     tools_used: list, context: str) -> str:
        """Generate final navigation proposals based on all reasoning and analysis."""
        
        try:
            # Create comprehensive proposal generation prompt
            proposal_prompt = f"""Based on the following comprehensive analysis, generate specific navigation proposals:

            Target: {target_info}

            Reasoning Process:
            {self._format_reasoning_history(reasoning_history)}

            Tool Analysis Results:
            {self._format_tool_results(tools_used)}

            Generate 2-3 navigation proposals in EXACT format:
            Navigation Action Proposals:
            Action 1: Distance X.Xm, Angle Y.Y°, Minimum Width Z.Zpx
            Action 2: Distance X.Xm, Angle Y.Y°, Minimum Width Z.Zpx

            Prioritize safety, efficiency, and goal achievement. Consider obstacles and spatial constraints."""

            response = self.llm.generate([
                {"role": "user", "content": proposal_prompt}
            ])
            
            proposals = response["choices"][0]["message"].get("content", "")
            
            self.callback.info(agent_id=self.workflow_instance_id, progress='📋 Generated Proposals', 
                             message=proposals)
            
            return proposals
            
        except Exception as e:
            # Fallback proposals
            return "Navigation Action Proposals:\nAction 1: Distance 1.0m, Angle 0.0°, Minimum Width 100px\nAction 2: Distance 0.5m, Angle 45.0°, Minimum Width 120px"
    
    def _build_initial_context(self) -> str:
        """Build initial context from previous navigation history."""
        
        context = "Navigation Context:\n"
        
        # Add previous pose information
        current_pose = self.stm(self.workflow_instance_id).get("current_pose", {})
        if current_pose:
            context += f"Current Position: {current_pose}\n"
        
        # Add last action result
        last_action = self.stm(self.workflow_instance_id).get("last_action_result", {})
        if last_action:
            context += f"Previous Action: {last_action}\n"
        
        # Add any previous planning reasoning
        prev_reasoning = self.stm(self.workflow_instance_id).get("planning_reasoning", [])
        if prev_reasoning:
            context += f"Previous Planning Steps: {len(prev_reasoning)} steps completed\n"
        
        return context
    
    def _format_reasoning_history(self, reasoning_history: list) -> str:
        """Format reasoning history for display."""
        formatted = ""
        for entry in reasoning_history:
            formatted += f"Step {entry['step']}: {entry['reasoning']}\n\n"
        return formatted
    
    def _format_tool_results(self, tool_results: list) -> str:
        """Format tool results for display."""
        formatted = ""
        for result in tool_results:
            formatted += f"{result['tool'].title()}: {result['result']}\n\n"
        return formatted 