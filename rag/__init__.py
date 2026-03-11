from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.document_loaders import UnstructuredHTMLLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_classic.chains import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.documents import Document

from selenium import webdriver
from selenium.webdriver.firefox.options import Options

from craw_utils import scrape_site

class RAG:
    
    def __init__(self, url: str, google_api_key: str, resource_type: str="Website Single Page", recursive_count: int=5, write_function=None):

        if(write_function is None):
            self.write_function = print
        else:
            self.write_function = write_function

        self.write_function("Initializing RAG...")

        self.url = url

        try:
            if(resource_type == "Website Single Page"):
                self.retriever = self.read_website() 
        except Exception as e:
            self.write_function(f"Failed to read website: {e}")
            raise

        if(resource_type == "Website Multiple Pages"):
            self.retriever = self.read_website_recursive(recursive_count)

        self.write_function("Initializing LLM...")
        llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=google_api_key)

        prompt = ChatPromptTemplate.from_template("""
        Act as a chatbot and answer questions about the website. Refer to the following context whenever possible
        <context>
        {context}
        </context>
        ---
        Question: {input}                                                                                                                 
        """)

        self.write_function("Creating document chain...")
        self.document_chain = create_stuff_documents_chain(llm, prompt)

    
    def read_website(self):
        
        self.write_function("Reading website...")
        options = Options()

        options.add_argument('--headless')

        driver = webdriver.Firefox(options=options)

        # From here its Selenium as usual, example:
        driver.get(self.url)

        text_html = driver.page_source

        with open('page.html', 'w') as f:
            f.write(text_html)

        driver.close()

        loader = UnstructuredHTMLLoader('page.html')
        # load the text from variable

        # Split the text
        text_documents = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        documents = text_splitter.split_documents(text_documents)

        # documents = [Document(page_content="Raymond Brownell was a senior officer in the Royal Australian Air Force and a World War I flying ace", metadata={"source": "https://en.wikipedia.org/wiki/Raymond_Brownell"})]

        self.write_function("Storing content in vector store...")

        # Create and fill the FAISS index
        embedder = HuggingFaceEmbeddings()
        
        db = FAISS.from_documents(documents, embedder)

        # Setup the retriever
        retriever = db.as_retriever()
        # faiss.write_index(retriever.index, "index.faiss")
        # print(f'retriever = {retriever}')
        self.write_function("Content stored in vector store.")
        return retriever
    
    def read_website_recursive(self, recursive_count):
        
        self.write_function("Reading website recursively...")
        options = Options()
        options.add_argument('--headless')
        driver = webdriver.Firefox(options=options)


        text_documents = scrape_site(driver, self.url, count=recursive_count, write_function=self.write_function)
        # print(f'data = {data}')

        self.write_function('Storing content in vector store...')
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        documents = text_splitter.split_documents(text_documents)

        # Create and fill the FAISS index
        embedder = HuggingFaceEmbeddings()
        
        db = FAISS.from_documents(documents, embedder)
        # db.save_local("winoen_index")

        # Setup the retriever
        retriever = db.as_retriever()
        return retriever
     
    def get_response(self, question: str):

        self.write_function("Creating retrieval chain and getting response from LLM...")
        retrieval_chain = create_retrieval_chain(self.retriever, self.document_chain)
        result = retrieval_chain.invoke({"input": question})
        self.write_function(f"Answer: {result['answer']}" )
        # print(f'get_response = {question}, {result}')
        return result['answer']