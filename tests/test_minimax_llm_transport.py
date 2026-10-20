"""Offline tests of the real SDK's serialized MiniMax requests."""

import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

import httpx
import yaml
from openai import AsyncOpenAI, OpenAI

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "omagent-core" / "src"))

from omagent_core.models.llms.minimax_llm import MiniMaxLLM
from omagent_core.models.llms.schemas import Message
from omagent_core.utils.registry import registry


class TestMiniMaxTransport(unittest.TestCase):
    """Capture HTTP payloads without replacing provider or SDK behavior."""

    def setUp(self):
        """Use in-memory HTTP transports for both real SDK clients."""
        self.requests = []
        self.http = httpx.Client(transport=httpx.MockTransport(self.respond))
        self.ahttp = httpx.AsyncClient(transport=httpx.MockTransport(self.respond))
        self.addCleanup(self.http.close)
        self.addCleanup(lambda: asyncio.run(self.ahttp.aclose()))
        for name, factory, client in (
            ("OpenAI", OpenAI, self.http),
            ("AsyncOpenAI", AsyncOpenAI, self.ahttp),
        ):
            patcher = patch(
                "omagent_core.models.llms.minimax_llm." + name,
                side_effect=lambda factory=factory, client=client, **kwargs: factory(
                    http_client=client, **kwargs
                ),
            )
            patcher.start()
            self.addCleanup(patcher.stop)

    def respond(self, request):
        """Record the serialized request and return a small API response."""
        payload = json.loads(request.content)
        self.requests.append((request, payload))
        if payload.get("stream"):
            chunk = {
                "id": "test",
                "object": "chat.completion.chunk",
                "created": 0,
                "model": payload["model"],
                "choices": [{"index": 0, "delta": {"content": "Hello"}}],
            }
            return httpx.Response(
                200,
                headers={"content-type": "text/event-stream"},
                text="data: " + json.dumps(chunk) + "\n\ndata: [DONE]\n\n",
            )
        return httpx.Response(200, json={
            "id": "test",
            "object": "chat.completion",
            "created": 0,
            "model": payload["model"],
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": "Hello"},
                "finish_reason": "stop",
            }],
        })

    def make_llm(self, **kwargs):
        """Resolve the registered provider with an explicit offline test key."""
        return registry.get_llm("MiniMaxLLM")(
            api_key="test-key", use_default_sys_prompt=False, **kwargs
        )

    def assert_model(self, expected):
        """Check routing, selected model, and absence of incompatible options."""
        request, payload = self.requests[-1]
        self.assertEqual(request.method, "POST")
        self.assertEqual(request.url.path, "/v1/chat/completions")
        self.assertEqual(payload["model"], expected)
        # Let the service apply its model-specific thinking defaults.
        for key in ("thinking", "reasoning_effort", "reasoning_split", "service_tier"):
            self.assertNotIn(key, payload)
        return request, payload

    @patch.object(MiniMaxLLM, "_get_location", return_value="unknown")
    def test_default_generate(self, _location):
        """An unconfigured provider sends Flash with its default system prompt."""
        llm = registry.get_llm("MiniMaxLLM")(api_key="test-key")
        result = llm.generate([Message.user("Hi")])
        self.assertEqual(result["choices"][0]["message"]["content"], "Hello")
        request, payload = self.assert_model("MiniMax-M3.1-Flash")
        self.assertEqual(request.url.host, "api.minimax.io")
        self.assertEqual(payload["messages"][0]["role"], "system")
        self.assertEqual(payload["messages"][-1], {"role": "user", "content": "Hi"})
        self.assertEqual(payload["max_tokens"], 2048)

    def test_example_configuration(self):
        """The shipped YAML reaches the same default model on the wire."""
        config_path = (Path(__file__).resolve().parents[1]
                       / "examples/step1_simpleVQA/configs/llms/minimax.yml")
        config = yaml.safe_load(config_path.read_text())
        config["api_key"] = "test-key"
        config["use_default_sys_prompt"] = False
        registry.get_llm(config["name"])(**config).generate([Message.user("Hi")])
        self.assert_model("MiniMax-M3.1-Flash")

    def test_explicit_models_and_endpoints(self):
        """Current, saved legacy, and custom IDs retain their configured route."""
        for endpoint in ("https://api.minimax.io/v1", "https://api.minimaxi.com/v1",
                         "https://custom.example/v1"):
            for model in ("MiniMax-M3.1-Flash", "MiniMax-M3", "MiniMax-M2.7",
                          "MiniMax-M2.5-highspeed", "saved-custom-model"):
                with self.subTest(endpoint=endpoint, model=model):
                    llm = self.make_llm(model_id=model, endpoint=endpoint)
                    llm.generate([Message.user("Hi")])
                    request, _ = self.assert_model(model)
                    self.assertEqual(str(request.url), endpoint + "/chat/completions")

    def test_image_and_history_preserved(self):
        """Changing the default preserves image content and conversation history."""
        messages = [
            Message.system("Describe the image"),
            Message.user("Earlier question"),
            Message(role="assistant", content="Earlier answer"),
            Message.user([
                {"type": "text", "text": "What is here?"},
                {"type": "image_url", "image_url": {
                    "url": "https://example.com/image.png", "detail": "low",
                }},
            ]),
        ]
        self.make_llm().generate(messages)
        _, payload = self.assert_model("MiniMax-M3.1-Flash")
        self.assertEqual([m["role"] for m in payload["messages"]],
                         ["system", "user", "assistant", "user"])
        self.assertEqual(payload["messages"][2]["content"], "Earlier answer")
        self.assertEqual(payload["messages"][3]["content"],
                         [c.model_dump(exclude_none=True) for c in messages[3].content])

    def test_async_generate(self):
        """The async public path retains each selected model."""
        for model in ("MiniMax-M3.1-Flash", "MiniMax-M3", "saved-custom-model"):
            with self.subTest(model=model):
                llm = self.make_llm(model_id=model)
                result = asyncio.run(llm.agenerate([Message.user("Hi")]))
                self.assertEqual(result["choices"][0]["message"]["content"], "Hello")
                self.assert_model(model)

    def test_streaming_generate(self):
        """Flash requests retain the synchronous streaming contract."""
        stream = self.make_llm(stream=True).generate([Message.user("Hi")])
        self.assertEqual([chunk.choices[0].delta.content for chunk in stream], ["Hello"])
        _, payload = self.assert_model("MiniMax-M3.1-Flash")
        self.assertTrue(payload["stream"])

    def test_environment_model_override(self):
        """A fresh interpreter sends the environment-selected model unchanged."""
        code = '''
import json
import httpx
from omagent_core.models.llms.minimax_llm import MiniMaxLLM
from omagent_core.models.llms.schemas import Message
from openai import OpenAI

def respond(request):
    assert json.loads(request.content)["model"] == "saved-environment-model"
    return httpx.Response(200, json={"choices": []})

llm = MiniMaxLLM(api_key="test-key", use_default_sys_prompt=False)
llm.client.close()
with httpx.Client(transport=httpx.MockTransport(respond)) as client:
    llm.client = OpenAI(api_key="test-key", http_client=client)
    llm.generate([Message.user("Hi")])
'''
        env = os.environ.copy()
        env["MINIMAX_MODEL_ID"] = "saved-environment-model"
        env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "omagent-core" / "src")
        subprocess.run([sys.executable, "-c", code], env=env, check=True,
                       capture_output=True, text=True, timeout=30)


if __name__ == "__main__":
    unittest.main()
