import json
import time
import argparse
from pathlib import Path
from omagent_core.utils.container import container
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.utils.registry import registry
from omagent_core.clients.devices.programmatic import ProgrammaticClient
from omagent_core.utils.logger import logging
from omagent_core.advanced_components.workflow.reflexion.workflow import ReflexionWorkflow
from omagent_core.engine.worker.base import BaseWorker

def parse_args():
    parser = argparse.ArgumentParser(description='Run batch test for Reflexion')
    parser.add_argument('--dataset', type=str, default='math500',
                      help='Dataset name')
    parser.add_argument('--dataset_file', type=str, 
                      default='/path/to/math500.jsonl',
                      help='Path to original questions file')
    
    return parser.parse_args()

@registry.register_worker()
class SimpleInterface(BaseWorker):
    def _run(self, query, id, *args, **kwargs):
        return {"query": query, "id": id}

def get_missing_questions(original_file, result_file):
    """Find missing questions"""
    try:
        # Read the original question list
        original_questions = {}
        with open(original_file, 'r') as f:
            for line in f:
                data = json.loads(line)
                original_questions[data['question']] = data['id']
        
        # Read existing results
        existing_questions = set()
        if os.path.exists(result_file):
            with open(result_file, 'r') as f:
                for line in f:
                    if line.strip():  # Skip empty lines
                        result = json.loads(line)
                        question = result.get('question', '')
                        if question:
                            existing_questions.add(question)
        
        # Find missing questions
        missing_questions = []
        for question, qid in original_questions.items():
            if question not in existing_questions:
                missing_questions.append({
                    'id': qid,
                    'question': question
                })
        
        return missing_questions
        
    except Exception as e:
        print(f"Error in get_missing_questions: {str(e)}")
        return []

def process_question(programmatic_client, question_data, result_file):
    """Process a single question"""
    query = question_data['question']
    id = question_data['id']
    
    try:
        print(f"Processing question ID {id}: {query}")
        
        # Process input using ProgrammaticClient
        workflow_input_list = [{"query": query, "id": id}]
        result = programmatic_client.start_batch_processor(workflow_input_list=workflow_input_list)
        
        # Format the result
        result_entry = {
            "id": id,
            "question": query,
            "body": result[0].get("body", ""),  # Get from result[0]
            "last_output": result[0].get("output", {}).get("output", {}).get("output", ""),
            "ground_truth": "",
            "prompt_tokens": result[0].get("token_usage", {}).get("prompt_tokens", 0),
            "completion_tokens": result[0].get("token_usage", {}).get("completion_tokens", 0),
            "status": "success"
        }
        
        with open(result_file, 'a') as outfile:
            json.dump(result_entry, outfile)
            outfile.write('\n')
        
        print(f"Successfully processed question ID {id}")
        return True
        
    except Exception as e:
        print(f"Error processing question ID {id}: {str(e)}")
        save_error_result(result_file, id, query, "error")
        return False

def save_error_result(result_file, id, query, error_type):
    """Save error result"""
    error_entry = {
        "id": id,
        "question": query,
        "body": "",
        "last_output": "",
        "ground_truth": "",
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "status": error_type
    }
    with open(result_file, 'a') as outfile:
        json.dump(error_entry, outfile)
        outfile.write('\n')

def main():
    args = parse_args()
    
    logging.init_logger("omagent", "omagent", level="INFO")
    
    CURRENT_PATH = Path(__file__).parents[0]
    registry.import_module(CURRENT_PATH.joinpath('agent'))
    
    # Configure container
    container.register_stm("SharedMemSTM")
    container.from_config(CURRENT_PATH.joinpath('container.yaml'))
    
    # Initialize workflow
    workflow = ConductorWorkflow(name='reflexion')
    
    # Configure Reflexion workflow
    reflexion_workflow = ReflexionWorkflow()
    reflexion_workflow.set_input(
        query=workflow.input('query'),
        id=workflow.input('id')
    )
    
    # Configure workflow execution flow
    workflow >> reflexion_workflow
    
    # Register workflow
    workflow.register(overwrite=True)
    
    # Initialize ProgrammaticClient
    config_path = CURRENT_PATH.joinpath('configs')
    programmatic_client = ProgrammaticClient(
        processor=workflow,
        config_path=config_path,
        workers=[]
    )
    
    print("Starting processing...")
    
    result_file = CURRENT_PATH.joinpath(f'{args.dataset}_results.jsonl')
    missing_questions = get_missing_questions(args.dataset_file, result_file)
    
    if not missing_questions:
        print("No missing questions found. All questions have been processed.")
        return
    
    total_questions = len(missing_questions)
    print(f"Found {total_questions} questions to process")
    
    try:
        for i, question_data in enumerate(missing_questions, 1):
            print(f"Processing question {i}/{total_questions}")
            success = process_question(programmatic_client, question_data, result_file)
            
            if not success:
                print("Cooling down after error...")
                time.sleep(10)
            else:
                time.sleep(2)
    finally:
        # Ensure processor is stopped after completion or error
        programmatic_client.stop_processor()
    
    print("Processing completed")

if __name__ == "__main__":
    main()
