from pathlib import Path
import json
from omagent_core.utils.registry import registry
from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.general import read_image

CURRENT_PATH = root_path = Path(__file__).parents[0]

def load_json(json_path: str):
    with open(json_path, 'r', encoding='utf-8') as f:
        res = json.load(f)
    return res

def get_body_data(body_data, language = 'en'):
    # 提取数据
    gender = body_data.get("Gender", "未知")
    age = body_data.get("Age", "未知")
    height = body_data.get("Height", "未知")
    weight = body_data.get("Weight", "未知")
    fat = body_data.get("Fat", "未知")
    striated_muscle = body_data.get("Striated_Muscle", "未知")
    muscle = body_data.get("Muscle", "未知")
    bone = body_data.get("Bone", "未知")
    visceral_fat_grade = body_data.get("Visceral_Fat_Grade", "未知")
    
    # 构建字符串
    body_data_string_zh = (
        f"性别: {gender}, "
        f"年龄: {age}, "
        f"身高: {height}, "
        f"体重: {weight}, "
        f"脂肪: {fat}, "
        f"骨骼肌: {striated_muscle}, "
        f"肌肉: {muscle}, "
        f"骨骼: {bone}, "
        f"内脏脂肪等级: {visceral_fat_grade}"
    )
    
    body_data_string_en = (
        f"Gender: {gender}, "
        f"Age: {age}, "
        f"Height: {height}, "
        f"Weight: {weight}, "
        f"Fat: {fat}, "
        f"Striated_Muscle: {striated_muscle}, "
        f"Muscle: {muscle}, "
        f"Bone: {bone}, "
        f"Visceral_Fat_Grade: {visceral_fat_grade}"
    )
    if language == 'zh':
        return body_data_string_zh
    else:
        return body_data_string_en

@registry.register_worker()
class BodyDataAcquisition(BaseWorker):
    """
    Body data input processor for processing the user's body data (future support for connecting to a body fat scale to access this data directly).
    
    The processor allows user body data and provides relevant analysis and recommendations around that data.
    
    Body data, which currently exists locally in the form of a file agent is automatically fetched, 
    (with future support for connecting to a body fat scale to fetch this data directly) 
    this data will be read and cached into the workflow's short term memory (or long term) for use by the downstream processor.
    
    """

    def _run(self, *args, **kwargs):
        """
        """
        try:
            body_data = load_json(CURRENT_PATH.joinpath("body_data.json"))
        
            body_data_string = get_body_data(body_data['Body_Data'])
            # img = read_image(input_source=image_path)
            # image_cache = {'<image_0>' : img}
            # self.stm(self.workflow_instance_id)['user_body_data'] = {"user_body_data": body_data_string}
            self.stm(self.workflow_instance_id)['user_body_data'] = body_data_string
            print(self.stm(self.workflow_instance_id)['user_body_data'])
        except Exception as e:
            print(CURRENT_PATH.joinpath("body_data.json"))
            print(e)
            pass
        
        return 
    



