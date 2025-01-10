from pathlib import Path
from typing import Any, List, Optional, Union

import httpx
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from pydantic import Field, field_validator

from ....models.llms.base import BaseLLM, BaseLLMBackend
from ....models.llms.openai_gpt import OpenaiGPTLLM
from ....models.llms.prompt import PromptTemplate
from ....utils.logger import logging
from ....utils.registry import registry
from ...base import ArgSchema, BaseTool

CURRENT_PATH = Path(__file__).parents[0]

ARGSCHEMA = {
    "search_query": {"type": "string", "description": "The search query."},
    "goals_to_browse": {
        "type": "string",
        "description": "What's you want to find on the website returned by search. If you need more details, request it in here. Examples: 'What is latest news about deepmind?', 'What is the main idea of this article?'",
    },
    "region": {
        "type": "string",
        "description": "The region code of the search, default to `en-US`. Available regions: `en-US`, `zh-CN`, `ja-JP`, `de-DE`, `fr-FR`, `en-GB`.",
        "required": True,
    },
    "num_results": {
        "type": "integer",
        "description": "The page number of results to return, default is 1, maximum is 3.",
        "required": True,
    },
}


@registry.register_tool()
class WebSearch(BaseTool, BaseLLMBackend):
    """Web Environment providing web interface and browsering."""

    class Config:
        """Configuration for this pydantic object."""

        extra = "allow"
        arbitrary_types_allowed = True

    args_schema: ArgSchema = ArgSchema(**ARGSCHEMA)
    description: str = (
        "Searches the web for multiple queries or mimic multiple API calls."
    )
    prompts: List[PromptTemplate] = Field(
        default=[
            PromptTemplate.from_file(
                CURRENT_PATH.joinpath("search_sys_prompt.prompt"), role="system"
            ),
            PromptTemplate.from_file(
                CURRENT_PATH.joinpath("search_user_prompt.prompt"), role="user"
            ),
        ]
    )

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
    bing_endpoint: str = "https://api.bing.microsoft.com/v7.0/search"

    @field_validator("bing_api_key")
    @classmethod
    def api_key_validator(cls, bing_api_key: Union[str, None]) -> Union[str, None]:
        if bing_api_key == None:
            logging.warning("Bing API key is not provided, rollback to duckduckgo.")
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
        self, search_query: str, goals_to_browse: str, region: str = None, num_results=3
    ) -> List[str]:
        """Search with search tools and browse the website returned by search. Note some websites may not be accessable due to network error.

        :param string search_query: The search query.
        :param string goals_to_browse: What's you want to find on the website returned by search. If you need more details, request it in here. Examples: 'What is latest news about deepmind?', 'What is the main idea of this article?'
        :param string? region: The region code of the search, default to `en-US`. Available regions: `en-US`, `zh-CN`, `ja-JP`, `de-DE`, `fr-FR`, `en-GB`.
        :return string: The results of the search.
        """
        # self.callback.info(
        #     agent_id=self.workflow_instance_id,
        #     progress=f"Conqueror",
        #     message=f'Searching for "{search_query}".',
        # )
        if region is None:
            region = "en-US"
        if self.bing_api_key is None:
            pages = [
                {"name": ret["title"], "snippet": ret["body"], "url": ret["href"]}
                for ret in DDGS().text(search_query, region="wt-wt")
            ]

        else:
            try:
                result = requests.get(
                    self.bing_endpoint,
                    headers={"Ocp-Apim-Subscription-Key": self.bing_api_key},
                    params={"q": search_query, "mkt": region},
                    timeout=10,
                )

                result.raise_for_status()
                result = result.json()
                pages = result["webPages"]["value"]
            except Exception as e:
                logging.error(f"Bing search failed: {e}")
                return [
                    {
                        "name": "",
                        "snippet": "",
                        "url": "",
                        "page": "",
                    }
                ]

        search_results = []

        for idx in range(min(len(pages), num_results)):
            try:
                page = self.browse_website(pages[idx]["url"], goals_to_browse)
                page = self.simple_infer(search_results=page)["choices"][0]["message"][
                    "content"
                ]
            except httpx.HTTPStatusError as e:
                page = e.response.text
            except Exception as e:
                page = str(e)

            message = {
                "name": pages[idx]["name"],
                "snippet": pages[idx]["snippet"],
                "url": pages[idx]["url"],
                "page": page,
            }
            search_results.append(message)

        return search_results

    def browse_website(self, url: str, goals_to_browse: str) -> str:
        """Give a http or https url to browse a website and return the summarize text. Note some websites may not be accessable due to network error. This tool only return the content of give url and cannot provide any information need interaction with the website.

        :param string url: The realworld Uniform Resource Locator (web address) to scrape text from. Never provide something like "<URL of the second news article>", give real url!!! Example: 'https://www.deepmind.com/'
        :param string goals_to_browse: The goals for browse the given `url` (e.g. what you want to find on webpage.). If you need more details, request it in here.
        :return string: The content of the website, with formatted text.
        """
        # self._check_url_valid(url)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36"
        }
        res = requests.get(url, headers=headers, timeout=30)
        if res.status_code in [301, 302, 307, 308]:
            res = requests.get(res.headers["location"])
        else:
            res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = "\n".join(chunk for chunk in chunks if chunk)

        links = soup.find_all("a")
        if len(links) > 0:
            text += "\n\nLinks:\n"
            for link in links:
                if link.string != None and link.get("href") != None:
                    striped_link_string = link.string.strip()
                    if striped_link_string != "" and link.get("href").startswith(
                        "http"
                    ):
                        text += f"{striped_link_string} ({link.get('href')})\n"

        return text
