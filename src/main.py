import streamlit as st
import requests, asyncio
from client.orchestrator import orchestrator

# Set page title
st.set_page_config(page_title="Daryl's Personal Assistant", page_icon="💬")

# Initialize session state to store chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if "username" not in st.session_state:
    st.session_state.username = "Guest"  # default username

# Layout: title on left, username input on right
col1, col2 = st.columns([4, 1])
with col1:
    st.title("Chat with Daryl's Personal Assistant")
with col2:
    st.session_state.username = st.text_input(
        "Username", 
        st.session_state.username, 
        label_visibility="collapsed",  # hide label
        placeholder="Enter name..."
    )

st.divider()

# Display existing chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input box
if question := st.chat_input("Type your message..."):
    # Add user message to history
    username = str(st.session_state.get("username", "Guest"))
    st.session_state.messages.append({"role": "user", "content": question})
    
    # Display the user message
    with st.chat_message("user"):
        st.markdown(question)

    # Generate text stream
    with st.chat_message("assistant"):
        response_box = st.empty()

        async def run_stream():
            full_response = ""
            async for chunk in orchestrator(username, question):
                # Assume your orchestrator yields text pieces
                text_piece = str(chunk)
                full_response += text_piece
                response_box.markdown(full_response)
            return full_response

        # Run async stream and capture final text
        response = asyncio.run(run_stream())

    # Add bot message to history
    st.session_state.messages.append({"role": "assistant", "content": response})
