import os
import streamlit as st
import requests

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://ai-service:8000")

st.title("Chatbot")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What's on your mind?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            resp = requests.post(
                f"{AI_SERVICE_URL}/chat",
                json={"messages": st.session_state.messages},
                timeout=60.0
            )
            resp.raise_for_status()
            response = resp.json()["response"]
        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
