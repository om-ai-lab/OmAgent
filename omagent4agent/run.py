import os
import json
import yaml
from omagent_core.engine.workflow.conductor_workflow import ConductorWorkflow
from omagent_core.clients.devices.programmatic.client import ProgrammaticClient
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.models.llms.prompt import PromptTemplate
from omagent_core.models.llms.prompt.parser import StrParser
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.models.llms.schemas import Message
from pydantic import Field
from typing import List
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.utils.logger import logging
from pathlib import Path
from omagent_core.utils.registry import registry
from omagent_core.clients.devices.programmatic import ProgrammaticClient
from omagent_core.advanced_components.worker.inputs.input_interface import InputInterface
import textwrap
import os
import sys
import glob
import shutil
import traceback
import re 

os.environ["OMAGENT_MODE"] = "lite"

class OmAgentMaker(BaseLLMBackend):
    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_file("prompts/workflow_prompt.txt", role="system"),
            PromptTemplate.from_file("prompts/worker_prompt.txt", role="system"),
            PromptTemplate.from_file("prompts/config_prompt.txt", role="system"),
            PromptTemplate.from_file("prompts/debug_prompt.txt", role="system"),
            PromptTemplate.from_file("prompts/workflow_code_prompt.txt", role="system"), 
        ]
    )
    llm: OpenaiGPTLLM ={    
        "name": "OpenaiGPTLLM", 
        "model_id": "gpt-4o", 
        "vision": True,
        "api_key": os.getenv("custom_openai_key"),
        "response_format": "json_object",
        "use_default_sys_prompt":False
        }
    output_parser: StrParser = StrParser()


    def call_llm(self, prompt: str) -> str:
        # Create a Message object
        message = Message(role="user", content=prompt)
        # Call the LLM with the Message object
        response = self.llm.generate([message])
        # Extract the content from the response
        content = response['choices'][0]['message']['content']
        return content

    # New planning method to generate a plain-text plan based on the input content
    def planning_step(self, prompt: str) -> str:
        planning_prompt = (
            f"Plan out a solution for the following task: {prompt}.\n"
            "Provide a detailed, step-by-step description of the approach without including any code. You are a vision agent to solve this task by coding on the fly. define what vision tools you need to use to solve this task. and how flow you need to solve this, we solve this by inference, but training the data, so do not include the training step. We will solve this by calling apis like ChatGPT or object detection apis or face detection, etc. First, what APIs do you need and what to solve in the flow.  "
        )
        plan_text = self.call_llm(planning_prompt)        
        return plan_text

    def generate_agent(self, prompt: str, input: dict, folder: str):
        """
        Generate a complete agent based on the input description.

        Args:
            input (dict): The input description containing details like image and content.
            folder (str): The folder path where the agent structure will be created.
        """
        # Step 0: Planning step – generate a plan from the task description
        plan = self.planning_step(prompt)
        
        # Step 1: Create the necessary directory structure
        self.create_directory_structure(folder)

        # Step 2: Define workers and workflow (now including the planning text)
        while True:
            workflow_info = self.define_workers_and_workflow(prompt, input, folder, plan)
            # Validate the generated workflow JSON
            if self.validate_workflow_json(workflow_info['workflow']):
                break
            print("Invalid workflow JSON, regenerating...")

        # Step 3: Implement workers
        generated_workers = self.implement_workers(folder, workflow_info)

        #self.generate_workflow_code(folder, workflow_info, generated_workers)  
        
        # Step 4: Save configuration files
        self.save_configuration_files(folder, generated_workers)    

        # Step 5: Execute the workflow
        #self.execute_workflow(input, folder, workflow_info, generated_workers)
        #self.execute_workflow_from_folder(input, folder)

        # Step 6: Execute the workflow from folder
        #self.execute_workflow_from_folder(folder)

        # Step 6: Debugging and error handling
        #self.debug_and_retry(folder)
    def generate_workflow_code(self, folder: str, workflow_info: dict, generated_workers: dict):
        workflow_code_prompt = self.prompts[4].format(
            workflow_json=workflow_info['workflow'],
            simple_codes="\n".join(
                "".join(worker["simple_codes"]) if isinstance(worker["simple_codes"], list) else worker["simple_codes"]
                for worker in generated_workers["workers"]
            )
        )
        workflow_code = self.call_llm(workflow_code_prompt)
        with open(os.path.join(folder, "workflow.py"), "w") as f:
            f.write(workflow_code)

    def debug(self, inputs: dict, folder: str):
        while True:
            # Clear cached modules
            agents_dir = os.path.join(folder, "agent")
            for module_name in list(sys.modules.keys()):
                module = sys.modules[module_name]
                if module_name.startswith("agent") or (hasattr(module, '__file__') and module.__file__ and agents_dir in module.__file__):
                    del sys.modules[module_name]
                    print(module_name)
                    # Extract the class name from the module name
                    class_name = module_name.split('.')[-1]
                    try:
                        registry.unregister_worker(class_name)
                    except KeyError:
                        print(f"Module {class_name} not found in registry, skipping unregistration.")
            
            # Re-import updated modules
            target_folder = os.path.abspath(folder)
            if target_folder not in sys.path:
                sys.path.insert(0, target_folder)
            try:
                registry.import_module(os.path.join(target_folder, "agent"))
            except Exception as e:
                temp = {}
                temp["traceback"] = traceback.format_exc()
                temp["input"] = inputs
                temp["error"] = str(e)                
                temp["class"] = re.search(f'File ".*/{folder}/agent/(.*).py', temp["traceback"]).group(1).split("/")[0]                
                self.debug_and_retry(temp, folder, inputs)
                continue

            # Execute with fresh modules
            output = self.execute_workflow_from_folder(inputs=inputs, folder=folder)
            print (output)
            if "error" not in output:
                break
            
            # Debug and update files
            input("Press Enter to continue...")
            debug_output = self.debug_and_retry(output, folder, inputs)
            
        return output

    def debug_and_retry(self, output: dict, folder: str, inputs: dict):
        import json
        workflow_path = glob.glob(os.path.join(folder, "*_workflow.json"))[0]
        workflow_json = json.load(open(workflow_path))
        
        task_name = output["class"]
        if not task_name:
            return output
        
        code_path = os.path.join(folder, "agent", task_name, f"{task_name}.py")
        with open(code_path, "r") as f:
            code = f.read()
        
        debug_prompt = self.prompts[3].format(
            error_message=output["traceback"],
            workflow=workflow_json,
            code=code,
            inputs=output["input"]
        )
        
        
        llm_response = self.call_llm(debug_prompt)
        
        if "```python" in llm_response:
            llm_response = llm_response.split("```python")[1].split("```")[0]
            with open(code_path, "w") as f:
                f.write(llm_response)
        if "```json" in llm_response:
            llm_response = llm_response.split("```json")[1].split("```")[0]
            with open(workflow_path, "w") as f:
                json.dump(json.loads(llm_response), f, indent=4)
        
        return llm_response


    def create_directory_structure(self, folder: str):
        # Create the necessary directory structure
        os.makedirs(os.path.join(folder, 'agent'), exist_ok=True)
        os.makedirs(os.path.join(folder, 'configs', 'llms'), exist_ok=True)
        os.makedirs(os.path.join(folder, 'configs', 'tools'), exist_ok=True)
        os.makedirs(os.path.join(folder, 'configs', 'workers'), exist_ok=True)

    def define_workers_and_workflow(self, prompt, input: dict, folder: str, plan: str):
        # Generate a detailed prompt for the LLM that now includes the planning summary
        prompt = self.prompts[0].format(content=prompt, input=input, plan=plan)
        
        # Call the LLM with the generated prompt
        llm_response = self.call_llm(prompt).strip()
        print(llm_response)

        # Check if the response contains code fences and remove them
        if llm_response.startswith("```json"):
            llm_response = llm_response[7:]  # Remove the starting ```json
        if llm_response.endswith("```"):
            llm_response = llm_response[:-3]  # Remove the ending ```
        # Process workflow JSON
        workflow = json.loads(llm_response)       
        workflow_description = workflow['description']

        # Generate a file name based on the task description
        workflow_name = workflow["name"]
        workflow_file_name = f"{workflow_name}_workflow.json"

        workflow_path = os.path.join(folder, workflow_file_name)
        with open(workflow_path, 'w') as f:
            json.dump(workflow, f, indent=4)
        
        return {"workflow_file_name":workflow_file_name, "workflow_name": workflow_name, "workflow": workflow, "workflow_description": workflow_description, "workflow_path": workflow_path}

    def implement_workers(self, folder: str, workflow_info: dict):
        # Load the worker prompt from an external file
        
        # Parse the LLM response to extract worker descriptions
        workers_section = workflow_info['workflow_description']
        generated_workers = {"workers": [], "name":workflow_info['workflow_name'], "workflow_path": workflow_info['workflow_path']}
        codes = []
        simple_codes = []
        for worker in workers_section:   
            if worker["Worker_Name"] == "InputInterface":
                continue
            worker_prompt_template = self.prompts[1].format(workflow_name=worker["Worker_Name"], workflow=str(workflow_info['workflow']), worker_description=worker["Role"], previous_codes="\n".join(codes))   
            llm_response = self.call_llm(worker_prompt_template)
            print(llm_response)
            # Create a directory for the worker
            worker_dir = os.path.join(folder, 'agent', worker["Worker_Name"])
            os.makedirs(worker_dir, exist_ok=True)
            
            # Save the worker implementation to a file
            worker_file_path = os.path.join(worker_dir, f"{worker['Worker_Name']}.py")
            if "```python" in llm_response:
                llm_response = llm_response.split("```python")[1].split("```")[0]            
            codes.append("# worker name: "+worker["Worker_Name"]+"\n"+llm_response)
            simple_codes.append("# worker name: "+worker["Worker_Name"]+"\n how to import: from agent."+worker["Worker_Name"]+"."+worker["Worker_Name"]+" import "+worker["Worker_Name"]+"\n simple code: "+self.keep_only_class_and_return(llm_response))
            with open(worker_file_path, 'w') as f:
                f.write(llm_response)
            
            generated_workers["workers"].append({"worker_name": worker['Worker_Name'], "worker_file_path": worker_file_path, "code": llm_response, "simple_codes": simple_codes})
        
        agents_dir = os.path.join(folder, "agent")
        for root, dirs, files in os.walk(agents_dir):
            for d in dirs:
                sub_folder_path = os.path.join(root, d)
                init_file = os.path.join(sub_folder_path, "__init__.py")
                if not os.path.isfile(init_file):
                    with open(init_file, "w") as f:
                        f.write("# Auto-generated __init__.py for agents sub-package\n")
                    print(f"Ensured sub-package: {init_file}")

        return generated_workers

    def keep_only_class_and_return(self, code: str):
        simple_code = ""
        for line in code.split("\n"):
            if "class" in line or "def" in line or "return" in line:
                simple_code += line+"\n"
        return simple_code

    def copy_config_files(self, folder: str, generated_workers: dict):
        config_dir = os.path.join(folder, 'configs',"llms")
        if os.path.exists(config_dir):
            for file in os.listdir(config_dir):
                shutil.copy(os.path.join(config_dir, file), os.path.join(folder, 'configs', 'llms', file))
        config_dir = os.path.join(folder, 'configs',"tools")
        if os.path.exists(config_dir):
            for file in os.listdir(config_dir):
                shutil.copy(os.path.join(config_dir, file), os.path.join(folder, 'configs', 'tools', file))

        for worker in generated_workers["workers"]:
            worker_code = worker["code"]
            worker_name = worker["worker_name"]
            
            with open(os.path.join(folder, 'configs', 'workers', f'{worker_name}.yml'), 'w') as f:                                
                f.write("name: "+worker_name+"\n")
                if "llm:" in worker_code:
                    if "image" in worker_code:
                        f.write("llm: ${sub|vlm}\n")
                    else:
                        f.write("llm: ${sub|llm}\n")
                if "tool_manager:" in worker_code:
                    f.write("tool_manager: ${sub|all_tools}\n")

    def save_configuration_files(self, folder: str, generated_workers: dict):
        # Save default LLM configuration for gpt4o
        
        llm_gpt4o_config_path = os.path.join(folder, 'configs', 'llms', 'gpt4o.yml')
        llm_gpt4o_config_content = textwrap.dedent("""
            name: OpenaiGPTLLM
            model_id: gpt-4o
            api_key: ${env| custom_openai_key, openai_api_key}
            endpoint: ${env| custom_openai_endpoint, https://api.openai.com/v1}
            temperature: 0
            vision: true
            response_format: json_object
            use_default_sys_prompt: false
        """)
        with open(llm_gpt4o_config_path, 'w') as f:
            f.write(llm_gpt4o_config_content.strip())

        # Save default LLM configuration for text_res
        llm_text_res_config_path = os.path.join(folder, 'configs', 'llms', 'text_res.yml')
        llm_text_res_config_content = textwrap.dedent("""
            name: OpenaiGPTLLM
            model_id: gpt-4o
            api_key: ${env| custom_openai_key, openai_api_key}
            endpoint: ${env| custom_openai_endpoint, https://api.openai.com/v1}
            temperature: 0
            stream: false
            response_format: text
            use_default_sys_prompt: false
        """)
        with open(llm_text_res_config_path, 'w') as f:
            f.write(llm_text_res_config_content.strip())

        # Save default tools configuration
        tools_config_path = os.path.join(folder, 'configs', 'tools', 'all_tools.yml')
        tools_config_content = textwrap.dedent("""
            llm: ${sub|text_res}
            tools:
             - name: GeneralOD    
               url: http://10.0.0.132:8005/inf_predict
             - name: SuperResolution
               api_url: http://10.0.0.26:8010/superres
             - name: TavilyWebSearch
               tavily_api_key: ${env|tavily_api_key, null}
        """)
        with open(tools_config_path, 'w') as f:
            f.write(tools_config_content.strip())

        # Parse the LLM response to extract worker descriptions
        for worker in generated_workers["workers"]:
            worker_code = worker["code"]
            worker_name = worker["worker_name"]
            worker_config_prompt = self.prompts[2].format(code=worker_code)
            #llm_response = self.call_llm(worker_config_prompt)
            
            with open(os.path.join(folder, 'configs', 'workers', f'{worker_name}.yml'), 'w') as f:                                
                f.write("name: "+worker_name+"\n")
                if "llm:" in worker_code:
                    f.write("llm: ${sub|text_res}\n")
                if "tool_manager:" in worker_code:
                    f.write("tool_manager: ${sub|all_tools}\n")


    def execute_workflow(self, inputs, folder, workflow_info: dict, generated_workers: dict):
        # Logic to execute the workflow
        logging.init_logger("omagent", "omagent", level="INFO")
        workflow_path = workflow_info["workflow_path"]
        # Set current working directory path
        CURRENT_PATH = Path(__file__).parents[0]
                # Add the target folder (e.g., "person_playing_cellphone") to sys.path
        target_folder = os.path.abspath(folder)
        if target_folder not in sys.path:
            sys.path.insert(0, target_folder)
        print(f"Added {target_folder} to sys.path")
        # Import registered modules
        os.environ["OMAGENT_MODE"] = "lite"
        registry.import_module(CURRENT_PATH.joinpath("agent"))
        workflow_json = json.load(open(workflow_path))
        workflow = ConductorWorkflow(name=workflow_json["name"])
        workflow.load(workflow_path)
        client = ProgrammaticClient(processor=workflow, config_path="/".join(workflow_path.split("/")[:-1])+"/configs")
        client.start_processor_with_input(inputs)

    def execute_workflow_from_folder(self, inputs: dict, folder: str):
        # Logic to execute the workflow

        logging.init_logger("omagent", "omagent", level="INFO")
        workflow_path = glob.glob(os.path.join(folder, "*_workflow.json"))[0]

        # Add the target folder (e.g., "person_playing_cellphone") to sys.path
        target_folder = os.path.abspath(folder)
        if target_folder not in sys.path:
            sys.path.insert(0, target_folder)
        print(f"Added {target_folder} to sys.path")
        os.environ["OMAGENT_MODE"] = "lite"
        # Now, import the agents package from the target folder
        registry.import_module(os.path.join(target_folder, "agent"))

        with open(workflow_path) as f:
            workflow_json = json.load(f)

        workflow = ConductorWorkflow(name=workflow_json["name"])
        workflow.load(workflow_path)
        client = ProgrammaticClient(
            processor=workflow,
            config_path="/".join(workflow_path.split("/")[:-1])+"/configs",
        )
        output = client.start_processor_with_input(inputs)        
        return output


    def debug_and_retry(self, output: dict, folder: str, inputs: dict):
        import re
        import importlib
        import sys
        workflow_path = glob.glob(os.path.join(folder, "*_workflow.json"))[0]
        workflow_json = json.load(open(workflow_path))
        
        task_name = output["class"]
        print("task_name:", task_name)
        if task_name == "":
            return output
        
        code_path = os.path.join(folder, "agent", task_name, f"{task_name}.py")
        with open(code_path, "r") as f:
            code = f.read()
            print(output, output)
            debug_prompt = self.prompts[3].format(error_message=output["traceback"], workflow=workflow_json, code=code, inputs=output["input"])
            print(debug_prompt)
            llm_response = self.call_llm(debug_prompt)
            print(llm_response)
            if "```python" in llm_response:
                llm_response = llm_response.split("```python")[1].split("```")[0]
                with open(code_path, "w") as f:
                    f.write(llm_response)

                # Ensure the module is reloaded
                module_name = f"agent.{task_name}"
                if module_name in sys.modules:
                    # Reload the module
                    importlib.reload(sys.modules[module_name])
                else:
                    # Load the module if not already loaded
                    import importlib.util
                    spec = importlib.util.spec_from_file_location(module_name, code_path)
                    mod = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = mod
                    spec.loader.exec_module(mod)

            if "```json" in llm_response:
                llm_response = llm_response.split("```json")[1].split("```")[0]
                with open(workflow_path, "w") as f:
                    json.dump(json.loads(llm_response), f, indent=4)
                    print("modified workflow:", llm_response)
         
        return llm_response
        
    def validate_workflow_json(self, workflow_json: dict) -> bool:
        """
        Validate the generated workflow JSON based on specific rules.

        Returns:
            bool: True if the JSON is valid, False otherwise.
        """
        # Check for SWITCH task type
        for task in workflow_json.get('tasks', []):
            if task['type'] == 'SWITCH':
                if not task.get('inputParameters'):
                    print(f"Error: SWITCH task '{task['name']}' has empty inputParameters.")
                    return False

        # Check for DO_WHILE task type
        for task in workflow_json.get('tasks', []):
            if task['type'] == 'DO_WHILE':
                loop_condition = task.get('loopCondition')
                loop_over = task.get('loopOver', [])
                if not loop_condition or not loop_over:
                    print(f"Error: DO_WHILE task '{task['name']}' is missing loopCondition or loopOver.")
                    return False
                # Extract taskReferenceName from loopCondition
                task_ref_name = loop_condition.split('$.')[1].split('[')[0]
                if not any(t['taskReferenceName'] == task_ref_name for t in loop_over):
                    print(f"Error: taskReferenceName '{task_ref_name}' in loopCondition is not in loopOver for task '{task['name']}'.")
                    return False


        return True

if __name__ == "__main__":    
    auto_agent = OmAgentMaker()
    print ("start")    
    """    
    auto_agent.generate_agent(input={"image_path": "/Users/kyusonglee/Documents/proj/OmAgent/auto_agent/demo.jpeg"}, 
        prompt="detect mouse in the kitchen and tell me what is the mouse doing. If there is no mouse, please check again with zoom in the image. If mouse is detected, then please confirm again with llm. The output should save the image with the bbox if the mouse is detected.", 
        folder="mouse_in_the_kitchen"
    )  
    """
    #auto_agent.generate_agent(input={"input": "test"}, 
    #    prompt="very simple workflow to test SWITCH and DO_WHILE loop", 
    #    folder="test"
    #)  
    
    
    #auto_agent.generate_agent(input=[{"timestamp": 1, "frame_image": "frame1.jpg"}, {"timestamp": 2, "frame_image": "frame2.jpg"}, {"timestamp": 3, "frame_image": "frame3.jpg"}], 
    #    prompt="The video sequence frames will be given. Detect the people who have stayed at the entrance of the finance office for more than 5 minutes. If suspect, please capture the image of the person. and save the person's image and how long they have stayed at the entrance of the finance office.", 
    #    folder="person_in_the_finance_office"
    #)
    #auto_agent.execute_workflow_from_folder(inputs={"image": "/Users/kyusonglee/Documents/proj/OmAgent/auto_agent/demo.jpeg"}, folder="mouse_in_the_kitchen")
    #auto_agent.debug(inputs={"image_path": "/Users/kyusonglee/Downloads/rat.jpg"}, folder="mouse_in_the_kitchen")
    auto_agent.debug(inputs={"input": 1}, folder="test")
    #auto_agent.execute_workflow_from_folder(inputs={"image": "/Users/kyusonglee/Documents/proj/OmAgent/auto_agent/demo.jpeg"}, folder="mouse_in_the_kitchen")

