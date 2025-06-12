from omagent_core.omagent4agent import *
from omagent_core.utils.general import read_image
import json
import base64
from io import BytesIO

@registry.register_worker()
class NavigationPlanner(BaseWorker, BaseLLMBackend):
    llm: OpenaiGPTLLM
    tool_manager: ToolManager
    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_template(
                "You are a robotic navigation planning expert. Generate specific navigation proposals using VLM analysis, map data, and memory insights. "
                "Format proposals EXACTLY as:\n"
                "Navigation Action Proposals:\n"
                "Action 1: Distance X.Xm, Angle Y.Y°, Minimum Width Z.Zpx\n"
                "Action 2: ...\n"
                "Include 2-3 proposals maximum. Prioritize paths toward target location while avoiding obstacles.",
                role="system"
            ),
            PromptTemplate.from_template(
                "{{target_info}}\n"
                "Current Environment Analysis:\n{{env_analysis}}\n"
                "Map Insights:\n{{map_analysis}}\n"
                "Relevant Memory Context:\n{{memory_context}}\n"
                "RGB Image:\n{{rgb_image}}\n"
                "Map Image:\n{{map_image}}",
                role="user"
            )
        ]
    )
    
    def _run(self, *args, **kwargs):
        self.callback.info(agent_id=self.workflow_instance_id, progress='🚀 Navigation Planning', message="Starting navigation planning process")
        
        
        if True:
            # Retrieve navigation targets from memory
            target_object = self.stm(self.workflow_instance_id).get("target_object", "")
            target_location = self.stm(self.workflow_instance_id).get("target_location", "")
            target_info = f"Target: {target_object} at {target_location}" if target_object else "No specific target defined"
            self.callback.info(agent_id=self.workflow_instance_id, progress='🎯 Navigation Target', message=target_info)
            
            # Check if we can reuse cached environment data
            
            # If no cached data, get current environment state (only when necessary)
            self.callback.info(agent_id=self.workflow_instance_id, progress='📡 Environment Data', message="Retrieving current environment state")
            env_state_json = self.tool_manager.execute(
                tool_name="mcp_ut-dog_get_environment_state",
                args={}
            )
            env_state = json.loads(env_state_json)
            rgb_data = env_state.get("observation", {}).get("rgb", "")
            map_data = env_state.get("map", "")
            
                
            # Display current observation data
            if rgb_data:
                self.callback.info_image(self.workflow_instance_id, progress="RGB", image=rgb_data)
            if map_data:
                self.callback.info_image(self.workflow_instance_id, progress="Map", image=map_data)

            # Analyze environment using VLM-R1 only if analysis not already in STM
            if True:
                self.callback.info(agent_id=self.workflow_instance_id, progress='🔍 Environment Analysis', message="Analyzing current observation")
                env_analysis_json = self.tool_manager.execute(
                    tool_name="mcp_vlm-r1_analyze_image",
                    args={
                        "image_path": rgb_data,
                        "question": "Describe navigable spaces, obstacles, and potential movement directions with distance estimates."
                    }
                )
                env_analysis_data = json.loads(env_analysis_json)
                env_analysis = env_analysis_data.get("result", "")
                # Cache analysis for reuse
            
            # Process map data using VLM-R1 only if not already in STM
            if True:
                self.callback.info(agent_id=self.workflow_instance_id, progress='🧭 Map Analysis', message="Analyzing navigation map")
                map_analysis_json = self.tool_manager.execute(
                    tool_name="mcp_vlm-r1_analyze_image",
                    args={
                        "image_path": map_data,
                        "question": "Identify open paths, obstacles, and optimal routes considering current position."
                    }
                )
                map_analysis_data = json.loads(map_analysis_json)
                map_analysis = map_analysis_data.get("result", "")
                # Cache analysis for reuse

            # Show analyses to user
            self.callback.info(agent_id=self.workflow_instance_id, progress='📊 Environment Analysis', message=env_analysis)
            self.callback.info(agent_id=self.workflow_instance_id, progress='📈 Map Analysis', message=map_analysis)

            # Reuse memory context if available, or make a targeted query
            if True:
                self.callback.info(agent_id=self.workflow_instance_id, progress='🧠 Memory Search', message=f"Searching memory for information about {target_object}")
                memory_context = self.tool_manager.execute(
                    tool_name="mcp_mem0_search_robot_observations",
                    args={"query": f"{target_object} near {target_location} spatial relationships"}
                )
                # Cache for reuse
                self.stm(self.workflow_instance_id)["memory_context"] = memory_context

            # Generate navigation proposals using LLM
            self.callback.info(agent_id=self.workflow_instance_id, progress='🧩 Generating Proposals', message="Creating navigation action plan")
            proposals = self.simple_infer(
                target_info=target_info,
                env_analysis=env_analysis,
                map_analysis=map_analysis,
                memory_context=memory_context                
            )["choices"][0]["message"]["content"]
            
            # Store and visualize proposals
            self.stm(self.workflow_instance_id)["navigation_proposals"] = proposals
            self.callback.info(agent_id=self.workflow_instance_id, progress='📋 Navigation Plan', message=proposals)

            self.callback.info(agent_id=self.workflow_instance_id, progress='✅ Planning Complete', message="Navigation planning finished")

        #except Exception as e:
        #    self.callback.info(agent_id=self.workflow_instance_id, progress='❌ Error', message=f"Navigation planning failed: {str(e)}")
        #    # Store empty proposals to prevent workflow stall
        #    self.stm(self.workflow_instance_id)["navigation_proposals"] = "No viable proposals generated"
