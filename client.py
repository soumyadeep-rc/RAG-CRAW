import streamlit as st
from rag import RAG
from dotenv import load_dotenv
import os

import asyncio

def get_or_create_eventloop():
    try:
        return asyncio.get_event_loop()
    except RuntimeError as ex:
        if "There is no current event loop in thread" in str(ex):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return asyncio.get_event_loop()

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

placeholder = st.empty()
def write_in_placeholder(text:str, placeholder=placeholder):
    if(placeholder is None):
        st.write(text)
    else:
        placeholder.info(text)

if 'data_loaded' not in st.session_state:
    st.session_state['data_loaded'] = False

if 'resource_processor' not in st.session_state:
    st.session_state['resource_processor'] = None

st.title("Resource Augmented Generation")


# Dropdown to choose the type of RAG
resource_type = st.selectbox(  
    "Select Resource Type",
    ("Website Single Page", "Website Multiple Pages")
)

# Conditional input fields based on the selected resource type
if resource_type == "Website Single Page":
    website_url = st.text_input("Enter website URL")
    api_key = st.text_input("Enter Google API Key")

    if(api_key == ""):
        load_dotenv('.env')
        api_key = os.getenv('GOOGLE_API_KEY')

    if st.button("Load Website"):
        st.session_state['resource_processor'] = RAG(website_url, api_key, write_function=write_in_placeholder)
        st.session_state['data_loaded'] = True
        placeholder.empty()
        st.success("Website data loaded successfully")

if resource_type == "Website Multiple Pages":
    website_url = st.text_input("Enter website URL")
    api_key = st.text_input("Enter Google API Key")
    number_of_pages = st.number_input("Enter number of pages to crawl (max. 50)", min_value=1, max_value=50)

    if(api_key == ""):
        load_dotenv('.env')
        api_key = os.getenv('GOOGLE_API_KEY')

    if st.button("Load Website"):
        st.session_state['resource_processor'] = RAG(website_url, api_key, write_function=write_in_placeholder, resource_type="Website Multiple Pages", recursive_count=number_of_pages)
        st.session_state['data_loaded'] = True
        st.success("Website data loaded successfully")

# Handling questions or queries based on the loaded data
if st.session_state['data_loaded']:
    question = st.text_input("Enter your question")
    if st.button("Get Answer"):
        if st.session_state['resource_processor']:
            response = st.session_state['resource_processor'].get_response(question)
        else:
            st.error("No resource processor available.")