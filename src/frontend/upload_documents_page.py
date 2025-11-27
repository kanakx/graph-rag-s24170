import streamlit as st
import requests

API_URL = "http://localhost:8000"

st.markdown("""
    <style>
    /* Hide the file uploader's file list */
    [data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] + section {
        display: none;
    }
    
    /* Alternative: Hide all uploaded file items */
    [data-testid="stFileUploaderFile"] {
        display: none;
    }
    </style>
""", unsafe_allow_html=True)

if 'uploaded_file_names' not in st.session_state:
    st.session_state.uploaded_file_names = set()

st.subheader("Upload New Documents")
uploaded_files = st.file_uploader(
    "Upload Documents",
    accept_multiple_files=True, type="pdf"
)

for f in uploaded_files:
    if f.name not in st.session_state.uploaded_file_names:
        files = {"file": (f.name, f, "application/pdf")}
        response = requests.post(f"{API_URL}/files", files=files)

        if response.ok:
            st.session_state.uploaded_file_names.add(f.name)
            st.success(f"Uploaded the file {f.name}")
            st.rerun()
        else:
            st.error(f"Failed to upload the file {f.name} ({response.status_code})")

st.divider()

st.subheader("Uploaded Files")
try:
    response = requests.get(f"{API_URL}/files")
    if response.ok:
        files = response.json()
        if files:
            for file in files:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"📄 {file.get('id', file)}")
                with col2:
                    if st.button("🗑", key=f"delete_{file.get('id')}"):
                        delete_response = requests.delete(f"{API_URL}/files/{file.get('id')}")
                        if delete_response.ok:
                            st.success(f"Deleted {file.get('id')}")
                            st.rerun()
                        else:
                            st.error(f"Failed to delete {file.get('id')}")
        else:
            st.info("No files uploaded yet.")
    else:
        st.error("Failed to fetch files.")
except requests.exceptions.RequestException:
    st.error("Could not connect to the API.")
