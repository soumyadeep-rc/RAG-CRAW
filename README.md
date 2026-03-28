# RAG-CRAW — Your Web RAG Assistant

A high-performance **Retrieval-Augmented Generation (RAG)** application that crawls live web pages, indexes their content into a vector store, and answers user queries using **Gemini 2.5 Flash** — all through a sleek, real-time Streamlit interface.

---

## 📌 Key Features

- **Intelligent Web Crawling** — Uses headless Selenium (Firefox/Geckodriver) to scrape single pages or recursively crawl entire domains, extracting clean, structured text via `UnstructuredHTMLLoader`.
- **Gemini 2.5 Flash Integration** — Leverages Google's latest high-speed LLM for rapid, grounded response generation with low latency.
- **Fail-Safe Embedding Logic** — Implements a custom batching system (`models/gemini-embedding-exp-03-07`) that processes chunks in batches of 80. On quota exhaustion, the system automatically waits 65 seconds before resuming — ensuring 100% embedding success even for large sites.
- **Vectorized Search via FAISS** — All embedded chunks are stored in a FAISS index for millisecond-latency similarity retrieval at query time.
- **Modern Chat UX** — A sleek, indigo-themed dark mode Streamlit interface with real-time streaming responses and chat history.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| AI Orchestration | LangChain |
| Frontend | Streamlit |
| Vector Store | FAISS |
| LLM & Embeddings | Google Generative AI (Gemini) |
| Browser Automation | Selenium (Firefox + Geckodriver) |

---

## ⚙️ How It Works

1. **Ingestion** — Selenium fetches the raw HTML of the target URL(s), which is then cleaned and converted to plain text using `UnstructuredHTMLLoader`.

2. **Chunking** — The extracted text is split using `RecursiveCharacterTextSplitter` into 1000-character segments with overlap to preserve contextual continuity across chunk boundaries.

3. **Rate-Limited Embedding** — Chunks are sent to Google's embedding API in batches of 80. If the quota is hit mid-batch, the system pauses for 65 seconds before continuing — making it robust for large-scale crawls without manual intervention.

4. **Retrieval** — At query time, the top-k most semantically relevant chunks are pulled from the FAISS index and injected as context into Gemini 2.5 Flash, which generates a grounded, factual response.

---

## 📁 Project Structure

```
RAG-CRAW/
├── client.py              # Streamlit frontend — UI logic, chat interface, session state
├── rag/
│   └── __init__.py        # Core RAG class — LLM orchestration, embeddings, FAISS indexing
├── crow_utils.py          # Utility functions for recursive web scraping via Selenium
└── .streamlit/
    └── config.toml        # Custom UI theme and branding configuration
```

---

## 🔧 Installation & Setup

### 1. Prerequisites

Ensure the following are installed on your system before proceeding:

- [Firefox](https://www.mozilla.org/en-US/firefox/new/)
- [Geckodriver](https://github.com/mozilla/geckodriver/releases) (must be accessible in your system `PATH`)
- Python 3.10+

### 2. Clone & Install

```bash
git clone https://github.com/soumyadeep-rc/RAG-CRAW.git
cd RAG-CRAW
pip install -r requirements.txt
```

### 3. Environment Variables

Create a `.env` file in the root directory:

```plaintext
GOOGLE_API_KEY=your_gemini_api_key_here
```

> You can obtain a Gemini API key from [Google AI Studio](https://aistudio.google.com/).

### 4. Run the App

```bash
streamlit run client.py
```

The app will be available at `http://localhost:8501` by default.

---

## 🔍 Usage

1. Open the app in your browser.
2. Enter the URL of the web page or site you want to ingest.
3. The system will crawl, chunk, embed, and index the content into FAISS.
4. Ask any question in the chat interface — the RAG pipeline retrieves relevant context and generates a grounded answer via Gemini.

---

## 📐 Architecture Overview

```
User Query
    │
    ▼
Streamlit UI (client.py)
    │
    ▼
RAG Core (rag/__init__.py)
    ├── Selenium Crawler (crow_utils.py)
    │       └── UnstructuredHTMLLoader → Raw Text
    ├── RecursiveCharacterTextSplitter → Chunks
    ├── Gemini Embedding API (batched, rate-limited) → Vectors
    ├── FAISS Index → Similarity Search
    └── Gemini 2.5 Flash → Final Answer
```

---

## ⚠️ Known Limitations

- Crawling is limited to publicly accessible, JavaScript-rendered pages. Pages behind authentication or bot-detection (e.g., Cloudflare) may not be fully scraped.
- Embedding quota limits on the free tier of Google AI may slow down ingestion for very large sites (mitigated by the built-in retry logic).
- FAISS index is currently in-memory and not persisted between sessions; re-ingestion is required on app restart.

---

## 📄 License

Distributed under the [MIT License](LICENSE).

---

**Developed by [Soumyadeep Roy Chowdhury](https://github.com/soumyadeep-rc)**
Jadavpur University IT '28
This project is licensed under the MIT License. See the LICENSE file for details.
