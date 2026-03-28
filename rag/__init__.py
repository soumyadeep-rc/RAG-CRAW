import time
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import UnstructuredHTMLLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
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
        self.google_api_key = google_api_key

        try:
            if(resource_type == "Website Single Page"):
                self.retriever = self.read_website() 
        except Exception as e:
            self.write_function(f"Failed to read website: {e}")
            raise

        if(resource_type == "Website Multiple Pages"):
            self.retriever = self.read_website_recursive(recursive_count)

        self.write_function("Initializing LLM...")
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=self.google_api_key)

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

        driver.get(self.url)
        text_html = driver.page_source

        with open('page.html', 'w', encoding='utf-8') as f:
            f.write(text_html)

        driver.quit()

        loader = UnstructuredHTMLLoader('page.html')
        text_documents = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        documents = text_splitter.split_documents(text_documents)

        if not documents:
            self.write_function("❌ Error: No content could be extracted. The site might be blocking the crawler.")
            return None

        self.write_function("Storing content in vector store...")

        embedder = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001", 
            google_api_key=self.google_api_key
        )
        
        # --- BATCHING LOGIC START ---
        self.write_function(f"Found {len(documents)} text chunks. Embedding in batches to avoid rate limits...")
        db = None
        batch_size = 80

        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]
            total_batches = (len(documents) + batch_size - 1) // batch_size
            self.write_function(f"Embedding batch {i // batch_size + 1} of {total_batches}...")
            
            if db is None:
                db = FAISS.from_documents(batch, embedder)
            else:
                db.add_documents(batch)
                
            if i + batch_size < len(documents):
                self.write_function("Pausing for 65 seconds to respect Google's free API limits...")
                time.sleep(65)
        # --- BATCHING LOGIC END ---

        retriever = db.as_retriever()
        self.write_function("Content stored in vector store.")
        return retriever
    
    def read_website_recursive(self, recursive_count):
        
        self.write_function("Reading website recursively...")
        options = Options()
        options.add_argument('--headless')
        driver = webdriver.Firefox(options=options)

        try:
            text_documents = scrape_site(driver, self.url, count=recursive_count, write_function=self.write_function)
        finally:
            driver.quit() 

        self.write_function('Storing content in vector store...')
        
        if not text_documents:
            self.write_function("Warning: No extractable documents found to embed.")
            return None

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        documents = text_splitter.split_documents(text_documents)

        embedder = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001", 
            google_api_key=self.google_api_key
        )
        
        # --- BATCHING LOGIC START ---
        self.write_function(f"Found {len(documents)} text chunks. Embedding in batches to avoid rate limits...")
        db = None
        batch_size = 80

        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]
            total_batches = (len(documents) + batch_size - 1) // batch_size
            self.write_function(f"Embedding batch {i // batch_size + 1} of {total_batches}...")
            
            if db is None:
                db = FAISS.from_documents(batch, embedder)
            else:
                db.add_documents(batch)
                
            if i + batch_size < len(documents):
                self.write_function("Pausing for 65 seconds to respect Google's free API limits...")
                time.sleep(65)
        # --- BATCHING LOGIC END ---

        retriever = db.as_retriever()
        return retriever
      
    def get_response(self, question: str):
        if not getattr(self, 'retriever', None):
            return "I couldn't extract any readable text from that website to answer your question."

        self.write_function("Creating retrieval chain and getting response from LLM...")
        retrieval_chain = create_retrieval_chain(self.retriever, self.document_chain)
        result = retrieval_chain.invoke({"input": question})
        return result['answer']