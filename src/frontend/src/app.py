import streamlit as st

pages = {
    "Features": [
        st.Page("upload_documents_page.py", title="Upload Documents"),
        st.Page("chatbot_page.py", title="Chat with AI"),
    ],
}

pg = st.navigation(pages)
pg.run()
