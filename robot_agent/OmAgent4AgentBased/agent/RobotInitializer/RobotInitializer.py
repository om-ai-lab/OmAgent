from omagent_core.omagent4agent import *
import json
import re
from datetime import datetime

@registry.register_worker()
class RobotInitializer(BaseWorker, BaseLLMBackend):
    """
    Fast and efficient robot initializer that combines instruction parsing 
    and environment setup in a single optimized step.
    """
    llm: OpenaiGPTLLM
    tool_manager: ToolManager
    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_template(
                "You are a robot initialization system. Parse navigation instructions and extract target information efficiently. "
                "Return JSON format: {\"target_object\": \"object_name\", \"target_location\": \"location_description\", \"constraints\": \"any_constraints\"}",
                role="system"
            ),
            PromptTemplate.from_template(
                "Parse this navigation instruction: {{instruction}}\n"
                "Extract the target object, location, and any constraints.",
                role="user"
            )
        ]
    )
    
    def _run(self, *args, **kwargs):
        self.callback.info(agent_id=self.workflow_instance_id, progress='🚀 Robot Initialization', 
                         message="Starting fast robot initialization")
        
        try:
            # Get navigation instruction from input
            instruction = kwargs.get("instruction", "Find any chair in the room")
            self.callback.info(agent_id=self.workflow_instance_id, progress='📝 Instruction', 
                             message=f"Processing: {instruction}")
            
            # Parse instruction using LLM
            parsing_result = self.simple_infer(instruction=instruction)
            content = parsing_result["choices"][0]["message"]["content"]
            
            # Extract target information
            try:
                # Try to parse as JSON first
                if "{" in content and "}" in content:
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        target_info = json.loads(json_match.group())
                    else:
                        raise ValueError("No JSON found")
                else:
                    raise ValueError("No JSON format")
            except:
                # Fallback parsing
                target_object = re.search(r'target_object["\']?\s*:\s*["\']([^"\']+)', content, re.IGNORECASE)
                target_location = re.search(r'target_location["\']?\s*:\s*["\']([^"\']+)', content, re.IGNORECASE)
                
                target_info = {
                    "target_object": target_object.group(1) if target_object else "any object",
                    "target_location": target_location.group(1) if target_location else "anywhere",
                    "constraints": "none"
                }
            
            # Store parsed information in STM
            self.stm(self.workflow_instance_id)["target_object"] = target_info.get("target_object", "any object")
            self.stm(self.workflow_instance_id)["target_location"] = target_info.get("target_location", "anywhere")
            self.stm(self.workflow_instance_id)["constraints"] = target_info.get("constraints", "none")
            
            self.callback.info(agent_id=self.workflow_instance_id, progress='🎯 Target Parsed', 
                             message=f"Object: {target_info['target_object']}, Location: {target_info['target_location']}")
            
            # Reset and initialize environment
            self.callback.info(agent_id=self.workflow_instance_id, progress='🔄 Environment Reset', 
                             message="Resetting THOR environment")
            
            reset_result = self.tool_manager.execute(
                tool_name="mcp_thor_reset_environment",
                args={}
            )
            
            self.callback.info(agent_id=self.workflow_instance_id, progress='🔄 Reset Result', 
                             message=f"Reset result: {reset_result}")
            
            # Capture initial observation
            self.callback.info(agent_id=self.workflow_instance_id, progress='📸 Initial Capture', 
                             message="Capturing initial environment state")
            
            env_state_json = self.tool_manager.execute(
                tool_name="mcp_thor_get_environment_state",
                args={}
            )
            env_state = json.loads(env_state_json) if isinstance(env_state_json, str) else env_state_json
            
            # Validate environment state
            if not env_state or not env_state.get("observation"):
                self.callback.info(agent_id=self.workflow_instance_id, progress='⚠️ Invalid State', 
                                 message="Environment state appears invalid or empty")
            else:
                self.callback.info(agent_id=self.workflow_instance_id, progress='✅ State Valid', 
                                 message=f"Environment state captured successfully")
            
            # Store initial state
            self.stm(self.workflow_instance_id)["initial_state"] = env_state
            self.stm(self.workflow_instance_id)["step_count"] = 0
            self.stm(self.workflow_instance_id)["initialization_time"] = datetime.now().isoformat()
            
            # Store initial position for movement tracking
            initial_pose = env_state.get("pose", [0, 0, 0])
            self.stm(self.workflow_instance_id)["last_position"] = initial_pose
            
            # Display initial observation
            rgb_data = env_state.get("observation", {}).get("rgb", "")
            map_data = env_state.get("map", "")
            if rgb_data:
                self.callback.info_image(self.workflow_instance_id, progress="RGB", image=rgb_data)
            else:
                self.callback.info(agent_id=self.workflow_instance_id, progress='⚠️ No RGB', 
                                 message="No RGB data in initial state")
            if map_data:
                self.callback.info_image(self.workflow_instance_id, progress="Map", image=map_data)
            else:
                self.callback.info(agent_id=self.workflow_instance_id, progress='⚠️ No Map', 
                                 message="No map data in initial state")
            
            # Test movement to verify THOR is working
            self.callback.info(agent_id=self.workflow_instance_id, progress='🧪 Testing Movement', 
                             message="Testing THOR environment with a small rotation")
            
            test_result = self.tool_manager.execute(
                tool_name="mcp_thor_step",
                args={"action": "RotateRight", "degrees": 30}
            )
            
            if isinstance(test_result, str):
                try:
                    test_data = json.loads(test_result)
                except:
                    test_data = {"result": {"code": "1", "message": "Failed to parse test result"}}
            else:
                test_data = test_result
            
            test_success = test_data.get("result", {}).get("code") == "0"
            self.callback.info(agent_id=self.workflow_instance_id, progress='🧪 Test Result', 
                             message=f"Test movement: {'SUCCESS' if test_success else 'FAILED'} - {test_data.get('result', {}).get('message', 'No message')}")
            
            # Rotate back to original position
            if test_success:
                self.tool_manager.execute(
                    tool_name="mcp_thor_step",
                    args={"action": "RotateLeft", "degrees": 30}
                )
            
            self.callback.info(agent_id=self.workflow_instance_id, progress='✅ Initialization Complete', 
                             message="Robot ready for navigation")
            
        except Exception as e:
            self.callback.info(agent_id=self.workflow_instance_id, progress='❌ Initialization Error', 
                             message=f"Failed to initialize: {str(e)}")
            # Set default values to prevent workflow failure
            self.stm(self.workflow_instance_id)["target_object"] = "any object"
            self.stm(self.workflow_instance_id)["target_location"] = "anywhere"
            self.stm(self.workflow_instance_id)["step_count"] = 0 