import os
import requests
import io
import base64
from typing import Any, Dict, List, Union, Optional
from PIL import Image

from pydantic import Field

from omagent_core.utils.registry import registry
from omagent_core.models.llms.base import BaseLLM
from omagent_core.models.llms.schemas import Content, Message


@registry.register_llm()
class VStarLLM(BaseLLM):
    """VStar LLM backend for visual understanding tasks."""
    
    endpoint: str = Field(
        default=os.getenv("ENDPOINT", "https://vstar.om-ai.com"),
        description="The endpoint of VStar service"
    )
    # temperature: float = Field(default=1.0, description="The temperature of LLM")
    # max_tokens: int = Field(default=2048, description="The max tokens of LLM")
    
    class Config:
        """Configuration for this Pydantic object."""
        protected_namespaces = ()
        extra = "allow"

    def model_post_init(self, __context: Any) -> None:
        """Initialize the VStar client."""
        # No specific client initialization needed for REST API calls
        pass

    def _image_to_base64(self, img: Image.Image) -> str:
        """Convert a PIL.Image object to base64 encoding.
        
        Args:
            img (Image.Image): The image to convert.
        
        Returns:
            str: Base64 encoded string of the image.
        """
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    def _prepare_vstar_request(self, prompt: str, image: Image.Image, **kwargs) -> Dict:
        """Prepare VStar API request data from the prompt and image.
        
        Args:
            prompt (str): The text prompt for the VStar API.
            image (Image.Image): The image to be processed.
        
        Returns:
            Dict: A dictionary containing the prepared request data.
        
        Raises:
            ValueError: If the image is None.
        """
        # Ensure prompt is not None
        if prompt is None:
            prompt = ""
        
        # Ensure image is provided
        if image is None:
            raise ValueError("Image is required for VStar API")
        
        # Prepare request data
        encoded_image = self._image_to_base64(image)
        data = {
            "prompt": prompt,
            "image_base64": encoded_image
        }
        
        # Update with any additional keyword arguments
        data.update(kwargs)
        return data
    
    def _call(self, prompt: str, image: Image.Image, model: str = "vqa_llm", mode: str = None, **kwargs) -> Dict:
        """Call the VStar API and return the response.
        
        Args:
            prompt (str): The text prompt for the API.
            image (Image.Image): The image to be processed.
            model (str): The model type to use (default is "vqa_llm").
            mode (str): The mode of operation (optional).
        
        Returns:
            Dict: The response from the VStar API formatted to match LLM output structure.
        
        Raises:
            RuntimeError: If the API response status code is not 200.
        """
        # Validate model and mode
        assert model in ["vqa_llm", "visual_search_model", "vqa_llm_post"], f"Invalid model: {model}"
        
        if model == "visual_search_model":
            assert mode in ["vqa", "detection", "segmentation"], f"Invalid mode: {mode}"
            data = self._prepare_vstar_request(prompt, image, mode=mode, **kwargs)
        else:
            assert mode is None, f"Mode should not be provided for model {model}"
            data = self._prepare_vstar_request(prompt, image, **kwargs)
        
        # Make API request
        response = requests.post(f"{self.endpoint}/{model}", json=data)
        
        # Check for successful response
        if response.status_code != 200:
            raise RuntimeError(f"Error: Received status code {response.status_code}")
        
        response_data = response.json()
        
        # Format response to match LLM output structure
        result = {
            "id": f"vstar-{model}-{mode}",
            "object": "chat.completion",
            "created": int(response.elapsed.total_seconds()),
            "model": "vstar",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_data.get("generated_text", response_data.get("response", ""))
                    },
                    "finish_reason": "stop"
                }
            ]
        }
        
        return result
    
    def vqa(self, prompt: str, image: Image.Image, **kwargs) -> Dict:
        """Perform Visual Question Answering (VQA) using the VStar LLM.
        
        Args:
            prompt (str): The question to be answered.
            image (Image.Image): The image to analyze.
        
        Returns:
            Dict: The response from the VStar API for the VQA task.
        """
        return self._call(prompt, image, model="vqa_llm", **kwargs)
    
    def visual_search(self, target_object_name: str, image: Image.Image, mode: str, **kwargs) -> Dict:
        """Perform a visual search for a target object using the VStar LLM.
        
        Args:
            target_object_name (str): The name of the object to locate.
            image (Image.Image): The image to search within.
            mode (str): The mode of the visual search (e.g., "vqa", "detection", "segmentation").
        
        Returns:
            Dict: The response from the VStar API for the visual search task.
        
        Raises:
            AssertionError: If the mode is invalid.
        """
        assert mode in ["vqa", "detection", "segmentation"], f"Invalid mode: {mode}"
        if mode == "vqa":
            prompt = f"According to the common sense knowledge and possible visual cues, what is the most likely location of the {target_object_name} in the image?"
        else:
            prompt = f"Please locate the {target_object_name} in this image."
        
        return self._call(prompt, image, model="visual_search_model", mode=mode, **kwargs)
    
    def vqa_post(self, prompt: str, image: Image.Image, **kwargs) -> Dict:
        """Perform post-processing for Visual Question Answering (VQA) using the VStar LLM.
        
        Args:
            prompt (str): The question to be answered.
            image (Image.Image): The image to analyze.
        
        Returns:
            Dict: The response from the VStar API for the VQA post-processing task.
        """
        return self._call(prompt, image, model="vqa_llm_post", **kwargs)
    
