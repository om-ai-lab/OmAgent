from omagent_core.omagent4agent import *
from omagent_core.utils.general import read_image
import json
from datetime import datetime

@registry.register_worker()
class ObservationProcessor(BaseWorker, BaseLLMBackend):
    llm: OpenaiGPTLLM
    tool_manager: ToolManager
    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_template(
                "You are a robotic observation analyst. Format object properties and spatial relationships into structured reports. "
                "Include: 1) Object list with color/size/shape 2) Relative positions 3) Distance estimates 4) Notable spatial patterns",
                role="system"
            ),
            PromptTemplate.from_template(
                "Raw detection data:\n{{object_data}}\n\nVLM analysis:\n{{vlm_analysis}}\n"
                "Combine into comprehensive observation with metric measurements:",
                role="user"
            )
        ]
    )
    
    def _run(self, *args, **kwargs):
        self.callback.info(agent_id=self.workflow_instance_id, progress='🚀 Observation Processing', message="Starting observation analysis")
        
        try:
            # Check if we already have cached environment data
            
            # Get environment state only if needed
            self.callback.info(agent_id=self.workflow_instance_id, progress='📡 Environment Data', message="Retrieving environment state")
            env_state_json = self.tool_manager.execute(
                tool_name="mcp_ut-dog_get_environment_state",
                args={}
            )
            env_state = json.loads(env_state_json)
            rgb_data = env_state.get("observation", {}).get("rgb", "")
            map_data = env_state.get("map", "")
            pose = env_state.get("pose", [])
            

            
            # Display current data
            if rgb_data:
                self.callback.info_image(self.workflow_instance_id, progress="RGB", image=rgb_data)
            if map_data:
                self.callback.info_image(self.workflow_instance_id, progress="Map", image=map_data)

            # Check if we already have object detection data
            objects_data = self.stm(self.workflow_instance_id).get("detected_objects", None)
            
            # Only run detection if needed
            if not objects_data and rgb_data:
                self.callback.info(agent_id=self.workflow_instance_id, progress='🔍 Object Detection', message="Detecting objects in scene")
                detection_json = self.tool_manager.execute(
                    tool_name="mcp_vlm-r1_detect_objects",
                    args={"image_path": rgb_data}
                )
                detection_result = json.loads(detection_json)
                objects_data = detection_result.get("raw_output", {}).replace("```json", "").replace("```", "")
                
                # Cache for reuse
                self.stm(self.workflow_instance_id)["detected_objects"] = objects_data
            
            # Check if we already have spatial analysis
            spatial_analysis = self.stm(self.workflow_instance_id).get("spatial_analysis", None)
            
            # Only run spatial analysis if needed
            if not spatial_analysis and rgb_data:
                self.callback.info(agent_id=self.workflow_instance_id, progress='🧭 Spatial Analysis', message="Analyzing spatial relationships")
                analysis_json = self.tool_manager.execute(
                    tool_name="mcp_vlm-r1_analyze_image",
                    args={
                        "image_path": rgb_data,
                        "question": "Describe object positions relative to each other and the agent using cardinal directions and metric distances."
                    }
                )
                analysis_result = json.loads(analysis_json)
                spatial_analysis = analysis_result
                
                # Cache for reuse
                self.stm(self.workflow_instance_id)["spatial_analysis"] = spatial_analysis
            
            # Display detected information
            self.callback.info(agent_id=self.workflow_instance_id, progress='📊 Detected Objects', message=str(objects_data))
            self.callback.info(agent_id=self.workflow_instance_id, progress='📈 Spatial Analysis', message=str(spatial_analysis))

            # Generate structured observation report
            self.callback.info(agent_id=self.workflow_instance_id, progress='📝 Generating Report', message="Creating structured observation report")
            observation_text = self.simple_infer(
                object_data=str(objects_data),
                vlm_analysis=spatial_analysis
            )["choices"][0]["message"]["content"]
            
            # Display and store observation
            self.callback.info(agent_id=self.workflow_instance_id, progress='📋 Observation Report', message=observation_text)
            
            # Store observation in memory (only once)
            self.callback.info(agent_id=self.workflow_instance_id, progress='💾 Memory Storage', message="Storing observation in memory")
            self.tool_manager.execute(
                tool_name="mcp_mem0_store_robot_observation",
                args={"observation": observation_text}
            )
            
            # Get current pose for change detection
            current_pose = pose if pose else self.stm(self.workflow_instance_id).get("current_pose", [])
            location = f"{current_pose[0]},{current_pose[1]}" if len(current_pose)>=2 else "unknown"
            self.callback.info(agent_id=self.workflow_instance_id, progress='📍 Current Location', message=location)
            
            # Detect environment changes
            self.callback.info(agent_id=self.workflow_instance_id, progress='🔄 Change Detection', message="Checking for environment changes")
            change_report = self.tool_manager.execute(
                tool_name="mcp_mem0_detect_environment_changes",
                args={
                    "current_observation": observation_text,
                    "location": location
                }
            )
            self.callback.info(agent_id=self.workflow_instance_id, progress='📊 Environment Changes', message=str(change_report))

            # Update STM with latest analysis
            self.stm(self.workflow_instance_id)["last_observation"] = {
                "objects": objects_data,
                "spatial_analysis": spatial_analysis,
                "observation_text": observation_text,
                "timestamp": datetime.now().isoformat()
            }
            
            self.callback.info(agent_id=self.workflow_instance_id, progress='✅ Processing Complete', message="Observation processing finished")

        except Exception as e:
            self.callback.info(agent_id=self.workflow_instance_id, progress='❌ Error', message=f"Observation processing failed: {str(e)}")
            self.stm(self.workflow_instance_id)["observation_error"] = True
