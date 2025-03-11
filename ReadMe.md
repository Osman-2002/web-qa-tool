# Web Q&A Tool

A web-based tool that allows users to ingest content from URLs and ask questions based solely on that content using the OpenAI API.

## Features
- Input one or more URLs to scrape their text content.
- Ask questions about the ingested content.
- Receive answers grounded strictly in the scraped content, without external knowledge.

## Requirements
- Python 3.x
- Libraries: `flask`, `requests`, `beautifulsoup4`, `openai`
- An OpenAI API key (sign up at [platform.openai.com](https://platform.openai.com/))

## Installation
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/web-qa-tool.git
   cd web-qa-tool