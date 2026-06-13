import streamlit as st
import time
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
    monologue_container.warning(f"Thinking: Alert received. {selected_mfr} is offline. Querying graph topology...")
    report_container.empty()
    
    # Placeholder for the actual Agent Execution Loop
    time.sleep(1.5)
    
    monologue_container.warning("Thinking: Discovered vulnerable SKUs. Now checking POTENTIAL_SUBSTITUTE_FOR edges...")
    time.sleep(1.5)
    
    monologue_container.success("Task Complete. Rendering report.")
    
    # Placeholder for the final Agent Output
    mock_report = f"""
    ### Outage Impact: {selected_mfr}
    * **Vulnerable SKU:** GTIN-100234 (3ml Safety Syringe)
    * **Price:** $14.50
    
    ### Recommended Alternatives
    Based on UNSPSC classification (42142611), the graph suggests investigating alternative regional suppliers.
    """
    report_container.markdown(mock_report)