from omagent_core.omagent4agent import *
import json
import re
from datetime import datetime

@registry.register_worker()
class SmartNavigator(BaseWorker, BaseLLMBackend):
    """
    Unified smart navigation worker that combines planning, execution, 
    observation, and goal verification in one optimized cycle.
    """
    llm: OpenaiGPTLLM
    tool_manager: ToolManager
    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_template(
                "You are an intelligent robot navigator. Analyze the environment, plan actions, and verify goals efficiently. "
                "Always respond with JSON format containing: navigation_action, reasoning, goal_status, and confidence_score.",
                role="system"
            ),
            PromptTemplate.from_template(
                "Target: {{target_object}} at {{target_location}}\n"
                "Current Environment: {{env_analysis}}\n"
                "Detected Objects: {{detected_objects}}\n"
                "Step: {{step_count}}/10\n\n"
                "Plan the next navigation action and assess goal achievement.",
                role="user"
            )
        ]
    )
    
    max_steps: int = Field(default=10, description="Maximum navigation steps")
    
    def _run(self, *args, **kwargs):
        self.callback.info(agent_id=self.workflow_instance_id, progress='🧠 Smart Navigation', 
                         message="Starting unified navigation cycle")
        
        try:
            # Get current step count and targets
            step_count = self.stm(self.workflow_instance_id).get("step_count", 0) + 1
            self.stm(self.workflow_instance_id)["step_count"] = step_count
            
            target_object = self.stm(self.workflow_instance_id).get("target_object", "any object")
            target_location = self.stm(self.workflow_instance_id).get("target_location", "anywhere")
            
            self.callback.info(agent_id=self.workflow_instance_id, progress=f'📍 Step {step_count}', 
                             message=f"Navigating to find {target_object} at {target_location}")
            
            # Check if max steps reached
            if step_count >= self.max_steps:
                self.callback.info(agent_id=self.workflow_instance_id, progress='⏰ Max Steps', 
                                 message="Maximum navigation steps reached")
                self.stm(self.workflow_instance_id)["max_steps_reached"] = True
                self.stm(self.workflow_instance_id)["goal_achieved"] = False
                return
            
            # Get current environment state
            env_state_json = self.tool_manager.execute(
                tool_name="mcp_thor_get_environment_state",
                args={}
            )
            env_state = json.loads(env_state_json) if isinstance(env_state_json, str) else env_state_json
            rgb_data = env_state.get("observation", {}).get("rgb", "")
            map_data = env_state.get("map", "")
            
            # Display current view and map
            if rgb_data:
                self.callback.info_image(self.workflow_instance_id, progress="RGB", image=rgb_data)
            if map_data:
                self.callback.info_image(self.workflow_instance_id, progress="Map", image=map_data)
            
            # Fast environment analysis
            env_analysis = self._analyze_environment(rgb_data)
            
            # Quick object detection
            detected_objects = self._detect_objects(rgb_data)
            
            # Check for goal achievement first
            goal_achieved = self._check_goal_achievement(detected_objects, target_object, target_location)
            
            if goal_achieved:
                self.callback.info(agent_id=self.workflow_instance_id, progress='🎯 Goal Achieved!', 
                                 message=f"Successfully found {target_object}")
                self.stm(self.workflow_instance_id)["goal_achieved"] = True
                self.stm(self.workflow_instance_id)["max_steps_reached"] = False
                return
            
            # Plan and execute next action
            action_result = self._plan_and_execute_action(env_analysis, detected_objects, target_object, target_location, step_count)
            
            # Store results
            self.stm(self.workflow_instance_id)["last_action"] = action_result
            self.stm(self.workflow_instance_id)["goal_achieved"] = False
            self.stm(self.workflow_instance_id)["max_steps_reached"] = False
            
            self.callback.info(agent_id=self.workflow_instance_id, progress='✅ Navigation Step Complete', 
                             message=f"Step {step_count} completed: {action_result.get('action', 'unknown')}")
            
        except Exception as e:
            self.callback.info(agent_id=self.workflow_instance_id, progress='❌ Navigation Error', 
                             message=f"Navigation failed: {str(e)}")
            self.stm(self.workflow_instance_id)["goal_achieved"] = False
            self.stm(self.workflow_instance_id)["max_steps_reached"] = True
    
    def _analyze_environment(self, rgb_data: str) -> str:
        """Fast environment analysis using VLM."""
        try:
            if not rgb_data:
                return "No visual data available"
            
            analysis_json = self.tool_manager.execute(
                tool_name="mcp_vlm-r1_analyze_image",
                args={
                    "image_path": rgb_data,
                    "question": "Quickly describe navigable paths, obstacles, and interesting objects. Be concise."
                }
            )
            analysis_result = json.loads(analysis_json)
            return analysis_result.get("result", "Analysis failed")
            
        except Exception as e:
            return f"Environment analysis error: {str(e)}"
    
    def _detect_objects(self, rgb_data: str) -> str:
        """Fast object detection."""
        try:
            if not rgb_data:
                return "No objects detected"
            
            detection_json = self.tool_manager.execute(
                tool_name="mcp_vlm-r1_detect_objects",
                args={"image_path": rgb_data}
            )
            detection_result = json.loads(detection_json)
            objects_data = detection_result.get("raw_output", "No objects found")
            
            # Clean up the response
            if isinstance(objects_data, str):
                objects_data = objects_data.replace("```json", "").replace("```", "").strip()
            
            return str(objects_data)
            
        except Exception as e:
            return f"Object detection error: {str(e)}"
    
    def _check_goal_achievement(self, detected_objects: str, target_object: str, target_location: str) -> bool:
        """Quick goal verification."""
        try:
            # Simple keyword matching for speed
            detected_lower = detected_objects.lower()
            target_lower = target_object.lower()
            
            # Check if target object is mentioned in detected objects
            if target_lower in detected_lower or "any object" in target_lower:
                # Additional verification with LLM for accuracy
                verification_prompt = f"""
                Detected objects: {detected_objects}
                Target: {target_object} at {target_location}
                
                Is the target object present? Answer only: YES or NO
                """
                
                response = self.llm.generate([
                    {"role": "user", "content": verification_prompt}
                ])
                
                result = response["choices"][0]["message"].get("content", "").strip().upper()
                return "YES" in result
            
            return False
            
        except Exception as e:
            self.callback.info(agent_id=self.workflow_instance_id, progress='⚠️ Verification Error', 
                             message=f"Goal verification failed: {str(e)}")
            return False
    
    def _plan_and_execute_action(self, env_analysis: str, detected_objects: str, target_object: str, target_location: str, step_count: int) -> dict:
        """Plan and execute navigation action in one step."""
        try:
            # Generate smart navigation decision
            navigation_prompt = f"""
            Environment: {env_analysis}
            Objects: {detected_objects}
            Target: {target_object} at {target_location}
            Step: {step_count}
            
            Choose the best action:
            1. MoveAhead - move forward
            2. RotateLeft - turn left 90°
            3. RotateRight - turn right 90°
            4. MoveBack - move backward
            5. LookUp - look up
            6. LookDown - look down
            
            Respond with JSON: {{"action": "ActionName", "reasoning": "why", "confidence": 0.8}}
            """
            
            response = self.llm.generate([
                {"role": "user", "content": navigation_prompt}
            ])
            
            content = response["choices"][0]["message"].get("content", "")
            
            # Parse action decision
            try:
                if "{" in content and "}" in content:
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        action_plan = json.loads(json_match.group())
                    else:
                        raise ValueError("No JSON found")
                else:
                    raise ValueError("No JSON format")
            except:
                # Fallback to simple action
                action_plan = {"action": "MoveAhead", "reasoning": "Default forward movement", "confidence": 0.5}
            
            action_name = action_plan.get("action", "MoveAhead")
            reasoning = action_plan.get("reasoning", "No reasoning provided")
            
            self.callback.info(agent_id=self.workflow_instance_id, progress=f'🎯 Action Plan', 
                             message=f"{action_name}: {reasoning}")
            
            # Execute the action
            execution_result = self._execute_action(action_name)
            
            return {
                "action": action_name,
                "reasoning": reasoning,
                "success": execution_result.get("success", True),
                "step": step_count,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.callback.info(agent_id=self.workflow_instance_id, progress='❌ Planning Error', 
                             message=f"Action planning failed: {str(e)}")
            # Execute default action
            return {
                "action": "MoveAhead",
                "reasoning": f"Error in planning: {str(e)}",
                "success": False,
                "step": step_count,
                "timestamp": datetime.now().isoformat()
            }
    
    def _execute_action(self, action_name: str) -> dict:
        """Execute the planned action."""
        try:
            # Map action names to THOR actions
            action_mapping = {
                "MoveAhead": {"action": "MoveAhead", "magnitude": 0.25},
                "MoveBack": {"action": "MoveBack", "magnitude": 0.25},
                "RotateLeft": {"action": "RotateLeft", "degrees": 90},
                "RotateRight": {"action": "RotateRight", "degrees": 90},
                "LookUp": {"action": "LookUp", "degrees": 30},
                "LookDown": {"action": "LookDown", "degrees": 30}
            }
            
            thor_action = action_mapping.get(action_name, {"action": "MoveAhead", "magnitude": 0.25})
            
            # Execute action in THOR
            result = self.tool_manager.execute(
                tool_name="mcp_thor_step",
                args=thor_action
            )
            
            self.callback.info(agent_id=self.workflow_instance_id, progress=f'⚡ Executed', 
                             message=f"Action {action_name} completed")
            
            return {"success": True, "result": result}
            
        except Exception as e:
            self.callback.info(agent_id=self.workflow_instance_id, progress='❌ Execution Error', 
                             message=f"Failed to execute {action_name}: {str(e)}")
            return {"success": False, "error": str(e)} 