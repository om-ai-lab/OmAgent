"""Unit tests for MiniMaxLLM provider."""

import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Add the source path so we can import omagent_core
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "omagent-core",
        "src",
    ),
)

from omagent_core.models.llms.minimax_llm import (
    MINIMAX_API_BASE,
    MINIMAX_MODELS,
    MiniMaxLLM,
)
from omagent_core.models.llms.schemas import Content, Message, Role


class TestMiniMaxLLMConfig(unittest.TestCase):
    """Test MiniMaxLLM configuration and initialization."""

    @patch.dict(os.environ, {"MINIMAX_API_KEY": "test-key-123"})
    @patch("omagent_core.models.llms.minimax_llm.OpenAI")
    @patch("omagent_core.models.llms.minimax_llm.AsyncOpenAI")
    def test_default_config(self, mock_async, mock_sync):
        """Test default configuration values."""
        llm = MiniMaxLLM(api_key="test-key-123")
        self.assertEqual(llm.model_id, "MiniMax-M3")
        self.assertEqual(llm.endpoint, MINIMAX_API_BASE)
        self.assertAlmostEqual(llm.temperature, 0.7)
        self.assertEqual(llm.max_tokens, 2048)
        self.assertFalse(llm.stream)

    @patch("omagent_core.models.llms.minimax_llm.OpenAI")
    @patch("omagent_core.models.llms.minimax_llm.AsyncOpenAI")
    def test_custom_config(self, mock_async, mock_sync):
        """Test custom configuration values."""
        llm = MiniMaxLLM(
            api_key="test-key",
            model_id="MiniMax-M2.5-highspeed",
            temperature=0.3,
            max_tokens=4096,
            stream=True,
        )
        self.assertEqual(llm.model_id, "MiniMax-M2.5-highspeed")
        self.assertAlmostEqual(llm.temperature, 0.3)
        self.assertEqual(llm.max_tokens, 4096)
        self.assertTrue(llm.stream)

    @patch("omagent_core.models.llms.minimax_llm.OpenAI")
    @patch("omagent_core.models.llms.minimax_llm.AsyncOpenAI")
    def test_client_initialization(self, mock_async_cls, mock_sync_cls):
        """Test that OpenAI clients are initialized with correct params."""
        llm = MiniMaxLLM(api_key="test-key", endpoint="https://custom.api.com/v1")
        mock_sync_cls.assert_called_once_with(
            api_key="test-key", base_url="https://custom.api.com/v1"
        )
        mock_async_cls.assert_called_once_with(
            api_key="test-key", base_url="https://custom.api.com/v1"
        )


class TestTemperatureClamping(unittest.TestCase):
    """Test temperature clamping behavior."""

    @patch("omagent_core.models.llms.minimax_llm.OpenAI")
    @patch("omagent_core.models.llms.minimax_llm.AsyncOpenAI")
    def test_temperature_zero(self, mock_async, mock_sync):
        """Test temperature=0 is accepted."""
        llm = MiniMaxLLM(api_key="test-key", temperature=0)
        self.assertAlmostEqual(llm.temperature, 0.0)

    @patch("omagent_core.models.llms.minimax_llm.OpenAI")
    @patch("omagent_core.models.llms.minimax_llm.AsyncOpenAI")
    def test_temperature_one(self, mock_async, mock_sync):
        """Test temperature=1.0 is accepted."""
        llm = MiniMaxLLM(api_key="test-key", temperature=1.0)
        self.assertAlmostEqual(llm.temperature, 1.0)

    @patch("omagent_core.models.llms.minimax_llm.OpenAI")
    @patch("omagent_core.models.llms.minimax_llm.AsyncOpenAI")
    def test_temperature_clamp_high(self, mock_async, mock_sync):
        """Test temperature > 1.0 is clamped to 1.0."""
        llm = MiniMaxLLM(api_key="test-key", temperature=2.0)
        self.assertAlmostEqual(llm.temperature, 1.0)

    @patch("omagent_core.models.llms.minimax_llm.OpenAI")
    @patch("omagent_core.models.llms.minimax_llm.AsyncOpenAI")
    def test_temperature_clamp_negative(self, mock_async, mock_sync):
        """Test negative temperature is clamped to 0."""
        llm = MiniMaxLLM(api_key="test-key", temperature=-0.5)
        self.assertAlmostEqual(llm.temperature, 0.0)

    @patch("omagent_core.models.llms.minimax_llm.OpenAI")
    @patch("omagent_core.models.llms.minimax_llm.AsyncOpenAI")
    def test_temperature_clamp_in_call(self, mock_async, mock_sync):
        """Test temperature clamping during _call kwargs."""
        llm = MiniMaxLLM(api_key="test-key", temperature=0.5)
        clamped = llm._clamp_temperature(1.5)
        self.assertAlmostEqual(clamped, 1.0)
        clamped = llm._clamp_temperature(-1.0)
        self.assertAlmostEqual(clamped, 0.0)


class TestThinkTagStripping(unittest.TestCase):
    """Test think tag stripping from model responses."""

    @patch("omagent_core.models.llms.minimax_llm.OpenAI")
    @patch("omagent_core.models.llms.minimax_llm.AsyncOpenAI")
    def setUp(self, mock_async, mock_sync):
        self.llm = MiniMaxLLM(api_key="test-key")

    def test_strip_think_tags(self):
        """Test basic think tag stripping."""
        content = "<think>internal reasoning</think>The answer is 42."
        result = self.llm._strip_think_tags(content)
        self.assertEqual(result, "The answer is 42.")

    def test_strip_multiline_think_tags(self):
        """Test multiline think tag stripping."""
        content = "<think>\nstep 1\nstep 2\nstep 3\n</think>\nFinal answer."
        result = self.llm._strip_think_tags(content)
        self.assertEqual(result, "Final answer.")

    def test_no_think_tags(self):
        """Test content without think tags is unchanged."""
        content = "Hello, world!"
        result = self.llm._strip_think_tags(content)
        self.assertEqual(result, "Hello, world!")

    def test_none_content(self):
        """Test None content returns None."""
        result = self.llm._strip_think_tags(None)
        self.assertIsNone(result)

    def test_empty_think_tags(self):
        """Test empty think tags are stripped."""
        content = "<think></think>Result."
        result = self.llm._strip_think_tags(content)
        self.assertEqual(result, "Result.")


class TestResponseFormat(unittest.TestCase):
    """Test response format validation."""

    @patch("omagent_core.models.llms.minimax_llm.OpenAI")
    @patch("omagent_core.models.llms.minimax_llm.AsyncOpenAI")
    def test_text_format(self, mock_async, mock_sync):
        """Test text response format."""
        llm = MiniMaxLLM(api_key="test-key", response_format="text")
        self.assertEqual(llm.response_format, {"type": "text"})

    @patch("omagent_core.models.llms.minimax_llm.OpenAI")
    @patch("omagent_core.models.llms.minimax_llm.AsyncOpenAI")
    def test_json_format(self, mock_async, mock_sync):
        """Test json_object response format."""
        llm = MiniMaxLLM(api_key="test-key", response_format="json_object")
        self.assertEqual(llm.response_format, {"type": "json_object"})

    @patch("omagent_core.models.llms.minimax_llm.OpenAI")
    @patch("omagent_core.models.llms.minimax_llm.AsyncOpenAI")
    def test_dict_format(self, mock_async, mock_sync):
        """Test dict response format."""
        llm = MiniMaxLLM(api_key="test-key", response_format={"type": "json_object"})
        self.assertEqual(llm.response_format, {"type": "json_object"})


class TestMessageConversion(unittest.TestCase):
    """Test message conversion to API format."""

    @patch("omagent_core.models.llms.minimax_llm.OpenAI")
    @patch("omagent_core.models.llms.minimax_llm.AsyncOpenAI")
    def setUp(self, mock_async, mock_sync):
        self.llm = MiniMaxLLM(api_key="test-key", use_default_sys_prompt=False)

    def test_simple_text_message(self):
        """Test simple text message conversion."""
        messages = [Message.user("Hello")]
        result = self.llm._msg2req(messages)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["role"], Role.USER)
        self.assertEqual(result[0]["content"], "Hello")

    def test_system_message(self):
        """Test system message conversion."""
        messages = [
            Message.system("You are helpful"),
            Message.user("Hi"),
        ]
        result = self.llm._msg2req(messages)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["role"], Role.SYSTEM)
        self.assertEqual(result[1]["role"], Role.USER)

    def test_default_sys_prompt(self):
        """Test default system prompt is prepended."""
        llm = self.__class__._create_llm(use_default_sys_prompt=True)
        messages = [Message.user("Hi")]
        result = llm._msg2req(messages)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["role"], "system")
        self.assertIn("Current Datetime", result[0]["content"])

    @classmethod
    @patch("omagent_core.models.llms.minimax_llm.OpenAI")
    @patch("omagent_core.models.llms.minimax_llm.AsyncOpenAI")
    def _create_llm(cls, mock_async=None, mock_sync=None, **kwargs):
        return MiniMaxLLM(api_key="test-key", **kwargs)


class TestCallMethod(unittest.TestCase):
    """Test the _call method."""

    @patch("omagent_core.models.llms.minimax_llm.OpenAI")
    @patch("omagent_core.models.llms.minimax_llm.AsyncOpenAI")
    def test_call_success(self, mock_async, mock_sync):
        """Test successful _call."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.model_dump.return_value = {
            "choices": [
                {
                    "message": {"content": "Hello! How can I help?", "role": "assistant"},
                    "index": 0,
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15,
            },
        }
        mock_client.chat.completions.create.return_value = mock_response
        mock_sync.return_value = mock_client

        llm = MiniMaxLLM(api_key="test-key", use_default_sys_prompt=False)
        messages = [Message.user("Hello")]
        result = llm._call(messages)

        self.assertEqual(result["choices"][0]["message"]["content"], "Hello! How can I help?")
        mock_client.chat.completions.create.assert_called_once()

    @patch("omagent_core.models.llms.minimax_llm.OpenAI")
    @patch("omagent_core.models.llms.minimax_llm.AsyncOpenAI")
    def test_call_with_think_tags(self, mock_async, mock_sync):
        """Test _call strips think tags from response."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.model_dump.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "<think>reasoning here</think>The answer is 42.",
                        "role": "assistant",
                    },
                    "index": 0,
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }
        mock_client.chat.completions.create.return_value = mock_response
        mock_sync.return_value = mock_client

        llm = MiniMaxLLM(api_key="test-key", use_default_sys_prompt=False)
        messages = [Message.user("What is 6*7?")]
        result = llm._call(messages)

        self.assertEqual(result["choices"][0]["message"]["content"], "The answer is 42.")

    @patch("omagent_core.models.llms.minimax_llm.OpenAI")
    @patch("omagent_core.models.llms.minimax_llm.AsyncOpenAI")
    def test_call_no_api_key(self, mock_async, mock_sync):
        """Test _call raises error without api key."""
        llm = MiniMaxLLM(api_key="", use_default_sys_prompt=False)
        messages = [Message.user("Hello")]
        with self.assertRaises(ValueError):
            llm._call(messages)

    @patch("omagent_core.models.llms.minimax_llm.OpenAI")
    @patch("omagent_core.models.llms.minimax_llm.AsyncOpenAI")
    def test_call_streaming(self, mock_async, mock_sync):
        """Test _call returns stream object when streaming."""
        mock_client = MagicMock()
        mock_stream = MagicMock()
        mock_client.chat.completions.create.return_value = mock_stream
        mock_sync.return_value = mock_client

        llm = MiniMaxLLM(api_key="test-key", stream=True, use_default_sys_prompt=False)
        messages = [Message.user("Hello")]
        result = llm._call(messages)

        self.assertEqual(result, mock_stream)

    @patch("omagent_core.models.llms.minimax_llm.OpenAI")
    @patch("omagent_core.models.llms.minimax_llm.AsyncOpenAI")
    def test_call_temperature_clamping(self, mock_async, mock_sync):
        """Test that temperature is clamped in _call."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.model_dump.return_value = {
            "choices": [{"message": {"content": "ok", "role": "assistant"}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }
        mock_client.chat.completions.create.return_value = mock_response
        mock_sync.return_value = mock_client

        llm = MiniMaxLLM(api_key="test-key", use_default_sys_prompt=False)
        messages = [Message.user("Hello")]
        llm._call(messages, temperature=5.0)

        call_kwargs = mock_client.chat.completions.create.call_args
        self.assertAlmostEqual(call_kwargs.kwargs["temperature"], 1.0)


class TestModelConstants(unittest.TestCase):
    """Test model constants and metadata."""

    def test_minimax_models_defined(self):
        """Test that all MiniMax models are defined."""
        self.assertIn("MiniMax-M3", MINIMAX_MODELS)
        self.assertIn("MiniMax-M2.7", MINIMAX_MODELS)
        self.assertIn("MiniMax-M2.7-highspeed", MINIMAX_MODELS)
        self.assertIn("MiniMax-M2.5", MINIMAX_MODELS)
        self.assertIn("MiniMax-M2.5-highspeed", MINIMAX_MODELS)

    def test_model_context_sizes(self):
        """Test model context window sizes."""
        self.assertEqual(MINIMAX_MODELS["MiniMax-M3"], 1000000)
        self.assertEqual(MINIMAX_MODELS["MiniMax-M2.7"], 204800)
        self.assertEqual(MINIMAX_MODELS["MiniMax-M2.7-highspeed"], 1048576)
        self.assertEqual(MINIMAX_MODELS["MiniMax-M2.5"], 204800)
        self.assertEqual(MINIMAX_MODELS["MiniMax-M2.5-highspeed"], 204800)

    def test_api_base_url(self):
        """Test MiniMax API base URL."""
        self.assertEqual(MINIMAX_API_BASE, "https://api.minimax.io/v1")


class TestRegistration(unittest.TestCase):
    """Test registry integration."""

    def test_llm_registered(self):
        """Test that MiniMaxLLM is registered in the registry."""
        from omagent_core.utils.registry import registry

        llm_cls = registry.get_llm("MiniMaxLLM")
        self.assertIsNotNone(llm_cls)
        self.assertEqual(llm_cls.__name__, "MiniMaxLLM")


if __name__ == "__main__":
    unittest.main()
