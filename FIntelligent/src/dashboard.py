import streamlit as st
import asyncio
import pandas as pd
from autogen_agentchat_demo import AgentsOrchestrator

# --- Streamlit App ---
st.set_page_config(layout="wide")  # Use wide layout

st.title("Financial Intelligent Agent Dashboard")
# Initialize chat history in session state if not already present
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

# --- Top Scrollable Pane ---
st.markdown(
    "<div style='max-height:300px; overflow-y:auto; border:1px solid #ccc; padding:1px;'>",
    unsafe_allow_html=True,
)
#portfolio_type = st.selectbox("Portfolio Type", ["Financial", "Projects", "Other"])
#timeframe = st.selectbox("Timeframe", ["1M", "3M", "6M", "1Y", "All"])
show_agentchat = st.checkbox("AgentChat API", value=True)
#show_multi = st.checkbox("Multi-Agents", value=True)
show_team = st.radio(
    "Multi-Agent Orchestrator:",
    options = ["MagneticOne", "Swarm", "SelectorGroupChat"],
    index=0,
    key="show_team",
)
show_log = st.checkbox("Logging", value=True)
show_state = st.checkbox("State Management", value=True)
show_memory = st.checkbox("Memory Management", value=True)
show_hitl = st.checkbox("Human in the Loop", value=True)


st.markdown("</div>", unsafe_allow_html=True)

# --- Bottom Scrollable Pane: Chat History ---
st.markdown(
    "<div style='max-height:400px; overflow-y:auto; border:1px solid #ccc; padding:1px;'>",
    unsafe_allow_html=True,
)

# Show chat input immediately and handle response generation with a working spinner
user_input = st.chat_input("Type your message here...", key="chat_input")
if user_input:
    cmd = user_input.strip().lower()
    if cmd in ("clear", "clearchat"):
        st.session_state['chat_history'] = []
        st.rerun()
    # Append user message to history
    st.session_state['chat_history'].append({'role': 'user', 'content': user_input})
    # Show spinner while agents generate response
    with st.spinner("Agents are working to fulfill your request..."):
        new_msgs = asyncio.run(AgentsOrchestrator().team_magenticone_messages(user_input))
    # Append agent responses
    for m in new_msgs:
        st.session_state['chat_history'].append({'role': m.source, 'content': m.content})
    st.rerun()

for msg in st.session_state['chat_history']:
    st.chat_message(msg['role']).markdown(msg['content'])

st.markdown("</div>", unsafe_allow_html=True)
# To run: save as dashboard.py and run `streamlit run dashboard.py` in terminal