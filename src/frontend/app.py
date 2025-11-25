import streamlit as st

pages = {
    "Features": [
        st.Page("chatbot_page.py", title="Chat with AI"),
        st.Page("upload_documents_page.py", title="Upload Documents"),
    ],
}

pg = st.navigation(pages)
pg.run()
