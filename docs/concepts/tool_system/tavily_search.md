# Introduce to Tavily Websearch tool

# Introduction

Tavily is a search engine tailored for AI agents, compared to the search data obtained from Bing and other search engines, the data retrieved by Tavily is cleaner.

# How to use

## Use Tavily websearch tool

YAML file in configs folder defines available tools, Tavily websearch tool can be simply utilized by add following config.

```yaml
llm: ${sub|text_res}
tools:
    - ...other tools...
    - name: TavilyWebSearch # set to use Tavily websearch tool
      tavily_api_key: ${env|tavily_api_key, null} # set the Tavily API key using environment variables.
```

## Get Tavily api key

1.  Open Tavily with [https://tavily.com/](https://tavily.com/).
    
2.  Login or sign up if you don't have account, then it will jump to the dashboard page automatically.
    
3.  ![image.png](../../images/tavily_guide.png)You can create a new API key. Copy it and set the environment variable like `export tavily_api_key=tvly-xxx`in terminal or `os.environ['tavily_api_key'] = "tvly-xxx"`in `run_cli/app/webpage.py`
    

## Input Parameters

1.  search\_query: 
    1.  type: string
    2.  description: The search query, the task need to be done.
2.  topic:
    1.  type: string
    2.  enum: ["general", "news"], # only can be general or news 
    3. description: This will optimized the search for the selected topic with tailored and curated information. Default is `general`. 
3.  include\_answer 
    1.  type: boolean,      
    2.  description: Whether to include the conclude answer in the search results. Default is `True`.
    3.  required: True
    
4.  include\_images:
    
    1.  type: boolean
        
    2.  description: Whether to include the images in the search results. Default is `False`.
        
    3.  required: True
    
5.  include\_raw\_content
    
    1.  type: boolean
        
    2.  description: Whether to include the raw content in the search results. Default is `False`.
    
6.  days
    
    1.  type: integer
        
    2.  description: The number of days to search for, only available when \`topic\` is \`news\`. Default is `3`.
    
7.  max\_results
    
    1.  type: integer
        
    2.  description: The maximum number of results to return. Default is `5`.
        
    3.  required: True
        

## Output Data

1.  answer
    
    1.  type: string
        
    2.  description: The conclude answer of the search query.
    
2.  images
    
    1.  type: List[string]
        
    2.  description: List of image urls, related image data of the search query.
    
3.  results
    
    1.  type: List[string]
        
    2.  description: List of content, where each content represents a search result.
        

## Quick Experience

```yaml
from omagent_core.tool_system.tools.web_search.tavily_search import TavilyWebSearch

tavily_search = TavilyWebSearch(tavily_api_key="tvly-xxx")

res = tavily_search._run(
    search_query="What is the capital of France?",
    topic="general",
    include_answer=True,
    include_images=True,
    include_raw_content=False,
    days=3,
    max_results=5,
)
print(res)

```