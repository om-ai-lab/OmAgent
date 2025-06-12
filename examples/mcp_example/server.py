import os
import argparse
import sys
import tempfile
import shutil
import uuid
from typing import Optional, Dict, Any, List
import re
from urllib.parse import urlparse

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

# Try to import requests for URL handling
try:
    import requests
except ImportError:
    print("requests not found – installing...")
    import subprocess
    subprocess.check_call([
        sys.executable,
        "-m",
        "pip",
        "install",
        "requests"
    ])
    import requests

# Import our VLM-R1 model ---------------------------------------------------------------------------
try:
    from vlm_r1 import VLMR1
except ImportError as e:
    print(f"Error importing VLMR1: {e}")
    print("Make sure the src/vlm_r1.py file exists and all dependencies are installed.")
    print("You may need to install additional packages, e.g.:\n  pip install torch transformers pillow flash-attn bitsandbytes")
    sys.exit(1)

# -----------------------------------------------------------------------------------------------
# Create the MCP server instance
mcp = FastMCP("VLM-R1 Server – fastmcp 2.x")

# Keep a global handle to the loaded model so that we only pay the load cost once
_model: Optional[VLMR1] = None

# Global temp directory for downloaded images
_temp_dir = None

def get_temp_dir():
    """Get or create a temporary directory for downloaded images."""
    global _temp_dir
    if _temp_dir is None or not os.path.exists(_temp_dir):
        _temp_dir = tempfile.mkdtemp(prefix="vlm_r1_images_")
    return _temp_dir

def is_url(path: str) -> bool:
    """Check if the given string is a URL."""
    try:
        result = urlparse(path)
        return all([result.scheme, result.netloc])
    except:
        return False

def download_image(url: str) -> str:
    """Download an image from URL and return the local path."""
    try:
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        
        # Try to get the filename from the URL or generate a random one
        content_type = response.headers.get('Content-Type', '')
        if 'image' not in content_type:
            raise ValueError(f"URL does not point to an image (content-type: {content_type})")
            
        # Determine file extension
        if 'image/jpeg' in content_type or 'image/jpg' in content_type:
            ext = '.jpg'
        elif 'image/png' in content_type:
            ext = '.png'
        elif 'image/gif' in content_type:
            ext = '.gif'
        elif 'image/webp' in content_type:
            ext = '.webp'
        elif 'image/bmp' in content_type:
            ext = '.bmp'
        else:
            ext = '.jpg'  # Default to jpg
            
        # Create temporary file
        temp_dir = get_temp_dir()
        temp_path = os.path.join(temp_dir, f"{uuid.uuid4()}{ext}")
        
        # Save the image
        with open(temp_path, 'wb') as f:
            shutil.copyfileobj(response.raw, f)
            
        return temp_path
    except Exception as e:
        raise ValueError(f"Failed to download image from URL: {str(e)}")

def init_model(
    model_path: str,
    use_flash_attention: bool = True,
    low_cpu_mem_usage: bool = True,
    load_in_8bit: bool = False,
    specific_device: Optional[str] = None,
):
    """Lazy-load the VLM-R1 model (only once per process)."""
    global _model
    if _model is None:
        print(f"[fastmcp-server] Loading VLM-R1 from '{model_path}' … This can take a few minutes.")
        # When we pin the device, we must keep low_cpu_mem_usage=True per transformers semantics
        if specific_device is not None:
            low_cpu_mem_usage = True

        _model = VLMR1.load(
            model_path=model_path,
            use_flash_attention=use_flash_attention,
            low_cpu_mem_usage=low_cpu_mem_usage,
            load_in_8bit=load_in_8bit,
            specific_device=specific_device,
        )
        print("[fastmcp-server] Model ready! 🚀")
    return _model

# -------------------------------------------------------------------------------------------------
# RESOURCE: expose images so that remote clients can fetch binary data if they wish
@mcp.resource("image://{image_path}")
def image_resource(image_path: str) -> bytes:  # noqa: D401
    """Return the raw bytes of *image_path* so that clients can embed / inspect it."""
    if is_url(image_path):
        try:
            local_path = download_image(image_path)
            with open(local_path, "rb") as fh:
                return fh.read()
        except Exception as e:
            raise ValueError(f"Failed to fetch image from URL: {str(e)}")
    else:
        if not os.path.exists(image_path):
            raise ValueError(f"Image not found at '{image_path}'.")
        with open(image_path, "rb") as fh:
            return fh.read()

# -------------------------------------------------------------------------------------------------
# TOOL: generic analyse image
@mcp.tool()
async def analyze_image(
    image_path: str,
    question: Optional[str] = None,
    max_new_tokens: int = 1024,
    max_image_size: int = 448,
    resize_mode: str = "shorter",
    ctx: Context | None = None,
) -> Dict[str, Any]:
    """Run the multimodal VLM-R1 model on *image_path*.

    The *image_path* can be a local file path or a URL to an image.
    The default *question* asks for a detailed description. A custom question can be supplied by
    callers. The returned dict mirrors the output of :py:meth:`VLMR1.predict`.
    """
    global _model
    if _model is None:
        _model = init_model(DEFAULT_MODEL_PATH)
        
    if _model is None:
        raise RuntimeError("Model not initialised – call init_model() first or start the server with --model-path …")

    local_image_path = image_path
    
    # If image_path is a URL, download it
    if is_url(image_path):
        try:
            local_image_path = download_image(image_path)
        except Exception as e:
            return {"error": f"Failed to download image from URL: {str(e)}"}
    elif not os.path.exists(image_path):
        return {"error": f"Image not found: {image_path}"}

    if question is None:
        question = (
            "Describe this image in detail. First output the thinking process in <think></think> tags "
            "and then output the final answer in <answer></answer> tags."
        )

    # Run prediction directly
    try:
        result = _model.predict(
            image_path=local_image_path,
            question=question,
            max_new_tokens=max_new_tokens,
            max_image_size=max_image_size,
            resize_mode=resize_mode,
        )
        return result
    except Exception as e:
        return {"error": f"Error during prediction: {str(e)}"}

# -------------------------------------------------------------------------------------------------
# TOOL: object detection helper
@mcp.tool()
async def detect_objects(
    image_path: str,
    max_new_tokens: int = 1024,
    max_image_size: int = 448,
    ctx: Context | None = None,
) -> Dict[str, Any]:
    """Detect objects in *image_path* using VLM-R1. The image_path can be a local file or URL."""
    global _model
    if _model is None:
        _model = init_model(DEFAULT_MODEL_PATH)
        
    if _model is None:
        raise RuntimeError("Model not initialised – call init_model() first or start the server with --model-path …")

    local_image_path = image_path
    
    # If image_path is a URL, download it
    if is_url(image_path):
        try:
            local_image_path = download_image(image_path)
        except Exception as e:
            return {"error": f"Failed to download image from URL: {str(e)}"}
    elif not os.path.exists(image_path):
        return {"error": f"Image not found: {image_path}"}

    # Run prediction directly
    try:
        result = _model.predict(
            image_path=local_image_path,
            question="Detect all objects in this image. Provide bounding boxes if possible.",
            max_new_tokens=max_new_tokens,
            max_image_size=max_image_size,
            resize_mode="shorter",
        )
        return result
    except Exception as e:
        return {"error": f"Error during prediction: {str(e)}"}

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
# PROMPT helper – illustrates prompt templates
@mcp.prompt()
def image_analysis_prompt(image_path: str) -> str:
    """Generate a prompt to analyze an image (can be a local file or URL)."""
    return (
        "Please analyse the image at "
        f"{image_path}. First describe what you see, then identify key objects or elements in the image."
    )

# -------------------------------------------------------------------------------------------------
# Command-line interface so that users can run this file directly
DEFAULT_MODEL_PATH = "omlab/VLM-R1-Qwen2.5VL-3B-OVD-0321"

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run a VLM-R1 server powered by fastmcp 2.x")
    p.add_argument("--model-path", default=DEFAULT_MODEL_PATH, help="HuggingFace repo or local checkpoint directory")
    p.add_argument("--device", default="cuda:0", help="Device to run on (e.g. cuda:0 or cpu)")
    p.add_argument("--use-flash-attention", action="store_true", help="Enable flash-attention kernels if available")
    p.add_argument("--low-cpu-mem", action="store_true", help="Load with low CPU memory footprint")
    p.add_argument("--load-in-8bit", action="store_true", help="Load in 8-bit precision")
    return p.parse_args()


def main():
    args = _parse_args()

    # Pre-load model so that first request is fast (optional but helpful)
    init_model(
        model_path=args.model_path,
        use_flash_attention=args.use_flash_attention,
        low_cpu_mem_usage=args.low_cpu_mem,
        load_in_8bit=args.load_in_8bit,
        specific_device=args.device,
    )
    
    # Create temp directory for downloaded images
    get_temp_dir()
    
    try:
        mcp.run(transport="sse", host="0.0.0.0", port=8008)
    finally:
        # Clean up temp directory on exit
        if _temp_dir and os.path.exists(_temp_dir):
            shutil.rmtree(_temp_dir, ignore_errors=True)


if __name__ == "__main__":
    main() 
