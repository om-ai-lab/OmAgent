import base64
from fastapi import FastAPI
from pydantic import BaseModel
from io import BytesIO
from PIL import Image
import numpy as np
from dataclasses import dataclass
from vstar_bench_eval import VQA_LLM, expand2square, normalize_bbox
from visual_search import VSM
import torch
from typing import List

@dataclass
class Args:
    vqa_model_path: str = None
    version: str = None
    conv_type: str = None
    vision_tower: str = None
vqa_args = Args(
    vqa_model_path="./seal_vqa_7b", # your path to seal_vqa_7b
    conv_type="v1"
)
print(f"Using model path: {vqa_args.vqa_model_path}")
vqa_llm = VQA_LLM(vqa_args)

vsm_args = Args(
    version="./seal_vsm_7b", # your path to seal_vsm_7b
    vision_tower="./clip-vit-large-patch14" # your path to clip-vit-large-patch14
)
vsm = VSM(vsm_args)

app = FastAPI()

class VQAOutput(BaseModel):
    generated_text: str

class VQAPayload(BaseModel):
    prompt: str
    image_base64: str

@app.post("/vqa_llm")
async def generate_from_base64(data: VQAPayload):
    prompt = data.prompt
    image_base64 = data.image_base64
    image_data = base64.b64decode(image_base64)
    image = Image.open(BytesIO(image_data))
    response = vqa_llm.free_form_inference(image, prompt)
    
    return VQAOutput(
        generated_text=response,
    )

class VSMOutput(BaseModel):
    response: object

class VSMPayload(BaseModel):
    prompt: str
    image_base64: str
    mode: str

@app.post("/visual_search_model")
async def generate_vsm(data: VSMPayload):
    prompt = data.prompt
    image_base64 = data.image_base64
    image_data = base64.b64decode(image_base64)
    image = Image.open(BytesIO(image_data))
    mode = data.mode
    response = vsm.inference(image, prompt, mode)
    print(response)
    if mode == 'segmentation':
        response = response.cpu().tolist()
    elif mode == 'vqa':
        pass
    elif mode == 'detection':
        response = [r.cpu().tolist() for r in response]
    return VSMOutput(
        response=response,
    )

class VQAPostPayload(BaseModel):
    prompt: str
    image_base64: str
    bboxes: List[List[int]]
    object_names: List[str]

@app.post("/vqa_llm_post")
async def generate_from_base64(data: VQAPostPayload):
    prompt = data.prompt
    image_base64 = data.image_base64
    bboxes = data.bboxes
    object_names = data.object_names
    image_data = base64.b64decode(image_base64)
    image = Image.open(BytesIO(image_data))
    
    if len(object_names) <= 2:
        images_long = [False]
        objects_long = [True]*len(object_names)
    else:
        images_long = [False]
        objects_long = [False]*len(object_names)
    object_crops = []
    for bbox in bboxes:
        object_crop = vqa_llm.get_object_crop(image, bbox, patch_scale=1.2)
        object_crops.append(object_crop)
    object_crops = torch.stack(object_crops, 0)
    image, left, top = expand2square(image, tuple(int(x*255) for x in vqa_llm.image_processor.image_mean))
    bbox_list = []
    for bbox in bboxes:
        bbox[0] += left
        bbox[1] += top
        bbox_list.append(bbox)
    bbox_list = [normalize_bbox(bbox, image.width, image.height) for bbox in bbox_list]
    focus_msg = "Additional visual information to focus on: "
    cur_focus_msg = focus_msg
    for i, (object_name, bbox) in enumerate(zip(object_names, bbox_list)):
        cur_focus_msg = cur_focus_msg + "{} <object> at location [{:.3f},{:.3f},{:.3f},{:.3f}]".format(object_name, bbox[0], bbox[1], bbox[2], bbox[3])
        if i != len(bbox_list)-1:
            cur_focus_msg = cur_focus_msg+"; "
        else:
            cur_focus_msg = cur_focus_msg +'.'
    question_with_focus = cur_focus_msg+"\n"+prompt
    
    response = vqa_llm.free_form_inference(image, question_with_focus, object_crops=object_crops, objects_long=objects_long, images_long=images_long)
    return VQAOutput(
        generated_text=response,
    )