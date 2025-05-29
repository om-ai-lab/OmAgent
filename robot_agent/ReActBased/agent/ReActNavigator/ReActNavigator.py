from omagent_core.omagent4agent import *
import json
import re
from datetime import datetime
from typing import List, Dict, Any

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
        
        # Fast environment analysis
        env_analysis = self._analyze_environment(rgb_data)
        
        # Quick object detection
        detected_objects = self._detect_objects(rgb_data)
        
        # Generate visual description for current context
        visual_description = self._generate_visual_description(rgb_data)
        
        # Get map data and analysis
        map_analysis = self._analyze_map_data()
        
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
            "env_analysis": env_analysis,
            "detected_objects": detected_objects,
            "visual_description": visual_description,
            "map_analysis": map_analysis,
            "previous_reasoning": previous_reasoning,
            "execution_history": execution_history,
            "spatial_scan_info": spatial_scan_info,
            "obstacle_analysis": obstacle_analysis,
            "movement_status": movement_status,
            "rgb_data": rgb_data
        }
        
        self.callback.info(agent_id=self.workflow_instance_id, progress='✅ Context Ready', 
                         message=f"Context gathered: RGB={'Available' if rgb_data else 'Missing'}, Spatial={'Available' if spatial_scan_info['scan_available'] else 'Missing'}")
        
        return context
    
    def _generate_visual_description(self, rgb_data: str) -> str:
        """Generate visual description for current navigation context."""
        if not rgb_data:
            return "No visual data available"
        
        analysis_json = self.tool_manager.execute(
            tool_name="mcp_vlm-r1_analyze_image",
            args={
                "image_path": rgb_data,
                "question": "Describe this scene for robot navigation focusing on spatial layout, key objects, and visual landmarks. Be concise."
            }
        )
        analysis_result = json.loads(analysis_json)
        return analysis_result.get("raw_output", "Visual analysis failed")
        
       
    
    def _analyze_map_data(self) -> str:
        """Analyze map data for spatial understanding and navigation planning."""
        # Get current environment state including map
        env_state_json = self.tool_manager.execute(
            tool_name="mcp_thor_get_environment_state",
            args={}
        )
        env_state = json.loads(env_state_json) if isinstance(env_state_json, str) else env_state_json
        map_data = env_state.get("map", "")
        
        if not map_data:
            return "No map data available"
        
        # Analyze map using VLM for spatial understanding
        map_analysis_json = self.tool_manager.execute(
            tool_name="mcp_vlm-r1_analyze_image",
            args={
                "image_path": map_data,
                "question": "Analyze this occupancy map for robot navigation. Identify: 1) Open navigable areas (light/green), 2) Obstacles (dark/black), 3) Current robot position, 4) Optimal movement directions, 5) Spatial layout and room structure. Be specific about directions and distances."
            }
        )
        map_analysis_result = json.loads(map_analysis_json)
        return map_analysis_result.get("raw_output", "Map analysis failed")
            
        
    
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
        """OBSERVING: Analyze results and update understanding."""
        
        self.callback.info(agent_id=self.workflow_instance_id, progress='👁️ ReAct OBSERVING', 
                         message="Analyzing action results")
        
        try:
            # Get new environment state after action
            self.callback.info(agent_id=self.workflow_instance_id, progress='🔍 Getting New State', 
                             message="Retrieving environment state after action")
            
            env_state_json = self.tool_manager.execute(
                tool_name="mcp_thor_get_environment_state",
                args={}
            )
            
            if isinstance(env_state_json, str):
                try:
                    env_state = json.loads(env_state_json)
                except json.JSONDecodeError as e:
                    self.callback.info(agent_id=self.workflow_instance_id, progress='⚠️ JSON Parse Error', 
                                     message=f"Failed to parse environment state: {str(e)}")
                    env_state = {}
            else:
                env_state = env_state_json
            
            new_rgb_data = env_state.get("observation", {}).get("rgb", "")
            new_map_data = env_state.get("map", "")
            
            self.callback.info(agent_id=self.workflow_instance_id, progress='📊 State Retrieved', 
                             message=f"RGB: {'Available' if new_rgb_data else 'Missing'}, Map: {'Available' if new_map_data else 'Missing'}")
            
            # Display new view and map after action
            if new_rgb_data:
                self.callback.info_image(self.workflow_instance_id, progress="RGB", image=new_rgb_data)
            else:
                self.callback.info(agent_id=self.workflow_instance_id, progress='⚠️ No RGB Data', 
                                 message="No RGB data available after action")
                
            if new_map_data:
                self.callback.info_image(self.workflow_instance_id, progress="Map", image=new_map_data)
            else:
                self.callback.info(agent_id=self.workflow_instance_id, progress='⚠️ No Map Data', 
                                 message="No map data available after action")
            
            # Quick analysis of new state
            new_objects = self._detect_objects(new_rgb_data) if new_rgb_data else "No new observation"
            new_visual_description = self._generate_visual_description(new_rgb_data) if new_rgb_data else "No new visual data"
            
            # Check if goal achieved after action
            goal_achieved = self._check_goal_achievement(
                new_objects, 
                context["target_object"], 
                context["target_location"]
            )
            
            # Generate observation analysis
            observation_prompt = f"""
            OBSERVATION ANALYSIS:
            Action Executed: {acting_result.get('action', 'unknown')}
            Action Success: {acting_result.get('success', False)}
            Previous Objects: {context['detected_objects']}
            New Objects: {new_objects}
            Previous Visual Scene: {context['visual_description']}
            New Visual Scene: {new_visual_description}
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
                                message=observation_analysis[:150] + "..." if len(observation_analysis) > 150 else observation_analysis)
            
            return {
                "observation": observation_analysis,
                "goal_achieved": goal_achieved,
                "new_objects": new_objects,
                "new_visual_description": new_visual_description,
                "action_success": acting_result.get("success", False),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.callback.info(agent_id=self.workflow_instance_id, progress='❌ Observation Error', 
                             message=f"Failed to analyze observation: {str(e)}")
            return {
                "observation": f"Observation analysis failed: {str(e)}",
                "goal_achieved": False,
                "new_objects": "Error detecting objects",
                "new_visual_description": "Error generating visual description",
                "action_success": acting_result.get("success", False),
                "timestamp": datetime.now().isoformat()
            }
            

    
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
        return analysis_result.get("result", "Analysis failed")
        
        
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