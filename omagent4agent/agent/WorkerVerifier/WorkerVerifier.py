from pathlib import Path
from typing import List

from omagent_core.engine.worker.base import BaseWorker
from omagent_core.models.llms.base import BaseLLMBackend, BaseLLM
from omagent_core.models.llms.prompt import PromptTemplate
from omagent_core.utils.registry import registry
from pydantic import Field
from omagent_core.models.llms.prompt.parser import *    

CURRENT_PATH = root_path = Path(__file__).parents[0]

@registry.register_worker()
class WorkerVerifier(BaseLLMBackend, BaseWorker):  
    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_file(CURRENT_PATH.joinpath("worker_verifier_system.prompt"), role="system"),
            PromptTemplate.from_file(CURRENT_PATH.joinpath("worker_verifier_user.prompt"), role="user"),   
        ]
    )
    llm: BaseLLM
    def _run(self, *args, **kwargs):                
        generated_workers = self.stm(self.workflow_instance_id)["generated_workers"]       
        folder_path = self.stm(self.workflow_instance_id)["folder_path"]
        workflow_json = self.stm(self.workflow_instance_id)["workflow_json"]
        checks = [False] * len(generated_workers["workers"])
        repeat = 0
        while repeat < 5:
            for i, worker in enumerate(generated_workers["workers"]):
                code = worker["code"]
                worker_name = worker["worker_name"]
                worker_file_path = worker["worker_file_path"]  
            
                output = self.simple_infer(code=code, workflow_json=workflow_json)["choices"][0]["message"].get("content")
                output = self.parser(output)
            
                if output["is_correct"]:
                    print ("The code is correct and working.", worker_name, worker_file_path)
                    checks[i] = True
                    continue
                else:
                    print (output)
                    print ("The code is not correct.", worker_name, worker_file_path)
                    new_code = output["new_code"]
                    error_message = output["error_message"]
                    self.stm(self.workflow_instance_id)["generated_workers"]["workers"][i]["code"] = new_code
                    print (f"Error: {error_message}")
                    print (f"New code: {new_code}")
                    yn = input("Do you want to save the new code? (y/n)")
                    print (worker_file_path)
                    if yn == "y":
                        with open(worker_file_path, "w") as f:
                            f.write(new_code)
                        f.close()
                    else:
                        print ("The new code is not saved.")
                if not any(checks):
                    repeat += 1
                    continue
                
    def parser(self, output):
        if "```json" in output:
            output = output.split("```json")[1].split("```")[0]
        output = json.loads(output)
        return output

    def test_import(self, code):
        import_code_only = []
        for line in code.split("\n"):            
            if "@registry.register_worker()" in line:
                break
            import_code_only.append(line)
        try:
            print ("import_code_only")
            print ("\n".join(import_code_only))
            exec("\n".join(import_code_only))
        except ImportError as e:
            print ({"is_correct": False, "error_message": str(e)})
            return {"is_correct": False, "error_message": str(e)}
        print ({"is_correct": True, "error_message": ""})
        return {"is_correct": True, "error_message": ""}
    
