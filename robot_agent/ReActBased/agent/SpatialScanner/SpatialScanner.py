from omagent_core.omagent4agent import *
import json
import math
from datetime import datetime
from typing import List, Dict, Any

@registry.register_worker()
class SpatialScanner(BaseWorker, BaseLLMBackend):
    """
    Spatial scanner that performs a 360-degree scan to gather comprehensive spatial information
    before navigation begins. This helps the robot understand the full environment layout
    and plan better navigation strategies.
    """
    llm: OpenaiGPTLLM
    tool_manager: ToolManager
    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_template(
                "You are a spatial analysis expert for robot navigation. Analyze multiple views from a 360-degree scan "
                "to create a comprehensive understanding of the environment layout, navigable areas, obstacles, and points of interest.",
                role="system"
            ),
            PromptTemplate.from_template(
                "SPATIAL SCAN ANALYSIS:\n"
                "Target: {{target_object}} at {{target_location}}\n"
                "Scan Views: {{scan_count}} views captured\n"
                "View Data: {{view_data}}\n"
                "Map Analysis: {{map_analysis}}\n\n"
                "Based on this 360-degree scan, provide:\n"
                "1. SPATIAL LAYOUT: Overall room structure and layout\n"
                "2. NAVIGABLE AREAS: Clear paths and open spaces for movement\n"
                "3. OBSTACLES: Walls, furniture, barriers (including glass/transparent)\n"
                "4. POINTS OF INTEREST: Objects and areas relevant to the target\n"
                "5. NAVIGATION STRATEGY: Recommended exploration sequence and directions\n\n"
                "Focus on creating a spatial understanding that will guide efficient navigation.",
                role="user"
            )
        ]
    )
    
    scan_angles: List[int] = Field(default=[0, 45, 90, 135, 180, 225, 270, 315], description="Angles for 360-degree scan")
    
    def _run(self, *args, **kwargs):
        self.callback.info(agent_id=self.workflow_instance_id, progress='🔄 360° Spatial Scan', 
                         message="Starting comprehensive spatial scanning")
        
        try:
            # Get target information
            target_object = self.stm(self.workflow_instance_id).get("target_object", "any object")
            target_location = self.stm(self.workflow_instance_id).get("target_location", "anywhere")
            
            self.callback.info(agent_id=self.workflow_instance_id, progress='🎯 Scan Target', 
                             message=f"Scanning for: {target_object} at {target_location}")
            
            # Perform 360-degree scan
            scan_results = self._perform_360_scan()
            
            # Analyze spatial layout
            spatial_analysis = self._analyze_spatial_layout(scan_results, target_object, target_location)
            
            # Store comprehensive spatial information
            self.stm(self.workflow_instance_id)["spatial_scan_complete"] = True
            self.stm(self.workflow_instance_id)["spatial_analysis"] = spatial_analysis
            self.stm(self.workflow_instance_id)["scan_results"] = scan_results
            self.stm(self.workflow_instance_id)["navigation_strategy"] = spatial_analysis.get("navigation_strategy", "")
            
            self.callback.info(agent_id=self.workflow_instance_id, progress='✅ Spatial Scan Complete', 
                             message=f"360° scan completed. Strategy: {spatial_analysis.get('navigation_strategy', 'Explore systematically')[:100]}...")
            
            return {"scan_complete": True, "spatial_analysis": spatial_analysis}
            
        except Exception as e:
            self.callback.info(agent_id=self.workflow_instance_id, progress='❌ Scan Error', 
                             message=f"Spatial scanning failed: {str(e)}")
            # Set fallback values
            self.stm(self.workflow_instance_id)["spatial_scan_complete"] = False
            self.stm(self.workflow_instance_id)["navigation_strategy"] = "Explore cautiously with rotation-based discovery"
            return {"scan_complete": False}
    
    def _perform_360_scan(self) -> List[Dict[str, Any]]:
        """Perform a 360-degree scan by rotating and capturing views."""
        
        scan_results = []
        
        self.callback.info(agent_id=self.workflow_instance_id, progress='📸 Starting 360° Scan', 
                         message=f"Capturing {len(self.scan_angles)} views")
        
        for i, angle in enumerate(self.scan_angles):
            self.callback.info(agent_id=self.workflow_instance_id, progress=f'📷 View {i+1}/{len(self.scan_angles)}', 
                             message=f"Capturing view at {angle}°")
            
            # Rotate to the target angle (relative rotation)
            if i > 0:
                rotation_needed = self.scan_angles[i] - self.scan_angles[i-1]
                if rotation_needed != 0:
                    self._rotate_to_angle(rotation_needed)
            
            # Capture current view
            view_data = self._capture_view(angle)
            scan_results.append(view_data)
            
            print (view_data.keys())
            # Display the captured view
            if view_data.get("rgb_data"):
                self.callback.info_image(self.workflow_instance_id, progress=f"RGB", image=view_data["rgb_data"])
            if view_data.get("map_data"):
                self.callback.info_image(self.workflow_instance_id, progress=f"Map", image=view_data["map_data"])
        
        self.callback.info(agent_id=self.workflow_instance_id, progress='✅ Scan Capture Complete', 
                         message=f"Captured {len(scan_results)} views for analysis")
        
        return scan_results
    
    def _rotate_to_angle(self, degrees: int):
        """Rotate the robot by the specified degrees."""
        try:
            if degrees > 0:
                action = "RotateRight"
            else:
                action = "RotateLeft"
                degrees = abs(degrees)
            
            result = self.tool_manager.execute(
                tool_name="mcp_thor_step",
                args={"action": action, "degrees": degrees}
            )
            
            self.callback.info(agent_id=self.workflow_instance_id, progress='🔄 Rotation', 
                             message=f"Rotated {action} {degrees}°")
            
        except Exception as e:
            self.callback.info(agent_id=self.workflow_instance_id, progress='⚠️ Rotation Error', 
                             message=f"Failed to rotate: {str(e)}")
    
    def _capture_view(self, angle: int) -> Dict[str, Any]:
        """Capture and analyze the current view."""
        try:
            # Get current environment state
            env_state_json = self.tool_manager.execute(
                tool_name="mcp_thor_get_environment_state",
                args={}
            )
            env_state = json.loads(env_state_json) if isinstance(env_state_json, str) else env_state_json
            
            rgb_data = env_state.get("observation", {}).get("rgb", "")
            map_data = env_state.get("map", "")
            pose = env_state.get("pose", [0, 0, 0])
            
            # Analyze this view
            view_analysis = self._analyze_view(rgb_data, angle)
            
            return {
                "angle": angle,
                "rgb_data": rgb_data,
                "map_data": map_data,
                "pose": pose,
                "analysis": view_analysis,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "angle": angle,
                "error": str(e),
                "analysis": f"Failed to capture view at {angle}°: {str(e)}"
            }
    
    def _analyze_view(self, rgb_data: str, angle: int) -> str:
        """Analyze a single view for spatial information."""
        if not rgb_data:
            return f"No visual data at {angle}°"
        
        try:
            analysis_json = self.tool_manager.execute(
                tool_name="mcp_vlm-r1_analyze_image",
                args={
                    "image_path": rgb_data,
                    "question": f"Analyze this view at {angle}° for robot navigation. Identify: 1) Open navigable areas and clear paths, 2) Obstacles and barriers (walls, furniture, glass), 3) Interesting objects and landmarks, 4) Spatial depth and room layout. Be specific about what's accessible vs blocked."
                }
            )
            analysis_result = json.loads(analysis_json)
            return analysis_result.get("raw_output", f"Analysis failed for {angle}° view")
            
        except Exception as e:
            return f"View analysis error at {angle}°: {str(e)}"
    
    def _analyze_spatial_layout(self, scan_results: List[Dict[str, Any]], target_object: str, target_location: str) -> Dict[str, Any]:
        """Analyze the complete 360-degree scan to understand spatial layout."""
        
        self.callback.info(agent_id=self.workflow_instance_id, progress='🧠 Spatial Analysis', 
                         message="Analyzing 360° scan for spatial understanding")
        
        # Compile view data for analysis
        view_data = []
        for result in scan_results:
            angle = result.get("angle", 0)
            analysis = result.get("analysis", "No analysis")
            view_data.append(f"View {angle}°: {analysis}")
        
        # Get map analysis
        map_analysis = "No map data"
        if scan_results and scan_results[0].get("map_data"):
            map_analysis = self._analyze_map_comprehensive(scan_results[0]["map_data"])
        
        try:
            # Generate comprehensive spatial analysis
            spatial_response = self.simple_infer(
                target_object=target_object,
                target_location=target_location,
                scan_count=len(scan_results),
                view_data="\n".join(view_data),
                map_analysis=map_analysis
            )
            
            spatial_content = spatial_response["choices"][0]["message"]["content"]
            
            # Parse the spatial analysis
            parsed_analysis = self._parse_spatial_analysis(spatial_content)
            
            return parsed_analysis
            
        except Exception as e:
            return {
                "spatial_layout": "Analysis failed",
                "navigable_areas": "Unknown",
                "obstacles": "Unknown", 
                "points_of_interest": "Unknown",
                "navigation_strategy": "Explore cautiously with systematic rotation",
                "error": str(e)
            }
    
    def _analyze_map_comprehensive(self, map_data: str) -> str:
        """Comprehensive map analysis for spatial understanding."""
        if not map_data:
            return "No map data available"
        
        try:
            map_analysis_json = self.tool_manager.execute(
                tool_name="mcp_vlm-r1_analyze_image",
                args={
                    "image_path": map_data,
                    "question": "Analyze this occupancy map comprehensively. Identify: 1) Overall room shape and layout, 2) Open navigable areas (light/green regions), 3) Obstacles and walls (dark/black regions), 4) Current robot position, 5) Optimal exploration paths and movement directions, 6) Spatial relationships and connectivity between areas."
                }
            )
            map_result = json.loads(map_analysis_json)
            return map_result.get("raw_output", "Map analysis failed")
            
        except Exception as e:
            return f"Map analysis error: {str(e)}"
    
    def _parse_spatial_analysis(self, content: str) -> Dict[str, Any]:
        """Parse the spatial analysis response into structured data."""
        
        # Extract sections using simple text parsing
        sections = {
            "spatial_layout": self._extract_section(content, "SPATIAL LAYOUT"),
            "navigable_areas": self._extract_section(content, "NAVIGABLE AREAS"),
            "obstacles": self._extract_section(content, "OBSTACLES"),
            "points_of_interest": self._extract_section(content, "POINTS OF INTEREST"),
            "navigation_strategy": self._extract_section(content, "NAVIGATION STRATEGY")
        }
        
        # If sections not found, use the full content
        if not any(sections.values()):
            sections["navigation_strategy"] = content
        
        return sections
    
    def _extract_section(self, content: str, section_name: str) -> str:
        """Extract a specific section from the analysis content."""
        import re
        
        # Look for section headers
        pattern = rf"{section_name}:?\s*(.*?)(?=\n\d+\.|$|\n[A-Z\s]+:)"
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        
        if match:
            return match.group(1).strip()
        
        return "" 