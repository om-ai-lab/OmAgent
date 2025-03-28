from typing import List
from copy import deepcopy
from PIL import Image, ImageDraw
from omagent_core.models.llms.schemas import Message
import re
from omagent_core.utils.general import encode_image

import numpy as np
import torch
from .tree import *

import spacy
nlp = spacy.load("en_core_web_sm")  # Load spaCy for NLP processing


# Constants for question templates and confidence thresholds
DECOMPOSED_QUESTION_TEMPLATE = "What is the appearance of the {}?"  # Template for generating object-specific questions
ANSWERING_CONFIDENCE_THRESHOLD_UPPER = 0.4  # Upper confidence threshold for accepting answers
ANSWERING_CONFIDENCE_THRESHOLD_LOWER = 0  # Lower bound for confidence before terminating search

# Constants for image processing parameters
SMALLEST_SIZE = 384  # Minimum size for image patches (px)
DEPTH_LIMIT = 5  # Maximum depth of image tree
NUM_INTERVEL = 2  # Number of nodes to add after each threshold adjustment

# Calculate node processing limit based on tree depth
def pop_limit_func(max_depth):
    """
    Determine the maximum number of nodes to process based on tree depth.
    Scales linearly with depth to balance thoroughness and efficiency.
    
    Args:
        max_depth: Maximum depth of the image tree
        
    Returns:
        int: Number of nodes to process before adjusting thresholds
    """
    return max_depth * 3

POP_LIMIT = pop_limit_func  # Function to calculate processing limit
THRESHOLD_DECREASE = [0.1, 0.1, 0.2]  # Sequence of threshold reductions during search


def get_visual_cues_generation_conversation(question: str):
    """
    Generate a conversation prompt for identifying visual cues in the image.
    Uses few-shot examples to guide the model in identifying relevant objects.
    
    Args:
        question: User's question about the image
        
    Returns:
        list: Conversation messages for the LLM
    """
    conversation = []
    # Prepare few-shot examples with question template and example pairs
    prompt = {
        "question_template": "Question: {}\nIf you want to answer the question, which objects' information do you need?",
        "question_list": [
            "What is the color of the boy's bag?",
            "Is the yellow car on the left or right side of the white car?",
            "Tell me the number on the black board above the dog.",
            "Is the girl with pink hair on the left or right side of the man with backpack?",
            "What kind of animal is on the red sign?",
            "How many cars in the image?"
        ],
        "response_list": [
            "To answer the question, I need know the location of the boy with a bag so that I can determine the color of the bag. So I need the information about the following objects: boy with a bag.",
            "To answer the question, I need know the location of the yellow car and the white car so that I can determine the positional relationship between the two of them. So I need the information about the following objects: white car and yellow car.",
            "To answer the question, I need know the location of the black board above the dog so that I can determine the number on it. So I need the information about the following objects: black board above the dog.",
            "To answer the question, I need know the location of the girl with pink hair and the man with backpack so that I can determine the positional relationship between the two of them. So I need the information about the following objects: girl with pink hair and man with backpack.",
            "To answer the question, I need know the location of the red sign so that I can determine the kind of animal on it. So I need the information about the following objects: red sign.",
            "To answer the question, I need know the location of all cars so that I can determine the number of cars. So I need the information about the following objects: all cars."
        ]
    }
    # Add example QA pairs to conversation
    for q, a in zip(prompt["question_list"], prompt["response_list"]):
        conversation.extend([
            Message.user(prompt["question_template"].format(q)),
            Message.assistant(a)
        ])
    
    # Add user question
    conversation.append(Message.user(prompt["question_template"].format(question)))
    
    return conversation

def get_prompt_tag(image_list):
    """
    Determine the prompt type based on the number of images.
    
    Args:
        image_list: List of images in the conversation
        
    Returns:
        str: 'global' for single image, 'zoom' for image with zoomed region
        
    Raises:
        ValueError: If unsupported number of images
    """
    if len(image_list) == 1:
        prompt_tag = "global"  # Single image - global view
    elif len(image_list) == 2:
        prompt_tag = "zoom"  # Two images - main image and zoomed region
    else:
        raise ValueError
    return prompt_tag


def get_confidence_conversation(node: Node, image_pil: Image.Image, confidence_type: str, input_ele, root_anyres=True):
    """
    Generate a conversation for evaluating confidence of a node.
    
    Args:
        node: The image tree node to evaluate
        image_pil: Original image
        confidence_type: Type of confidence to evaluate ('existence', 'latent', or 'answering')
        input_ele: Visual element or question to evaluate
        root_anyres: Whether to use any resolution for root node
        
    Returns:
        list: Conversation messages for the LLM
        
    Raises:
        AssertionError: If invalid confidence type
    """
    assert confidence_type in ['existence', 'latent', 'answering']
    zoom_eye_method = ZoomEyeMethod()
    # Process node into appropriate image format (original or with highlighted region)
    image_list = zoom_eye_method.process_nodes_to_image_list([node], image_pil, root_anyres=root_anyres)
    prompt_tag = get_prompt_tag(image_list)
    
    # Define prompts for different confidence types and image formats
    prompts = {
        "global":{
            "pre_informations": [""],
            "latent_prompt": "According to your common sense knowledge and the content of image, is it possible to find a {} by further zooming in the image? Answer Yes or No and tell the reason.",
            "existence_prompt": "Is there a {} in the image? Answer Yes or No.",
            "answering_prompt": "Question: {}\nCould you answer the question based on the the available visual information? Answer Yes or No.",
        },
        "zoom":{
            "pre_informations": ["This is the main image, and the section enclosed by the {BOX_COLOR} rectangle is the focus region.\n", "This is the zoomed-in view of the focus region.\n"],
            "latent_prompt": "According to your common sense knowledge and the content of the zoomed-in view, along with its location in the image, is it possible to find a {} by further zooming in the current view? Answer Yes or No and tell the reason.",
            "existence_prompt": "Is there a {} in the zoomed-in view? Answer Yes or No.",
            "answering_prompt": "Question: {}\nCould you answer the question based on the the available visual information? Answer Yes or No.",
        },
    }
    pre_informations = prompts[prompt_tag]["pre_informations"]
    instruction = prompts[prompt_tag][f"{confidence_type}_prompt"].format(input_ele)
    
    # Build conversation with images and instructions
    conversation = []
    input_content = []
    for image, pre_information in zip(image_list, pre_informations):
        if pre_information != "":
            input_content.append(pre_information)
        input_content.append(image)
    input_content.append(instruction)
    conversation.append(Message.user(input_content))
    
    return conversation
    
def calculate_confidence_from_logprobs(response, yes_tokens=["yes", "Yes", "YES"], no_tokens=["no", "No", "NO"]):
    """
    Calculate confidence score from model logprobs for Yes/No questions.
    
    Args:
        response: LLM response containing logprobs
        yes_tokens: List of tokens representing "yes"
        no_tokens: List of tokens representing "no"
        
    Returns:
        float: Confidence value in range [-1, 1], positive for "yes", negative for "no"
    """
    first_token_logprobs = response['choices'][0]['logprobs']['content'][0]['top_logprobs']

    yes_logprob = float('-inf')
    no_logprob = float('-inf')

    # Find the highest logprob for yes and no tokens
    for item in first_token_logprobs:
        if item['token'] in yes_tokens:
            yes_logprob = max(yes_logprob, item['logprob'])
        elif item['token'] in no_tokens:
            no_logprob = max(no_logprob, item['logprob'])
            
    # If neither yes nor no tokens found
    if yes_logprob == float('-inf') and no_logprob == float('-inf'):
        return 0.0

    # Convert logprobs to normalized confidence score
    logprob_yesno = [yes_logprob, no_logprob]
    yes_prob = torch.softmax(torch.tensor(logprob_yesno), dim=-1)[0] 
    confidence = 2 * (yes_prob.item() - 0.5)  # Map from [0,1] to [-1,1]

    return confidence  

def get_output_conversation(candidates: List[Node], image_pil: Image.Image, question: str):
    """
    Generate a conversation for producing the final answer.
    
    Args:
        candidates: List of nodes identified as relevant to the question
        image_pil: Original image
        question: User's question
        
    Returns:
        list: Conversation messages for the LLM
    """
    zoom_eye_method = ZoomEyeMethod()
    # Process candidate nodes into appropriate image format
    image_list = zoom_eye_method.process_nodes_to_image_list(candidates, image_pil)
    conversation = []
    input_content = []
    for image in image_list:
        input_content.append(image)
    input_content.append(question)
    conversation.append(Message.user(input_content))
    return conversation

def extract_targets(sentence: str, pattern = r"So I need the information about the following objects: (.+)"):
    """
    Extract target objects from the model's response.
    
    Args:
        sentence: Model response text
        pattern: Regex pattern to extract object list
        
    Returns:
        str: Extracted target objects as text, or None if not found
    """
    match = re.search(pattern, sentence)
    if match:
        return match.group(1)
    return None

def split_targets_sentence(targets_sentence:str, split_tag = r' and |, '):
    """
    Split a comma or 'and' separated list of target objects.
    
    Args:
        targets_sentence: String containing multiple targets
        split_tag: Regex pattern for splitting
        
    Returns:
        list: Individual target objects, or None if input is None
    """
    if targets_sentence is None:
        return None
    if targets_sentence.endswith('.'):
        targets_sentence = targets_sentence[:-1]  # Remove trailing period
    targets = re.split(split_tag, targets_sentence)
    return targets

def include_pronouns(text):
    """
    Check if text includes pronouns (which should be filtered out).
    
    Args:
        text: Text to check for pronouns
        
    Returns:
        bool: True if pronouns are present, False otherwise
    """
    doc = nlp(text)
    for token in doc:
        if token.pos_ == 'PRON':
            return True
    return False

def visualize_bbox_and_arrow(image: Image.Image, bbox, color="red", thickness=2, xyxy=False):
    """
    Draw a bounding box on an image.
    
    Args:
        image: PIL Image to draw on
        bbox: Bounding box coordinates
        color: Color of the bounding box
        thickness: Line thickness
        xyxy: Whether bbox format is [x1,y1,x2,y2] instead of [x,y,w,h]
        
    Returns:
        list: Adjusted bounding box coordinates
    """
    if not xyxy:
        x1, y1, w, h = bbox
        x2 = x1 + w
        y2 = y1 + h
    else:
        x1, y1, x2, y2 = bbox
    # Ensure bbox is within image bounds
    x1 = max(0, x1 - thickness)
    y1 = max(0, y1 - thickness)
    x2 = min(image.width, x2 + thickness)
    y2 = min(image.height, y2 + thickness)
    draw = ImageDraw.Draw(image)
    new_bbox = [x1, y1, x2, y2]
    draw.rectangle((x1, y1, x2, y2), outline=color, width=thickness)
    min_distance = thickness * 6
    center_x = image.width//2
    center_y = image.height//2
    center_x_bbox = (x1+x2)//2
    center_y_bbox = (y1+y2)//2
    return new_bbox

def expand2square(pil_img, background_color):
    """
    Expand image to square with padding if needed.
    
    Args:
        pil_img: Original PIL image
        background_color: Color for padding
        
    Returns:
        tuple: (Square image, x_offset, y_offset)
    """
    width, height = pil_img.size
    if width == height:
        return deepcopy(pil_img), 0, 0
    elif width > height:
        result = Image.new(pil_img.mode, (width, width), background_color)
        result.paste(pil_img, (0, (width - height) // 2))
        return result, 0, (width - height) // 2
    else:
        result = Image.new(pil_img.mode, (height, height), background_color)
        result.paste(pil_img, ((height - width) // 2, 0))
        return result, (height - width) // 2, 0

def bbox_area(bbox):
    """
    Calculate the area of a bounding box.
    
    Args:
        bbox: Bounding box in [x1,y1,x2,y2] format
        
    Returns:
        int: Area of the bounding box
    """
    x_min, y_min, x_max, y_max = bbox
    return (x_max - x_min) * (y_max - y_min)

def intersect_bbox(bboxA, bboxB, distance_buffer=50):
    """
    Find the intersection between two bounding boxes with buffer.
    
    Args:
        bboxA: First bounding box
        bboxB: Second bounding box
        distance_buffer: Buffer distance to expand boxes
        
    Returns:
        list: Intersection bounding box, or None if no intersection
    """
    bbox1 = [v-distance_buffer if i<2 else v+distance_buffer for i, v in enumerate(bboxA)]
    bbox2 = [v-distance_buffer if i<2 else v+distance_buffer for i, v in enumerate(bboxB)]
    
    x_min = max(bbox1[0], bbox2[0])
    y_min = max(bbox1[1], bbox2[1])
    x_max = min(bbox1[2], bbox2[2])
    y_max = min(bbox1[3], bbox2[3])

    if x_max > x_min and y_max > y_min:
        return (x_min, y_min, x_max, y_max)
    
    return None


def merge_bboxes(bbox1, bbox2):
    """
    Merge two bounding boxes into one containing both.
    
    Args:
        bbox1: First bounding box
        bbox2: Second bounding box
        
    Returns:
        tuple: Merged bounding box
    """
    return (
        min(bbox1[0], bbox2[0]),
        min(bbox1[1], bbox2[1]),
        max(bbox1[2], bbox2[2]),
        max(bbox1[3], bbox2[3])
    )

def union_all_bboxes(bboxes):
    """
    Find the union of all bounding boxes in a list.
    
    Args:
        bboxes: List of bounding boxes
        
    Returns:
        tuple: Union bounding box, or None if list is empty
    """
    if len(bboxes) == 0:
        return None
    ret = bboxes[0]
    for bbox in bboxes[1:]:
        ret = merge_bboxes(ret, bbox)
    return ret

def merge_bbox_list(bboxes, threshold=0):
    """
    Merge all intersecting bounding boxes in a list.
    
    Args:
        bboxes: List of bounding boxes
        threshold: Overlap threshold for merging (0-1)
        
    Returns:
        list: Merged bounding boxes
    """
    changed = True
    while changed:
        changed = False
        new_bboxes = []
        used = set()

        for i in range(len(bboxes)):
            if i in used:
                continue
            merged = False

            for j in range(len(bboxes)):
                if j in used or i == j:
                    continue
                intersection = intersect_bbox(bboxes[i], bboxes[j])
                if intersection:
                    if threshold == 0 or (threshold > 0 and (bbox_area(intersection) >= threshold * bbox_area(bboxes[i]) or bbox_area(intersection) >= threshold * bbox_area(bboxes[j]))):
                        new_bbox = merge_bboxes(bboxes[i], bboxes[j])
                        new_bboxes.append(new_bbox)
                        used.update([i, j])
                        changed = True
                        merged = True
                        break
            if not merged and i not in used:
                new_bboxes.append(bboxes[i])

        bboxes = new_bboxes

    return bboxes

BOX_COLOR = 'red'  # Color for highlighting bounding boxes

class ZoomEyeMethod:
    """
    Class for processing image regions and creating visual representations.
    Handles the visual aspects of the ZoomEye system including image cropping,
    bounding box visualization, and image formatting.
    """
    def __init__(self, background_color=(127, 127, 127), patch_scale=1.2, bias_value=0.6):
        """
        Initialize the ZoomEye image processing method.
        
        Args:
            background_color: Color for padding and background
            patch_scale: Scale factor for image patches
            bias_value: Bias value for confidence weighting
        """
        self.background_color = background_color
        self.patch_scale = patch_scale
        self.input_size = (SMALLEST_SIZE, SMALLEST_SIZE)
        self.bias_value = bias_value

    def is_root_only(self, nodes: List[Node]):
        """Check if the list contains only the root node."""
        return (len(nodes)==1 and nodes[0].is_root)
    
    def include_root(self, nodes: List[Node]):
        """Check if the list includes the root node."""
        return any(node.is_root for node in nodes)
    
    def get_bbox_in_square_image(self, bbox, left, top):
        """Adjust bbox coordinates for a square padded image."""
        x1, y1, x2, y2 = bbox
        return [x1+left, y1+top, x2+left, y2+top]

    def get_patch(self, bbox, image_width, image_height, patch_size, patch_scale=None):
        """
        Calculate patch coordinates based on object bbox.
        Centers the patch on the object and ensures minimum size.
        
        Args:
            bbox: Object bounding box [x,y,w,h]
            image_width: Width of the original image
            image_height: Height of the original image
            patch_size: Minimum patch size
            patch_scale: Optional scaling factor
            
        Returns:
            list: Patch coordinates [left,top,right,bottom]
        """
        object_width = int(np.ceil(bbox[2]))
        object_height = int(np.ceil(bbox[3]))

        object_center_x = int(bbox[0] + bbox[2]/2)
        object_center_y = int(bbox[1] + bbox[3]/2)

        patch_width = max(object_width, patch_size)
        patch_height = max(object_height, patch_size)
        if patch_scale is not None:
            patch_width = int(patch_width*patch_scale)
            patch_height = int(patch_height*patch_scale)

        left = max(0, object_center_x-patch_width//2)
        right = min(left+patch_width, image_width)

        top = max(0, object_center_y-patch_height//2)
        bottom = min(top+patch_height, image_height)

        return [left, top, right, bottom]

    def draw_bbox_arrow_in_square_image(self, square_image, resized_bbox, color):
        """Draw bounding box on an image with appropriate thickness."""
        thickness = square_image.width//120
        new_bbox = visualize_bbox_and_arrow(square_image, resized_bbox, color, thickness, xyxy=True)
        return new_bbox

    def process_nodes_to_image_list(self, nodes: List[Node], image_pil, root_anyres=True):
        """
        Process nodes into a list of images for visualization.
        
        For root node: returns just the original image
        For other nodes: returns original image with highlighted region + zoomed view
        
        Args:
            nodes: List of nodes to visualize
            image_pil: Original image
            root_anyres: Whether to use original resolution for root node
            
        Returns:
            list: List of images for the conversation
        """
        square_image, left, top = expand2square(image_pil, self.background_color)
        if self.is_root_only(nodes):
            return [deepcopy(image_pil)] if root_anyres else [square_image.resize(self.input_size)]
        if len(nodes) == 0 or self.include_root(nodes):
            return [deepcopy(image_pil)]
        
        # Get and merge bounding boxes for all nodes
        resized_bboxes = [self.get_patch(node.state.bbox, image_pil.width, image_pil.height, patch_size=self.input_size[0], patch_scale=self.patch_scale) for node in nodes]
        resized_bboxes = merge_bbox_list(resized_bboxes, threshold=0)

        # Draw bounding boxes on the square image
        full_color_bboxes = []
        for i in range(len(resized_bboxes)):
            resized_bbox = self.get_bbox_in_square_image(resized_bboxes[i], left, top)
            color_bbox = self.draw_bbox_arrow_in_square_image(square_image, resized_bbox, BOX_COLOR)
            full_color_bboxes.append(color_bbox)
        
        # Create zoomed view of the union of all bounding boxes
        union_color_bboxes = union_all_bboxes(full_color_bboxes)
        if union_color_bboxes is None:
            return [square_image]
        zoomed_view = square_image.crop(union_color_bboxes)
        print(union_color_bboxes)

        return [square_image.resize(self.input_size), zoomed_view]
    
    def get_confidence_weight(self, node: Node, max_depth: int):
        """
        Calculate confidence weight based on node depth.
        Deeper nodes get higher weight to prioritize detailed regions.
        
        Args:
            node: Node to calculate weight for
            max_depth: Maximum depth of the tree
            
        Returns:
            float: Confidence weight between bias_value and 1.0
        """
        coeff = (1 - self.bias_value) / (max_depth ** 2)
        return coeff * (node.depth**2) + self.bias_value