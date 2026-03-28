import streamlit as st
from rag import RAG
from dotenv import load_dotenv
import os

# 1. Setup Page Configuration
st.set_page_config(page_title="RAG-CRAW", page_icon="🕸️", layout="wide")

# 2. Load API Key
load_dotenv('.env')
MY_API_KEY = os.getenv('GOOGLE_API_KEY')

# 3. Custom CSS for the Footer
footer_css = """
<style>
.footer {
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100%;
    background-color: #1e212b;
    color: #fafafa;
    text-align: center;
    padding: 10px;
    font-size: 14px;
    z-index: 999;
    border-top: 1px solid #6366f1;
}
.footer a {
    color: #6366f1;
    text-decoration: none;
    margin: 0 10px;
    font-weight: bold;
}
.footer a:hover {
    text-decoration: underline;
}
</style>
<div class="footer">
    Developed with ❤️ by <b>Soumyadeep Roy Chowdhury</b> © 2026 | Jadavpur University IT '28 | 
    <a href="https://github.com/soumyadeep-rc" target="_blank">GitHub</a>
    <a href="https://www.linkedin.com/in/soumyadeep-roy-chowdhury101/" target="_blank">LinkedIn</a>
    <a href="mailto:soumyadeeproychowdhury101@gmail.com">Gmail</a>
</div>
"""
st.markdown(footer_css, unsafe_allow_html=True)

# 4. Initialize Session States
if 'data_loaded' not in st.session_state:
    st.session_state['data_loaded'] = False
if 'resource_processor' not in st.session_state:
    st.session_state['resource_processor'] = None
if 'messages' not in st.session_state:
    st.session_state['messages'] = [{"role": "assistant", "content": "Hello! Load a website in the sidebar, and then ask me anything about it."}]

st.title("🕸️ RAG-CRAW : Your Web RAG Assistant")
st.caption("Powered by Gemini 2.5 Flash & LangChain")

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Crawler Settings")
    
    resource_type = st.selectbox("Resource Type", ("Website Single Page", "Website Multiple Pages"))
    website_url = st.text_input("Enter website URL", placeholder="https://example.com")
    
    if resource_type == "Website Multiple Pages":
        number_of_pages = st.number_input("Pages to crawl (max 50)", min_value=1, max_value=50, value=5)
    else:
        number_of_pages = 1

    if st.button("Load Website", use_container_width=True):
        if not website_url:
            st.warning("Please enter a URL first.")
        elif not MY_API_KEY:
            st.error("Backend API Key is missing! Check .env file.")
        else:
            with st.status("Initializing Crawler...", expanded=True) as status:
                try:
                    if resource_type == "Website Single Page":
                        st.session_state['resource_processor'] = RAG(website_url, MY_API_KEY, write_function=st.write)
                    else:
                        st.session_state['resource_processor'] = RAG(website_url, MY_API_KEY, resource_type="Website Multiple Pages", recursive_count=number_of_pages, write_function=st.write)
                    
                    st.session_state['data_loaded'] = True
                    status.update(label="Website processed and loaded!", state="complete", expanded=False)
                except Exception as e:
                    status.update(label="Failed to process website.", state="error")
                    st.error(f"Error details: {e}")

# --- MAIN CHAT UI ---
# Add padding at the bottom so the last message isn't hidden by the footer
st.markdown("<div style='margin-bottom: 80px;'></div>", unsafe_allow_html=True)

for msg in st.session_state['messages']:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input("Ask a question about the loaded website..."):
    st.session_state['messages'].append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    if not st.session_state['data_loaded'] or not st.session_state['resource_processor']:
        error_msg = "Please load a website in the sidebar before asking questions!"
        st.session_state['messages'].append({"role": "assistant", "content": error_msg})
        st.chat_message("assistant").error(error_msg)
    else:
        with st.chat_message("assistant"):
            with st.spinner("Scanning vector database..."):
                response = st.session_state['resource_processor'].get_response(prompt)
                st.write(response)
                st.session_state['messages'].append({"role": "assistant", "content": response})