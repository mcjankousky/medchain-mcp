import asyncio
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from google import genai
from google.genai import types

async def run_supply_chain_agent():
    print("🤖 Initializing Autonomous Supply Chain Agent...")
    
    # 1. Boot up the MCP Server in the background via stdio
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "server.mcp_server"], 
        env=os.environ.copy()
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("✅ Connected to MedChain MCP Server.")

            # 2. Fetch the raw tools from the MCP Server
            mcp_response = await session.list_tools()
            mcp_tools = mcp_response.tools
            print(f"🛠️  Found {len(mcp_tools)} tools. Translating schemas...")

            # ==========================================
            # 3. THE TRANSLATION & SCRUBBING BLOCK
            # ==========================================
            def sanitize_schema(schema: dict) -> dict:
                """Recursively removes keys that the Gemini API rejects."""
                if not isinstance(schema, dict):
                    return schema
                
                clean_schema = {}
                for key, value in schema.items():
                    # Strip out the offending keys
                    if key in ["additionalProperties", "additional_properties"]:
                        continue
                    
                    # Recursively clean nested dictionaries and lists
                    if isinstance(value, dict):
                        clean_schema[key] = sanitize_schema(value)
                    elif isinstance(value, list):
                        clean_schema[key] = [
                            sanitize_schema(item) if isinstance(item, dict) else item 
                            for item in value
                        ]
                    else:
                        clean_schema[key] = value
                return clean_schema

            gemini_tools = []
            for tool in mcp_tools:
                # Scrub the schema before passing it to Gemini
                safe_schema = sanitize_schema(tool.inputSchema)
                
                gemini_tools.append(
                    types.Tool(
                        function_declarations=[
                            types.FunctionDeclaration(
                                name=tool.name,
                                description=tool.description,
                                parameters=safe_schema  
                            )
                        ]
                    )
                )
            # ==========================================

            # 4. Initialize Gemini Client and Config with System Instructions
            client = genai.Client()
            config = types.GenerateContentConfig(
                tools=gemini_tools,
                temperature=0.1, # Low temperature for analytical accuracy
                system_instruction=(
                    "You are an autonomous Supply Chain Crisis Management AI. "
                    "You MUST use your provided tools to query the database to answer the user's prompt. "
                    "NEVER ask for permission to proceed. "
                    "NEVER say you don't have pricing information until AFTER you have queried the graph. "
                    "Execute the tools immediately, analyze the database returns, and output the final strategic report."
                )
            )

            # 5. Define the Agent's Prompt
            prompt = (
                "A massive storm just took Medtronic offline. "
                "What specific SKUs are vulnerable, and what alternative products "
                "can we buy to replace them? Give me SKUs and prices."
            )
            print(f"🚨 ALERT RECEIVED: {prompt}\n")
            print("🧠 Agent is thinking and querying the graph...\n")

            # ==========================================
            # 6. Initialize a Stateful Chat Context
            # ==========================================
            chat = client.chats.create(
                model='gemini-2.5-flash',
                config=config
            )

            # 7. Start the Agentic Loop
            response = chat.send_message(prompt)

            # 8. Handle Tool Calls in a continuous loop
            while response.function_calls:
                function_responses = [] # Collect all responses for this specific turn
                
                for function_call in response.function_calls:
                    tool_name = function_call.name
                    tool_args = function_call.args
                    print(f"   [Agent Calling Tool] -> {tool_name}({tool_args})")
                    
                    # Execute the requested tool against the MCP server
                    tool_result = await session.call_tool(tool_name, tool_args)
                    
                    # Package the result for Gemini
                    function_responses.append(
                        types.Part.from_function_response(
                            name=tool_name,
                            response={"result": tool_result.content}
                        )
                    )
                
                # Send the formatted database responses back into the active chat
                response = chat.send_message(function_responses)

            # 9. Print the Final Synthesized Report
            print("\n================ FINAL AGENT REPORT ================\n")
            print(response.text)
            print("\n====================================================\n")

if __name__ == "__main__":
    asyncio.run(run_supply_chain_agent())