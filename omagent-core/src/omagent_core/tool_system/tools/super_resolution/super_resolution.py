from ...base import BaseModelTool, ArgSchema
from ....utils.registry import registry
import requests
from PIL import Image
from io import BytesIO
import base64


ARGSCHEMA = {
    "image": {
        "type": "any",
        "description": "Image to be processed, can be a URL, local path, or base64 encoded image.",
        "required": True,
    }
}

@registry.register_tool()
class SuperResolution(BaseModelTool):
    args_schema: ArgSchema = ArgSchema(**ARGSCHEMA)
    description: str = "Super resolution tool using LDM Super Resolution pipeline from Diffusers."
    api_url: str = "http://10.0.0.26:8010/superres"      

    def _run(
        self,
        image,
        *args,
        **kwargs,
    ) -> dict:
        """
        Run super resolution on the provided image by calling an external API.

        Args:
            image: Image input which can be a URL string, base64 string, or PIL image.
        Returns:
            dict: A dictionary containing the upscaled PIL image.
        """
        # Determine the type of image input and prepare the payload
        payload = {}
        if isinstance(image, str):
            if image.startswith('http://') or image.startswith('https://'):
                payload = {"image_url": image}
            else:
                # Assume it's a base64 string
                payload = {"base64_image": image}
        elif isinstance(image, Image.Image):
            # Convert the PIL image to a base64 string
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            base64_image = base64.b64encode(buffered.getvalue()).decode()
            payload = {"base64_image": base64_image}
        else:
            raise ValueError("Unsupported image type. Please use a URL string, base64 string, or PIL image.")

        # URL of the FastAPI endpoint
        api_url = self.api_url

        # Send a POST request to the API endpoint
        response = requests.post(api_url, json=payload)

        if response.status_code == 200:
            data = response.json()
            encoded_image = data.get("upscaled_image")
            if not encoded_image:
                raise ValueError("No upscaled image found in response.")

            # Decode the base64 string into image bytes
            image_bytes = base64.b64decode(encoded_image)
            upscaled_image = Image.open(BytesIO(image_bytes))

            return {"upscaled_image": upscaled_image}
        else:
            raise RuntimeError(f"Error from API: {response.status_code} {response.text}")
