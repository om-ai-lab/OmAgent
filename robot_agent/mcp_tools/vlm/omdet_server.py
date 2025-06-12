import os
import argparse
import sys
import base64
from typing import Optional, Dict, Any, List
import torch
from PIL import Image
import requests
from io import BytesIO

# Ensure the latest fastmcp is installed -----------------------------------------------------------
try:
    from fastmcp import FastMCP, Context
except ImportError:
    print("fastmcp not found – installing from GitHub ...")
    import subprocess
    subprocess.check_call([
        sys.executable,
        "-m",
        "pip",
        "install",
        "git+https://github.com/jlowin/fastmcp.git"
    ])
    from fastmcp import FastMCP, Context

# Import OmDet Turbo dependencies ---------------------------------------------------------------------------
try:
    from transformers import AutoProcessor, OmDetTurboForObjectDetection
except ImportError as e:
    print(f"Error importing transformers: {e}")
    print("You need to install required packages:\n  pip install torch transformers pillow")
    sys.exit(1)

# -----------------------------------------------------------------------------------------------
# Create the MCP server instance
mcp = FastMCP("OmDet Turbo Server – fastmcp 2.x")

# Keep global handles to the loaded model components so we only pay the load cost once
_processor: Optional[Any] = None
_model: Optional[Any] = None

def init_model(
    model_path: str = "omlab/omdet-turbo-swin-tiny-hf",
    device: str = "cuda:0",
    load_in_8bit: bool = False,
):
    """Lazy-load the OmDet Turbo model (only once per process)."""
    global _processor, _model
    
    if _processor is None or _model is None:
        print(f"[fastmcp-server] Loading OmDet Turbo from '{model_path}' … This may take a moment.")
        
        device_map = device if device != "cpu" else None
        _processor = AutoProcessor.from_pretrained(model_path)
        
        if load_in_8bit:
            _model = OmDetTurboForObjectDetection.from_pretrained(
                model_path,
                device_map=device_map,
                load_in_8bit=True,
            )
        else:
            _model = OmDetTurboForObjectDetection.from_pretrained(model_path)
            if device != "cpu":
                _model = _model.to(device)
                
        print("[fastmcp-server] Model ready! 🚀")
    
    return _processor, _model

# -------------------------------------------------------------------------------------------------
# RESOURCE: expose images so that remote clients can fetch binary data if they wish
@mcp.resource("image://{image_path}")
def image_resource(image_path: str) -> bytes:  # noqa: D401
    """Return the raw bytes of *image_path* so that clients can embed / inspect it."""
    if not os.path.exists(image_path):
        raise ValueError(f"Image not found at '{image_path}'.")
    with open(image_path, "rb") as fh:
        return fh.read()

# -------------------------------------------------------------------------------------------------
# Helper function to load images from path, URL, or base64 string
def load_image(image_source: str) -> Image.Image:
    """Load an image from a local path, URL, or base64 string.
    
    Args:
        image_source: Local path, URL, or base64-encoded string of an image
        
    Returns:
        PIL Image object
    """
    # Check if it's a base64 string
    if image_source.startswith('data:image/'):
        # Extract the base64 part after the comma
        base64_data = image_source.split(',')[1]
        image_data = base64.b64decode(base64_data)
        return Image.open(BytesIO(image_data))
    elif image_source.startswith(('http://', 'https://')):
        # Load from URL
        response = requests.get(image_source, stream=True)
        response.raise_for_status()  # Raise exception for HTTP errors
        return Image.open(BytesIO(response.content))
    else:
        # Try to decode as pure base64 string (without data URI prefix)
        try:
            image_data = base64.b64decode(image_source)
            return Image.open(BytesIO(image_data))
        except Exception:
            # Load from local path as fallback
            if not os.path.exists(image_source):
                raise ValueError(f"Image not found at '{image_source}'.")
            return Image.open(image_source)

# -------------------------------------------------------------------------------------------------
# TOOL: detect objects in image with specified classes
@mcp.tool()
def detect_objects(
    image_path_or_url_or_base64: str,
    classes: List[str],
    score_threshold: float = 0.3,
    nms_threshold: float = 0.3,
    ctx: Context | None = None,
) -> Dict[str, Any]:
    """Detect specified objects in an image using OmDet Turbo."""
    # Initialize model synchronously
    processor, model = init_model()
    if processor is None or model is None:
        raise RuntimeError("Model not initialised – call init_model() first or start the server with proper arguments")

    try:
        # Load image
        image = load_image(image_path_or_url_or_base64)
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Prepare text input - join classes with comma if multiple
        text_input = ", ".join(classes) if isinstance(classes, list) else classes
        
        # Process image - NOTE: Use 'images' (plural) not 'image' (singular)
        inputs = processor(images=image, text=text_input, return_tensors="pt")
        
        # Move inputs to model device if using GPU
        if next(model.parameters()).device.type != "cpu":
            inputs = {k: v.to(next(model.parameters()).device) for k, v in inputs.items()}
        
        # Run inference
        with torch.no_grad():
            outputs = model(**inputs)
        
        # Post-process results
        results = processor.post_process_grounded_object_detection(
            outputs,
            classes=classes,
            target_sizes=[image.size[::-1]],  # Height, Width format
            score_threshold=score_threshold,
            nms_threshold=nms_threshold
        )
        
        # Format results for API response
        detections = []
        if results and len(results) > 0:
            result = results[0]
            
            # Handle case where results might be empty
            scores = result.get("scores", [])
            class_names = result.get("classes", [])
            boxes = result.get("boxes", [])
            
            for score, class_name, box in zip(scores, class_names, boxes):
                # Convert tensor to float if necessary
                if hasattr(score, 'item'):
                    score_val = score.item()
                else:
                    score_val = float(score)
                
                # Convert box coordinates to list
                if hasattr(box, 'tolist'):
                    box_coords = [round(i, 2) for i in box.tolist()]
                else:
                    box_coords = [round(float(i), 2) for i in box]
                
                detections.append({
                    "class": str(class_name),
                    "score": round(score_val, 3),
                    "bbox": box_coords  # Changed from "box" to "bbox" for consistency
                })
        
        return {
            "detections": detections,
            "image_size": image.size,
            "classes_requested": classes,
            "num_detections": len(detections)
        }
    
    except Exception as e:
        import traceback
        error_details = {
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }
        print(f"[ERROR] Object detection failed: {error_details}")
        return error_details

# -------------------------------------------------------------------------------------------------
# TOOL: list available images in a directory
@mcp.tool()
def list_images(directory: str = ".") -> List[str]:
    """Return a list of image files (by path) found in *directory*."""
    exts = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
    if not os.path.exists(directory):
        return {"error": f"Directory not found: {directory}"}
    return [os.path.join(directory, f) for f in os.listdir(directory) if os.path.splitext(f)[1].lower() in exts]

# -------------------------------------------------------------------------------------------------
# Command-line interface so that users can run this file directly
DEFAULT_MODEL_PATH = "omlab/omdet-turbo-swin-tiny-hf"

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run an OmDet Turbo server powered by fastmcp 2.x")
    p.add_argument("--model-path", default=DEFAULT_MODEL_PATH, help="HuggingFace repo or local checkpoint directory")
    p.add_argument("--device", default="cuda:1", help="Device to run on (e.g. cuda:0 or cpu)")
    p.add_argument("--load-in-8bit", action="store_true", help="Load in 8-bit precision")
    p.add_argument("--port", type=int, default=8089, help="Port to run server on")
    return p.parse_args()


def main():
    args = _parse_args()

    # Pre-load model so that first request is fast (optional but helpful)
    init_model(
        model_path=args.model_path,
        device=args.device,
        load_in_8bit=args.load_in_8bit,
    )
    
    mcp.run(transport="sse", host="0.0.0.0", port=args.port)


if __name__ == "__main__":
    main()
