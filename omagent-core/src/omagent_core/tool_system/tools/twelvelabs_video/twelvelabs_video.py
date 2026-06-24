from typing import Any, Dict

from pydantic import field_validator

from ....utils.logger import logging
from ....utils.registry import registry
from ...base import ArgSchema, BaseTool

ARGSCHEMA = {
    "task": {
        "type": "string",
        "enum": ["analyze", "embed"],
        "description": "Which TwelveLabs capability to use. `analyze` runs the Pegasus model to "
        "understand a video and answer a prompt (requires `video_url`). `embed` runs the Marengo "
        "model to produce a multimodal embedding vector for a piece of text or an image "
        "(requires `text` or `image_url`).",
        "required": True,
    },
    "prompt": {
        "type": "string",
        "description": "For `analyze`: the question or instruction about the video, "
        "e.g. 'Describe what happens in this video' or 'List every product shown'.",
        "required": False,
    },
    "text": {
        "type": "string",
        "description": "For `embed`: the text to embed into a multimodal vector "
        "(shares an embedding space with video, so it can be used for video retrieval).",
        "required": False,
    },
    "image_url": {
        "type": "string",
        "description": "For `embed`: a public URL to an image to embed into a multimodal vector.",
        "required": False,
    },
    "video_url": {
        "type": "string",
        "description": "For `analyze`: a public URL to the video file. TwelveLabs fetches it server-side.",
        "required": False,
    },
    "max_tokens": {
        "type": "integer",
        "description": "For `analyze`: maximum number of tokens to generate. Default is 2048.",
        "required": False,
    },
}


@registry.register_tool()
class TwelveLabsVideo(BaseTool):
    """Video understanding and multimodal embedding tool backed by the TwelveLabs API.

    Wraps two TwelveLabs models:
    - Pegasus (``analyze``): video understanding -- answer a natural language prompt about a video.
    - Marengo (``embed``): produce a 512-dim multimodal embedding vector from text or an image.
      Text/image/video share one embedding space, so a text or image vector can retrieve videos.

    Get a free API key at https://twelvelabs.io and provide it via ``api_key``
    (typically ``${env|twelvelabs_api_key}`` in a tool config).
    """

    class Config:
        """Configuration for this pydantic object."""

        extra = "allow"
        arbitrary_types_allowed = True

    args_schema: ArgSchema = ArgSchema(**ARGSCHEMA)
    description: str = (
        "Understand videos and generate multimodal embeddings with TwelveLabs. "
        "Use task='analyze' to answer questions about a video (Pegasus), or "
        "task='embed' to get an embedding vector for text or an image (Marengo)."
    )
    api_key: str
    analyze_model_name: str = "pegasus1.5"
    embed_model_name: str = "marengo3.0"

    @field_validator("api_key")
    @classmethod
    def api_key_validator(cls, api_key: str) -> str:
        if not api_key:
            raise ValueError(
                "TwelveLabs API key is not provided. Get a free key at https://twelvelabs.io."
            )
        return api_key

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        # Imported here so the dependency is only required when the tool is used.
        from twelvelabs import TwelveLabs

        self.client = TwelveLabs(api_key=self.api_key)

    def _run(
        self,
        task: str,
        prompt: str = None,
        text: str = None,
        image_url: str = None,
        video_url: str = None,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        if task == "analyze":
            return self._analyze(
                prompt=prompt, video_url=video_url, max_tokens=max_tokens
            )
        elif task == "embed":
            return self._embed(text=text, image_url=image_url)
        else:
            raise ValueError(
                "Unknown task {!r}. Must be one of 'analyze' or 'embed'.".format(task)
            )

    def _analyze(self, prompt: str, video_url: str, max_tokens: int) -> Dict[str, Any]:
        if not video_url:
            raise ValueError("`video_url` is required for task='analyze'.")
        if not prompt:
            raise ValueError("`prompt` is required for task='analyze'.")
        from twelvelabs.types.video_context import VideoContext_Url

        try:
            res = self.client.analyze(
                model_name=self.analyze_model_name,
                video=VideoContext_Url(url=video_url),
                prompt=prompt,
                max_tokens=max_tokens,
            )
            return {"text": res.data, "finish_reason": res.finish_reason}
        except Exception as e:
            logging.error(f"TwelveLabs analyze failed: {e}")
            return {"text": "", "error": str(e)}

    def _embed(self, text: str, image_url: str) -> Dict[str, Any]:
        if not text and not image_url:
            raise ValueError(
                "Either `text` or `image_url` is required for task='embed'."
            )
        if text and image_url:
            raise ValueError(
                "Provide exactly one of `text` or `image_url` for task='embed', not both."
            )
        try:
            if text:
                res = self.client.embed.create(
                    model_name=self.embed_model_name, text=text
                )
                vector = res.text_embedding.segments[0].float_
            else:
                res = self.client.embed.create(
                    model_name=self.embed_model_name, image_url=image_url
                )
                vector = res.image_embedding.segments[0].float_
            return {"embedding": vector, "dimension": len(vector)}
        except Exception as e:
            logging.error(f"TwelveLabs embed failed: {e}")
            return {"embedding": [], "error": str(e)}
