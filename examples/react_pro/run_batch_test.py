from omagent_core.utils.container import container
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from pathlib import Path
from omagent_core.utils.registry import registry
from omagent_core.clients.devices.programmatic import ProgrammaticClient
from omagent_core.utils.logger import logging
from omagent_core.advanced_components.workflow.react_pro.workflow import ReactProWorkflow
import json
import argparse


def read_input_texts(file_path):
    """Read questions from jsonl file"""
    input_texts = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():  
                data = json.loads(line)
                input_texts.append((data['question'], str(data['id'])))
    return input_texts


def process_results(results, dataset_name="aqua", model_id="gpt-3.5-turbo", alg="ReAct-Pro"):
    """Convert results to standard format"""
    formatted_output = {
        "dataset": dataset_name,
        "model_id": model_id,
        "alg": alg,
        "model_result": []
    }
    
    for result in results:
        output_data = result.get('output', {})
        
        model_result = {
            "id": output_data.get('id'),
            "question": output_data.get('query'),
            "body": output_data.get('body', {}),
            "last_output": output_data.get('output', ''),
            "step_number": output_data.get('step_number', 0),
            "prompt_tokens": output_data.get('token_usage', {}).get('prompt_tokens', 0),
            "completion_tokens": output_data.get('token_usage', {}).get('completion_tokens', 0)
        }
        
        formatted_output["model_result"].append(model_result)
    
    return formatted_output


def run_workflow(args):
    """Run the ReAct Pro workflow with given arguments"""
    logging.init_logger("omagent", "omagent", level="INFO")

    # Set current working directory path
    CURRENT_PATH = Path(__file__).parents[0]
    ROOT_PATH = CURRENT_PATH.parents[1]  

    # Import registered modules
    registry.import_module(CURRENT_PATH.joinpath('agent'))

    # Load container configuration from YAML file
    container.register_stm("SharedMemSTM")
    container.from_config(CURRENT_PATH.joinpath('container.yaml'))

    # Initialize workflow
    workflow = ConductorWorkflow(name='react_pro_workflow_example')

    # Configure React Pro workflow
    react_workflow = ReactProWorkflow()
    react_workflow.set_input(
        query=workflow.input('query'),
        id=workflow.input('id')
    )

    # Configure workflow execution flow
    workflow >> react_workflow 

    # Register workflow
    workflow.register(overwrite=True)

    # Read input data
    input_file = ROOT_PATH / args.input_file
    input_data = read_input_texts(input_file)

    # Initialize programmatic client
    config_path = CURRENT_PATH.joinpath('configs')
    programmatic_client = ProgrammaticClient(
        processor=workflow,
        config_path=config_path,
        workers=[]  
    )

    # Prepare input data
    workflow_input_list = [
        {"query": item[0], "id": str(item[1])} for item in input_data
    ]

    print(f"Processing {len(workflow_input_list)} queries in this split...")

    # Process data
    res = programmatic_client.start_batch_processor(
        workflow_input_list=workflow_input_list
    )

    # Process results
    formatted_results = process_results(
        res, 
        dataset_name=args.dataset_name,
        model_id=args.model_id,
        alg=args.alg
    )

    # Create output directory if it doesn't exist
    output_dir = ROOT_PATH / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save results to file
    output_file = output_dir / f"{args.dataset_name}_{args.alg}_{args.model_id}_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(formatted_results, f, ensure_ascii=False, indent=2)

    programmatic_client.stop_processor()
    print(f"Results saved to {output_file}")
    print("All splits processed successfully!")


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run ReAct Pro workflow on dataset')
    parser.add_argument('--input_file', type=str, default="data/hotpot_dev_select_500_data_test_0107.jsonl",
                      help='Input dataset file path (relative to project root)')
    parser.add_argument('--dataset_name', type=str, default="hotpot",
                      help='Name of the dataset')
    parser.add_argument('--model_id', type=str, default="gpt-3.5-turbo",
                      help='Model identifier')
    parser.add_argument('--alg', type=str, default="ReAct-Pro",
                      help='Algorithm name')
    parser.add_argument('--output_dir', type=str, default="data",
                      help='Output directory for results (relative to project root)')
    
    args = parser.parse_args()
    run_workflow(args) 