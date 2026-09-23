"""Smoke test of the legacy POC on LangChain/LangGraph 1.x (maintainers only, not part of the exam).

Fake LLM, no API key. Run from the repo root:
  uv run --no-project --python 3.12 --with-requirements requirements.txt --with pytest==9.1.1 \
      pytest -o addopts="" -p no:cacheprovider maintainers/
"""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("LLM_API_KEY", "fake-key")

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel  # noqa: E402
from langchain_core.messages import AIMessage, ToolMessage  # noqa: E402


class ToolCallingFakeModel(GenericFakeChatModel):
    def bind_tools(self, tools, **kwargs):
        return self


@pytest.fixture
def chatbot(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    csv = tmp_path / "sales.csv"
    csv.write_text("region,amount\nnorth,10\nsouth,32\n")

    from Pages.graph import nodes
    from Pages.backend import PythonChatbot
    from Pages.data_models import InputData

    code = "print(sales['amount'].sum())"
    fake = ToolCallingFakeModel(messages=iter([
        AIMessage(content="", tool_calls=[{
            "name": "complete_python_task", "id": "c1",
            "args": {"thought": "Sum amounts", "python_code": code},
        }]),
        AIMessage(content="Total amount is 42."),
    ]))
    monkeypatch.setattr(nodes, "model", nodes.chat_template | fake)
    data = [InputData(variable_name="sales", data_path=str(csv), data_description="Sales by region")]
    return PythonChatbot(), data


def test_llm_is_configurable_by_env():
    from Pages.graph import nodes

    assert nodes.llm.model_name == os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
    assert str(nodes.llm.openai_api_base).rstrip("/") == os.getenv(
        "LLM_API_BASE", "https://api.groq.com/openai/v1").rstrip("/")


def test_poc_graph_runs_tool_loop(chatbot):
    bot, data = chatbot
    bot.user_sent_message("What is the total amount?", data)

    tool_msgs = [m for m in bot.chat_history if isinstance(m, ToolMessage)]
    assert tool_msgs and tool_msgs[0].content.strip() == "42"
    assert bot.chat_history[-1].content == "Total amount is 42."
    assert bot.intermediate_outputs
