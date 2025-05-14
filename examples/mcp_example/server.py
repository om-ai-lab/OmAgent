from vlm_r1 import run_vlm_r1
from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP("VLM-R1-Server")


# Add an addition tool
@mcp.tool()
def vlm_r1(image_path, question):
    """A VLM to solve question of an image. Please input the image path and question."""
    model_name = "omlab/VLM-R1-Qwen2.5VL-3B-OVD-0321"
    if image_path is None:
        image_path = "/data0/qdl/test/old_women.png"
    if question is None:
        question = "Describe this image."
    return run_vlm_r1(model_name, image_path, question)


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run()
