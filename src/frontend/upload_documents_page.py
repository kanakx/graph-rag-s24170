import streamlit as st
import requests

API_URL = "http://localhost:8000"

uploaded_files = st.file_uploader(
    "Upload Documents",
    accept_multiple_files=True, type="pdf"
)

for f in uploaded_files:
    files = {"file": (f.name, f, "application/pdf")}
    response = requests.post(f"{API_URL}/files", files=files)

    if response.ok:
        st.success(f"Uploaded the file {f.name}")
    else:
        st.error(f"Failed to upload the file {f.name} ({response.status_code})")
