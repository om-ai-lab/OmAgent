from io import BytesIO
from pathlib import Path
from typing import Any, List, Optional, Union

import httpx
import requests
from PIL import Image
from pydantic import field_validator

from ....utils.registry import registry
from ...base import ArgSchema, BaseTool

CURRENT_PATH = Path(__file__).parents[0]

ARGSCHEMA = {
    "search_query": {
        "type": "string",
        "description": "The image keyword that wants to search.",
        "required": True,
    },
    "license": {
        "type": "string",
        "description": "Set license to public to search for images in the public domain",
        "required": True,
    },
    "image_type": {
        "type": "string",
        "description": "Set the imageType to photo to search only for photos.",
        "required": True,
    },
    "num_results": {
        "type": "integer",
        "description": "The number of results to return, default is 3, maximum is 5.",
        "required": True,
    },
}


@registry.register_tool()
class Text2ImageSearch(BaseTool):
    class Config:
        """Configuration for this pydantic object."""

        extra = "allow"
        arbitrary_types_allowed = True

    args_schema: ArgSchema = ArgSchema(**ARGSCHEMA)
    description: str = "Text to image search."

    def __init__(__pydantic_self__, **data: Any) -> None:
        super().__init__(**data)
        __pydantic_self__.client = httpx.AsyncClient(
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36"
            },
            verify=False,
            timeout=30.0,
            http2=True,
        )

    bing_api_key: Optional[str]
    bing_endpoint: str = "https://api.bing.microsoft.com/v7.0/images/search"

    @field_validator("bing_api_key")
    @classmethod
    def api_key_validator(cls, bing_api_key: Union[str, None]) -> Union[str, None]:
        if bing_api_key == None:
            raise ValueError("Bing API key is required for this tool.")
        return bing_api_key

    def _check_url_valid(self, url: str):
        local_prefixes = [
            "file:///",
            "file://127.0.0.1",
            "file://localhost",
            "http://localhost",
            "https://localhost",
            "http://2130706433",
            "https://2130706433",
            "http://127.0.0.1",
            "https://127.0.0.1",
            "https://0.0.0.0",
            "http://0.0.0.0",
            "http://0000",
            "https://0000",
        ]
        if any(url.startswith(prefix) for prefix in local_prefixes):
            raise ValueError(f"URL {url} is a local url, blocked!")
        if not (url.startswith("http") or url.startswith("file")):
            raise ValueError(
                f"URL {url} is not a http or https url, please give a valid url!"
            )

    def _run(
        self,
        search_query: str,
        license: str,
        image_type: str = "photo",
        num_results: int = 3,
    ) -> List[dict]:
        """
        This method is used to search for images based on the provided search query, license, image type, and number of results.

        Parameters:
        search_query (str): The keyword to search for images.
        license (str): The license type for the images. Set license to public to search for images in the public domain.
        image_type (str, optional): The type of images to search for. Default is "photo".
        num_results (int, optional): The number of results to return. Default is 3, maximum is 5.

        Returns:
        List[dict]: A list of dictionaries containing the image details. Each dictionary contains the name of the image,
        the image itself, and the URL of the host page.

        Raises:
        HTTPError: If the GET request to the Bing Image Search API fails.
        Exception: If there is an error while browsing the image.
        """
        # Send a GET request to the Bing Image Search API
        result = requests.get(
            self.bing_endpoint,
            headers={"Ocp-Apim-Subscription-Key": self.bing_api_key},
            params={"q": search_query, "license": license, "imageType": image_type},
            timeout=10,
        )

        # Raise an HTTPError if the GET request fails
        result.raise_for_status()

        # Parse the JSON response
        result = result.json()

        # Extract the image results from the response
        images = result["value"]

        image_results = []

        # Loop through the image results
        for idx in range(min(len(images), num_results)):
            try:
                # Browse the image
                img = self.browse_image(
                    images[idx]["contentUrl"], images[idx]["thumbnailUrl"]
                )
            except Exception as e:
                # Raise an exception if there is an error while browsing the image
                raise e

            # Create a dictionary containing the image details
            img_detail = {
                "name": images[idx]["name"],
                "img": img,
                "host_page_url": images[idx]["hostPageUrl"],
            }

            # Append the image details to the list of image results
            image_results.append(img_detail)

        # Return the list of image results
        return image_results

    def browse_image(self, content_url: str, thumbnail_url: str) -> Image.Image:
        """
        This method is used to fetch an image from a given URL. If fetching the image from the content URL fails,
        it attempts to fetch the image from the thumbnail URL.

        Parameters:
        content_url (str): The URL of the image to fetch.
        thumbnail_url (str): The URL of the thumbnail of the image to fetch.

        Returns:
        Image.Image: The fetched image.

        Raises:
        Exception: If there is an error while fetching the image from both the content URL and the thumbnail URL.
        """
        try:
            # Attempt to fetch the image from the content URL
            img = Image.open(BytesIO(requests.get(content_url).content))
        except Exception as e:
            # If fetching the image from the content URL fails, attempt to fetch the image from the thumbnail URL
            img = Image.open(BytesIO(requests.get(thumbnail_url).content))
        # Return the fetched image
        return img

    async def _arun(
        self,
        search_query: str,
        license: str,
        image_type: str = "photo",
        num_results: int = 3,
    ) -> List[dict]:
        result = await self.client.get(
            self.bing_endpoint,
            headers={"Ocp-Apim-Subscription-Key": self.bing_api_key},
            params={"q": search_query, "license": license, "imageType": image_type},
            timeout=10,
        )

        result.raise_for_status()
        result = result.json()
        images = result["value"]

        image_results = []

        for idx in range(min(len(images), num_results)):
            try:
                img = await self.async_abrowse_image(
                    images[idx]["contentUrl"], images[idx]["thumbnailUrl"]
                )
            except Exception as e:
                raise e

            img_detail = {
                "name": images[idx]["name"],
                "img": img,
                "host_page_url": images[idx]["hostPageUrl"],
            }
            image_results.append(img_detail)

        return image_results

    async def async_abrowse_image(self, content_url, thumbnail_url) -> Image.Image:
        try:
            img = Image.open(BytesIO(self.client.get(content_url).content))
        except Exception as e:
            img = Image.open(BytesIO(self.client.get(thumbnail_url).content))
        return img
