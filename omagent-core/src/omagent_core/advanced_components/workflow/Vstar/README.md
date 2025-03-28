# VStar Operator

VStar is a workflow that utilizes visual contextual information to process high-definition images. It utilizes hierarchical image structures and adaptive thresholding to efficiently identify objects relevant to user queries.

You can refer to the example in the `examples/VStar` directory to understand how to use this operator.

## Inputs, Outputs, and Configs

### Inputs:
The inputs that the VStar operator requires are as follows:
| Name      | Type | Required | Description |
|-----------|------|----------|-------------|
| query     | str  | true     | The text question about the image content |
| image_path| str  | true     | Path to the image file for analysis |
| qid       | str  | false    | Optional query identifier for tracking purposes |

### Outputs:
The outputs that the VStar operator returns are as follows:
| Name    | Type | Description |
|---------|------|-------------|
| result  | dict | The result of the VStar workflow. It includes the final answer, identified visual elements, prompt tokens, completion tokens, and the original query. |

### Configs:
The config of the VStar operator is as follows. You can simply copy and paste the following config into your project as a `vstar_workflow.yml` file.
```yml
- name: VQA_LLM_Preprocess

- name: VstarLoopCheck

- name: VQA_LLM
  llm: ${sub|vstar}

- name: VstarSearchPreprocess

- name: VstarSearch
  llm: ${sub|vstar}

- name: VstarSearchCheck

- name: VQA_LLM_Post
  llm: ${sub|vstar}
```

The VStar operator settings are as follows:
| Name | Type | Description |
|----------------------------------|--------|-------------------------------------------------------------------------------------------------|
| CONFIDENCE_HIGH | float | The upper confidence threshold for accepting a node during the search. If the confidence score of a detected object exceeds this threshold, it is considered a valid detection. |
| CONFIDENCE_LOW | float | The lower confidence threshold below which the search stops. If the confidence score falls below this threshold, the search will cease for that particular object. |
| TARGET_CUE_THRESHOLD | float | This parameter defines the maximum depth of the image tree to explore during the search process. It helps limit the search to a manageable level, preventing excessive computation. |
| TARGET_CUE_THRESHOLD_DECAY | float | This value is used to adjust the confidence threshold dynamically during the search process. As the search progresses, this decay factor reduces the threshold, allowing for more flexible detection of objects. |
| TARGET_CUE_THRESHOLD_MINIMUM | list | A sequence of threshold reductions to apply during adaptive search. This list specifies how much to decrease the confidence threshold at each step, allowing for a gradual adjustment based on search results. |
| SMALLEST_SIZE | int | This parameter defines the minimum size of the image to process. Images smaller than this size will be ignored, ensuring that the search focuses on relevant, adequately sized images. |
| MAX_SEARCH_STEP | int | The maximum number of nodes to process in a single search iteration. This limit helps control the computational load and ensures that the search process remains efficient. |

Set these parameters in `omagent-core/src/omagent_core/advanced_components/workflow/Vstar/agent/vstar/utils.py`.

```python
CONFIDENCE_HIGH = 0.5
CONFIDENCE_LOW = 0.3
TARGET_CUE_THRESHOLD = 6.0
TARGET_CUE_THRESHOLD_DECAY = 0.7
TARGET_CUE_THRESHOLD_MINIMUM = 3.0
SMALLEST_SIZE = 224
MAX_SEARCH_STEP = 10
```

## How VStar Works

VStar operates in multiple stages:

1. **VQA LLM Preprocess**: Prepares the input data for the VQA LLM by reading the image and storing it in the state management system (STM).
2. **VQA LLM**: Executes the Visual Question Answering task using the VStar LLM to get answers or target based on the input image and query.
3. **Vstar Search Preprocess**: Initializes the search parameters based on the missing objects identified in the VQA LLM response.
4. **Vstar Search**: Performs a confidence-guided search to locate visual elements in the image.
5. **Vstar Loop Check**: Manages iterations across multiple visual cues to ensure all relevant objects are searched.
6. **Vstar Search Check**: Determines when the search is complete and collects found candidates.
7. **VQA LLM Post**: Processes the results and prepares the final output for the user.

The search process uses a priority-based traversal with multiple confidence metrics to efficiently locate visual elements while maintaining high precision.

## Example Usage

Here's a simple example of how to use the VStar operator in a workflow:

```python
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from omagent_core.advanced_components.workflow.Vstar.workflow import VstarWorkflow

# Initialize workflow
workflow = ConductorWorkflow(name='VStarExample')

# Create input task
input_task = simple_task(
    task_def_name='VstarInput',
    task_reference_name='vstar_input'
)

# Initialize VStar workflow
vstar_workflow = VstarWorkflow()

# Connect input to VStar workflow
vstar_workflow.set_input(
    query=input_task.output("query"),
    image_path=input_task.output("image_path")
)

# Configure workflow execution flow
workflow >> input_task >> vstar_workflow

# Register workflow
workflow.register(overwrite=True)
```

This combines the power of visual understanding with efficient search algorithms to provide detailed analysis of image content based on natural language queries.