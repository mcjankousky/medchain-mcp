import pytest
import asyncio
import os
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# ==========================================
# PILLAR 3: THE GOLDEN DATASET
# ==========================================
# A curated list of test cases representing the actual chaos of a healthcare supply chain.
GOLDEN_DATASET = [
    {
        "prompt": "What does Medtronic make?",
        "expected_tools": ["query_supply_chain_topology"],
        "expected_facts": ["3ml Safety Syringe", "GTIN-100234"]
    },
    {
        "prompt": "We are out of GTIN-100234. What can we buy instead?",
        "expected_tools": ["get_product_alternatives"],
        "expected_facts": ["GTIN-777112", "GTIN-888441", "Stent Pro"]
    }
]

# ==========================================
# PILLAR 2: LLM-AS-A-JUDGE SCHEMA
# ==========================================
# Returns a structured Pydantic object containing a boolean PASS/FAIL and a reasoning string.
class EvaluationResult(BaseModel):
    passed: bool = Field(
        description="Return True if the agent explicitly stated the expected facts and completed the task."
    )
    reasoning: str = Field(
        description="A brief explanation of why the agent passed or failed based on faithfulness and groundedness."
    )

def sanitize_schema(schema: dict) -> dict:
    """Recursively removes keys that the Gemini API rejects."""
    if not isinstance(schema, dict):
        return schema
    clean_schema = {}
    for key, value in schema.items():
        if key in ["additionalProperties", "additional_properties"]:
            continue
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

# ==========================================
# THE AUTOMATED TEST SUITE
# ==========================================
@pytest.mark.asyncio
@pytest.mark.parametrize("test_case", GOLDEN_DATASET)
async def test_agent_behavior(test_case):
    print(f"\n🧪 Running EvalOps for prompt: '{test_case['prompt']}'")
    
    # 1. Boot up the MCP Server
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "server.mcp_server"], 
        env=os.environ.copy()
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 2. Fetch and translate tools
            mcp_response = await session.list_tools()
            gemini_tools = [
                types.Tool(
                    function_declarations=[
                        types.FunctionDeclaration(
                            name=t.name,
                            description=t.description,
                            parameters=sanitize_schema(t.inputSchema)
                        )
                    ]
                ) for t in mcp_response.tools
            ]

            client = genai.Client()
            config = types.GenerateContentConfig(
                tools=gemini_tools,
                temperature=0.0, # Zero temperature for strict evaluation
                system_instruction="You are an autonomous Supply Chain AI. You MUST use tools to answer."
            )

            chat = client.chats.create(model='gemini-2.5-flash', config=config)
            
            # Execute the agent and track its trajectory
            response = chat.send_message(test_case['prompt'])
            executed_tools = []

            while response.function_calls:
                function_responses = []
                for function_call in response.function_calls:
                    tool_name = function_call.name
                    executed_tools.append(tool_name) # Track the tool call
                    
                    tool_result = await session.call_tool(tool_name, function_call.args)
                    
                    function_responses.append(
                        types.Part.from_function_response(
                            name=tool_name,
                            response={"result": tool_result.content}
                        )
                    )
                response = chat.send_message(function_responses)

            agent_final_text = response.text

            # ==========================================
            # PILLAR 1: TRAJECTORY EVALUATION
            # ==========================================
            # We must evaluate the sequence of decisions it made deterministically.
            for expected_tool in test_case["expected_tools"]:
                assert expected_tool in executed_tools, f"Trajectory Failed: Agent never called {expected_tool}"
            print("✅ Trajectory Evaluation Passed.")

            # ==========================================
            # PILLAR 2: LLM-AS-A-JUDGE EXECUTION
            # ==========================================
            judge_prompt = f"""
            You are an objective AI evaluator. Review the Agent's Final Response against the Expected Facts.
            Did the agent accurately include these facts and successfully complete the task?
            
            Agent's Final Response:
            {agent_final_text}
            
            Expected Facts to be present:
            {test_case['expected_facts']}
            """
            
            judge_response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=judge_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=EvaluationResult,
                    temperature=0.0
                )
            )
            
            # Parse the Judge's structured output
            evaluation = judge_response.parsed
            
            print(f"⚖️ Judge Reasoning: {evaluation.reasoning}")
            
            # If the Judge returns FAIL, your CI/CD pipeline breaks.
            assert evaluation.passed is True, f"Semantic Check Failed: {evaluation.reasoning}"
            print("✅ Semantic Check Passed.")