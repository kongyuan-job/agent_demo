from langchain_core.messages import HumanMessage, SystemMessage
from langchain_deepseek import ChatDeepSeek
from langchain_openai import ChatOpenAI
from langgraph.runtime import Runtime
from typing_extensions import TypedDict
from typing import Any
import json
import re
from langgraph.graph.state import StateGraph, START
from simple_react_agent import agent
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

# 使用langgraph推荐方式定义大模型
llm = ChatDeepSeek(
    model="deepseek-chat",
    temperature=0,
    base_url="https://api.deepseek.com/v1",
    api_key="sk-xxx"
)


class CalculatorInput(BaseModel):
    """Input schema for calculator tool"""
    expression: str = Field(
        description="需要计算的数学表达式，例如: '1+1', '2*3', '(1+1)*3'"
    )

@tool(args_schema=CalculatorInput)
def calculate(expression: str) -> str:
    """Execute calculation"""
    try:
        # Security: only allow safe characters
        allowed_chars = set('0123456789+-*/.() ')
        if not all(c in allowed_chars for c in expression):
            return "错误: 包含不安全的字符"

        result = eval(expression)
        return f"计算结果: {result}"
    except Exception as e:
        return f"计算错误: {str(e)}"

tools = [calculate]

llm.bind_tools([calculate])

class State(TypedDict):
    output_data: dict[str, Any]


class Result(BaseModel):
    answer: str = Field(description="计算结果")


def _extract_numeric_string(text: str) -> str | None:
    # Match integers or decimals, including negative numbers
    matches = re.findall(r"-?\d+(?:\.\d+)?", text)
    if not matches:
        return None
    # Use the last number found as the final result
    return matches[-1]


def create_node(node_name: str):
    def call_react_agent(state: State, runtime: Runtime):
        # Transform the state to the subgraph state
        agent = create_react_agent(
            model=llm,
            tools=tools,
            prompt="选择工具，回答用户的问题。",
            response_format= Result
        )
        subgraph_output = agent.invoke({"messages": [HumanMessage(content=f"用户问题: {runtime.context[node_name]["prompt"]}")]})
        # Transform response back to the parent state
        output_data = state.get("output_data")
        if not output_data:
            output_data = {}
        output_data[node_name] = subgraph_output.get("structured_response").answer
        return {**state, "output_data": output_data}

    def call_summary_agent(state: State, runtime: Runtime):
        # Transform the state to the subgraph state
        agent = create_react_agent(
            model=llm,
            tools=tools,
            prompt=(
                "选择工具，回答用户的问题。"
            ),
            response_format= Result
        )
        output_data = state.get("output_data")
        prompt = "汇总下面的结果:"
        for key ,value in output_data.items():
            prompt += f"\n {value}"
        subgraph_output = agent.invoke({"messages": [HumanMessage(content=prompt)]})
        # Prefer provider-structured JSON, fallback to regex extraction
        if not output_data:
            output_data = {}
        output_data[node_name] = subgraph_output.get("structured_response")
        return {**state, "output_data":output_data}
    if "node_3" == node_name:
        return call_summary_agent
    else:
        return call_react_agent

builder = StateGraph(State)
builder.add_node("node_1", create_node("node_1"))
builder.add_node("node_2", create_node("node_2"))
builder.add_node("node_3", create_node("node_3"))
builder.add_edge(START, "node_1")
builder.add_edge("node_1", "node_2")
builder.add_edge("node_2", "node_3")
graph = builder.compile()

for chunk in graph.stream(
        input={"output_data": {}},
        context={"node_1": {"prompt": "1+1的结果，乘以2，再加3"}, "node_2": {"prompt": "1+2的结果，乘以4，再加5"}},
        subgraphs=True,
        stream_mode="updates",
):
    print(chunk)
