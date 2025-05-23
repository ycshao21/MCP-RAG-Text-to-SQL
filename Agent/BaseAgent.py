import os
import json
import asyncio
from typing import Optional, List, Dict, Any
from contextlib import AsyncExitStack, asynccontextmanager
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv
from openai import OpenAI
import gc


class BaseClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.model: str = "deepseek-v3-250324"
        self.client = OpenAI(
            api_key=os.getenv("API_KEY"), base_url=os.getenv("BASE_URL")
        )

    async def connect_to_server(
        self, command: str, args: List[str], env: Optional[Dict[str, str]] = None
    ) -> None:
        """Connect to the MCP server via stdio protocol."""
        server_params = StdioServerParameters(command=command, args=args, env=env)
        stdio_reader, stdio_writer = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(stdio_reader, stdio_writer)
        )

        await self.session.initialize()
        tools = await self.session.list_tools()
        print("🛠️  Available tools:", [tool.name for tool in tools.tools])

    async def process_query(
        self, query: str, system_prompt: Optional[str] = None
    ) -> str:
        """Process a query with support for multi-round tool usage."""
        if not self.session:
            raise RuntimeError(
                "Session is not initialized. Call connect_to_server first."
            )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ]

        tool_list_response = await self.session.list_tools()
        tools = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description[:1024],
                    "parameters": tool.inputSchema,
                },
            }
            for tool in tool_list_response.tools
        ]

        try:
            while True:
                response = self.client.chat.completions.create(
                    model=self.model, messages=messages, tools=tools, tool_choice="auto"
                )
                message = response.choices[0].message
                print(f"📨 Assistant message: {message}")

                if hasattr(message, "tool_calls") and message.tool_calls:
                    for tool_call in message.tool_calls:
                        tool_name = tool_call.function.name
                        tool_args = json.loads(tool_call.function.arguments)

                        print(f"🔧 Calling tool: {tool_name} with args: {tool_args}")
                        tool_result = await self.session.call_tool(tool_name, tool_args)

                        messages.append(
                            {
                                "role": "assistant",
                                "content": None,
                                "tool_calls": [
                                    {
                                        "id": tool_call.id,
                                        "type": "function",
                                        "function": {
                                            "name": tool_name,
                                            "arguments": tool_call.function.arguments,
                                        },
                                    }
                                ],
                            }
                        )
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": str(tool_result.content),
                            }
                        )

                        print(f"📥 Tool result: {tool_result.content}")

                    # 回到循环顶部，继续 process 新的 messages（包含 tool result）
                    continue

                # 如果没有 tool_call，说明模型已经生成最终文本回复
                return message.content or ""

        except Exception as e:
            print(f"❌ API call error: {e}")
            return f"Error: {str(e)}"



    async def cleanup(self) -> None:
        """Clean up all opened async resources."""
        try:
            await self.exit_stack.aclose()
            gc.collect()
        except Exception as e:
            print(f"⚠️ Error during cleanup: {e}")


if __name__ == "__main__":
    load_dotenv()

    async def main():
        client = BaseClient()
        try:
            await client.connect_to_server(
                command="npx", args=["@modelcontextprotocol/server-sequential-thinking"]
            )
            query = "你有多少工具可以使用?"
            prompt = "用中文回答"
            result = await client.process_query(query, prompt)
            print("✅ Final Result:", result)
        finally:
            await client.cleanup()

    asyncio.run(main())
