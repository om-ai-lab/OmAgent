# ZoomEye Operator

ZoomEye is a workflow operator that combines visual understanding with confidence-guided search to locate and analyze visual elements in images. It builds a hierarchical image tree and uses adaptive thresholding to efficiently identify objects relevant to user queries.

You can refer to the example in the `examples/ZoomEye` directory to understand how to use this operator.

# Inputs, Outputs and configs

## Inputs:
The inputs that the ZoomEye operator requires are as follows:
| Name     | Type | Required | Description |
| -------- | ----- | ----- | ---- |
| query | str | true | The text question about the image content |
| image_path | str | true | Path to the image file for analysis |
| qid | str | false | Optional query identifier for tracking purposes |

## Outputs:
The outputs that the ZoomEye operator returns are as follows:
| Name     | Type | Description |
| -------- | ----- | ---- |
| result | dict | The result of the ZoomEye workflow. It includes the final answer, identified visual elements, prompt tokens, completion tokens, and the original query. |

## Configs:
The config of the ZoomEye operator is as follows, you can simply copy and paste the following config into your project as a zoomeye_workflow.yml file.
```yml
- name: VisualCueGeneration
  llm: ${sub|gpt}

- name: ZoomEyePreprocess

- name: ZoomEyeSearch
  llm: ${sub|gpt}
  
- name: ZoomEyeSearchCheck

- name: ZoomEyeLoopCheck

- name: ZoomEyeOutput
  llm: ${sub|gpt}

```

The ZoomEye operator settings are as follows:
| Name     | Type | Description |
| -------- | ----- | ---- |
| answering_confidence_threshold_upper | float | The upper confidence threshold for accepting a node during search |
| depth_limit | int | The maximum depth of the image tree to explore |
| threshold_decrease | list | Sequence of threshold reductions to apply during adaptive search |
| pop_limit | int | Maximum number of nodes to process in a single search iteration |
| answering_confidence_threshold_lower | float | The lower confidence threshold below which search stops |
| num_interval | int | Number of additional nodes to process after each threshold adjustment |
| smallest_size | int | The smallest size of the image to process |
| threshold_decrease | list | Sequence of threshold reductions to apply during adaptive search |

Set these parameters here`omagent-core/src/omagent_core/advanced_components/workflow/ZoomEye/schemas/utils.py`

```python

# Constants for question templates and thresholds
ANSWERING_CONFIDENCE_THRESHOLD_UPPER = 0.4
ANSWERING_CONFIDENCE_THRESHOLD_LOWER = 0

# Constants for image processing
SMALLEST_SIZE = 384
DEPTH_LIMIT = 5
NUM_INTERVEL = 2

# Pop limit calculation
def pop_limit_func(max_depth):
    return max_depth * 3

POP_LIMIT = pop_limit_func
THRESHOLD_DECREASE = [0.1, 0.1, 0.2]
```

## How ZoomEye Works

ZoomEye operates in multiple stages:

1. **Visual Cue Generation**: Analyzes the image and query to identify key visual elements to search for
2. **ZoomEye Preprocess**: Prepares the search environment for each visual cue and initializes the image tree
3. **ZoomEye Search**: Performs confidence-guided traversal of the image tree to locate visual elements
4. **ZoomEye Search Check**: Determines when the search is complete and collects found candidates
5. **ZoomEye Loop Check**: Manages iterations across multiple visual cues
6. **ZoomEye Output**: Synthesizes the search results into a comprehensive response

The search process uses a priority-based traversal with multiple confidence metrics (existence, latent, and answering) to efficiently locate visual elements while maintaining high precision.

## Example Usage

Here's a simple example of how to use the ZoomEye operator in a workflow:

```python
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.engine.workflow.task.simple_task import simple_task
from omagent_core.advanced_components.workflow.ZoomEye.workflow import ZoomEyeWorkflow

# Initialize workflow
workflow = ConductorWorkflow(name='ZoomEyeExample')

# Create input task
input_task = simple_task(
    task_def_name='ZoomEyeInput',
    task_reference_name='zoomeye_input'
)

# Initialize ZoomEye workflow
zoomeye_workflow = ZoomEyeWorkflow()

# Connect input to ZoomEye workflow
zoomeye_workflow.set_input(
    query=input_task.output("query"),
    image_path=input_task.output("image_path")
)

# Configure workflow execution flow
workflow >> input_task >> zoomeye_workflow

# Register workflow
workflow.register(overwrite=True)
```

This combines the power of visual understanding with efficient search algorithms to provide detailed analysis of image content based on natural language queries.
