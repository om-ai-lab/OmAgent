from omagent_core.omagent4agent import *
import logging
import json
from typing import Dict, Any, List, Optional
import io, base64
from PIL import Image

@registry.register_worker()
class BrowserAgent(BaseWorker, BaseLLMBackend):
    """
    An agent that uses Playwright to navigate websites, extract information, and perform actions
    sequentially based on the extracted information until all required data is gathered.
    """
    tool_manager: ToolManager
    llm: OpenaiGPTLLM
    max_steps: int = 10  # Maximum number of steps to prevent infinite loops
    
    def _run(self, instructions: str, starting_url: str, goal: str = None, *args, **kwargs) -> dict:
        """
        Main execution method for the browser agent.
        
        Args:
            instructions: Detailed instructions of what information to gather and what actions to take
            starting_url: The URL to start browsing from
            goal: Optional goal statement to determine when to stop gathering information
            
        Returns:
            Dict containing gathered information and action history
        """
        try:
            # Initialize browser if needed and navigate to the starting URL
            snapshot = self._initialize_browser(starting_url)
            
            # Tracking variables
            step_count = 0
            action_history = []
            gathered_info = {}
            
            # Main execution loop
            while step_count < self.max_steps:
                step_count += 1
                logging.info(f"Executing step {step_count} of {self.max_steps}")
                
                # Capture current page state for analysis
                #snapshot = self._capture_page_snapshot()
                
                # Decide next action based on current state, instructions, and goal
                action_decision = self._decide_next_action(
                    snapshot=snapshot,
                    instructions=instructions,
                    goal=goal,
                    action_history=action_history,
                    gathered_info=gathered_info
                )
                
                # If action decision indicates we're done, break the loop
                if action_decision.get("is_complete", False):
                    logging.info("Goal achieved, stopping browser agent")
                    break
                
                # Execute the decided action
                action_result = self._execute_action(action_decision)
                
                # Record action and results
                action_record = {
                    "step": step_count,
                    "action": action_decision,
                    "result": action_result
                }
                action_history.append(action_record)
                
                # Update gathered information if new data is found
                if action_result.get("extracted_data"):
                    gathered_info.update(action_result.get("extracted_data"))
            
            # Close browser when done (unless specified to keep open)
            if not kwargs.get("keep_browser_open", False):
                self._close_browser()
            
            # Return the final results
            return {
                "success": True,
                "steps_taken": step_count,
                "gathered_information": gathered_info,
                "action_history": action_history
            }
            
        except Exception as e:
            logging.error(f"Browser agent execution failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _initialize_browser(self, starting_url: str) -> Dict[str, Any]:
        """Initialize browser and navigate to starting URL"""
        try:
            # First check if browser needs to be installed
            install_result = self.tool_manager.execute(
                tool_name="mcp_playwright_browser_install",
                args={}
            )
            logging.info(f"Browser installation check: {install_result}")
            
            # Navigate to the starting URL
            navigation_result = self.tool_manager.execute(
                tool_name="mcp_playwright_browser_navigate",
                args={"url": starting_url}
            )
            
            # Wait for page to load completely
            self.tool_manager.execute(
                tool_name="mcp_playwright_browser_wait",
                args={"state": "networkidle"}
            )
            #print (navigation_result)
            #if not navigation_result.get("success", False):
            #    raise RuntimeError(f"Failed to navigate to {starting_url}")
                
            return navigation_result
        
        except Exception as e:
            logging.error(f"Browser initialization failed: {str(e)}")
            raise
    
    def _capture_page_snapshot(self) -> Dict[str, Any]:
        """Capture current page state for analysis"""
        #try:
        if True:
            # Get page snapshot (DOM, text content, etc.)
            snapshot = self.tool_manager.execute(
                tool_name="mcp_playwright_browser_snapshot",
                args={}
            )
            
            # Take a screenshot for visual analysis if needed
            screenshot = self.tool_manager.execute(
                tool_name="mcp_playwright_browser_take_screenshot",
                args={}
            )
            img = Image.open(io.BytesIO(base64.decodebytes(bytes(screenshot, "utf-8"))))
            file_path = "temp.jpg"
            img.save('temp.jpg')
            
            # Combine the information
            return {
                "snapshot": snapshot,
                "screenshot": file_path
            }
            
        #except Exception as e:
        #    logging.error(f"Failed to capture page snapshot: {str(e)}")
        #    return {"error": str(e)}
    
    def _decide_next_action(self, snapshot: Dict, instructions: str, goal: str, 
                           action_history: List[Dict], gathered_info: Dict) -> Dict[str, Any]:
        """
        Use LLM to decide what action to take next based on current state and instructions
        """
        try:
            # Create a prompt for the LLM
            prompt = self._create_action_decision_prompt(
                snapshot=snapshot,
                instructions=instructions,
                goal=goal,
                action_history=action_history,
                gathered_info=gathered_info
            )
            
            # Get LLM response
            messages = [
                {"role": "system", "content": "You are a browser automation assistant that decides the next action to take based on the current state of a web page and the instruction goal."},
                {"role": "user", "content": prompt}
            ]
            
            llm_response = self.llm.generate(messages=messages)
            
            # Parse the LLM output to get the action decision
            try:
                action_decision = json.loads(llm_response)
            except json.JSONDecodeError:
                # If LLM response is not valid JSON, try to extract JSON using regex
                import re
                json_match = re.search(r'```json\s*(.*?)\s*```', llm_response, re.DOTALL)
                if json_match:
                    action_decision = json.loads(json_match.group(1))
                else:
                    raise ValueError("Could not parse LLM response into a valid action decision")
            
            return action_decision
            
        except Exception as e:
            logging.error(f"Action decision failed: {str(e)}")
            # Return a safe fallback action if decision making fails
            return {
                "action_type": "extract_content",
                "selector": "body",
                "explanation": "Fallback action due to decision error"
            }
    
    def _create_action_decision_prompt(self, snapshot: Dict, instructions: str, goal: str,
                                      action_history: List[Dict], gathered_info: Dict) -> str:
        """Create a prompt for the LLM to decide the next action"""
        # Format the current page state
        page_state = f"Current URL: {snapshot.get('url')}\nPage Title: {snapshot.get('title')}\n"
        
        # Format action history
        history_str = "\n".join([
            f"Step {action['step']}: {action['action']['action_type']} - {action['action'].get('explanation', 'No explanation')}"
            for action in action_history[-3:] # Only include the last 3 actions to save token space
        ])
        
        # Format gathered information
        gathered_info_str = json.dumps(gathered_info, indent=2)
        
        # The available actions that can be taken
        available_actions = """
        Available actions:
        1. click: Click on an element (requires selector)
        2. type: Type text into an input field (requires selector and text)
        3. extract_content: Extract text content from elements (requires selector)
        4. navigate: Navigate to a new URL (requires url)
        5. select_option: Select an option from a dropdown (requires selector and value)
        6. wait: Wait for something to happen (requires state or timeout)
        7. go_back: Go back to the previous page
        8. complete: Mark the task as complete when all required information is gathered
        """
        
        # Format the prompt
        prompt = f"""
        # Browser Automation Task
        
        ## Instructions
        {instructions}
        
        ## Goal
        {goal if goal else 'No specific goal provided, follow the instructions.'}
        
        ## Current Page State
        {page_state}
        
        ## Snapshot Content Summary
        {snapshot.get('snapshot', {}).get('text_content', 'No text content available')}
        
        ## Action History
        {history_str if action_history else 'No previous actions.'}
        
        ## Information Gathered So Far
        {gathered_info_str if gathered_info else '{}'}
        
        {available_actions}
        
        Based on the current state, decide the next action to take.
        Respond with a JSON object that includes:
        1. action_type: The type of action to take (from the available actions list)
        2. selector: CSS selector for the element to interact with (if applicable)
        3. value: Value to use for the action (e.g., text to type, URL to navigate to)
        4. explanation: Brief explanation of why you're taking this action
        5. extracted_data: What data this action is expected to collect (if applicable)
        6. is_complete: true/false whether the goal has been achieved
        
        Example:
        ```json
        {
          "action_type": "click",
          "selector": "#search-button",
          "explanation": "Clicking the search button to submit the query",
          "is_complete": false
        }
        ```
        
        ONLY respond with the JSON object, no additional text.
        """
        
        return prompt
    
    def _execute_action(self, action_decision: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the decided action using the appropriate Playwright tool"""
        action_type = action_decision.get("action_type")
        
        try:
            if action_type == "click":
                return self._execute_click(action_decision)
            elif action_type == "type":
                return self._execute_type(action_decision)
            elif action_type == "extract_content":
                return self._execute_extract(action_decision)
            elif action_type == "navigate":
                return self._execute_navigate(action_decision)
            elif action_type == "select_option":
                return self._execute_select(action_decision)
            elif action_type == "wait":
                return self._execute_wait(action_decision)
            elif action_type == "go_back":
                return self._execute_go_back()
            elif action_type == "complete":
                return {"success": True, "message": "Task complete"}
            else:
                return {"success": False, "error": f"Unknown action type: {action_type}"}
                
        except Exception as e:
            logging.error(f"Failed to execute action {action_type}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _execute_click(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a click action"""
        selector = action.get("selector")
        if not selector:
            return {"success": False, "error": "No selector provided for click action"}
        
        result = self.tool_manager.execute(
            tool_name="mcp_playwright_browser_click",
            args={"selector": selector}
        )
        
        # Wait for any resulting navigation or network activity
        self.tool_manager.execute(
            tool_name="mcp_playwright_browser_wait",
            args={"state": "networkidle"}
        )
        
        return result
    
    def _execute_type(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a type action"""
        selector = action.get("selector")
        text = action.get("value")
        
        if not selector or not text:
            return {"success": False, "error": "Missing selector or text for type action"}
        
        result = self.tool_manager.execute(
            tool_name="mcp_playwright_browser_type",
            args={"selector": selector, "text": text}
        )
        
        return result
    
    def _execute_extract(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute content extraction"""
        selector = action.get("selector")
        if not selector:
            return {"success": False, "error": "No selector provided for extract action"}
        
        # Get snapshot with content
        snapshot = self.tool_manager.execute(
            tool_name="mcp_playwright_browser_snapshot",
            args={"selector": selector}
        )
        
        # Extract relevant data
        data_key = action.get("data_key", "extracted_content")
        return {
            "success": True,
            "extracted_data": {
                data_key: snapshot.get("text_content", "")
            }
        }
    
    def _execute_navigate(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute navigation to a URL"""
        url = action.get("value")
        if not url:
            return {"success": False, "error": "No URL provided for navigate action"}
        
        result = self.tool_manager.execute(
            tool_name="mcp_playwright_browser_navigate",
            args={"url": url}
        )
        
        # Wait for page to load
        self.tool_manager.execute(
            tool_name="mcp_playwright_browser_wait",
            args={"state": "networkidle"}
        )
        
        return result
    
    def _execute_select(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute selection from dropdown"""
        selector = action.get("selector")
        value = action.get("value")
        
        if not selector or not value:
            return {"success": False, "error": "Missing selector or value for select action"}
        
        result = self.tool_manager.execute(
            tool_name="mcp_playwright_browser_select_option",
            args={"selector": selector, "values": [value]}
        )
        
        return result
    
    def _execute_wait(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute wait action"""
        state = action.get("state", "networkidle")
        timeout = action.get("timeout", 30000)
        
        result = self.tool_manager.execute(
            tool_name="mcp_playwright_browser_wait",
            args={"state": state, "timeout": timeout}
        )
        
        return result
    
    def _execute_go_back(self) -> Dict[str, Any]:
        """Go back to the previous page"""
        result = self.tool_manager.execute(
            tool_name="mcp_playwright_browser_go_back",
            args={}
        )
        
        # Wait for page to load
        self.tool_manager.execute(
            tool_name="mcp_playwright_browser_wait",
            args={"state": "networkidle"}
        )
        
        return result
    
    def _close_browser(self) -> Dict[str, Any]:
        """Close the browser when done"""
        return self.tool_manager.execute(
            tool_name="mcp_playwright_browser_close",
            args={}
        ) 