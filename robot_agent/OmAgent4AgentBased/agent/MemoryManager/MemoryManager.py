from omagent_core.omagent4agent import *
from omagent_core.utils.general import read_image

@registry.register_worker()
class MemoryManager(BaseWorker, BaseLLMBackend):
    llm: OpenaiGPTLLM
    tool_manager: ToolManager
    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_template(
                "You are a robotic memory management system. Format observation data into structured memory entries and generate semantic search queries.",
                role="system"
            ),
            PromptTemplate.from_template(
                "Process the following observation data:\n{{object_data}}\n\nSpatial analysis:\n{{spatial_analysis}}\n\n"
                "Generate a comprehensive memory entry highlighting key environmental features and object relationships:",
                role="user"
            )
        ]
    )
    
    def _run(self, *args, **kwargs):
        self.callback.info(agent_id=self.workflow_instance_id, progress='🚀 Memory Management', message="Starting memory management cycle")
        
        try:
            # First check if we already have a processed observation in STM
            last_obs = self.stm(self.workflow_instance_id).get("last_observation", {})
            
            # If we have a full observation with text already processed by ObservationProcessor, use it
            if last_obs and "observation_text" in last_obs:
                self.callback.info(agent_id=self.workflow_instance_id, progress='♻️ Using Processed Data', message="Using pre-processed observation data")
                memory_entry = last_obs["observation_text"]
                self.callback.info(agent_id=self.workflow_instance_id, progress='📋 Observation Data', message=memory_entry)
            
            # Otherwise check if we have object and spatial data to process
            elif last_obs and "objects" in last_obs and "spatial_analysis" in last_obs:
                object_data = last_obs.get("objects", [])
                spatial_analysis = last_obs.get("spatial_analysis", "")
                
                if object_data and spatial_analysis:
                    self.callback.info(agent_id=self.workflow_instance_id, progress='🧠 Processing Observation', message="Formatting observation for memory storage")
                    # Generate structured memory entry using LLM
                    memory_entry = self.simple_infer(
                        object_data=str(object_data),
                        spatial_analysis=spatial_analysis
                    )["choices"][0]["message"]["content"]
                    self.callback.info(agent_id=self.workflow_instance_id, progress='📋 Memory Entry', message=memory_entry)
                else:
                    self.callback.info(agent_id=self.workflow_instance_id, progress='⚠️ Missing Data', message="Incomplete observation data in STM")
                    return
            else:
                self.callback.info(agent_id=self.workflow_instance_id, progress='⚠️ No Data', message="No observation data found in STM")
                return

            # Only store in persistent memory if it contains meaningful information
            if memory_entry and len(memory_entry.strip()) > 10:
                self.callback.info(agent_id=self.workflow_instance_id, progress='💾 Memory Storage', message="Storing observation in persistent memory")
                self.tool_manager.execute(
                    tool_name="mcp_mem0_store_robot_observation",
                    args={"observation": memory_entry}
                )
            
            # Get current pose for change detection
            current_pose = self.stm(self.workflow_instance_id).get("current_pose", [])
            location = f"{current_pose[0]},{current_pose[1]}" if len(current_pose)>=2 else "unknown"
            self.callback.info(agent_id=self.workflow_instance_id, progress='📍 Current Location', message=location)
            
            # Only do change detection if we have a valid memory entry and location
            if memory_entry and location != "unknown":
                self.callback.info(agent_id=self.workflow_instance_id, progress='🔄 Change Detection', message="Comparing with previous observations")
                change_report = self.tool_manager.execute(
                    tool_name="mcp_mem0_detect_environment_changes",
                    args={
                        "current_observation": memory_entry,
                        "location": location
                    }
                )
                self.callback.info(agent_id=self.workflow_instance_id, progress='📊 Changes Detected', message=str(change_report))
            
            # Check if search query is needed based on targeting information
            target_object = self.stm(self.workflow_instance_id).get("target_object", "")
            
            # Only perform semantic search if there's a specific target
            if target_object:
                self.callback.info(agent_id=self.workflow_instance_id, progress='🔍 Memory Search', message=f"Searching for information about {target_object}")
                search_query = f"Objects similar to {target_object} and their spatial relationships"
                search_results = self.tool_manager.execute(
                    tool_name="mcp_mem0_search_robot_observations",
                    args={"query": search_query}
                )
                self.callback.info(agent_id=self.workflow_instance_id, progress='🔎 Search Results', message=str(search_results))
                
                # Cache search results in STM for other workers
                self.stm(self.workflow_instance_id)["memory_search_results"] = search_results
            
            self.callback.info(agent_id=self.workflow_instance_id, progress='✅ Memory Cycle Complete', message="Memory management finished")

        except Exception as e:
            self.callback.info(agent_id=self.workflow_instance_id, progress='❌ Error', message=f"Memory management failed: {str(e)}")
            self.stm(self.workflow_instance_id)["memory_error"] = True
