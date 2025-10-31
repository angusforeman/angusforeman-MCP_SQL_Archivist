"""
Azure OpenAI Chat Client with MCP Server Integration

This script creates a chat interface that:
1. Connects to Azure OpenAI for LLM capabilities
2. Integrates with a local MCP server for tools/resources
3. Translates between Azure OpenAI function calling and MCP protocol
"""

import asyncio
import json
import os
import sys
from typing import Any

from dotenv import load_dotenv
from openai import AsyncAzureOpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# ANSI color codes
class Colors:
    GREEN = '\033[92m'
    ORANGE = '\033[38;5;208m'
    CYAN = '\033[36m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

# Load environment variables
load_dotenv()

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

# MCP Server Configuration - use current Python interpreter
MCP_SERVER_COMMAND = sys.executable  # Use the same Python that's running this script
MCP_SERVER_SCRIPT = os.getenv("MCP_SERVER_SCRIPT", "MCP_Hardcoded_stdio.py")
MCP_SERVER_ARGS = [MCP_SERVER_SCRIPT]

# Alternative: Use legacy MCP_SERVER_ARGS from .env if specified
legacy_args = os.getenv("MCP_SERVER_ARGS")
if legacy_args:
    # Parse comma-separated args (e.g., "run,python,MCP_DB_stdio.py")
    args_list = legacy_args.split(",")
    if len(args_list) >= 3 and args_list[0] == "run" and args_list[1] == "python":
        # Override with the script from legacy format
        MCP_SERVER_SCRIPT = args_list[2]
        MCP_SERVER_ARGS = [MCP_SERVER_SCRIPT]

# Check if MCP_SERVER_PARAMS environment variable contains --quiet (must be after legacy_args processing)
MCP_SERVER_PARAMS = os.getenv("MCP_SERVER_PARAMS", "")
if '--quiet' in MCP_SERVER_PARAMS:
    MCP_SERVER_ARGS.append("--quiet")

# System prompt configuration
SYSTEM_PROMPT_FILE = os.getenv("SYSTEM_PROMPT_FILE", "system_prompt.txt")

# Model parameters for grounded, factual responses
# Temperature: Lower = more focused/deterministic, Higher = more creative/random
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.1"))
# Top-p (nucleus sampling): Lower = more focused, Higher = more diverse
TOP_P = float(os.getenv("TOP_P", "0.1"))
# Max tokens in response
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1000"))
# Presence penalty: Penalizes new topics (0.0 to 2.0)
PRESENCE_PENALTY = float(os.getenv("PRESENCE_PENALTY", "0.0"))
# Frequency penalty: Penalizes repetition (0.0 to 2.0)
FREQUENCY_PENALTY = float(os.getenv("FREQUENCY_PENALTY", "0.3"))


def load_system_prompt() -> str:
    """Load system prompt from file."""
    try:
        with open(SYSTEM_PROMPT_FILE, 'r', encoding='utf-8') as f:
            prompt = f.read().strip()
            print(f"📄 Loaded system prompt from: {SYSTEM_PROMPT_FILE}")
            return prompt
    except FileNotFoundError:
        print(f"⚠️  System prompt file not found: {SYSTEM_PROMPT_FILE}")
        print("   Using default system prompt")
        return "You are a helpful AI assistant with access to specialized tools and resources."
    except Exception as e:
        print(f"⚠️  Error loading system prompt: {e}")
        print("   Using default system prompt")
        return "You are a helpful AI assistant with access to specialized tools and resources."


class AzureOpenAIMCPChat:
    """Chat client integrating Azure OpenAI with MCP server."""

    def __init__(self):
        """Initialize the chat client."""
        self.azure_client = AsyncAzureOpenAI(
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_key=AZURE_OPENAI_KEY,
            api_version=AZURE_OPENAI_API_VERSION,
        )
        self.mcp_session: ClientSession | None = None
        self.system_prompt = load_system_prompt()
        self.conversation_history = [
            {"role": "system", "content": self.system_prompt}
        ]
        self.available_tools = {}

    async def connect_mcp_server(self):
        """Connect to the MCP server and retrieve available tools."""
        print("🔌 Connecting to MCP server...")
        print(f"   Command: {MCP_SERVER_COMMAND}")
        print(f"   Args: {MCP_SERVER_ARGS}")
        
        try:
            server_params = StdioServerParameters(
                command=MCP_SERVER_COMMAND,
                args=MCP_SERVER_ARGS,
            )

            # Initialize MCP client using async with (proper context management)
            print("   Starting MCP server process...")
            self.stdio = stdio_client(server_params)
            self.read_stream, self.write_stream = await self.stdio.__aenter__()
            
            print("   Creating client session...")
            self.session_context = ClientSession(self.read_stream, self.write_stream)
            self.mcp_session = await self.session_context.__aenter__()
            
            print("   Initializing session...")
            await asyncio.wait_for(self.mcp_session.initialize(), timeout=10.0)
            
            # Get available tools from MCP server
            print("   Listing tools...")
            tools_result = await asyncio.wait_for(self.mcp_session.list_tools(), timeout=5.0)
            
            # Convert MCP tools to Azure OpenAI function format
            for tool in tools_result.tools:
                self.available_tools[tool.name] = {
                    "mcp_tool": tool,
                    "openai_function": {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description or "",
                            "parameters": tool.inputSchema or {"type": "object", "properties": {}},
                        },
                    },
                }
            
            print(f"✅ Connected! Found {len(self.available_tools)} tools:")
            for name in self.available_tools.keys():
                print(f"   - {name}")
        except asyncio.TimeoutError:
            print("❌ Error: Connection to MCP server timed out")
            print("   Check that MCP_Hardcoded_stdio.py exists and can run")
            raise
        except Exception as e:
            print(f"❌ Error connecting to MCP server: {e}")
            import traceback
            traceback.print_exc()
            raise

    async def call_mcp_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """Call an MCP tool and return the result."""
        if not self.mcp_session:
            return "Error: MCP session not initialized"
        
        try:
            result = await self.mcp_session.call_tool(tool_name, arguments)
            # Extract content from result
            if result.content:
                return "\n".join([
                    item.text if hasattr(item, 'text') else str(item)
                    for item in result.content
                ])
            return str(result)
        except Exception as e:
            return f"Error calling tool {tool_name}: {str(e)}"

    async def chat(self, user_message: str) -> str:
        """Send a message and get a response with tool calling support."""
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message,
        })

        # Prepare tools for Azure OpenAI
        tools = [tool["openai_function"] for tool in self.available_tools.values()]

        # Call Azure OpenAI with grounded parameters
        response = await self.azure_client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=self.conversation_history,
            tools=tools if tools else None,
            tool_choice="auto" if tools else None,
            temperature=TEMPERATURE,
            top_p=TOP_P,
            max_tokens=MAX_TOKENS,
            presence_penalty=PRESENCE_PENALTY,
            frequency_penalty=FREQUENCY_PENALTY,
        )

        assistant_message = response.choices[0].message

        # Handle tool calls
        if assistant_message.tool_calls:
            # Add assistant message with tool calls to history
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in assistant_message.tool_calls
                ],
            })

            # Execute each tool call
            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                print(f"{Colors.CYAN}🔧 Calling tool: {tool_name}{Colors.RESET}")
                tool_result = await self.call_mcp_tool(tool_name, tool_args)
                
                # Add tool result to history
                self.conversation_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result,
                })

            # Get final response after tool execution
            final_response = await self.azure_client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT,
                messages=self.conversation_history,
                temperature=TEMPERATURE,
                top_p=TOP_P,
                max_tokens=MAX_TOKENS,
                presence_penalty=PRESENCE_PENALTY,
                frequency_penalty=FREQUENCY_PENALTY,
            )
            
            final_message = final_response.choices[0].message.content
            self.conversation_history.append({
                "role": "assistant",
                "content": final_message,
            })
            
            return final_message
        else:
            # No tool calls, just return the response
            content = assistant_message.content
            self.conversation_history.append({
                "role": "assistant",
                "content": content,
            })
            return content
    async def cleanup(self):
        """Clean up resources."""
        if hasattr(self, 'session_context'):
            await self.session_context.__aexit__(None, None, None)
        if hasattr(self, 'stdio'):
            await self.stdio.__aexit__(None, None, None)


async def main():
    """Main chat loop."""
    print(f"\n📋 Configuration:")
    print(f"   Endpoint: {AZURE_OPENAI_ENDPOINT}")
    print(f"   Deployment: {AZURE_OPENAI_DEPLOYMENT}")
    print(f"   API Version: {AZURE_OPENAI_API_VERSION}")
    print(f"\n🎛️  Model Parameters (for grounded responses):")
    print(f"   Temperature: {TEMPERATURE} (lower = more focused)")
    print(f"   Top-p: {TOP_P} (lower = more deterministic)")
    print(f"   Max Tokens: {MAX_TOKENS}")
    print(f"   Presence Penalty: {PRESENCE_PENALTY}")
    print(f"   Frequency Penalty: {FREQUENCY_PENALTY}")
    print()

    chat_client = AzureOpenAIMCPChat()
    
    try:
        # Connect to MCP server
        await chat_client.connect_mcp_server()
        
        print("\n💬 Chat started! Type 'quit' or 'exit' to end.\n")
        
        # Chat loop
        while True:
            # Get input with colored prompt
            user_input = input(f"{Colors.GREEN}You:{Colors.GREEN} ").strip()
            
            if user_input.lower() in ["quit", "exit", "bye"]:
                print(f"{Colors.RESET}👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            try:
                response = await chat_client.chat(user_input)
                print(f"\n{Colors.ORANGE}Archivist:{Colors.RESET} {Colors.ORANGE}{response}{Colors.RESET}\n")
            except Exception as e:
                error_msg = str(e)
                print(f"❌ Error: {error_msg}\n")
                
                if "404" in error_msg or "Resource not found" in error_msg:
                    print("💡 This usually means:")
                    print("   1. The deployment name is incorrect")
                    print("      Check your Azure OpenAI Studio for the exact deployment name")
                    print("   2. The endpoint URL is wrong")
                    print("      Should be: https://YOUR-RESOURCE-NAME.openai.azure.com/")
                    print("   3. The model deployment doesn't exist")
                    print(f"\n   Current deployment name: '{AZURE_OPENAI_DEPLOYMENT}'")
                    print(f"   Current endpoint: '{AZURE_OPENAI_ENDPOINT}'")
                    print("\n   Update these in your .env file\n")
    
    finally:
        await chat_client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
