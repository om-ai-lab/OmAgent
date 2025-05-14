import os
os.environ['custom_openai_endpoint'] = 'http://140.207.201.47:11434/v1'
os.environ['custom_openai_key'] = 'sk-4zr6uGzVbNfIiq7U513aCc94Af614792938cE9AdB7D0E295'

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
            "Find the domain of the expression $\\frac{\\sqrt{x-2}}{\\sqrt{5-x}}$.",
        "r":
            "The expressions inside each square root must be non-negative. Therefore, $x-2 \\ge 0$, so $x\\ge2$, and $5 - x \\ge 0$, so $x \\le 5$. Also, the denominator cannot be equal to zero, so $5-x>0$, which gives $x<5$. Therefore, the domain of the expression is $\\boxed{[2,5)}$.",
        "a":
            "The final answer is $[2,5)$. I hope it is correct."
    }, {
        "q": "If $\\det \\mathbf{A} = 2$ and $\\det \\mathbf{B} = 12,$ then find $\\det (\\mathbf{A} \\mathbf{B}).$",
        "r": "We have that $\\det (\\mathbf{A} \\mathbf{B}) = (\\det \\mathbf{A})(\\det \\mathbf{B}) = (2)(12) = \\boxed{24}.$",
        "a": "The final answer is $24$. I hope it is correct."
    }, {
        "q": "Terrell usually lifts two 20-pound weights 12 times. If he uses two 15-pound weights instead, how many times must Terrell lift them in order to lift the same total weight?",
        "r": """If Terrell lifts two 20-pound weights 12 times, he lifts a total of $2\\cdot 12\\cdot20=480$ pounds of weight. If he lifts two 15-pound weights instead for $n$ times, he will lift a total of $2\\cdot15\\cdot n=30n$ pounds of weight. Equating this to 480 pounds, we can solve for $n$:
        \\begin{align*}
        30n&=480\\
        \\Rightarrow\\qquad n&=480/30=\\boxed{16}
        \\end{align*}""",
        "a": "The final answer is $16$. I hope it is correct."
    }, {
        "q": """If the system of equations
                \\begin{align*}
                6x-4y&=a,\\
                6y-9x &=b.
                \\end{align*}
                has a solution $(x, y)$ where $x$ and $y$ are both nonzero, find $\\frac{a}{b},$ assuming $b$ is nonzero.""",
        "r": "If we multiply the first equation by $-\\frac{3}{2}$, we obtain $$6y-9x=-\\frac{3}{2}a.$$Since we also know that $6y-9x=b$, we have $$-\\frac{3}{2}a=b\\Rightarrow\\frac{a}{b}=\\boxed{-\\frac{2}{3}}.$$",
        "a": "The final answer is $-\\frac{2}{3}$. I hope it is correct."
    }
]


def read_jsonl(file_path):
    with open(file_path, 'r') as file:
        data = [json.loads(line.strip()) for line in file if line.strip()]
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
            "id": d['id'],
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
    container.from_config( CURRENT_PATH.joinpath( 'container_8.yaml' ) )

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
    res = programmatic_client.start_batch_processor( workflow_input_list=workflow_input_list, max_tasks=5 )
    programmatic_client.stop_processor()

    results = process_results( res, dataset_name=dataset_name, alg=alg )
    file = write_json( data=results, file_path=output_path, file_name=output_name )

    print( f"{dataset_name} evaluation results saved in {file}" )


def arguments():
    parser = argparse.ArgumentParser( description='COT Evaluation' )

    parser.add_argument( '--cot_method', type=str, default='few_shot', help='COT Method' )
    parser.add_argument( '--model_id', type=str, default='qwen2:0.5b', help='Model ID' )

    parser.add_argument( '--dataset_name', type=str, default='math500', help='Dataset Name' )
    parser.add_argument( '--dataset_path', type=str, default='/data23/ljc/project/wang_ze/OmAgent/examples/cot/data/math500_test_converted.jsonl', help='Dataset Path' )

    parser.add_argument( '--output_path', type=str, default='/data23/ljc/project/wang_ze/OmAgent/examples/cot/Output', help='Output Path' )
    parser.add_argument( '--output_name', type=str, default='math500_results', help='Output Name' )

    print( f"Arguments: {parser.parse_args()}" )
    return parser.parse_args()


if __name__ == '__main__':
    args = arguments()
    
    # 运行5次，每次保存的输出文件名加上编号
    for i in range(1, 6):
        print(f"Run number {i}...")
        evaluator(
            model_id=args.model_id,
            dataset_name=args.dataset_name,
            dataset_path=args.dataset_path,
            output_path=args.output_path,
            output_name=f"{args.output_name}_{i}",
            cot_method=args.cot_method
        )
