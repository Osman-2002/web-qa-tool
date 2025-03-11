from flask import Flask, request, render_template, jsonify
import requests
from bs4 import BeautifulSoup
import re
from openai import OpenAI
import os

app = Flask(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "ENTER-APIKEY-HERE"))  

content_store = []

def scrape_url(url):
    """Scrape text content from a URL."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = " ".join(chunk for chunk in chunks if chunk)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if len(s) > 10]
    except Exception as e:
        return [f"Error scraping {url}: {str(e)}"]

def ingest_urls(urls):
    """Ingest content from URLs."""
    global content_store
    content_store = []
    for url in urls.split(','):
        url = url.strip()
        if url:
            sentences = scrape_url(url)
            content_store.extend(sentences)

def estimate_tokens(text):
    """Roughly estimate the number of tokens in a text (1 token ≈ 0.75 words)."""
    words = len(text.split())
    return int(words / 0.75) + 1  

def truncate_context(context, max_tokens, question):
    """Truncate context to fit within max_tokens, preserving the question."""
    base_prompt = (
        "You are an AI that answers questions based solely on the provided context. "
        "Do not use any external knowledge or make assumptions beyond the given text. "
        "If the answer is not clear from the context, say 'The answer is not available in the provided content.'\n\n"
        "Context:\n\n\nQuestion: " + question + "\n\nAnswer:"
    )
    base_tokens = estimate_tokens(base_prompt)
    
    max_context_tokens = max_tokens - base_tokens - 150  
    
    if estimate_tokens(context) <= max_context_tokens:
        return context
    
    truncated = ""
    for sentence in context.split('\n'):
        if estimate_tokens(truncated + sentence) <= max_context_tokens:
            truncated += sentence + "\n"
        else:
            break
    return truncated.strip()

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/ingest', methods=['POST'])
def ingest():
    urls = request.json.get('urls', '')
    ingest_urls(urls)
    return jsonify({'status': 'success', 'message': f"Ingested {len(content_store)} sentences"})

@app.route('/ask', methods=['POST'])
def ask():
    question = request.json.get('question', '')
    if not question or not content_store:
        return jsonify({'answer': 'Please ingest URLs first or ask a question.'})
    
    context = "\n".join(content_store)
    
    max_tokens = 16385  
    truncated_context = truncate_context(context, max_tokens, question)
    
    prompt = (
        "You are an AI that answers questions based solely on the provided context. "
        "Do not use any external knowledge or make assumptions beyond the given text. "
        "If the answer is not clear from the context, say 'The answer is not available in the provided content.'\n\n"
        "Context:\n" + truncated_context + "\n\n"
        "Question: " + question + "\n\n"
        "Answer:"
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers based only on the provided context."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.5
        )
        answer = response.choices[0].message.content.strip()
    except Exception as e:
        answer = f"Error calling OpenAI API: {str(e)}"
    
    return jsonify({'answer': answer})

if __name__ == '__main__':
    app.run(debug=True)

