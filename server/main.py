import io
import os
import re
import sys
from PIL import Image
import pytesseract
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import trafilatura
from bs4 import BeautifulSoup
from langchain_text_splitters import RecursiveCharacterTextSplitter
from vector import vector_store
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from qdrant_client.http import models
from playwright.sync_api import sync_playwright  # Using sync_api
from dotenv import load_dotenv
load_dotenv()
# Fixed trailing space in model name
llm = ChatOpenAI(
    model=os.getenv("CHAT_MODEL"),
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("API_URL"),  # Or use os.getenv("OPENROUTER_API_KEY")
)

app = FastAPI()


origins = [
    "http://localhost:3000",
    os.getenv("FRONTEND_URL")  # <-- Now uses the correct environment variable
]
print(origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # <-- अब यह सही वेरिएबल इस्तेमाल करेगा
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class ChatRequest(BaseModel):
    url: str
    text: str

@app.get("/")
def home():
    return {"status": "Server is running successfully!"}

@app.post("/chat")
def chat(request: ChatRequest):
    print("chat route hittings")
    f_filter = models.Filter(
        must=[
            models.FieldCondition(
                key="metadata.source",
                match=models.MatchValue(value=request.url)
            )
        ]
    )
    search_docs = vector_store.similarity_search(request.text, filter=f_filter)
    
    context = "\n\n".join([doc.page_content for doc in search_docs]) if search_docs else "No context found."
    
    # FIXED: Escape curly braces so LangChain doesn't crash on JSON/code blocks inside blog content
    safe_context = context.replace("{", "{{").replace("}", "}}")
    
    system_prompt = (
        "You are a helpful AI assistant. Your primary job is to read and analyze "
        "the provided article context to answer the user's question.\n\n"
        "Rules:\n"
        "- First, look for the answer within the provided context.\n"
        "- If the same article or source has been uploaded multiple times resulting "
        "in repeated chunks in the context, treat it as a single unified text and "
        "avoid redundant or repetitive explanations.\n"
        "- If the user asks for the **conclusion** of the article or asks **why the writer wrote a specific line/statement**, analyze the context deeply.\n"
        "- If needed, use your broader knowledge base or search the web context to explain the deeper meaning, background, or rationale behind the writer's statements while connecting it back to the article.\n"
        "- If the user asks a related question or a word/concept that requires broader "
        "explanation beyond the text (implying a general search or deeper context), "
        "feel free to explain it clearly using your broader knowledge base while "
        "connecting it back to the article context if applicable.\n"
        "- Be concise, helpful, and professional.\n\n"
        f"Context:\n{safe_context}"
    )

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{text}")
    ])

    chain = prompt_template | llm
    results = chain.invoke({"text": request.text})
    raw_answer = results.content
    cleaned_answer = re.sub(r'[#%^]+', '', raw_answer).strip()
    
    return {
        "question": request.text,
        "answer": cleaned_answer
    }

@app.post("/url")
def Url_upload(Url: str):  # Standard def to safely run Sync Playwright via FastAPI threadpool
    download = None
    
    # Step 0: Use Playwright Sync API safely inside FastAPI's threadpool worker
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page.goto(Url, timeout=60000)
            
            # Use domcontentloaded and a safe wait timeout to let JS render content completely
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(3000) 
            
            download = page.content()
            browser.close()
    except Exception as e:
        print(f"Playwright failed, falling back to requests: {str(e)}")
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = requests.get(Url, headers=headers, timeout=15)
            if response.status_code == 200:
                download = response.text
            else:
                raise HTTPException(status_code=400, detail=f"Website blocked the request (Status: {response.status_code})")
        except Exception as req_err:
            raise HTTPException(status_code=400, detail=f"Failed to fetch URL content: {str(req_err)}")

    if not download:
        raise HTTPException(status_code=400, detail="Failed to fetch URL content.")
        
    article = None
    
    # Step 1: Try extracting text using trafilatura
    try:
        article = trafilatura.extract(download)
    except Exception:
        pass
        
    # Step 2: Fallback to BeautifulSoup if trafilatura fails
    if not article or len(article.strip()) < 20:
        try:
            print("Trafilatura failed. Falling back to BeautifulSoup text extraction...")
            soup = BeautifulSoup(download, "html.parser")
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            article = soup.get_text(separator="\n", strip=True)
        except Exception:
            pass
            
    if not article or len(article.strip()) < 5:
        raise HTTPException(status_code=400, detail="Failed to extract readable text from this webpage.")
        
    print(f"Extracted article length: {len(article)}")
    
    # Split documentation into multiple chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=200
    )
    docs = text_splitter.create_documents(
        texts=[article], 
        metadatas=[{"source": Url}]
    )
    print(f"Split documentation into {len(docs)} chunks.")
    
    texts = [doc.page_content for doc in docs]
    metadatas = [doc.metadata for doc in docs]

    vector_store.add_texts(texts=texts, metadatas=metadatas)

    return {
        "msg": f"Article successfully extracted via Playwright, processed into {len(docs)} chunks, and embedded!"
    }