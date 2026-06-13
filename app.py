import streamlit as st
import time
import asyncio
import traceback
from database.graph_repository import GraphRepository
from client import run_supply_chain_agent


# --- Page Configuration ---
st.set_page_config(page_title="MedChain Disruption Simulator", layout="wide")
st.title("🏥 MedChain Disruption Simulator")
st.markdown("Inject simulated supply chain failures and watch the AI agent navigate the Knowledge Graph to find alternatives.")

# --- Database Connection ---
#@st.cache_resource
#def get_db_connection():
#    return GraphRepository()

#repo = get_db_connection()

# --- Sidebar: Disruption Controls ---
#st.sidebar.header("Simulation Parameters")

# Fetch active manufacturers from the database dynamically
#try:
#    manufacturers = repo.driver.execute_query(
#        "MATCH (m:Manufacturer) RETURN m.name AS name",
#        database_="neo4j"
#    ).records
#    mfr_options = [record["name"] for record in manufacturers]
#except Exception as e:
#    mfr_options = ["Medtronic", "Baxter", "Stryker"] # Fallback if DB is offline

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
    with st.spinner("Agent is actively navigating the Knowledge Graph..."):
        try:
            # We use asyncio.run to execute the async agent from sync Streamlit
            final_report = asyncio.run(
                run_supply_chain_agent(
                    target_manufacturer=selected_mfr, 
                    status_callback=update_ui_status
                )
            )
            
            # 4. Render the final output
            monologue_container.success("Task Complete. Strategy finalized.")
            report_container.markdown(final_report)
            
        except Exception as e:
            st.error(f"Agent Execution Failed: {str(e)}")
            # Dump the actual error stack to the Streamlit UI!
            with st.expander("🔍 View Full Traceback"):
                st.code(traceback.format_exc())