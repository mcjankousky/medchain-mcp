import os
import asyncio
from google import genai
from google.genai import types
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run_supply_chain_agent(target_manufacturer: str, status_callback=None):
    """
    Boots the MCP server, initializes the Gemini agent, and autonomously resolves a supply chain disruption.
    """
    if status_callback:
        status_callback("🤖 Initializing Autonomous Supply Chain Agent...")
        
    # 1. Boot up the MCP Server in the background via stdio
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "server.mcp_server"], 
        env=os.environ.copy()
    )

    # Everything below happens INSIDE the server lifecycle
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            if status_callback:
                status_callback("✅ Connected to MedChain MCP Server. Fetching tools...")

            # 2. Fetch the raw tools from the MCP Server
            mcp_response = await session.list_tools()
            mcp_tools = mcp_response.tools

            # 3. Schema Translation & Scrubbing (Your logic)
            def sanitize_schema(schema: dict) -> dict:
                if not isinstance(schema, dict): return schema
                clean_schema = {}
                for key, value in schema.items():
                    if key in ["additionalProperties", "additional_properties"]: continue
                    if isinstance(value, dict):
                        clean_schema[key] = sanitize_schema(value)
                    elif isinstance(value, list):
                        clean_schema[key] = [sanitize_schema(item) if isinstance(item, dict) else item for item in value]
                    else:
                        clean_schema[key] = value
                return clean_schema

            gemini_tools = []
            for tool in mcp_tools:
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

            # 4. Initialize Gemini Client
            client = genai.Client()
            config = types.GenerateContentConfig(
                tools=gemini_tools,
                temperature=0.1,
                system_instruction=(
                    "You are an autonomous Supply Chain Crisis Management AI. "
                    "You MUST use your provided tools to query the database to answer the user's prompt. "
                    "NEVER ask for permission to proceed. "
                    "Execute the tools immediately, analyze the database returns, and output the final strategic report."
                )
            )

            # ==========================================
            # 5. THE EXECUTION LOOP
            # ==========================================
            prompt = f"""
            A catastrophic supply chain failure has taken {target_manufacturer} offline.
            1. Query the database to find all SKUs manufactured by them.
            2. For each vulnerable SKU, find an alternative POTENTIAL_SUBSTITUTE_FOR.
            3. Generate a strategic procurement report.
            """

            if status_callback:
                status_callback(f"🧠 Prompting Gemini to resolve {target_manufacturer} crisis...")

            # Create a chat session to maintain conversation history
            chat = client.chats.create(model="gemini-3.1-flash-lite", config=config)
            response = chat.send_message(prompt)

            # While the AI decides it needs to use a tool, keep intercepting and executing
            while response.function_calls:
                for tool_call in response.function_calls:
                    if status_callback:
                        status_callback(f"🛠️ Executing {tool_call.name} with args: {tool_call.args}")

                    # Execute the tool natively against the Neo4j Graph via the MCP session
                    mcp_result = await session.call_tool(tool_call.name, tool_call.args)
                    
                    # Feed the database response back to Gemini
                    response = chat.send_message(
                        types.Part.from_function_response(
                            name=tool_call.name,
                            response={"result": mcp_result.content[0].text}
                        )
                    )

            # When the while loop finishes, the AI has generated its final text response
            if status_callback:
                status_callback("✅ Strategy finalized. Rendering report.")
            
            return response.text

# Fallback for terminal testing
if __name__ == "__main__":
    final_report = asyncio.run(run_supply_chain_agent("Medtronic", print))
    print("\n\n" + final_report)