# Ollama
You can use Ollama to run your own model locally.
Following the instruction of [Ollama](https://github.com/ollama/ollama) to install Ollama.

### Start Ollama serving
Start Ollama serving:
```bash
ollama serve
```
Then pull the model you want to use:
```bash
ollama pull <your-ollama-model>
```
You can also run Ollama in other ways by the instruction of [Ollama](https://github.com/ollama/ollama).

### Modify the yaml of llms
Yaml is almost same as OpenaiGPT, just change the endpoint to the ollama url.
```yaml
name: OpenaiGPTLLM
model_id: <your-ollama-model>
api_key: ${env| custom_openai_key, abcd} # api_key is not needed
endpoint: ${env| custom_openai_endpoint, http://<your-ollama-endpoint-domain>:11434/v1}
temperature: 0
vision: true
```
Then you can use your local Ollama serving.