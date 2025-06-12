import os
import re
import torch
import warnings
import gc
from typing import Union, Dict, List, Tuple, Optional
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info
from PIL import Image
import numpy as np

class VLMR1:
    def __init__(self, model, processor):
        """Initialize the VLMR1 model with a loaded model and processor."""
        self.model = model
        self.processor = processor
        # Don't move the model to device here, as it may be distributed across devices
        # when using device_map="auto"
        self.device = next(model.parameters()).device

    @classmethod
    def load(cls, model_path: str, use_flash_attention: bool = True, low_cpu_mem_usage: bool = True, 
             load_in_4bit: bool = False, load_in_8bit: bool = False, specific_device: Optional[str] = None):
        """Load the VLMR1 model from a checkpoint path.
        
        Args:
            model_path: Path to the model checkpoint
            use_flash_attention: Whether to use flash attention for better performance
            low_cpu_mem_usage: Whether to use low CPU memory usage during loading
            load_in_4bit: Whether to load the model in 4-bit precision
            load_in_8bit: Whether to load the model in 8-bit precision
            specific_device: Optional specific device to load the model on (e.g., 'cuda:0', 'cpu')
                             If None, will use device_map="auto" to distribute across GPUs
        
        Returns:
            A VLMR1 instance
        """
        # Clear CUDA cache before loading model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            gc.collect()
        
        # Determine attention implementation
        attn_implementation = "eager"  # Default fallback
        
        if use_flash_attention:
            try:
                # Try to import flash_attn to check if it's available
                import flash_attn
                attn_implementation = "flash_attention_2"
            except ImportError:
                warnings.warn(
                    "FlashAttention2 was requested but 'flash_attn' package is not installed. "
                    "Falling back to eager implementation. "
                    "To use FlashAttention2, install it with: pip install flash-attn --no-build-isolation"
                )
        
        # Configure quantization parameters
        quantization_config = None
        if load_in_4bit or load_in_8bit:
            try:
                from transformers import BitsAndBytesConfig
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=load_in_4bit,
                    load_in_8bit=load_in_8bit,
                    bnb_4bit_compute_dtype=torch.bfloat16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4"
                )
            except ImportError:
                warnings.warn(
                    "Quantization was requested but 'bitsandbytes' package is not installed. "
                    "Falling back to non-quantized model. "
                    "To use quantization, install it with: pip install bitsandbytes"
                )
        
        # Set device map for efficient memory usage
        device_map = None
        torch_dtype = torch.bfloat16
        
        if specific_device:
            device_map = specific_device
        elif torch.cuda.is_available():
            # If multiple GPUs and no specific device requested, use "auto"
            if torch.cuda.device_count() > 1:
                device_map = "auto"
            else:
                device_map = "cuda:0"  # Single GPU, use it directly
        
        # Load the model with memory optimization settings
        model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            model_path,
            torch_dtype=torch_dtype,
            attn_implementation=attn_implementation,
            low_cpu_mem_usage=low_cpu_mem_usage,
            quantization_config=quantization_config,
            device_map=device_map,
        )
        
        processor = AutoProcessor.from_pretrained(model_path)
        
        return cls(model, processor)
    
    def predict(self, image_path: str, question: str = None, max_new_tokens: int = 128,
                max_image_size: int = 512, resize_mode: str = "shorter") -> Dict:
        """Make a prediction using the model on a given image.
        
        Args:
            image_path: Path to the image file
            question: Optional question to ask about the image
                      If None, a generic prompt will be used
            max_new_tokens: Maximum number of tokens to generate
            max_image_size: Maximum size (in pixels) for the image dimension
            resize_mode: How to resize the image ('shorter', 'longer', or 'both')
                         - 'shorter': Resize the shorter side to max_image_size, maintain aspect ratio
                         - 'longer': Resize the longer side to max_image_size, maintain aspect ratio
                         - 'both': Force both dimensions to be at most max_image_size
        
        Returns:
            Dictionary containing the prediction results
        """
        # Clear CUDA cache before inference
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            gc.collect()

        if question is None:
            question = "Describe this image in detail. First output the thinking process in <think> </think> tags and then output the final answer in <answer> </answer> tags."
            
        # Resize the image to reduce memory usage
        resized_image_path = self._resize_image(image_path, max_image_size, resize_mode)
        
        # Prepare input for the model
        message = [{
            "role": "user",
            "content": [
                {"type": "image", "image": f"file://{resized_image_path}"},
                {"type": "text", "text": question}
            ]
        }]
        
        # Process input
        text = self.processor.apply_chat_template(message, tokenize=False, add_generation_prompt=True)
        image_inputs, video_inputs = process_vision_info(message)
        
        # Get the primary device used by the model for consistent device placement
        # For distributed models, this will be the device of the first parameter
        model_device = next(self.model.parameters()).device
        
        # Process inputs on CPU first to avoid OOM during preprocessing
        inputs = self.processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        )
        
        # Move inputs to the appropriate device (same as model's primary device)
        inputs = {k: v.to(model_device) if hasattr(v, 'to') else v for k, v in inputs.items()}
        
        # Generate with memory-efficient settings
        with torch.no_grad():
            # Force model to use the same device for all operations
            # This is important for distributed models to ensure consistent device usage
            generated_ids = self.model.generate(
                **inputs, 
                use_cache=True, 
                max_new_tokens=max_new_tokens, 
                do_sample=False,
                # Memory optimization settings
                early_stopping=True,
                num_beams=1,  # Disable beam search to save memory
            )
        
        # Clean up temporary resized image if created
        if resized_image_path != image_path and os.path.exists(resized_image_path):
            try:
                os.remove(resized_image_path)
            except:
                pass
        
        # Decode the response - use dictionary access rather than attribute access
        input_length = len(inputs['input_ids'][0])
        generated_ids_trimmed = generated_ids[0, input_length:]
        output_text = self.processor.decode(
            generated_ids_trimmed, 
            skip_special_tokens=True, 
            clean_up_tokenization_spaces=False
        )
        
        # Extract bounding box if available
        bbox = self._extract_bbox_answer(output_text)
        
        # Prepare result
        result = {
            "raw_output": output_text,
            "bbox": bbox if bbox != [0, 0, 0, 0] else None
        }
        
        # Extract thinking and answer sections
        think_match = re.search(r'<think>(.*?)</think>', output_text, re.DOTALL)
        if think_match:
            result["thinking"] = think_match.group(1).strip()
            
        answer_match = re.search(r'<answer>(.*?)</answer>', output_text, re.DOTALL)
        if answer_match:
            result["answer"] = answer_match.group(1).strip()
        
        return result
    
    def _resize_image(self, image_path: str, max_size: int, resize_mode: str) -> str:
        """Resize an image to reduce memory usage.
        
        Args:
            image_path: Path to the original image
            max_size: Maximum size in pixels
            resize_mode: How to resize ('shorter', 'longer', or 'both')
        
        Returns:
            Path to the resized image (could be same as input if no resize needed)
        """
        try:
            # Open the image
            image = Image.open(image_path)
            
            # Get current dimensions
            width, height = image.size
            
            # Skip if image is already small enough
            if width <= max_size and height <= max_size and resize_mode != "both":
                return image_path
                
            # Calculate new dimensions
            if resize_mode == "shorter":
                # Resize the shorter side to max_size
                if width < height:
                    new_width = max_size
                    new_height = int(height * (max_size / width))
                else:
                    new_height = max_size
                    new_width = int(width * (max_size / height))
            elif resize_mode == "longer":
                # Resize the longer side to max_size
                if width > height:
                    new_width = max_size
                    new_height = int(height * (max_size / width))
                else:
                    new_height = max_size
                    new_width = int(width * (max_size / height))
            else:  # 'both'
                # Scale both dimensions to be at most max_size
                scale = min(max_size / width, max_size / height)
                new_width = int(width * scale)
                new_height = int(height * scale)
            
            # Perform resize
            resized_image = image.resize((new_width, new_height), Image.LANCZOS)
            
            # Create output path
            temp_dir = os.path.dirname(image_path)
            if not temp_dir:
                temp_dir = "."
            file_name = os.path.basename(image_path)
            name, ext = os.path.splitext(file_name)
            resized_path = os.path.join(temp_dir, f"{name}_resized{ext}")
            
            # Save the resized image
            resized_image.save(resized_path)
            
            return resized_path
            
        except Exception as e:
            warnings.warn(f"Error resizing image: {e}. Using original image.")
            return image_path
    
    def _extract_bbox_answer(self, content: str) -> List[int]:
        """Extract bounding box coordinates from the model output."""
        answer_tag_pattern = r'<answer>(.*?)</answer>'
        bbox_pattern = r'\{.*\[(\d+),\s*(\d+),\s*(\d+),\s*(\d+)]\s*.*\}'
        
        content_answer_match = re.search(answer_tag_pattern, content, re.DOTALL)
        if content_answer_match:
            content_answer = content_answer_match.group(1).strip()
            bbox_match = re.search(bbox_pattern, content_answer, re.DOTALL)
            if bbox_match:
                return [int(bbox_match.group(1)), int(bbox_match.group(2)), 
                        int(bbox_match.group(3)), int(bbox_match.group(4))]
        
        return [0, 0, 0, 0]


# Simple usage example
if __name__ == "__main__":
    # Load the model with memory optimization
    model_path = "omlab/VLM-R1-Qwen2.5VL-3B-OVD-0321"
    
    # Enable these options to reduce memory usage
    model = VLMR1.load(
        model_path, 
        use_flash_attention=True,   # Enable if flash-attn is installed
        low_cpu_mem_usage=True,
        load_in_8bit=False,         # Enable 8-bit quantization to reduce GPU memory
        specific_device="cuda:0"    # Force model to use a single GPU to avoid device mismatch
    )
    
    # Make a prediction with reduced max_new_tokens and image size
    image_path = "data2.png"
    result = model.predict(
        image_path, 
        "detect person in the image",
        max_new_tokens=1024,      # Reduce from 128 to save memory
        max_image_size=448,    # Reduce image size to 224x224 pixels (standard VLM input)
        resize_mode="shorter"     # Force both dimensions to be max 224 pixels
    )
    print(result)
    print(result["answer"] if "answer" in result else result["raw_output"]) 
