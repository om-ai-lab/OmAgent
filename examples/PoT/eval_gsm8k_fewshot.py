import os
os.environ["OMAGENT_MODE"] = "lite"

# Import required modules and components
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
    """Parse command line arguments for GSM8K evaluation"""
    parser = argparse.ArgumentParser(description='Evaluate GSM8K dataset using Program of Thought')
    parser.add_argument('--endpoint', type=str, default="https://api.openai.com/v1",
                        help='OpenAI API endpoint')
    parser.add_argument('--api_key', type=str, default=None,
                        help='OpenAI API key')
    parser.add_argument('--model_id', type=str, default="gpt-3.5-turbo",
                        help='Model ID to use')
    parser.add_argument('--dataset_path', type=str, default="gsm8k_test.jsonl",
                        help='Path to dataset')
    parser.add_argument('--examples', type=str, default=None,
                        help='Path to examples file. If not provided, will use default examples')
    parser.add_argument('--output_path', type=str, default='output',
                        help='Path to output file. If not provided, will use default')
    return parser.parse_args()

def main():
    """Main function to run GSM8K evaluation"""
    # Parse command line arguments
    args = parse_args()

    # Set environment variables for OpenAI API
    os.environ["custom_openai_endpoint"] = args.endpoint
    os.environ["custom_openai_key"] = args.api_key
    os.environ["model_id"] = args.model_id

    # Load examples for few-shot learning
    if args.examples:
        with open(args.examples) as f:
            ex = f.read()
    else:
        # Default examples if none provided - contains simple arithmetic problems
        ex = '''
Question: There are 15 trees in the grove. Grove workers will plant trees in the grove today. After they are done, there will be 21 trees. How many trees did the grove workers plant today?
# Python code, return ans
total_trees = 15
after_planted_trees = 21
ans = after_planted_trees - total_trees

Question: If there are 3 cars in the parking lot and 2 more cars arrive, how many cars are in the parking lot?
# Python code, return ans
total_cars = 3
more_arrived_cars = 2
ans = total_cars + more_arrived_cars

Question: Leah had 32 chocolates and her sister had 42. If they ate 35, how many pieces do they have left in total?
# Python code, return ans
num_of_Leah_chocolates = 32
num_of_sister_chocolates = 42
total_chocolates = num_of_Leah_chocolates + num_of_sister_chocolates
eaten_chocolates = 35
ans = total_chocolates - eaten_chocolates

Question: Jason had 20 lollipops. He gave Denny some lollipops. Now Jason has 12 lollipops. How many lollipops did Jason give to Denny?
# Python code, return ans
num_of_Jason_lollipops = 20
num_of_given_lollipops = 12
ans = num_of_Jason_lollipops - num_of_given_lollipops

Question: Shawn has five toys. For Christmas, he got two toys each from his mom and dad. How many toys does he have now?
# Python code, return ans
num_of_Shawn_toys = 5
num_of_toys_from_mom = 2
num_of_toys_from_dad = 2
ans = num_of_Shawn_toys + num_of_toys_from_mom + num_of_toys_from_dad

Question: There were nine computers in the server room. Five more computers were installed each day, from monday to thursday. How many computers are now in the server room?
# Python code, return ans
num_of_computers_in_server_room = 9
num_of_computers_installed_each_day = 5
num_of_days = 4
ans = num_of_computers_in_server_room + num_of_computers_installed_each_day * num_of_days

Question: Michael had 58 golf balls. On tuesday, he lost 23 golf balls. On wednesday, he lost 2 more. How many golf balls did he have at the end of wednesday?
# Python code, return ans
num_of_Michael_golf_balls = 58
num_of_golf_balls_lost_on_tuesday = 23
num_of_golf_balls_lost_on_wednesday = 2
ans = num_of_Michael_golf_balls - num_of_golf_balls_lost_on_tuesday - num_of_golf_balls_lost_on_wednesday

Question: Olivia has $23. She bought five bagels for $3 each. How much money does she have left?
# Python code, return ans
num_of_Olivia_money = 23
num_of_bagels = 5
cost_of_each_bagel = 3
ans = num_of_Olivia_money - num_of_bagels * cost_of_each_bagel
'''

    # Load dataset and setup variables
    dataset_path = args.dataset_path
    model_id = args.model_id
    dataset_name = 'gsm8k'

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
    pot_workflow.set_input(query=workflow.input('query'), examples=workflow.input('examples'))
    workflow >> pot_workflow
    workflow.register(overwrite=True)

    # Initialize programmatic client
    config_path = CURRENT_PATH.joinpath('configs')
    programmatic_client = ProgrammaticClient(processor=workflow, config_path=config_path)

    # Prepare batch processing inputs
    output_json = []
    workflow_input_list = []
    for question in datasets[:10]:
        workflow_input_list.append({
            "id": question['id'], 
            "query": question['question'],
            "examples": ex
        })
    
    # Process questions in batches
    res = programmatic_client.start_batch_processor(workflow_input_list=workflow_input_list, max_tasks=5)
    
    # Collect results
    for r, w in zip(res, workflow_input_list):
        output_json.append({
            "id": w['id'],
            "question": w['query'],
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
