"""Integration tests for MiniMaxLLM provider.

These tests require a valid MINIMAX_API_KEY environment variable.
Skip with: pytest -m "not integration"
"""

import asyncio
import os
import sys
import unittest

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

MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY", "")
SKIP_REASON = "MINIMAX_API_KEY not set"


@unittest.skipUnless(MINIMAX_API_KEY, SKIP_REASON)
class TestMiniMaxLLMIntegration(unittest.TestCase):
    """Integration tests that hit the real MiniMax API."""

    def setUp(self):
        from omagent_core.models.llms.minimax_llm import MiniMaxLLM

        self.llm = MiniMaxLLM(
            api_key=MINIMAX_API_KEY,
            model_id="MiniMax-M3",
            temperature=0,
            max_tokens=100,
            use_default_sys_prompt=False,
        )

    def test_simple_completion(self):
        """Test a simple chat completion."""
        from omagent_core.models.llms.schemas import Message

        messages = [
            Message.system("You are a helpful assistant. Reply concisely. Do not use think tags."),
            Message.user("What is 2+2? Reply with just the number."),
        ]
        result = self.llm._call(messages)

        self.assertIn("choices", result)
        self.assertTrue(len(result["choices"]) > 0)
        content = result["choices"][0]["message"]["content"]
        self.assertIsNotNone(content)
        self.assertTrue(len(content) > 0)
        self.assertIn("4", content)

    def test_response_has_usage(self):
        """Test that response includes token usage information."""
        from omagent_core.models.llms.schemas import Message

        messages = [
            Message.system("Reply concisely. Do not use think tags."),
            Message.user("Say hello."),
        ]
        result = self.llm._call(messages)

        self.assertIn("usage", result)
        usage = result["usage"]
        self.assertIn("prompt_tokens", usage)
        self.assertIn("completion_tokens", usage)
        self.assertIn("total_tokens", usage)
        self.assertGreater(usage["total_tokens"], 0)

    def test_async_completion(self):
        """Test async chat completion."""
        from omagent_core.models.llms.schemas import Message

        messages = [
            Message.system("You are a helpful assistant. Reply concisely. Do not use think tags."),
            Message.user("What is 3+5? Reply with just the number."),
        ]

        result = asyncio.run(self.llm._acall(messages))

        self.assertIn("choices", result)
        content = result["choices"][0]["message"]["content"]
        self.assertIsNotNone(content)
        self.assertTrue(len(content) > 0)
        self.assertIn("8", content)


if __name__ == "__main__":
    unittest.main()
