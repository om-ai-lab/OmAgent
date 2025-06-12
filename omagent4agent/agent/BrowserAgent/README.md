# Browser Agent

A powerful agent that uses Playwright tools to automate browser interactions, gather information, and perform actions sequentially based on LLM decisions.

## Features

- Automated web browsing with intelligent action selection
- Sequential decision-making based on page content
- Information extraction and gathering
- Goal-oriented navigation
- Support for complex multi-step workflows

## How It Works

The Browser Agent follows this workflow:

1. Initialize browser and navigate to starting URL
2. Capture current page state (snapshot, screenshot)
3. Based on instructions and current state, decide the next action
4. Execute the chosen action (click, type, extract content, etc.)
5. Gather information if available
6. Repeat steps 2-5 until goal is completed or max steps reached
7. Return gathered information and action history

## Available Actions

The agent can perform the following actions:

- **click**: Click on an element using a CSS selector
- **type**: Type text into an input field
- **extract_content**: Extract text content from elements
- **navigate**: Navigate to a new URL
- **select_option**: Select an option from a dropdown
- **wait**: Wait for something to happen
- **go_back**: Go back to the previous page
- **complete**: Mark the task as complete

## Usage Example

```python
from omagent_core.utils.container import container
from omagent_core.tool_system.manager import ToolManager
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM

# Get the agent and set up dependencies
browser_agent = container.get_worker("BrowserAgent")
browser_agent.tool_manager = ToolManager(llm=my_llm)
browser_agent.llm = my_llm

# Run the agent with instructions
result = browser_agent._run(
    instructions="Your step-by-step instructions here",
    starting_url="https://example.com",
    goal="The goal to accomplish",
    max_steps=10,
    keep_browser_open=False
)

# Process results
print(result['gathered_information'])
```

## Parameters

- **instructions**: Detailed step-by-step instructions to follow
- **starting_url**: The URL to begin browsing from
- **goal**: (Optional) Goal statement to help determine completion
- **max_steps**: (Optional) Maximum number of steps to execute
- **keep_browser_open**: (Optional) Whether to keep the browser open after completion

## Return Value

The agent returns a dictionary containing:

```json
{
  "success": true,
  "steps_taken": 5,
  "gathered_information": {
    "item1_name": "Product Name",
    "item1_price": "$99.99",
    "item1_specs": "Technical specifications..."
  },
  "action_history": [
    {
      "step": 1,
      "action": { "action_type": "navigate", "value": "https://example.com" },
      "result": { "success": true }
    },
    // More actions...
  ]
}
```

## Best Practices

1. **Provide clear instructions**: Make the steps as explicit as possible.
2. **Use appropriate selectors**: When specifying elements to interact with, use specific CSS selectors.
3. **Set reasonable max_steps**: Adjust the maximum steps based on the complexity of your task.
4. **Handle errors**: The agent attempts error recovery, but check the success status.
5. **Test incrementally**: Start with simpler tasks and build up to more complex ones.

## Requirements

- Playwright tools must be available in the tool manager
- An LLM capable of decision-making based on web page content
- Python 3.8+ 