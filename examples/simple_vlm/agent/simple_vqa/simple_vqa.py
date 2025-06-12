from pathlib import Path
from typing import List

from omagent_core.omagent4agent import *
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.models.llms.base import BaseLLMBackend
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.models.llms.prompt.parser import StrParser
from omagent_core.models.llms.schemas import Content, Message
from omagent_core.utils.container import container
from omagent_core.utils.general import encode_image
from omagent_core.utils.registry import registry


@registry.register_worker()
class SimpleVQA(BaseWorker, BaseLLMBackend):
    llm: OpenaiGPTLLM
    tool_manager: ToolManager

    def _run(self, user_instruction: str, *args, **kwargs):
        # Initialize empty list for chat messages
        if True:
            print("🔍 Detecting objects...")
            #x = self.tool_manager.execute_task("detect person bbox at https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen-VL/assets/demo.jpeg")
            #print (x)


            detection_result = self.tool_manager.execute(
                tool_name="mcp_vlm-r1_detect_objects",
                args={"image_path": "https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen-VL/assets/demo.jpeg"}
            )
            print (f"VLM-R1 detection result: {detection_result}")
            #detection_result = json.loads(detection_result)
            #objects = detection_result.get("raw_output", {}).replace("```json", "").replace("```", "")
            
            # Spatial analysis with VLM-R1
            print("🧭 Analyzing spatial relationships...")
            analysis_result = self.tool_manager.execute(
                tool_name="mcp_vlm-r1_analyze_image",
                args={
                    "image_path": "https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen-VL/assets/demo.jpeg",
                    "question": "Describe images."
                }
            )
            print (f"VLM-R1 analysis result: {analysis_result}")
            analysis_result = json.loads(analysis_result)
 
        return analysis_result
