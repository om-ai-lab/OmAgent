from pathlib import Path
from typing import Any, Dict, Optional, Union

from pydantic import field_validator
from tavily import TavilyClient

from ....utils.logger import logging
from ....utils.registry import registry
from ...base import ArgSchema, BaseTool

CURRENT_PATH = Path(__file__).parents[0]

ARGSCHEMA = {
    "search_query": {
        "type": "string",
        "description": "The search query, the task need to be done.",
    },
    "topic": {
        "type": "string",
        "enum": ["general", "news"],
        "description": "This will optimized the search for the selected topic with tailored and curated information. Default is `general`.",
    },
    "include_answer": {
        "type": "boolean",
        "description": "Whether to include the conclude answer in the search results. Default is `True`.",
        "required": True,
    },
    "include_images": {
        "type": "boolean",
        "description": "Whether to include the images in the search results. Default is `False`.",
        "required": True,
    },
    "include_raw_content": {
        "type": "boolean",
        "description": "Whether to include the raw content in the search results. Default is `False`.",
        "required": False,
    },
    "days": {
        "type": "integer",
        "description": "The number of days to search for, only available when `topic` is `news`. Default is `3`.",
        "required": False,
    },
    "max_results": {
        "type": "integer",
        "description": "The maximum number of results to return. Default is `5`.",
        "required": True,
    },
}


@registry.register_tool()
class TavilyWebSearch(BaseTool):
    """Web Environment providing web interface and browsering."""

    class Config:
        """Configuration for this pydantic object."""

        extra = "allow"
        arbitrary_types_allowed = True

    args_schema: ArgSchema = ArgSchema(**ARGSCHEMA)
    description: str = "Searches the web for a query by tavily."
    tavily_api_key: Optional[str]

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self.tavily_client = TavilyClient(api_key=self.tavily_api_key)

    @field_validator("tavily_api_key")
    @classmethod
    def api_key_validator(cls, tavily_api_key: Union[str, None]) -> Union[str, None]:
        if tavily_api_key == None:
            raise ValueError("Tavily API key is not provided.")
        return tavily_api_key

    def _run(
        self,
        search_query: str,
        topic: str,
        include_answer: bool = True,
        include_images: bool = False,
        include_raw_content: bool = False,
        days: int = 3,
        max_results=5,
    ) -> Dict[str, Any]:
        """
        Search with search tools and browse the website returned by search. Note some websites may not be accessable due to network error.
        """
        # self.callback.info(
        #     agent_id=self.workflow_instance_id,
        #     progress=f"Conqueror",
        #     message=f"Detail of search structure: search_query: {search_query}, topic: {topic}, include_answer: {include_answer}, include_images: {include_images}, include_raw_content: {include_raw_content}, days: {days}, max_results: {max_results}.",
        # )

        try:
            search_results = self.tavily_client.search(
                query=search_query,
                topic=topic,
                days=days,
                max_results=max_results,
                include_answer=include_answer,
                include_raw_content=include_raw_content,
                include_images=include_images,
            )
            if include_answer:
                conclude_answer = search_results.get("answer", "")
            else:
                conclude_answer = ""
            if include_images:
                search_images = search_results.get("images", [])
            else:
                search_images = []
            results = search_results.get("results", [])
            if len(results):
                [each.pop("score") for each in results]
                if include_raw_content:
                    [each.pop("raw_content") for each in results]
            return {
                "answer": conclude_answer,
                "images": search_images,
                "results": results,
            }
        except Exception as e:
            logging.error(f"Tavily search failed: {e}")
            return {
                "answer": "",
                "images": [],
                "results": [],
            }
