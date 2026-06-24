# Introduce to TwelveLabs Video tool

# Introduction

[TwelveLabs](https://twelvelabs.io) provides state-of-the-art video understanding models. This tool wraps two of them:

- **Pegasus** (`task: analyze`) — video understanding. Answer a natural language prompt about a video, e.g. summarize it, list the objects shown, or describe what happens.
- **Marengo** (`task: embed`) — multimodal embeddings. Produce a 512-dim embedding vector from text or an image. Text, image and video share one embedding space, so a text/image vector can be used to retrieve relevant videos.

This lets OmAgent's multimodal agents reason about videos by URL without running a local video model.

# How to use

## Use the TwelveLabs Video tool

YAML file in the configs folder defines available tools. The TwelveLabs Video tool can be enabled by adding the following config.

```yaml
llm: ${sub|text_res}
tools:
    - ...other tools...
    - name: TwelveLabsVideo # enable the TwelveLabs video tool
      api_key: ${env|twelvelabs_api_key, null} # set the TwelveLabs API key via environment variable
```

## Get a TwelveLabs API key

1.  Open [https://twelvelabs.io](https://twelvelabs.io) and sign up (there is a generous free tier).

2.  Create an API key from the dashboard.

3.  Copy it and set the environment variable, e.g. `export twelvelabs_api_key=tlk-xxx` in your terminal, or `os.environ['twelvelabs_api_key'] = "tlk-xxx"` in `run_cli/app/webpage.py`.

## Input Parameters

1.  task
    1.  type: string
    2.  enum: ["analyze", "embed"]
    3.  description: Which capability to use. `analyze` runs Pegasus to answer a prompt about a video. `embed` runs Marengo to produce an embedding vector.
    4.  required: True
2.  prompt
    1.  type: string
    2.  description: For `analyze`: the question or instruction about the video.
3.  text
    1.  type: string
    2.  description: For `embed`: the text to embed into a multimodal vector.
4.  image_url
    1.  type: string
    2.  description: For `embed`: a public URL to an image to embed.
5.  video_url
    1.  type: string
    2.  description: For `analyze`: a public URL to the video file. TwelveLabs fetches it server-side.
6.  max_tokens
    1.  type: integer
    2.  description: For `analyze`: maximum number of tokens to generate. Default is `2048`.

## Output Data

For `task: analyze`:

1.  text
    1.  type: string
    2.  description: The model's answer about the video.
2.  finish_reason
    1.  type: string
    2.  description: Why generation stopped.

For `task: embed`:

1.  embedding
    1.  type: List[float]
    2.  description: The 512-dim embedding vector.
2.  dimension
    1.  type: integer
    2.  description: The vector dimension (512).

## Quick Experience

```python
from omagent_core.tool_system.tools.twelvelabs_video.twelvelabs_video import TwelveLabsVideo

tool = TwelveLabsVideo(api_key="tlk-xxx")

# Marengo embedding
res = tool.run({"task": "embed", "text": "a cat playing piano"})
print(res["dimension"], res["embedding"][:3])

# Pegasus video understanding
res = tool.run({
    "task": "analyze",
    "video_url": "https://example.com/your-video.mp4",
    "prompt": "Describe what happens in this video.",
})
print(res["text"])
```
