from dataclasses import dataclass, field
from typing import AsyncGenerator
from tenacity import wait_fixed, stop_after_attempt, AsyncRetrying
from anthropic.types import MessageParam, ModelParam, ToolUnionParam, ToolResultBlockParam
from tool import Tool
from client import anthropic_client


@dataclass
class EventText:
    text: str
    type: str = "text"


@dataclass
class EventInputJson:
    text: str
    type: str = "input_json"


@dataclass
class EventToolUse:
    tool: Tool
    type: str = "tool_use"


@dataclass
class EventToolResult:
    tool: Tool
    result: str
    type: str = "tool_result"

AgentEvent = EventText | EventInputJson | EventToolUse | EventToolResult


@dataclass
class Agent:
    system_prompt: str
    model: ModelParam
    tools: list[Tool]
    messages: list[MessageParam] = field(default_factory=list)
    available_tools: list[ToolUnionParam] = field(default_factory=list)

    def __post_init__(self):
        self.available_tools = [
            {
                "name": tool.__name__,
                "description": tool.__doc__ or "",
                "input_schema": tool.model_json_schema(),
            }
            for tool in self.tools
        ]

    def add_user_message(self, message: str):
        self.messages.append(MessageParam(role="user", content=message))

    async def agentic_loop(self) -> AsyncGenerator[AgentEvent, None]:
        async for attempt in AsyncRetrying(stop=stop_after_attempt(3), wait=wait_fixed(3)):
            with attempt:
                async with anthropic_client.messages.stream(
                    max_tokens=8000,
                    messages=self.messages,
                    model=self.model,
                    tools=self.available_tools,
                    system=self.system_prompt,
                ) as stream:
                    async for event in stream:
                        if event.type == "text":
                            event.text
                            yield EventText(text=event.text)
                        if event.type == "input_json":
                            yield EventInputJson(partial_json=event.partial_json)
                            event.partial_json
                            event.snapshot
                        if event.type == "thinking":
                            pass
                        if event.type == "content_block_stop":
                            pass
                    accumulated = await stream.get_final_message()
                    for content in accumulated.content:
                        if content.type == "tool_use":
                            tool_name = content.name
                            tool_args = content.input

                            for tool in self.tools:
                                if tool.__name__ == tool_name:
                                    t = tool.model_validate(tool_args)
                                    result = await t()
                                    yield EventToolResult(tool=t, result=result)
                                    self.messages.append(
                                        MessageParam(
                                            role="user",
                                            content=[
                                                ToolResultBlockParam(
                                                    type="tool_result",
                                                    tool_use_id=content.id,
                                                    content=result,
                                                )
                                            ],
                                        )
                                    )
                    if accumulated.stop_reason == "tool_use":
                        async for e in self.agentic_loop():
                            yield e
    
    async def run(self) -> AsyncGenerator[AgentEvent, None]:
        async for x in self.agentic_loop():
            yield x