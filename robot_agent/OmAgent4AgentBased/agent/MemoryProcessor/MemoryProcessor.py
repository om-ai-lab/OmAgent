from omagent_core.omagent4agent import *
import json
import base64
import os
from datetime import datetime
from typing import Dict, List, Any
import hashlib


@registry.register_worker()
class MemoryProcessor(BaseWorker, BaseLLMBackend):
    """
    Memory processor that saves all memories with images and text as log files AND stores them in Milvus.
    Provides dual storage: file-based logging for debugging and Milvus for semantic search and retrieval.
    """
    llm: OpenaiGPTLLM
    tool_manager: ToolManager
    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_template(
                "You are a memory logger that creates detailed memory entries for robot navigation logs. "
                "Create comprehensive memory entries that combine spatial, visual, and contextual information. "
                "Focus on key objects, spatial relationships, visual landmarks, and navigation-relevant information.",
                role="system"
            ),
            PromptTemplate.from_template(
                "MEMORY CONTEXT:\n"
                "Step {{step}}: {{action}} at {{location}}\n"
                "Objects: {{objects}}\n"
                "Environment: {{environment}}\n"
                "Visual Scene: {{visual_description}}\n"
                "Previous Visual Context: {{previous_visual_context}}\n\n"
                "Create a comprehensive memory entry that includes:\n"
                "1. Spatial information and location details\n"
                "2. Visual landmarks and scene characteristics\n"
                "3. Object relationships and navigation context\n"
                "4. Changes from previous observations\n\n"
                "Keep it detailed but organized (max 200 words):",
                role="user"
            )
        ]
    )
    
    logs_directory: str = Field(default="examples/robot/logs", description="Directory to save memory logs")
    milvus_collection_name: str = Field(default="robot_navigation_memories", description="Milvus collection name for storing memories")
    use_milvus: bool = Field(default=True, description="Whether to save memories to Milvus")
    
    def _run(self, *args, **kwargs):
        self.callback.info(agent_id=self.workflow_instance_id, progress='📝 Memory Logging', 
                         message="Saving navigation memory as log files")
        
        try:
            # Get current navigation data
            step_count = self.stm(self.workflow_instance_id).get("step_count", 0)
            last_react_result = self.stm(self.workflow_instance_id).get("last_react_result", {})
            
            # Skip if no new action or step 0
            if not last_react_result or step_count == 0:
                self.callback.info(agent_id=self.workflow_instance_id, progress='⏭️ Skip Logging', 
                                 message="No new action to log")
                return
            
            # Get current environment state
            env_state_json = self.tool_manager.execute(
                tool_name="mcp_thor_get_environment_state",
                args={}
            )
            env_state = json.loads(env_state_json) if isinstance(env_state_json, str) else env_state_json
            
            # Get current position and visual data
            pose = env_state.get("pose", [0, 0, 0])
            location = f"({pose[0]:.2f}, {pose[1]:.2f}, {pose[2]:.2f})" if len(pose) >= 3 else "unknown"
            rgb_data = env_state.get("observation", {}).get("rgb", "")
            map_data = env_state.get("map", "")
            
            # Create log directory if it doesn't exist
            os.makedirs(self.logs_directory, exist_ok=True)
            
            # Create session directory based on workflow instance ID
            session_dir = os.path.join(self.logs_directory, f"session_{self.workflow_instance_id[:8]}")
            os.makedirs(session_dir, exist_ok=True)
            
            # Save visual memory with detailed logging
            self._save_memory_log(
                session_dir, step_count, last_react_result, location, 
                rgb_data, map_data, env_state
            )
            
            self.callback.info(agent_id=self.workflow_instance_id, progress='✅ Memory Logged', 
                             message=f"Step {step_count} logged to {session_dir}")
            
        except Exception as e:
            self.callback.info(agent_id=self.workflow_instance_id, progress='❌ Logging Error', 
                             message=f"Memory logging failed: {str(e)}")
    
    def _save_memory_log(self, session_dir: str, step_count: int, react_result: Dict[str, Any], 
                        location: str, rgb_data: str, map_data: str, env_state: Dict[str, Any]):
        """Save comprehensive memory log with images and text."""
        
        timestamp = datetime.now()
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        
        # Create step directory
        step_dir = os.path.join(session_dir, f"step_{step_count:03d}_{timestamp_str}")
        os.makedirs(step_dir, exist_ok=True)
        
        # Generate visual description and object detection
        visual_description = self._generate_visual_description(rgb_data) if rgb_data else "No visual data"
        detected_objects = self._detect_objects(rgb_data) if rgb_data else "No objects detected"
        
        # Create comprehensive memory entry
        memory_entry = self._create_memory_entry(
            step_count, react_result, location, detected_objects, visual_description
        )
        
        # Save text log
        log_data = {
            "step": step_count,
            "timestamp": timestamp.isoformat(),
            "location": location,
            "pose": env_state.get("pose", []),
            "action": react_result.get("action", "unknown"),
            "action_parameter": react_result.get("action_parameter", ""),
            "reasoning": react_result.get("reasoning", ""),
            "observation": react_result.get("observation", ""),
            "execution_success": react_result.get("execution_success", False),
            "goal_achieved": react_result.get("goal_achieved", False),
            "detected_objects": detected_objects,
            "visual_description": visual_description,
            "memory_entry": memory_entry,
            "map_analysis": react_result.get("map_analysis", ""),
            "confidence": react_result.get("confidence", 0.0)
        }
        
        # Save JSON log
        log_file = os.path.join(step_dir, "memory_log.json")
        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        # Save markdown summary
        markdown_file = os.path.join(step_dir, "memory_summary.md")
        self._save_markdown_summary(markdown_file, log_data)
        
        # Save images if available
        if rgb_data:
            self._save_image_data(step_dir, "rgb_observation.jpg", rgb_data)
        
        if map_data:
            self._save_image_data(step_dir, "map_view.jpg", map_data)
        
        # Save to Milvus if enabled
        if self.use_milvus:
            try:
                self._save_to_milvus(log_data)
                self.callback.info(agent_id=self.workflow_instance_id, progress='💾 Milvus Saved', 
                                 message="Memory also saved to Milvus collection")
            except Exception as e:
                self.callback.info(agent_id=self.workflow_instance_id, progress='⚠️ Milvus Warning', 
                                 message=f"Milvus save failed: {str(e)}")
        
        self.callback.info(agent_id=self.workflow_instance_id, progress='💾 Files Saved', 
                         message=f"Saved: JSON, Markdown, {'RGB, ' if rgb_data else ''}{'Map' if map_data else ''}{'Milvus' if self.use_milvus else ''}")
    
    def _generate_visual_description(self, rgb_data: str) -> str:
        """Generate detailed visual description of the scene."""
        try:
            analysis_json = self.tool_manager.execute(
                tool_name="mcp_vlm-r1_analyze_image",
                args={
                    "image_path": rgb_data,
                    "question": "Describe this scene in detail focusing on: 1) Spatial layout and room structure, 2) Key objects and their positions, 3) Visual landmarks, 4) Lighting and atmosphere, 5) Navigation-relevant features. Be comprehensive and detailed."
                }
            )
            analysis_result = json.loads(analysis_json)
            return analysis_result.get("raw_output", "Visual analysis failed")
            
        except Exception as e:
            return f"Visual description error: {str(e)}"
    
    def _detect_objects(self, rgb_data: str) -> str:
        """Detect and describe objects in the scene."""
        try:
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
    
    def _create_memory_entry(self, step: int, action_data: dict, location: str, 
                           objects: str, visual_description: str) -> str:
        """Create a comprehensive memory entry."""
        try:
            action_name = action_data.get("action", "unknown")
            reasoning = action_data.get("reasoning", "")
            
            # Get previous visual context for comparison
            previous_context = "No previous context available"
            
            # Use LLM for structured memory entry
            memory_text = self.simple_infer(
                step=step,
                action=f"{action_name} - {reasoning}",
                location=location,
                objects=objects,
                environment="robot navigation environment",
                visual_description=visual_description,
                previous_visual_context=previous_context
            )["choices"][0]["message"]["content"]
            
            return memory_text
            
        except Exception as e:
            # Fallback to simple memory entry
            return f"Step {step}: {action_data.get('action', 'action')} at {location}. Objects: {objects[:100]}... Visual: {visual_description[:100]}... Reasoning: {action_data.get('reasoning', 'No reasoning')[:100]}..."
    
    def _save_markdown_summary(self, markdown_file: str, log_data: Dict[str, Any]):
        """Save a markdown summary of the memory log."""
        
        markdown_content = f"""# Navigation Memory Log - Step {log_data['step']}

## Basic Information
- **Timestamp**: {log_data['timestamp']}
- **Location**: {log_data['location']}
- **Pose**: {log_data['pose']}

## Action Details
- **Action**: {log_data['action']} {log_data['action_parameter']}
- **Execution Success**: {log_data['execution_success']}
- **Goal Achieved**: {log_data['goal_achieved']}
- **Confidence**: {log_data['confidence']}

## Reasoning
{log_data['reasoning']}

## Observation
{log_data['observation']}

## Visual Analysis
### Detected Objects
{log_data['detected_objects']}

### Visual Description
{log_data['visual_description']}

### Map Analysis
{log_data['map_analysis']}

## Memory Entry
{log_data['memory_entry']}

## Files in this Step
- `memory_log.json` - Complete data in JSON format
- `memory_summary.md` - This human-readable summary
- `rgb_observation.jpg` - RGB camera view (if available)
- `map_view.jpg` - Map view (if available)
"""
        
        with open(markdown_file, 'w') as f:
            f.write(markdown_content)
    
    def _save_image_data(self, step_dir: str, filename: str, image_data: str):
        """Save base64 image data to file."""
        try:
            # Remove data URL prefix if present
            if image_data.startswith('data:image'):
                image_data = image_data.split(',', 1)[1]
            
            # Decode base64 image data
            image_bytes = base64.b64decode(image_data)
            
            # Save to file
            image_path = os.path.join(step_dir, filename)
            with open(image_path, 'wb') as f:
                f.write(image_bytes)
                
        except Exception as e:
            # Save as text file if image decoding fails
            text_path = os.path.join(step_dir, f"{filename}.txt")
            with open(text_path, 'w') as f:
                f.write(f"Image data (could not decode): {image_data[:100]}...")

    def _save_to_milvus(self, log_data: Dict[str, Any]):
        """Save memory data to Milvus collection."""
        try:
            # Ensure collection exists
            self._ensure_milvus_collection()
            
            # Create unique ID for this memory entry
            memory_id = self._generate_memory_id(log_data)
            
            # Prepare data for Milvus insertion
            milvus_data = self._prepare_milvus_data(log_data, memory_id)
            
            # Insert into Milvus
            insert_result = self.tool_manager.execute(
                tool_name="mcp_milvus-sse_milvus_insert_data",
                args={
                    "collection_name": self.milvus_collection_name,
                    "data": milvus_data
                }
            )
            
            self.callback.info(agent_id=self.workflow_instance_id, progress='✅ Milvus Insert', 
                             message=f"Memory {memory_id} inserted into Milvus")
            
        except Exception as e:
            raise Exception(f"Failed to save to Milvus: {str(e)}")
    
    def _ensure_milvus_collection(self):
        """Ensure the Milvus collection exists, create if not."""
        try:
            # Check if collection exists
            collections_result = self.tool_manager.execute(
                tool_name="mcp_milvus-sse_milvus_list_collections",
                args={"input": "list"}
            )
            
            collections_data = json.loads(collections_result) if isinstance(collections_result, str) else collections_result
            existing_collections = collections_data.get("collections", [])
            
            if self.milvus_collection_name not in existing_collections:
                # Create collection with schema for robot navigation memories
                schema = {
                    "fields": [
                        {"name": "id", "type": "varchar", "max_length": 64, "is_primary": True},
                        {"name": "step", "type": "int64"},
                        {"name": "timestamp", "type": "varchar", "max_length": 100},
                        {"name": "session_id", "type": "varchar", "max_length": 50},
                        {"name": "location", "type": "varchar", "max_length": 100},
                        {"name": "pose_x", "type": "float"},
                        {"name": "pose_y", "type": "float"},
                        {"name": "pose_z", "type": "float"},
                        {"name": "action", "type": "varchar", "max_length": 100},
                        {"name": "action_parameter", "type": "varchar", "max_length": 500},
                        {"name": "reasoning", "type": "varchar", "max_length": 2000},
                        {"name": "observation", "type": "varchar", "max_length": 2000},
                        {"name": "execution_success", "type": "bool"},
                        {"name": "goal_achieved", "type": "bool"},
                        {"name": "detected_objects", "type": "varchar", "max_length": 2000},
                        {"name": "visual_description", "type": "varchar", "max_length": 2000},
                        {"name": "memory_entry", "type": "varchar", "max_length": 3000},
                        {"name": "map_analysis", "type": "varchar", "max_length": 1000},
                        {"name": "confidence", "type": "float"},
                        {"name": "memory_vector", "type": "float_vector", "dim": 1536}
                    ]
                }
                
                create_result = self.tool_manager.execute(
                    tool_name="mcp_milvus-sse_milvus_create_collection",
                    args={
                        "collection_name": self.milvus_collection_name,
                        "collection_schema": schema
                    }
                )
                
                # Load the collection into memory
                self.tool_manager.execute(
                    tool_name="mcp_milvus-sse_milvus_load_collection",
                    args={"collection_name": self.milvus_collection_name}
                )
                
                self.callback.info(agent_id=self.workflow_instance_id, progress='🆕 Milvus Collection', 
                                 message=f"Created and loaded collection: {self.milvus_collection_name}")
            else:
                # Load existing collection
                self.tool_manager.execute(
                    tool_name="mcp_milvus-sse_milvus_load_collection",
                    args={"collection_name": self.milvus_collection_name}
                )
                
        except Exception as e:
            raise Exception(f"Failed to ensure Milvus collection: {str(e)}")
    
    def _generate_memory_id(self, log_data: Dict[str, Any]) -> str:
        """Generate unique ID for memory entry."""
        session_id = self.workflow_instance_id[:8]
        step = log_data.get("step", 0)
        timestamp = log_data.get("timestamp", "")
        
        # Create hash from session + step + timestamp
        id_string = f"{session_id}_{step}_{timestamp}"
        return hashlib.md5(id_string.encode()).hexdigest()[:16]
    
    def _prepare_milvus_data(self, log_data: Dict[str, Any], memory_id: str) -> Dict[str, List[Any]]:
        """Prepare data for Milvus insertion."""
        pose = log_data.get("pose", [0.0, 0.0, 0.0])
        pose_x = float(pose[0]) if len(pose) > 0 else 0.0
        pose_y = float(pose[1]) if len(pose) > 1 else 0.0
        pose_z = float(pose[2]) if len(pose) > 2 else 0.0
        
        # Generate embedding for memory entry text
        memory_vector = self._generate_memory_embedding(log_data.get("memory_entry", ""))
        
        # Prepare single-row data for insertion
        milvus_data = {
            "id": [memory_id],
            "step": [log_data.get("step", 0)],
            "timestamp": [log_data.get("timestamp", "")],
            "session_id": [self.workflow_instance_id[:8]],
            "location": [log_data.get("location", "")[:100]],
            "pose_x": [pose_x],
            "pose_y": [pose_y],
            "pose_z": [pose_z],
            "action": [log_data.get("action", "")[:100]],
            "action_parameter": [log_data.get("action_parameter", "")[:500]],
            "reasoning": [log_data.get("reasoning", "")[:2000]],
            "observation": [log_data.get("observation", "")[:2000]],
            "execution_success": [log_data.get("execution_success", False)],
            "goal_achieved": [log_data.get("goal_achieved", False)],
            "detected_objects": [log_data.get("detected_objects", "")[:2000]],
            "visual_description": [log_data.get("visual_description", "")[:2000]],
            "memory_entry": [log_data.get("memory_entry", "")[:3000]],
            "map_analysis": [log_data.get("map_analysis", "")[:1000]],
            "confidence": [float(log_data.get("confidence", 0.0))],
            "memory_vector": [memory_vector]
        }
        
        return milvus_data
    
    def _generate_memory_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for memory text using OpenAI."""
        try:
            if not text or len(text.strip()) == 0:
                # Return zero vector for empty text
                return [0.0] * 1536
            
            # Use OpenAI embeddings through the LLM backend
            embedding_result = self.llm.generate_embedding(text[:8000])  # Truncate for API limits
            
            if isinstance(embedding_result, list) and len(embedding_result) > 0:
                return embedding_result
            else:
                # Fallback to zero vector
                return [0.0] * 1536
                
        except Exception as e:
            self.callback.info(agent_id=self.workflow_instance_id, progress='⚠️ Embedding Warning', 
                             message=f"Embedding generation failed: {str(e)}")
            # Return zero vector as fallback
            return [0.0] * 1536

    def search_memories(self, query_text: str, limit: int = 10, similarity_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Search for similar memories using text query."""
        try:
            if not self.use_milvus:
                return []
            
            # Generate embedding for query text
            query_vector = self._generate_memory_embedding(query_text)
            
            # Perform vector search in Milvus
            search_result = self.tool_manager.execute(
                tool_name="mcp_milvus-sse_milvus_vector_search",
                args={
                    "collection_name": self.milvus_collection_name,
                    "vector": query_vector,
                    "vector_field": "memory_vector",
                    "limit": limit,
                    "output_fields": "id,step,timestamp,session_id,location,action,reasoning,memory_entry,confidence",
                    "metric_type": "COSINE"
                }
            )
            
            search_data = json.loads(search_result) if isinstance(search_result, str) else search_result
            results = search_data.get("results", [])
            
            # Filter by similarity threshold
            filtered_results = [
                result for result in results 
                if result.get("distance", 0) >= similarity_threshold
            ]
            
            return filtered_results
            
        except Exception as e:
            self.callback.info(agent_id=self.workflow_instance_id, progress='⚠️ Search Warning', 
                             message=f"Memory search failed: {str(e)}")
            return []
    
    def search_memories_by_location(self, target_location: str, radius: float = 1.0, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for memories near a specific location."""
        try:
            if not self.use_milvus:
                return []
            
            # Parse target location coordinates
            if target_location.startswith("(") and target_location.endswith(")"):
                coords = target_location[1:-1].split(",")
                if len(coords) >= 2:
                    target_x = float(coords[0].strip())
                    target_y = float(coords[1].strip())
                    
                    # Create filter expression for location proximity
                    filter_expr = f"pose_x >= {target_x - radius} and pose_x <= {target_x + radius} and pose_y >= {target_y - radius} and pose_y <= {target_y + radius}"
                    
                    # Query Milvus with location filter
                    query_result = self.tool_manager.execute(
                        tool_name="mcp_milvus-sse_milvus_query",
                        args={
                            "collection_name": self.milvus_collection_name,
                            "filter_expr": filter_expr,
                            "output_fields": "id,step,timestamp,location,action,reasoning,memory_entry",
                            "limit": limit
                        }
                    )
                    
                    query_data = json.loads(query_result) if isinstance(query_result, str) else query_result
                    return query_data.get("results", [])
            
            return []
            
        except Exception as e:
            self.callback.info(agent_id=self.workflow_instance_id, progress='⚠️ Location Search Warning', 
                             message=f"Location-based memory search failed: {str(e)}")
            return [] 