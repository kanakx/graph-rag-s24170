import streamlit as st

uploaded_files = st.file_uploader(
    "Upload Documents", accept_multiple_files=True, type="pdf"
)
for uploaded_file in uploaded_files:
    pass  # TODO: File processing here
