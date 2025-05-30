from omagent_core.omagent4agent import *
import json
import re
from datetime import datetime
from typing import List, Dict, Any
import base64
import io
from PIL import Image

@registry.register_worker()
class ReActNavigator(BaseWorker, BaseLLMBackend):
    """
    Unified ReAct-based navigation worker that implements Reasoning, Acting, and Observing
    methodology in one optimized cycle for intelligent robot navigation with visual memory support.
    
    ReAct Methodology:
    1. REASONING: Analyze environment, memory, and goals to plan next action
    2. ACTING: Execute the planned action with monitoring
    3. OBSERVING: Analyze results and update understanding
    """
    llm: OpenaiGPTLLM
    tool_manager: ToolManager
    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_template(
                "You are an intelligent ReAct robot navigator with advanced obstacle detection. Use Reasoning, Acting, and Observing methodology. "
                "Always structure your response with clear REASONING, ACTION, and OBSERVATION sections. "
                "Focus on current observations, obstacle detection, and movement validation. Be systematic, logical, and adaptive in your approach. "
                "Pay special attention to blocked paths, failed movements, and transparent barriers like glass walls.",
                role="system"
            ),
            PromptTemplate.from_template(
                "NAVIGATION CONTEXT:\n"
                "Target: {{target_object}} at {{target_location}}\n"
                "Step: {{step_count}}/{{max_steps}}\n"
                "Environment: {{env_analysis}}\n"
                "Detected Objects: {{detected_objects}}\n"
                "Visual Scene: {{visual_description}}\n"
                "Map Analysis: {{map_analysis}}\n"
                "Previous Reasoning: {{previous_reasoning}}\n"
                "Execution History: {{execution_history}}\n"
                "Spatial Scan Info: {{spatial_scan_info}}\n"
                "Obstacle Detection: {{obstacle_analysis}}\n"
                "Movement Validation: {{movement_status}}\n\n"
                "Use ReAct methodology to navigate with spatial awareness:\n"
                "1. REASONING: Analyze the current situation including spatial scan data, obstacles, and movement history\n"
                "2. ACTION: Choose navigation actions based on spatial knowledge and current observations\n"
                "3. OBSERVATION: What do you expect to observe after this action?\n\n"
                "SPATIAL SCAN GUIDELINES:\n"
                "- If 360° spatial scan is available, use it to make CONFIDENT navigation decisions\n"
                "- Spatial scan provides comprehensive environment knowledge - trust this information\n"
                "- When spatial scan shows clear paths, prefer MoveAhead over excessive rotation\n"
                "- Use spatial knowledge to plan efficient exploration routes\n\n"
                "MOVEMENT STRATEGY:\n"
                "- WITH SPATIAL SCAN: Be confident in forward movement when scan indicates clear paths\n"
                "- WITHOUT SPATIAL SCAN: Be more cautious and use rotation for exploration\n"
                "- Balance spatial knowledge with immediate visual confirmation\n"
                "- Avoid excessive rotation when spatial scan shows navigable areas ahead\n\n"
                "OBSTACLE GUIDELINES:\n"
                "- If recent MoveAhead actions failed AND no spatial scan available, avoid MoveAhead\n"
                "- If spatial scan shows clear path but immediate view unclear, try small MoveAhead (0.25-0.5)\n"
                "- Glass walls and transparent barriers: check both spatial scan and current view\n"
                "- When movement fails despite spatial scan, update spatial understanding\n\n"
                "Available actions with configurable parameters:\n"
                "- MoveAhead [magnitude: 0.25-1.0] - Move forward (PREFERRED when spatial scan shows clear path)\n"
                "- MoveBack [magnitude: 0.25-1.0] - Move backward (for retreating from obstacles)\n"
                "- RotateLeft [degrees: 15-180] - Rotate left (for exploration or when blocked)\n"
                "- RotateRight [degrees: 15-180] - Rotate right (for exploration or when blocked)\n"
                "- LookUp [degrees: 15-90] - Look up\n"
                "- LookDown [degrees: 15-90] - Look down\n\n"
                "IMPORTANT: End your response with 'ACTION: [ActionName] [parameter_value]' where:\n"
                "- For movement: 'ACTION: MoveAhead 0.5' (magnitude 0.25-1.0) - PREFERRED with spatial scan\n"
                "- For rotation: 'ACTION: RotateLeft 45' (degrees 15-180) - for exploration or when blocked\n"
                "- For looking: 'ACTION: LookUp 30' (degrees 15-90)\n"
                "Respond with structured reasoning that leverages spatial scan data for confident navigation.",
                role="user"
            )
        ]
    )
    
    max_steps: int = Field(default=12, description="Maximum navigation steps for ReAct")
    max_reasoning_steps: int = Field(default=3, description="Maximum reasoning iterations per step")
    
    def _run(self, *args, **kwargs):
        self.callback.info(agent_id=self.workflow_instance_id, progress='🧠 ReAct Navigation', 
                         message="Starting ReAct-based navigation cycle")
        
        # Get current step count and targets
        step_count = self.stm(self.workflow_instance_id).get("step_count", 0) + 1
        self.stm(self.workflow_instance_id)["step_count"] = step_count
        
        target_object = self.stm(self.workflow_instance_id).get("target_object", "any object")
        target_location = self.stm(self.workflow_instance_id).get("target_location", "anywhere")
        
        self.callback.info(agent_id=self.workflow_instance_id, progress=f'🎯 ReAct Step {step_count}', 
                            message=f"Target: {target_object} at {target_location}")
        
        # Check if max steps reached
        if step_count >= self.max_steps:
            self.callback.info(agent_id=self.workflow_instance_id, progress='⏰ Max Steps Reached', 
                                message=f"Maximum ReAct steps ({self.max_steps}) reached")
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
            self.callback.info_image(self.workflow_instance_id, progress="MAP", image=map_data)
        
        # Execute ReAct cycle
        react_result = self._execute_react_cycle(
            step_count, target_object, target_location, rgb_data
        )
        
        # Store results
        self.stm(self.workflow_instance_id)["last_react_result"] = react_result
        self.stm(self.workflow_instance_id)["goal_achieved"] = react_result.get("goal_achieved", False)
        self.stm(self.workflow_instance_id)["max_steps_reached"] = False
        
        # Cache detected objects for MemoryProcessor
        if "detected_objects" in react_result:
            self.stm(self.workflow_instance_id)["last_detected_objects"] = react_result["detected_objects"]
        
        # Update reasoning history
        self._update_reasoning_history(react_result)
        
        if react_result.get("goal_achieved", False):
            self.callback.info(agent_id=self.workflow_instance_id, progress='🎉 Goal Achieved!', 
                                message=f"ReAct successfully found {target_object}")
            return {"goal_achieved": True}
        else:
            self.callback.info(agent_id=self.workflow_instance_id, progress='✅ ReAct Step Complete', 
                                message=f"Step {step_count}: {react_result.get('action', 'unknown')}")
            return {"goal_achieved": False}
        
    
    
    def _execute_react_cycle(self, step_count: int, target_object: str, target_location: str, rgb_data: str) -> Dict[str, Any]:
        """Execute the full ReAct cycle: Reasoning -> Acting -> Observing."""
        
        # Gather context for reasoning
        context = self._gather_context(rgb_data, target_object, target_location, step_count)
        
        # REASONING Phase
        reasoning_result = self._reasoning_phase(context)
        
        # Check for goal achievement during reasoning
        if reasoning_result.get("goal_achieved", False):
            return {
                "phase": "reasoning",
                "goal_achieved": True,
                "reasoning": reasoning_result.get("reasoning", ""),
                "action": "goal_completed",
                "observation": "Target object found during reasoning phase",
                "detected_objects": context.get("detected_objects", ""),
                "visual_description": context.get("visual_description", ""),
                "map_analysis": context.get("map_analysis", ""),
                "step": step_count,
                "timestamp": datetime.now().isoformat()
            }
        
        # ACTING Phase
        acting_result = self._acting_phase(reasoning_result, context)
        
        # OBSERVING Phase
        observing_result = self._observing_phase(acting_result, context)
        
        return {
            "phase": "complete_react_cycle",
            "goal_achieved": observing_result.get("goal_achieved", False),
            "reasoning": reasoning_result.get("reasoning", ""),
            "action": acting_result.get("action", ""),
            "observation": observing_result.get("observation", ""),
            "execution_success": acting_result.get("success", False),
            "confidence": reasoning_result.get("confidence", 0.5),
            "detected_objects": context.get("detected_objects", ""),
            "visual_description": context.get("visual_description", ""),
            "map_analysis": context.get("map_analysis", ""),
            "step": step_count,
            "timestamp": datetime.now().isoformat()
        }
    
    def _gather_context(self, rgb_data: str, target_object: str, target_location: str, step_count: int) -> Dict[str, Any]:
        """Gather all necessary context for ReAct reasoning including current observations and spatial scan data."""
        
        self.callback.info(agent_id=self.workflow_instance_id, progress='📊 Gathering Context', 
                         message=f"Collecting context for step {step_count}")
        
        # Get map data first
        env_state_json = self.tool_manager.execute(
            tool_name="mcp_thor_get_environment_state",
            args={}
        )
        env_state = json.loads(env_state_json) if isinstance(env_state_json, str) else env_state_json
        map_data = env_state.get("map", "")
        
        # Combined VLM analysis of both RGB and map images
        combined_analysis = self._analyze_scene_and_map_combined(rgb_data, map_data, target_object)
        
        # Get previous reasoning and execution history
        previous_reasoning = self._get_previous_reasoning()
        execution_history = self._get_execution_history()
        
        # Get spatial scan information if available
        spatial_scan_info = self._get_spatial_scan_context()
        
        # Enhanced obstacle detection with spatial context
        obstacle_analysis = self._analyze_obstacles_with_spatial_context(rgb_data, execution_history, spatial_scan_info)
        movement_status = self._validate_movement_history()
        
        context = {
            "target_object": target_object,
            "target_location": target_location,
            "step_count": step_count,
            "max_steps": self.max_steps,
            "env_analysis": combined_analysis.get("environment_analysis", "No environment analysis"),
            "detected_objects": combined_analysis.get("detected_objects", "No objects detected"),
            "visual_description": combined_analysis.get("visual_description", "No visual description"),
            "map_analysis": combined_analysis.get("map_analysis", "No map analysis"),
            "previous_reasoning": previous_reasoning,
            "execution_history": execution_history,
            "spatial_scan_info": spatial_scan_info,
            "obstacle_analysis": obstacle_analysis,
            "movement_status": movement_status,
            "rgb_data": rgb_data
        }
        
        self.callback.info(agent_id=self.workflow_instance_id, progress='✅ Context Ready', 
                         message=f"Combined analysis complete: RGB={'Available' if rgb_data else 'Missing'}, Map={'Available' if map_data else 'Missing'}")
        
        return context

    def _analyze_scene_and_map_combined(self, rgb_data: str, map_data: str, target_object: str) -> Dict[str, Any]:
        """Combined VLM analysis of both RGB and map data in a single call for efficiency."""
        
        if not rgb_data and not map_data:
            return {
                "environment_analysis": "No visual data available",
                "detected_objects": "No objects detected - no visual data",
                "visual_description": "No visual data available",
                "map_analysis": "No map data available"
            }
        
        # Create comprehensive prompt for unified analysis
        combined_prompt = f"""
Please analyze the provided concatenated image for robot navigation. The image contains:
LEFT SIDE: RGB camera view (robot's current visual perspective)
RIGHT SIDE: Occupancy map (bird's eye view of the environment)

Target object to find: {target_object}

Provide a JSON response with exactly these four sections:

{{
    "environment_analysis": "Analyze the RGB scene (left side) for robot navigation. Focus on: navigable paths, obstacles including walls/furniture/barriers, glass walls/windows/transparent barriers that would block movement, and interesting objects. Pay special attention to transparent or reflective surfaces that might block the robot's path.",
    
    "detected_objects": "List all visible objects in the RGB image (left side). Be specific about object types, their positions (left/right/center, near/far), and note if the target object '{target_object}' is visible.",
    
    "visual_description": "Describe the RGB scene (left side) for robot navigation focusing on spatial layout, key objects, visual landmarks, and overall scene composition. Be concise but informative.",
    
    "map_analysis": "Analyze the occupancy map (right side) for robot navigation. Identify: 1) Open navigable areas (light/green regions), 2) Obstacles and walls (dark/black regions), 3) Current robot position if visible, 4) Optimal movement directions, 5) Spatial layout and room structure. Be specific about directions and distances."
}}

Ensure your response is valid JSON format with all four required fields.
"""
        
        #try:
        if True:
            # Convert base64 images to PIL Images and concatenate
            combined_image_b64 = self._create_combined_image(rgb_data, map_data)
            
            if not combined_image_b64:
                # Fallback to individual calls if image processing fails
                return self._fallback_individual_analysis(rgb_data, map_data, target_object)
            
            # Call VLM with combined image
            analysis_json = self.tool_manager.execute(
                tool_name="mcp_vlm-r1_analyze_image",
                args={
                    "image_path": combined_image_b64,
                    "question": combined_prompt
                }
            )
            
            analysis_result = json.loads(analysis_json) if isinstance(analysis_json, str) else analysis_json
            raw_output = analysis_result.get("raw_output", "")
            # Parse the JSON response from VLM
            #try:
            if True:
                # Clean up the response - remove markdown formatting if present
                cleaned_output = raw_output.split("```json")[1].split("```")[0].strip()
                parsed_analysis = json.loads(cleaned_output)
                
                # Validate that all required fields are present
                required_fields = ["environment_analysis", "detected_objects", "visual_description", "map_analysis"]
                for field in required_fields:
                    if field not in parsed_analysis:
                        parsed_analysis[field] = f"Missing {field} from VLM response"
                print (parsed_analysis)
                self.callback.info(agent_id=self.workflow_instance_id, progress='🔍 Combined Analysis', 
                                 message="Successfully parsed combined VLM analysis")
                
                return parsed_analysis
                
            #except json.JSONDecodeError as e:
            #    self.callback.info(agent_id=self.workflow_instance_id, progress='⚠️ Parse Error', 
            #                     message=f"Failed to parse VLM JSON response: {str(e)}")
                
                # Fallback: try to extract information from unstructured response
            #    return self._extract_analysis_from_text(raw_output)
                
        #except Exception as e:
        #    self.callback.info(agent_id=self.workflow_instance_id, progress='❌ Analysis Error', 
        #                     message=f"Combined VLM analysis failed: {str(e)}")
            
        #    # Fallback to individual calls if combined analysis fails
        #    return self._fallback_individual_analysis(rgb_data, map_data, target_object)

    def _create_combined_image(self, rgb_data: str, map_data: str, target_width: int = 800, target_height: int = 400) -> str:
        """Convert base64 images to PIL Images, resize, concatenate horizontally, and return as base64."""
        
        try:
            images = []
            
            # Process RGB image
            if rgb_data:
                # Handle data URL format or plain base64
                if rgb_data.startswith('data:image'):
                    # Extract base64 part from data URL
                    rgb_b64 = rgb_data.split(',')[1]
                else:
                    rgb_b64 = rgb_data
                
                # Decode base64 to image
                rgb_bytes = base64.b64decode(rgb_b64)
                rgb_image = Image.open(io.BytesIO(rgb_bytes))
                
                # Convert to RGB if necessary
                if rgb_image.mode != 'RGB':
                    rgb_image = rgb_image.convert('RGB')
                
                # Resize to half target width to make room for map
                rgb_resized = rgb_image.resize((target_width // 2, target_height), Image.Resampling.LANCZOS)
                images.append(rgb_resized)
                
                self.callback.info(agent_id=self.workflow_instance_id, progress='🖼️ RGB Processed', 
                                 message=f"RGB image resized to {rgb_resized.size}")
            
            # Process Map image
            if map_data:
                # Handle data URL format or plain base64
                if map_data.startswith('data:image'):
                    # Extract base64 part from data URL
                    map_b64 = map_data.split(',')[1]
                else:
                    map_b64 = map_data
                
                # Decode base64 to image
                map_bytes = base64.b64decode(map_b64)
                map_image = Image.open(io.BytesIO(map_bytes))
                
                # Convert to RGB if necessary
                if map_image.mode != 'RGB':
                    map_image = map_image.convert('RGB')
                
                # Resize to half target width to make room for RGB
                map_resized = map_image.resize((target_width // 2, target_height), Image.Resampling.LANCZOS)
                images.append(map_resized)
                
                self.callback.info(agent_id=self.workflow_instance_id, progress='🗺️ Map Processed', 
                                 message=f"Map image resized to {map_resized.size}")
            
            # Handle single image case
            if len(images) == 1:
                # Only one image available, resize to full target width
                single_image = images[0].resize((target_width, target_height), Image.Resampling.LANCZOS)
                combined_image = single_image
            elif len(images) == 2:
                # Concatenate horizontally: RGB on left, Map on right
                combined_image = Image.new('RGB', (target_width, target_height), (255, 255, 255))
                combined_image.paste(images[0], (0, 0))  # RGB on left
                combined_image.paste(images[1], (target_width // 2, 0))  # Map on right
            else:
                # No images to process
                self.callback.info(agent_id=self.workflow_instance_id, progress='❌ No Images', 
                                 message="No valid images to process")
                return ""
            
            # Convert combined image back to base64
            buffer = io.BytesIO()
            combined_image.save(buffer, format='JPEG', quality=85)
            combined_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            # Create data URL format
            combined_data_url = f"data:image/jpeg;base64,{combined_b64}"
            
            self.callback.info(agent_id=self.workflow_instance_id, progress='✅ Images Combined', 
                             message=f"Combined image created: {combined_image.size}, {len(combined_b64)} chars")
            
            return combined_data_url
            
        except Exception as e:
            self.callback.info(agent_id=self.workflow_instance_id, progress='❌ Image Processing Error', 
                             message=f"Failed to process images: {str(e)}")
            return ""

    def _extract_analysis_from_text(self, text_response: str) -> Dict[str, Any]:
        """Extract analysis components from unstructured VLM text response."""
        
        # Try to find sections in the text response
        sections = {
            "environment_analysis": "",
            "detected_objects": "",
            "visual_description": "",
            "map_analysis": ""
        }
        
        # Simple pattern matching to extract sections
        for field in sections.keys():
            pattern = rf'{field}["\']?\s*:\s*["\']?([^"}}]+)'
            match = re.search(pattern, text_response, re.IGNORECASE | re.DOTALL)
            if match:
                sections[field] = match.group(1).strip()
            else:
                sections[field] = f"Could not extract {field} from response"
        
        # If no structured sections found, use the whole response for each field
        if all(not section or section.startswith("Could not extract") for section in sections.values()):
            fallback_text = text_response[:200] + "..." if len(text_response) > 200 else text_response
            sections = {
                "environment_analysis": fallback_text,
                "detected_objects": fallback_text,
                "visual_description": fallback_text,
                "map_analysis": fallback_text
            }
        
        return sections

    def _fallback_individual_analysis(self, rgb_data: str, map_data: str, target_object: str) -> Dict[str, Any]:
        """Fallback to individual VLM calls if combined analysis fails."""
        
        self.callback.info(agent_id=self.workflow_instance_id, progress='🔄 Fallback Mode', 
                         message="Using individual VLM calls as fallback")
        
        result = {}
        
        # Environment analysis
        if rgb_data:
            try:
                env_json = self.tool_manager.execute(
                    tool_name="mcp_vlm-r1_analyze_image",
                    args={
                        "image_path": rgb_data,
                        "question": "Analyze this scene for robot navigation. Focus on navigable paths, obstacles, and barriers."
                    }
                )
                env_result = json.loads(env_json) if isinstance(env_json, str) else env_json
                result["environment_analysis"] = env_result.get("raw_output", "Environment analysis failed")
            except:
                result["environment_analysis"] = "Environment analysis failed"
        else:
            result["environment_analysis"] = "No RGB data for environment analysis"
        
        # Object detection
        if rgb_data:
            try:
                obj_json = self.tool_manager.execute(
                    tool_name="mcp_vlm-r1_detect_objects",
                    args={"image_path": rgb_data}
                )
                obj_result = json.loads(obj_json) if isinstance(obj_json, str) else obj_json
                result["detected_objects"] = str(obj_result.get("raw_output", "No objects found"))
            except:
                result["detected_objects"] = "Object detection failed"
        else:
            result["detected_objects"] = "No RGB data for object detection"
        
        # Visual description
        if rgb_data:
            try:
                desc_json = self.tool_manager.execute(
                    tool_name="mcp_vlm-r1_analyze_image",
                    args={
                        "image_path": rgb_data,
                        "question": "Describe this scene for robot navigation focusing on spatial layout and key objects."
                    }
                )
                desc_result = json.loads(desc_json) if isinstance(desc_json, str) else desc_json
                result["visual_description"] = desc_result.get("raw_output", "Visual description failed")
            except:
                result["visual_description"] = "Visual description failed"
        else:
            result["visual_description"] = "No RGB data for visual description"
        
        # Map analysis
        if map_data:
            try:
                map_json = self.tool_manager.execute(
                    tool_name="mcp_vlm-r1_analyze_image",
                    args={
                        "image_path": map_data,
                        "question": "Analyze this occupancy map for robot navigation. Identify open areas, obstacles, and optimal movement directions."
                    }
                )
                map_result = json.loads(map_json) if isinstance(map_json, str) else map_json
                result["map_analysis"] = map_result.get("raw_output", "Map analysis failed")
            except:
                result["map_analysis"] = "Map analysis failed"
        else:
            result["map_analysis"] = "No map data for analysis"
        
        return result
    
    def _reasoning_phase(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """REASONING: Analyze situation and plan next action using ReAct methodology."""
        
        self.callback.info(agent_id=self.workflow_instance_id, progress='🤔 ReAct REASONING', 
                         message="Analyzing current situation and planning action")
        
        # Check for immediate goal achievement
        goal_achieved = self._check_goal_achievement(
            context["detected_objects"], 
            context["target_object"], 
            context["target_location"]
        )
        
        if goal_achieved:
            return {
                "reasoning": f"GOAL ACHIEVED: Target {context['target_object']} found in current view",
                "planned_action": "goal_completed",
                "confidence": 1.0,
                "goal_achieved": True
            }
        
        # Generate reasoning using LLM with current context
        reasoning_response = self.simple_infer(
            target_object=context["target_object"],
            target_location=context["target_location"],
            step_count=context["step_count"],
            max_steps=context["max_steps"],
            env_analysis=context["env_analysis"],
            detected_objects=context["detected_objects"],
            visual_description=context["visual_description"],
            map_analysis=context["map_analysis"],
            previous_reasoning=context["previous_reasoning"],
            execution_history=context["execution_history"],
            spatial_scan_info=context["spatial_scan_info"],
            obstacle_analysis=context["obstacle_analysis"],
            movement_status=context["movement_status"]
        )
        
        reasoning_content = reasoning_response["choices"][0]["message"]["content"]
        
        # Parse reasoning and extract planned action
        parsed_reasoning = self._parse_reasoning_response(reasoning_content)
        
        self.callback.info(agent_id=self.workflow_instance_id, progress='💭 Reasoning Complete', 
                            message=f"Planned action: {parsed_reasoning.get('planned_action', 'unknown')}")
        
        return parsed_reasoning
        
    
    
    def _acting_phase(self, reasoning_result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """ACTING: Execute the planned action with monitoring."""
        
        planned_action = reasoning_result.get("planned_action", "MoveAhead")
        action_parameter = reasoning_result.get("action_parameter", 0.5)
        reasoning = reasoning_result.get("reasoning", "")
        
        self.callback.info(agent_id=self.workflow_instance_id, progress='⚡ ReAct ACTING', 
                         message=f"Executing: {planned_action} {action_parameter}")
        
        # Execute the planned action with parameter
        execution_result = self._execute_action(planned_action, action_parameter)
        
        return {
            "action": planned_action,
            "action_parameter": action_parameter,
            "reasoning": reasoning,
            "success": execution_result.get("success", False),
            "result": execution_result.get("result", ""),
            "timestamp": datetime.now().isoformat()
        }
        
      
    
    def _observing_phase(self, acting_result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimized observing phase using single comprehensive MCP call
        """
        self.callback.info(agent_id=self.workflow_instance_id, progress='👁️ Observing Phase', 
                         message="Analyzing observation results with single comprehensive call...")
        
        #try:
        # Get new sensor data after action
        rgb_data = self.tool_manager.execute(tool_name="mcp_thor_get_environment_state", args={})
        if isinstance(rgb_data, str):
            rgb_data_dict = json.loads(rgb_data)
        else:
            rgb_data_dict = rgb_data
        new_rgb_data = rgb_data_dict.get("observation", {}).get("rgb", "")

        new_map_data = rgb_data_dict.get("map", "")
        
        # Display new observation if available
        if new_rgb_data:
            self.callback.info_image(self.workflow_instance_id, progress="Observation", image=new_rgb_data)
        else:
            self.callback.info(agent_id=self.workflow_instance_id, progress='⚠️ No Observation Data', 
                             message="No RGB data available after action")
        
        # Display new map if available
        if new_map_data:
            self.callback.info_image(self.workflow_instance_id, progress="Map", image=new_map_data)
        else:
            self.callback.info(agent_id=self.workflow_instance_id, progress='⚠️ No Map Data', 
                             message="No map data available after action")
        
        # Single comprehensive analysis instead of multiple separate calls
        comprehensive_analysis = self._analyze_scene_comprehensive(
            new_rgb_data, 
            context["target_object"], 
            context["target_location"]
        )
        print ("comprehensive_analysis:",comprehensive_analysis)
        # Extract results from comprehensive analysis
        new_objects = comprehensive_analysis["objects"]
        new_visual_description = comprehensive_analysis["visual_description"]
        goal_achieved = comprehensive_analysis["goal_achieved"]
        navigation_analysis = comprehensive_analysis.get("navigation_analysis", "")
        
        # Generate observation analysis using the comprehensive results
        observation_prompt = f"""
        OBSERVATION ANALYSIS:
        Action Executed: {acting_result.get('action', 'unknown')}
        Action Success: {acting_result.get('success', False)}
        Previous Objects: {context['detected_objects']}
        New Objects: {new_objects}
        Previous Visual Scene: {context['visual_description']}
        New Visual Scene: {new_visual_description}
        Navigation Analysis: {navigation_analysis}
        Map Context: {context.get('map_analysis', 'No map data')}
        Target: {context['target_object']} at {context['target_location']}
        
        Analyze what changed visually and spatially after this action. 
        How does this movement relate to the overall spatial layout? What does this mean for navigation strategy?
        """
        
        observation_response = self.llm.generate([
            {"role": "user", "content": observation_prompt}
        ])
        
        observation_analysis = observation_response["choices"][0]["message"].get("content", "")
        
        self.callback.info(agent_id=self.workflow_instance_id, progress='📊 Observation Analysis', 
                            message=observation_analysis)
        
        return {
            "observation": observation_analysis,
            "goal_achieved": goal_achieved,
            "new_objects": new_objects,
            "new_visual_description": new_visual_description,
            "navigation_analysis": navigation_analysis,
            "action_success": acting_result.get("success", False),
            "comprehensive_analysis_success": comprehensive_analysis["analysis_success"],
            "timestamp": datetime.now().isoformat()
        }
        
        #except Exception as e:
        #    self.callback.info(agent_id=self.workflow_instance_id, progress='❌ Observation Error', 
        #                     message=f"Failed to analyze observation: {str(e)}")
        #    return {
        #        "observation": f"Observation analysis failed: {str(e)}",
        #        "goal_achieved": False,
        #        "new_objects": "Error detecting objects",
        #        "new_visual_description": "Error generating visual description",
        #        "action_success": acting_result.get("success", False),
        #        "timestamp": datetime.now().isoformat()
        #    }
            

    
    def _parse_reasoning_response(self, reasoning_content: str) -> Dict[str, Any]:
        """Parse the LLM reasoning response to extract action, parameters, and confidence."""
        
        self.callback.info(agent_id=self.workflow_instance_id, progress='🔍 Parsing Response', 
                         message=f"LLM Response: {reasoning_content}...")
        
        # Extract planned action with parameters - updated patterns
        action_patterns = [
            r'ACTION:\s*(\w+)\s+([0-9.]+)',  # ACTION: MoveAhead 0.5
            r'ACTION:\s*(\w+)',              # ACTION: MoveAhead (fallback)
            r'action["\']?\s*:\s*["\']?(\w+)\s+([0-9.]+)',
            r'action["\']?\s*:\s*["\']?(\w+)',
            r'planned_action["\']?\s*:\s*["\']?(\w+)\s+([0-9.]+)',
            r'planned_action["\']?\s*:\s*["\']?(\w+)',
            r'I will\s+(\w+)\s+([0-9.]+)',
            r'I will\s+(\w+)',
            r'should\s+(\w+)\s+([0-9.]+)',
            r'should\s+(\w+)',
            r'execute\s+(\w+)\s+([0-9.]+)',
            r'execute\s+(\w+)'
        ]
        
        planned_action = "MoveAhead"  # default
        action_parameter = None
        matched_pattern = None
        
        for i, pattern in enumerate(action_patterns):
            match = re.search(pattern, reasoning_content, re.IGNORECASE)
            if match:
                action_candidate = match.group(1)
                parameter_candidate = match.group(2) if len(match.groups()) >= 2 else None
                
                # Validate that it's a known action
                valid_actions = ["MoveAhead", "MoveBack", "RotateLeft", "RotateRight", "LookUp", "LookDown"]
                if action_candidate in valid_actions:
                    planned_action = action_candidate
                    if parameter_candidate:
                        action_parameter = float(parameter_candidate)
                    matched_pattern = f"Pattern {i}: {pattern}"
                    break
        
        # Set default parameters if not specified
        if action_parameter is None:
            if planned_action in ["MoveAhead", "MoveBack"]:
                action_parameter = 0.5  # Default magnitude
            elif planned_action in ["RotateLeft", "RotateRight"]:
                action_parameter = 90   # Default rotation degrees
            elif planned_action in ["LookUp", "LookDown"]:
                action_parameter = 30   # Default look degrees
        
        # Validate parameter ranges
        if planned_action in ["MoveAhead", "MoveBack"]:
            action_parameter = max(0.25, min(1.0, action_parameter))  # Clamp magnitude
        elif planned_action in ["RotateLeft", "RotateRight"]:
            action_parameter = max(15, min(180, action_parameter))    # Clamp rotation degrees
        elif planned_action in ["LookUp", "LookDown"]:
            action_parameter = max(15, min(90, action_parameter))     # Clamp look degrees
        
        # Extract confidence
        confidence_match = re.search(r'confidence["\']?\s*:\s*([0-9.]+)', reasoning_content, re.IGNORECASE)
        confidence = float(confidence_match.group(1)) if confidence_match else 0.7
        
        self.callback.info(agent_id=self.workflow_instance_id, progress='🎯 Action Extracted', 
                         message=f"Action: {planned_action} {action_parameter} (via {matched_pattern or 'default'})")
        
        return {
            "reasoning": reasoning_content,
            "planned_action": planned_action,
            "action_parameter": action_parameter,
            "confidence": confidence,
            "goal_achieved": False,
            "matched_pattern": matched_pattern
        }
    
    def _analyze_environment(self, rgb_data: str) -> str:
        """Enhanced environment analysis with obstacle and glass wall detection."""
    
        if not rgb_data:
            return "No visual data available"
        
        analysis_json = self.tool_manager.execute(
            tool_name="mcp_vlm-r1_analyze_image",
            args={
                "image_path": rgb_data,
                "question": "Analyze this scene for robot navigation. Focus on: 1) Navigable paths and open areas, 2) Obstacles including walls, furniture, and barriers, 3) Glass walls, windows, or transparent barriers that would block movement, 4) Interesting objects. Pay special attention to any transparent or reflective surfaces that might block the robot's path. Be specific about what would prevent forward movement."
            }
        )
        analysis_result = json.loads(analysis_json)
        return analysis_result.get("raw_output", "Analysis failed")
        
        
    def _detect_objects(self, rgb_data: str) -> str:
        """Fast object detection."""
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
            
        
    
    def _check_goal_achievement(self, detected_objects: str, target_object: str, target_location: str) -> bool:
        """Quick goal verification."""
            # Simple keyword matching for speed
        detected_lower = detected_objects.lower()
        target_lower = target_object.lower()
        
        # Check if target object is mentioned in detected objects
        if target_lower in detected_lower or "any object" in target_lower:
            # Additional verification with LLM for accuracy
            verification_prompt = f"""
            Detected objects: {detected_objects}
            Target: {target_object} at {target_location}
            
            Is the target object clearly present and visible? Answer only: YES or NO
            """
            
            response = self.llm.generate([
                {"role": "user", "content": verification_prompt}
            ])
            
            result = response["choices"][0]["message"].get("content", "").strip().upper()
            return "YES" in result
        
        return False
       
    
    def _execute_action(self, action_name: str, action_parameter: float) -> Dict[str, Any]:
        """Execute the planned action with configurable parameters."""
        # Map action names to THOR actions with dynamic parameters
        if action_name in ["MoveAhead", "MoveBack"]:
            thor_action = {"action": action_name, "magnitude": action_parameter}
        elif action_name in ["RotateLeft", "RotateRight"]:
            thor_action = {"action": action_name, "degrees": action_parameter}
        elif action_name in ["LookUp", "LookDown"]:
            thor_action = {"action": action_name, "degrees": action_parameter}
        else:
            # Fallback for unknown actions
            thor_action = {"action": "MoveAhead", "magnitude": 0.25}
        
        self.callback.info(agent_id=self.workflow_instance_id, progress='🎮 Executing Action', 
                         message=f"THOR Action: {thor_action}")
        
        try:
            # Execute action in THOR
            result = self.tool_manager.execute(
                tool_name="mcp_thor_step",
                args=thor_action
            )
            
            # Parse the result to check for success
            if isinstance(result, str):
                try:
                    result_data = json.loads(result)
                except:
                    result_data = {"result": {"code": "1", "message": "Failed to parse result"}, "position": [0, 0, 0]}
            else:
                result_data = result
            
            # Extract the actual result from the THOR response structure
            thor_result = result_data.get("result", {})
            position = result_data.get("position", [0, 0, 0])
            
            # Check if the action was successful (THOR uses code "0" for success)
            action_success = thor_result.get("code") == "0" if isinstance(thor_result, dict) else False
            
            # Track position changes for debugging
            previous_position = self.stm(self.workflow_instance_id).get("last_position", [0, 0, 0])
            current_position = position if position else [0, 0, 0]
            
            # Enhanced position change detection
            position_changed = False
            if len(current_position) >= 3 and len(previous_position) >= 3:
                if action_name in ["MoveAhead", "MoveBack"]:
                    # For movement actions, check X and Z coordinates (horizontal movement)
                    position_changed = (
                        abs(current_position[0] - previous_position[0]) > 0.01 or
                        abs(current_position[2] - previous_position[2]) > 0.01
                    )
                elif action_name in ["RotateLeft", "RotateRight"]:
                    # For rotation actions, check Y coordinate (rotation angle)
                    position_changed = abs(current_position[1] - previous_position[1]) > 5
                else:
                    # For other actions (LookUp, LookDown), position change is less relevant
                    position_changed = True
            
            # Enhanced failure detection for movement actions
            movement_blocked = False
            if action_name in ["MoveAhead", "MoveBack"]:
                # Movement is considered blocked if:
                # 1. THOR reports failure (code != "0"), OR
                # 2. THOR reports success but position didn't actually change
                movement_blocked = not action_success or not position_changed
                
                if movement_blocked:
                    self.callback.info(agent_id=self.workflow_instance_id, progress='🚫 Movement Blocked', 
                                     message=f"Movement blocked: THOR success={action_success}, Position changed={position_changed}")
            
            # Store current position for next comparison
            self.stm(self.workflow_instance_id)["last_position"] = current_position
            
            # Enhanced logging with obstacle detection
            status_msg = "SUCCESS" if action_success else "FAILED"
            if movement_blocked:
                status_msg = "BLOCKED"
            
            self.callback.info(agent_id=self.workflow_instance_id, progress='📊 Action Result', 
                             message=f"Action {action_name} {action_parameter}: {status_msg} - {thor_result.get('message', 'No message')} - Position changed: {position_changed}")
            
            return {
                "success": action_success and not movement_blocked,  # Consider blocked movement as failure
                "result": result_data,
                "thor_result": thor_result,
                "position": position,
                "position_changed": position_changed,
                "movement_blocked": movement_blocked,
                "action_executed": action_name,
                "action_parameter": action_parameter,
                "thor_action": thor_action
            }
            
        except Exception as e:
            self.callback.info(agent_id=self.workflow_instance_id, progress='❌ Action Error', 
                             message=f"Failed to execute {action_name} {action_parameter}: {str(e)}")
            return {
                "success": False,
                "result": f"Execution error: {str(e)}",
                "thor_result": {"code": "1", "message": str(e)},
                "position": [0, 0, 0],
                "position_changed": False,
                "movement_blocked": False,
                "action_executed": action_name,
                "action_parameter": action_parameter,
                "thor_action": thor_action
            }
            
        
    
    def _get_previous_reasoning(self) -> str:
        """Get previous reasoning for context."""
        reasoning_history = self.stm(self.workflow_instance_id).get("reasoning_history", [])
        if not reasoning_history:
            return "No previous reasoning available"
        
        # Get last 2 reasoning steps for context
        recent_reasoning = reasoning_history[-2:]
        summary = "Previous reasoning:\n"
        for i, reasoning in enumerate(recent_reasoning):
            summary += f"Step {reasoning.get('step', 'unknown')}: {reasoning.get('reasoning', 'No reasoning')[:100]}...\n"
        
        return summary
    
    def _get_execution_history(self) -> str:
        """Get execution history for context."""
        react_history = self.stm(self.workflow_instance_id).get("react_history", [])
        if not react_history:
            return "No previous execution history"
        
        # Get last 3 executions
        recent_history = react_history[-3:]
        summary = "Recent actions:\n"
        for i, result in enumerate(recent_history):
            action = result.get("action", "unknown")
            action_parameter = result.get("action_parameter", "")
            success = result.get("execution_success", False)
            summary += f"Action {i+1}: {action} {action_parameter} ({'Success' if success else 'Failed'})\n"
        
        return summary
    
    def _update_reasoning_history(self, react_result: Dict[str, Any]):
        """Update reasoning history for future context."""
        reasoning_history = self.stm(self.workflow_instance_id).get("reasoning_history", [])
        reasoning_history.append({
            "step": react_result.get("step", 0),
            "reasoning": react_result.get("reasoning", ""),
            "action": react_result.get("action", ""),
            "action_parameter": react_result.get("action_parameter", ""),
            "success": react_result.get("execution_success", False),
            "visual_description": react_result.get("visual_description", ""),
            "map_analysis": react_result.get("map_analysis", ""),
            "timestamp": react_result.get("timestamp", "")
        })
        
        # Keep only last 5 reasoning steps for efficiency
        self.stm(self.workflow_instance_id)["reasoning_history"] = reasoning_history[-5:]
        
        # Update ReAct history
        react_history = self.stm(self.workflow_instance_id).get("react_history", [])
        react_history.append(react_result)
        self.stm(self.workflow_instance_id)["react_history"] = react_history[-5:]
    
    def _get_spatial_scan_context(self) -> Dict[str, Any]:
        """Get spatial scan information for navigation context."""
        
        spatial_scan_complete = self.stm(self.workflow_instance_id).get("spatial_scan_complete", False)
        
        if not spatial_scan_complete:
            return {
                "scan_available": False,
                "message": "No spatial scan available - navigation will be more cautious"
            }
        
        spatial_analysis = self.stm(self.workflow_instance_id).get("spatial_analysis", {})
        navigation_strategy = self.stm(self.workflow_instance_id).get("navigation_strategy", "")
        
        return {
            "scan_available": True,
            "spatial_layout": spatial_analysis.get("spatial_layout", ""),
            "navigable_areas": spatial_analysis.get("navigable_areas", ""),
            "obstacles": spatial_analysis.get("obstacles", ""),
            "points_of_interest": spatial_analysis.get("points_of_interest", ""),
            "navigation_strategy": navigation_strategy,
            "message": "360° spatial scan completed - confident navigation enabled"
        }
    
    def _analyze_obstacles_with_spatial_context(self, rgb_data: str, execution_history: str, spatial_info: Dict[str, Any]) -> str:
        """Enhanced obstacle analysis that considers spatial scan context."""
        
        if not rgb_data:
            return "No visual data available for obstacle analysis"
        
        try:
            # Base obstacle detection
            base_analysis = self._analyze_obstacles(rgb_data, execution_history)
            
            # If spatial scan is available, enhance the analysis
            if spatial_info.get("scan_available", False):
                spatial_context = f"""
SPATIAL SCAN CONTEXT:
- Navigable Areas: {spatial_info.get('navigable_areas', 'Unknown')}
- Known Obstacles: {spatial_info.get('obstacles', 'Unknown')}
- Navigation Strategy: {spatial_info.get('navigation_strategy', 'Unknown')}

Based on the 360° spatial scan, the robot has comprehensive knowledge of the environment layout.
This should increase confidence in movement decisions when paths are known to be clear."""
                
                enhanced_prompt = f"""Analyze this current view for immediate obstacles, considering the spatial scan context:

CURRENT VIEW ANALYSIS: {base_analysis}

{spatial_context}

ENHANCED ASSESSMENT:
Given the spatial scan information, provide an updated obstacle assessment that balances:
1. Immediate visual obstacles in current view
2. Spatial knowledge from 360° scan
3. Confidence level for forward movement

If the spatial scan indicates clear paths in this direction and current view doesn't show immediate obstacles, 
recommend CONFIDENT FORWARD MOVEMENT. If obstacles are detected, be appropriately cautious."""

                enhanced_json = self.tool_manager.execute(
                    tool_name="mcp_vlm-r1_analyze_image",
                    args={
                        "image_path": rgb_data,
                        "question": enhanced_prompt
                    }
                )
                enhanced_result = json.loads(enhanced_json)
                return enhanced_result.get("raw_output", base_analysis)
            
            return base_analysis
            
        except Exception as e:
            return f"Enhanced obstacle analysis error: {str(e)}"
    
    def _analyze_obstacles(self, rgb_data: str, execution_history: str) -> str:
        """Analyze obstacles including transparent barriers like glass walls."""
        if not rgb_data:
            return "No visual data available for obstacle analysis"
        
        try:
            # Enhanced obstacle detection prompt
            obstacle_prompt = """Analyze this image for navigation obstacles, paying special attention to:

1. TRANSPARENT BARRIERS: Glass walls, windows, glass doors, or transparent panels that would block robot movement
2. PHYSICAL OBSTACLES: Walls, furniture, objects blocking the path ahead
3. BLOCKED PATHS: Any barriers that would prevent forward movement
4. OPEN AREAS: Clear navigable space where the robot can move

Look carefully for reflections, transparent surfaces, or glass that might not be immediately obvious.
Consider the robot's perspective - what would actually block forward movement?

Provide a clear assessment: Is the forward path BLOCKED or OPEN? If blocked, what type of obstacle?"""

            analysis_json = self.tool_manager.execute(
                tool_name="mcp_vlm-r1_analyze_image",
                args={
                    "image_path": rgb_data,
                    "question": obstacle_prompt
                }
            )
            analysis_result = json.loads(analysis_json)
            obstacle_analysis = analysis_result.get("raw_output", "Obstacle analysis failed")
            
            # Enhanced analysis if we detect potential blocking
            if "glass" in obstacle_analysis.lower() or "window" in obstacle_analysis.lower() or "blocked" in obstacle_analysis.lower():
                # Additional check with execution history
                recent_failures = "failed" in execution_history.lower() or "moveahead" in execution_history.lower()
                if recent_failures:
                    obstacle_analysis += "\n\nWARNING: Recent movement failures detected combined with potential barriers. Forward movement is likely BLOCKED."
            
            return obstacle_analysis
            
        except Exception as e:
            return f"Obstacle analysis error: {str(e)}"
    
    def _validate_movement_history(self) -> str:
        """Validate recent movement attempts and detect if robot is stuck."""
        react_history = self.stm(self.workflow_instance_id).get("react_history", [])
        
        if not react_history:
            return "No movement history available"
        
        # Analyze last 3-5 actions for patterns
        recent_actions = react_history[-5:]
        move_attempts = []
        failed_forward_moves = 0
        consecutive_failures = 0
        stuck_indicators = []
        
        for i, action in enumerate(recent_actions):
            action_name = action.get("action", "")
            success = action.get("execution_success", False)
            
            if action_name == "MoveAhead":
                move_attempts.append({"success": success, "step": i})
                if not success:
                    failed_forward_moves += 1
                    consecutive_failures += 1
                    stuck_indicators.append(f"Failed MoveAhead at step {i}")
                else:
                    consecutive_failures = 0
        
        # Detect repeated actions (sign of being stuck)
        action_names = [action.get("action", "") for action in recent_actions]
        repeated_moves = action_names.count("MoveAhead")
        
        # Build status message
        if failed_forward_moves >= 2:
            status = "MOVEMENT SEVERELY BLOCKED"
            message = f"{failed_forward_moves} recent MoveAhead actions failed. Robot is blocked by obstacle(s). STRONG RECOMMENDATION: Try RotateLeft/Right to find alternate path, or MoveBack to retreat."
        elif failed_forward_moves == 1 and repeated_moves >= 2:
            status = "MOVEMENT POTENTIALLY BLOCKED"
            message = f"1 recent MoveAhead failed and {repeated_moves} total MoveAhead attempts detected. Possible obstacle ahead. RECOMMENDATION: Verify path is clear before moving forward, consider rotation."
        elif repeated_moves >= 3 and consecutive_failures > 0:
            status = "MOVEMENT PATTERN WARNING"
            message = f"Detected {repeated_moves} MoveAhead attempts with recent failures. Robot may be stuck in a loop. RECOMMENDATION: Try different action (rotate or look around)."
        elif consecutive_failures >= 2:
            status = "CONSECUTIVE MOVEMENT FAILURES"
            message = f"{consecutive_failures} consecutive movement failures detected. Robot is likely blocked. RECOMMENDATION: Rotate to find new path."
        elif move_attempts:
            successful_moves = sum(1 for attempt in move_attempts if attempt["success"])
            total_moves = len(move_attempts)
            status = "MOVEMENT OK"
            message = f"Movement status acceptable: {successful_moves}/{total_moves} recent movements successful."
        else:
            status = "NO RECENT MOVEMENT DATA"
            message = "No recent movement attempts to analyze."
        
        # Add stuck indicators if any
        if stuck_indicators:
            message += f" Stuck indicators: {', '.join(stuck_indicators)}"
        
        return f"{status}: {message}"

    def _generate_visual_description(self, rgb_data: str) -> str:
        """Generate a visual description of the current scene."""
        if not rgb_data:
            return "No visual data available for description"
        
        description_prompt = "Describe the current scene for robot navigation focusing on spatial layout and key objects."
        description_response = self.tool_manager.execute(
            tool_name="mcp_vlm-r1_analyze_image",
            args={
                "image_path": rgb_data,
                "question": description_prompt
            }
        )
        description_content = description_response.get("raw_output", "Visual description failed")
        
        self.callback.info(agent_id=self.workflow_instance_id, progress='📋 Visual Description', 
                            message=description_content)
        
        return description_content

    def _analyze_scene_comprehensive(self, rgb_data: str, target_object: str, target_location: str) -> Dict[str, Any]:
        """Comprehensive scene analysis with a single MCP call to get all information at once."""
        if not rgb_data:
            return {
                "objects": "No new observation",
                "visual_description": "No new visual data", 
                "goal_achieved": False,
                "analysis_success": False
            }
        
        try:
            # Single comprehensive MCP call that gets all information at once
            comprehensive_prompt = f"""
            Analyze this robot navigation scene comprehensively and provide ALL of the following information:

            1. OBJECT DETECTION: List all visible objects in the scene with their locations and descriptions.

            2. VISUAL DESCRIPTION: Describe the current scene for robot navigation, focusing on spatial layout, key objects, and navigable areas.

            3. GOAL ACHIEVEMENT: Check if the target object "{target_object}" at "{target_location}" is clearly present and visible in this scene.

            4. NAVIGATION ANALYSIS: Analyze navigable paths, obstacles, and movement opportunities.

            Please structure your response as follows:
            OBJECTS: [detailed object list]
            VISUAL_DESCRIPTION: [spatial layout description]
            GOAL_ACHIEVED: [YES/NO - is target object clearly visible]
            NAVIGATION: [path analysis and recommendations]
            """
            
            analysis_json = self.tool_manager.execute(
                tool_name="mcp_vlm-r1_analyze_image",
                args={
                    "image_path": rgb_data,
                    "question": comprehensive_prompt
                }
            )
            analysis_result = json.loads(analysis_json)
            raw_response = analysis_result.get("raw_output", "")
            print (raw_response)
            # Parse the structured response
            objects = self._extract_section(raw_response, "OBJECTS:")
            visual_description = self._extract_section(raw_response, "VISUAL_DESCRIPTION:")
            goal_check = self._extract_section(raw_response, "GOAL_ACHIEVED:")
            navigation_analysis = self._extract_section(raw_response, "NAVIGATION:")
            
            # Determine goal achievement
            goal_achieved = "YES" in goal_check.upper() if goal_check else False
            
            # If goal achievement is unclear, do additional verification
            if not goal_achieved and target_object.lower() in objects.lower():
                verification_prompt = f"""
                Detected objects: {objects}
                Target: {target_object} at {target_location}
                
                Is the target object clearly present and visible? Answer only: YES or NO
                """
                
                verification_response = self.llm.generate([
                    {"role": "user", "content": verification_prompt}
                ])
                
                verification_result = verification_response["choices"][0]["message"].get("content", "").strip().upper()
                goal_achieved = "YES" in verification_result
            
            return {
                "objects": objects or "No objects detected",
                "visual_description": visual_description or "No visual description available",
                "goal_achieved": goal_achieved,
                "navigation_analysis": navigation_analysis or "No navigation analysis available",
                "analysis_success": True,
                "raw_response": raw_response
            }
            
        except Exception as e:
            self.callback.info(agent_id=self.workflow_instance_id, progress='❌ Comprehensive Analysis Error', 
                             message=f"Failed comprehensive analysis: {str(e)}")
            return {
                "objects": "Analysis failed",
                "visual_description": "Analysis failed", 
                "goal_achieved": False,
                "navigation_analysis": "Analysis failed",
                "analysis_success": False,
                "error": str(e)
            }

    def _extract_section(self, text: str, section_header: str) -> str:
        """Extract a specific section from structured text response."""
        if not text or not section_header:
            return ""
        
        # Find the section header
        start_idx = text.find(section_header)
        if start_idx == -1:
            return ""
        
        # Move to content after header
        start_idx += len(section_header)
        
        # Find the next section header or end of text
        next_headers = ["OBJECTS:", "VISUAL_DESCRIPTION:", "GOAL_ACHIEVED:", "NAVIGATION:"]
        end_idx = len(text)
        
        for header in next_headers:
            if header != section_header:
                next_pos = text.find(header, start_idx)
                if next_pos != -1 and next_pos < end_idx:
                    end_idx = next_pos
        
        # Extract and clean the section content
        content = text[start_idx:end_idx].strip()
        return content 