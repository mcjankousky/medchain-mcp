import streamlit as st
import time
import asyncio
import traceback
import json

from database.graph_repository import GraphRepository
from client import run_supply_chain_agent

try:
    with open("mock_runs.json", "r") as f:
        mock_data = json.load(f)
except FileNotFoundError:
    mock_data = {}

# --- Page Configuration ---
st.set_page_config(page_title="MedChain Disruption Simulator", layout="wide")
st.title("🏥 MedChain Disruption Simulator")
st.markdown("Inject simulated supply chain failures and watch the AI agent navigate the Knowledge Graph to find alternatives.")

# --- Database Connection ---
@st.cache_resource
def get_db_connection():
    return GraphRepository()

repo = get_db_connection()

# --- Sidebar: Disruption Controls ---
st.sidebar.header("Simulation Parameters")

run_mode = st.sidebar.radio(
    "Execution Engine", 
    ["Simulated Replay (Free/Instant)", "Live AI Inference (API)"]
)

# Fetch active manufacturers from the database dynamically
try:
    manufacturers = repo.driver.execute_query(
        "MATCH (m:Manufacturer) RETURN m.name AS name",
        database_="neo4j"
    ).records
    mfr_options = [record["name"] for record in manufacturers]
except Exception as e:
    mfr_options = ["Medtronic", "Baxter", "Stryker"] # Fallback if DB is offline

mfr_options = ["Medtronic", "Baxter", "Stryker"]

selected_mfr = st.sidebar.selectbox("Select Target Manufacturer:", mfr_options)

simulate_btn = st.sidebar.button("🚨 Inject Disruption", type="primary")

# --- Main Dashboard Layout ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("🧠 Agent Monologue")
    monologue_container = st.empty()
    monologue_container.info("Agent is standing by...")

with col2:
    st.subheader("📄 Strategic Report")
    report_container = st.empty()
    report_container.markdown("*The finalized procurement strategy will appear here.*")

# --- Execution Logic ---
if simulate_btn:
    # 1. Prepare the UI
    monologue_container.empty()
    report_container.empty()
    
    # 2. Create a callback function to update the Streamlit UI live
    def update_ui_status(message: str):
        # We use a markdown box to append new thoughts to the monologue
        with monologue_container:
            st.info(message)
            
    # 3. Trigger the Agent
    # PATH A: The Simulated Replay
    if run_mode == "Simulated Replay (Free/Instant)":
        if selected_mfr in mock_data:
            with st.spinner("Simulating Agent Execution..."):
                for step in mock_data[selected_mfr]["steps"]:
                    update_ui_status(step)
                    time.sleep(1.2) 
                
                monologue_container.success("Task Complete (Simulated).")
                report_container.markdown(mock_data[selected_mfr]["report"])
        else:
            st.warning(f"No simulated data available for {selected_mfr}. Try Medtronic or switch to Live mode.")

    # PATH B: The Cloud-Protected Live API Request
    else:
        with st.spinner(f"Agent actively querying Graph DB via Gemini 3.1 Flash Lite..."):
            try:
                final_report = asyncio.run(
                    run_supply_chain_agent(
                        target_manufacturer=selected_mfr, 
                        status_callback=update_ui_status
                    )
                )
                monologue_container.success("Task Complete. Strategy finalized.")
                report_container.markdown(final_report)
                
            except Exception as e:
                error_msg = str(e).lower()
                
                # Intercept Cloud Quota Errors (429 / Exhausted)
                if "429" in error_msg or "quota" in error_msg or "exhausted" in error_msg:
                    st.error("🛑 **Daily Live Demo Limit Reached!**")
                    st.warning("To protect against bot abuse, the cloud infrastructure has paused live API calls for the day. Please switch the toggle to **'Simulated Replay'** to view the pre-calculated agent trajectory.")
                
                # Standard Error Handling for actual code breaks
                else:
                    st.error(f"Agent Execution Failed: {str(e)}")
                    with st.expander("🔍 View Full Traceback"):
                        st.code(traceback.format_exc())