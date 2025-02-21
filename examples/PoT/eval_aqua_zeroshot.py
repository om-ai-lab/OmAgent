# Import required modules and components
import os
os.environ["OMAGENT_MODE"] = "lite"

from omagent_core.utils.container import container
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.advanced_components.workflow.pot.workflow import PoTWorkflow
from pathlib import Path
from omagent_core.utils.registry import registry
from omagent_core.clients.devices.programmatic import ProgrammaticClient
from omagent_core.utils.logger import logging
import argparse
import json
import os


def parse_args():
    """Parse command line arguments for AQUA evaluation"""
    parser = argparse.ArgumentParser(description='Evaluate AQUA dataset using Program of Thought')
    parser.add_argument('--endpoint', type=str, default="https://api.openai.com/v1",
                        help='OpenAI API endpoint')
    parser.add_argument('--api_key', type=str, default=None,
                        help='OpenAI API key')
    parser.add_argument('--model_id', type=str, default="gpt-3.5-turbo",
                        help='Model ID to use')
    parser.add_argument('--dataset_path', type=str, default="aqua_test.jsonl",
                        help='Path to dataset')
    parser.add_argument('--output_path', type=str, default='output',
                        help='Path to output file. If not provided, will use default')
    return parser.parse_args()

def main():
    """Main function to run AQUA evaluation"""
    # Parse command line arguments
    args = parse_args()

    # Set environment variables for API
    os.environ["custom_openai_endpoint"] = args.endpoint
    os.environ["custom_openai_key"] = args.api_key
    os.environ["model_id"] = args.model_id

    # Load dataset and setup variables
    dataset_path = args.dataset_path
    model_id = args.model_id
    dataset_name = 'aqua'

    # Read dataset from JSONL file
    datasets = []
    with open(dataset_path, 'r') as f:
        for line in f:
            datasets.append(json.loads(line))

    # Setup logging and paths
    logging.init_logger("omagent", "omagent", level="INFO")
    CURRENT_PATH = Path(__file__).parents[0]
    container.register_stm("SharedMemSTM")

    # Initialize agent modules and configuration
    registry.import_module(project_path=CURRENT_PATH.joinpath('agent'))
    container.from_config(CURRENT_PATH.joinpath('container.yaml'))

    # Setup Program of Thought workflow
    workflow = ConductorWorkflow(name='PoT')
    pot_workflow = PoTWorkflow()
    pot_workflow.set_input(query=workflow.input('query'), examples=workflow.input('examples'), options=workflow.input('options'))
    workflow >> pot_workflow
    workflow.register(overwrite=True)

    # Initialize programmatic client
    config_path = CURRENT_PATH.joinpath('configs')
    programmatic_client = ProgrammaticClient(processor=workflow, config_path=config_path)

    # Prepare batch processing inputs
    output_json = []
    workflow_input_list = []
    for question in datasets:
        workflow_input_list.append({
            "id": question['id'],
            "query": question['question'],
            "examples": None,
            "options": str(question['options'])
        })

    # Process questions in batches
    res = programmatic_client.start_batch_processor(workflow_input_list=workflow_input_list, max_tasks=5)

    # Collect results
    for r, w in zip(res, workflow_input_list):
        output_json.append({
            "id": w['id'],
            "question": w['query']+'\nOptions: '+str(question['options']),
            "last_output": r['last_output'],
            "prompt_tokens": r['prompt_tokens'],
            "completion_tokens": r['completion_tokens']
        })

    # Prepare final output
    final_output = {
        "dataset_name": dataset_name,
        "model_id": model_id,
        "alg": "POT",
        "model_result": output_json
    }

    # Save results to output file
    if not os.path.exists(args.output_path):
        os.makedirs(args.output_path)
    with open(f'{args.output_path}/{dataset_name}_{model_id.replace("/","-")}_POT_output.json', 'w') as f:
        json.dump(final_output, f, indent=4)

    # Cleanup
    programmatic_client.stop_processor()

if __name__ == "__main__":
    main()
