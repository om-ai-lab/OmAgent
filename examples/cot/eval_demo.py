import os
import json
import argparse

from pathlib import Path

from omagent_core.utils.logger import logging
from omagent_core.utils.registry import registry
from omagent_core.utils.container import container
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.advanced_components.workflow.cot.workflow import CoTWorkflow
from omagent_core.clients.devices.programmatic.client import ProgrammaticClient

EXAMPLES = [
    {
        "q":
            "There are 15 trees in the grove. Grove workers will plant trees in the grove today. After they are done, there will be 21 trees. How many trees did the grove workers plant today?",
        "r":
            "There are 15 trees originally. Then there were 21 trees after some more were planted. So there must have been 21 - 15 = 6.",
        "a":
            "6"
    }, {
        "q": "If there are 3 cars in the parking lot and 2 more cars arrive, how many cars are in the parking lot?",
        "r": "There are originally 3 cars. 2 more cars arrive. 3 + 2 = 5.",
        "a": "5"
    }, {
        "q": "Leah had 32 chocolates and her sister had 42. If they ate 35, how many pieces do they have left in total?",
        "r": "Originally, Leah had 32 chocolates. Her sister had 42. So in total they had 32 + 42 = 74. After eating 35, they had 74 - 35 = 39.",
        "a": "39"
    }, {
        "q": "Jason had 20 lollipops. He gave Denny some lollipops. Now Jason has 12 lollipops. How many lollipops did Jason give to Denny?",
        "r": "Jason started with 20 lollipops. Then he had 12 after giving some to Denny. So he gave Denny 20 - 12 = 8.",
        "a": "8"
    }, {
        "q": "Shawn has five toys. For Christmas, he got two toys each from his mom and dad. How many toys does he have now?",
        "r": "Shawn started with 5 toys. If he got 2 toys each from his mom and dad, then that is 4 more toys. 5 + 4 = 9.",
        "a": "9"
    }, {
        "q":
            "There were nine computers in the server room. Five more computers were installed each day, from monday to thursday. How many computers are now in the server room?",
        "r":
            "There were originally 9 computers. For each of 4 days, 5 more computers were added. So 5 * 4 = 20 computers were added. 9 + 20 is 29.",
        "a":
            "29"
    }, {
        "q":
            "Michael had 58 golf balls. On tuesday, he lost 23 golf balls. On wednesday, he lost 2 more. How many golf balls did he have at the end of wednesday?",
        "r":
            "Michael started with 58 golf balls. After losing 23 on tuesday, he had 58 - 23 = 35. After losing 2 more, he had 35 - 2 = 33 golf balls.",
        "a":
            "33"
    }, {
        "q": "Olivia has $23. She bought five bagels for $3 each. How much money does she have left?",
        "r": "Olivia had 23 dollars. 5 bagels for 3 dollars each will be 5 x 3 = 15 dollars. So she has 23 - 15 dollars left. 23 - 15 is 8.",
        "a": "8"
    }
]


def read_jsonl( file_path ):
    with open( file_path, 'r', encoding='utf-8' ) as file:
        data = [ json.loads( line ) for line in file ]
    return data


def write_json( data, file_path, file_name ):
    file = os.path.join( file_path, f"{file_name}.json" )
    with open( file, 'w' ) as f:
        json.dump( data, f, indent=4 )
    return file


def prepare_data( file_path, cot_examples, cot_method, start=1 ):
    data = read_jsonl( file_path )

    return [
        {
            "id": idx,
            "query": d[ 'question' ],
            "cot_method": cot_method,
            "cot_examples": cot_examples
        } for idx, d in enumerate( data, start=start )
    ]


def process_results( res, dataset_name, alg ):
    return { "dataset": dataset_name, "model_id": os.environ.get( 'custom_model_id' ), "alg": alg, "model_result": res}


def setup_environ( model_id ):
    os.environ[ 'custom_model_id' ] = model_id

    print( f"Model ID: {model_id}" )


def evaluator( model_id, dataset_name, dataset_path, output_path, output_name, cot_method, alg='COT' ):
    # Set up the evaluator
    setup_environ( model_id=model_id )

    # Initialize logging
    logging.init_logger( "omagent", "omagent", level="INFO" )

    # Set current working directory path
    CURRENT_PATH = Path( __file__ ).parents[ 0 ]

    # Import registered modules
    registry.import_module( project_path=CURRENT_PATH.joinpath( 'agent' ) )

    container.register_stm( "RedisSTM" )
    # Load container configuration from YAML file
    container.from_config( CURRENT_PATH.joinpath( 'container.yaml' ) )

    workflow = ConductorWorkflow( name='cot_eval' )

    cot_workflow = CoTWorkflow()
    cot_workflow.set_input(
        id=workflow.input( 'id' ),
        query=workflow.input( 'query' ),
        cot_method=workflow.input( 'cot_method' ),
        cot_examples=workflow.input( 'cot_examples' )
    )

    workflow >> cot_workflow

    config_path = CURRENT_PATH.joinpath( "configs" )
    programmatic_client = ProgrammaticClient( processor=workflow, config_path=config_path, workers=[] )

    workflow_input_list = prepare_data( file_path=dataset_path, cot_examples=EXAMPLES, cot_method=cot_method )
    res = programmatic_client.start_batch_processor( workflow_input_list=workflow_input_list, max_tasks=15 )
    programmatic_client.stop_processor()

    results = process_results( res, dataset_name=dataset_name, alg=alg )
    file = write_json( data=results, file_path=output_path, file_name=output_name )

    print( f"{dataset_name} evaluation results saved in {file}" )


def arguments():
    parser = argparse.ArgumentParser( description='COT Evaluation' )

    parser.add_argument( '--cot_method', type=str, default='zero_shot', help='COT Method' )
    parser.add_argument( '--model_id', type=str, default='gpt-3.5-turbo', help='Model ID' )

    parser.add_argument( '--dataset_name', type=str, default='gsm8k', help='Dataset Name' )
    parser.add_argument( '--dataset_path', type=str, default='gsm8k.jsonl', help='Dataset Path' )

    parser.add_argument( '--output_path', type=str, default='Output', help='Output Path' )
    parser.add_argument( '--output_name', type=str, default='gsm8k_results', help='Output Name' )

    print( f"Arguments: {parser.parse_args()}" )
    return parser.parse_args()


if __name__ == '__main__':
    args = arguments()

    evaluator(
        model_id=args.model_id,
        dataset_name=args.dataset_name,
        dataset_path=args.dataset_path,
        output_path=args.output_path,
        output_name=args.output_name,
        cot_method=args.cot_method
    )
