<div align="center">

# 🔷 VersaGraph RAG Agent

### *Enterprise-Grade Retrieval-Augmented Generation Platform*

[![Python 3.13+](https://img.shields.io/badge/Python-3.13%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.129%2B-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-1.2%2B-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white)](https://www.langchain.com/)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector_DB-DC382D?style=for-the-badge&logo=qdrant&logoColor=white)](https://qdrant.tech/)
[![MongoDB](https://img.shields.io/badge/MongoDB-8.0-47A248?style=for-the-badge&logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![Gradio](https://img.shields.io/badge/Gradio-6.6%2B-F97316?style=for-the-badge&logo=gradio&logoColor=white)](https://gradio.app/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

---

**VersaGraph RAG Agent** is a production-ready, multi-document Retrieval-Augmented Generation (RAG) system that enables intelligent, context-aware conversations over your uploaded documents. Powered by LangChain, Qdrant vector search, and MongoDB persistence, it delivers accurate, citation-backed responses with full conversation memory.

[Getting Started](#-getting-started) •
[Architecture](#-architecture) •
[API Reference](#-api-reference) •
[Configuration](#%EF%B8%8F-configuration) •
[Contributing](#-contributing)

</div>

---

## 📋 Table of Contents

- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Configuration](#environment-configuration)
  - [Running the Application](#running-the-application)
- [API Reference](#-api-reference)
- [Project Structure](#-project-structure)
- [How It Works](#-how-it-works)
- [Configuration](#%EF%B8%8F-configuration)
- [License](#-license)

---

## ✨ Key Features

| Feature | Description |
|---|---|
| **Multi-Document RAG** | Upload and query across multiple PDF, DOCX, and TXT files simultaneously within a single chat session. |
| **Hybrid Memory System** | Combines short-term memory (recent MongoDB messages) with long-term semantic memory (Qdrant vector search over conversation history). |
| **Source Citations** | Every AI response includes precise citations with original filename and page number references. |
| **Multi-Provider LLM Support** | Seamlessly switch between **Groq** (cloud) and **Ollama** (local/self-hosted) LLM providers. |
| **Persona System** | Configure custom AI personas per chat session — Academic Researcher, Legal Analyst, Financial Advisor, and more. |
| **Asynchronous Architecture** | Fully async from API to database layer, leveraging `asyncio`, `AsyncMongoClient`, and `AsyncQdrantClient`. |
| **Intelligent Question Rephrasing** | Automatically reformulates follow-up questions into standalone queries optimized for vector search. |
| **Interactive Web UI** | Professional Gradio-based frontend with session management, document upload, and real-time chat. |
| **LangServe Integration** | Exposes the RAG chain via LangServe with a built-in interactive playground for development and testing. |
| **Docker-Ready Infrastructure** | Pre-configured `docker-compose.yml` for one-command deployment of Qdrant and MongoDB. |

---

## 🏗 Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                                  │
│                                                                      │
│   ┌──────────────────┐    ┌──────────────────┐                       │
│   │   Gradio Web UI   │    │ LangServe Client │                      │
│   │   (Port 7860)     │    │  / REST Client   │                      │
│   └────────┬─────────┘    └────────┬─────────┘                       │
│            └───────────┬───────────┘                                  │
└────────────────────────┼─────────────────────────────────────────────┘
                         │ HTTP
┌────────────────────────┼─────────────────────────────────────────────┐
│                   APPLICATION LAYER (FastAPI - Port 8000)             │
│                        │                                             │
│   ┌────────────────────┴─────────────────────────┐                   │
│   │              API Router                       │                   │
│   │  ┌──────────────┐  ┌─────────────────────┐   │                   │
│   │  │  /data/*      │  │  /chat/*             │   │                  │
│   │  │  Upload &     │  │  Invoke, History,    │   │                  │
│   │  │  Process      │  │  LangServe Playground│   │                  │
│   │  └──────┬───────┘  └──────────┬───────────┘   │                  │
│   └─────────┼─────────────────────┼───────────────┘                  │
│             │                     │                                   │
│   ┌─────────┴─────────┐ ┌────────┴────────────────────┐             │
│   │  File Processing   │ │     RAG Chain (LangChain)    │            │
│   │  Pipeline          │ │                              │            │
│   │                    │ │  ┌─────────┐  ┌───────────┐  │            │
│   │  Loader → Splitter │ │  │Rephrase │→ │ Retriever │  │            │
│   │  → Embedder →      │ │  │  Prompt │  │(Doc+Hist) │  │            │
│   │  Vector Store      │ │  └─────────┘  └─────┬─────┘  │            │
│   │                    │ │                      │        │            │
│   └────────────────────┘ │  ┌───────────────────┴──────┐ │           │
│                          │  │  QA Prompt + LLM → Answer │ │           │
│                          │  │  (with Citations)         │ │           │
│                          │  └───────────────────────────┘ │           │
│                          └────────────────────────────────┘           │
└──────────────────────────────────────────────────────────────────────┘
                         │                    │
┌────────────────────────┼────────────────────┼────────────────────────┐
│                   DATA LAYER                 │                        │
│                        │                    │                        │
│   ┌────────────────────┴───┐  ┌─────────────┴──────────┐            │
│   │       MongoDB          │  │       Qdrant            │            │
│   │   (Port 27017)         │  │   (Port 6333/6334)      │            │
│   │                        │  │                         │            │
│   │  • Chats Collection    │  │  • Document Vectors     │            │
│   │  • Messages Collection │  │    Collection           │            │
│   │  • Files Collection    │  │  • Chat History Vectors │            │
│   │                        │  │    Collection           │            │
│   └────────────────────────┘  └─────────────────────────┘            │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 🛠 Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Backend Framework** | FastAPI | High-performance async REST API |
| **LLM Orchestration** | LangChain | Chain composition, prompt management, output parsing |
| **LLM Providers** | Groq / Ollama | Cloud-based or self-hosted language model inference |
| **Vector Database** | Qdrant | Semantic similarity search over document chunks and chat history |
| **Document Database** | MongoDB | Persistent storage for chats, messages, and file metadata |
| **Embeddings** | Ollama Embeddings (via FastEmbed) | Text-to-vector encoding for documents and queries |
| **Document Loaders** | PyMuPDF, Docx2txt, TextLoader | Multi-format document ingestion (PDF, DOCX, TXT) |
| **Text Splitting** | RecursiveCharacterTextSplitter | Intelligent chunking with configurable overlap |
| **API Serving** | LangServe | REST interface for LangChain chains with built-in playground |
| **Frontend** | Gradio | Interactive web-based chat UI with session management |
| **Containerization** | Docker Compose | Infrastructure orchestration for databases |
| **Data Validation** | Pydantic | Request/response schema validation and settings management |

---

## 🚀 Getting Started

### Prerequisites

- **Python** 3.13.5+
- **Docker** & **Docker Compose** (for Qdrant and MongoDB)
- **uv** (recommended) or **pip** for dependency management
- **Ollama** (if using local LLM/embeddings) — [Install Ollama](https://ollama.com/)
- **Groq API Key** (if using Groq as LLM provider) — [Get API Key](https://console.groq.com/)

### Installation

**1. Clone the repository:**

```bash
git clone https://github.com/your-username/VersaGraph-RAG-Agent.git
cd VersaGraph-RAG-Agent
```

**2. Start infrastructure services:**

```bash
docker compose up -d
```

This launches:
- **Qdrant** vector database on ports `6333` (HTTP) and `6334` (gRPC)
- **MongoDB** on port `27017`

**3. Install Python dependencies:**

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

**4. Pull the embedding model (if using Ollama):**

```bash
ollama pull nomic-embed-text
```

### Environment Configuration

Create a `.env` file in the project root:

```env
# ── File Processing ──────────────────────────────
FILE_ALLOWED_TYPES=["application/pdf","text/plain","application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
FILE_MAX_SIZE_MB=50
FILE_UPLOAD_CHUNK_SIZE=131072

# ── Text Chunking ────────────────────────────────
CHUNK_SIZE=512
CHUNK_OVERLAP=64

# ── Vector Store (Qdrant) ────────────────────────
VECTOR_STORE_TYPE=qdrant
EMBEDDING_MODEL=nomic-embed-text
EMBED_MODEL_SIZE=768
DISTANCE_METRIC=Cosine
URL_QDRANT=http://localhost:6333
QDRANT_API_KEY=
COLLECTION_APP_NAME=versagraph_documents
COLLECTION_CHATS_HISTORY_NAME=versagraph_chat_history

# ── MongoDB ──────────────────────────────────────
MONGODB_URL=mongodb://admin:password@localhost:27017
MONGOBD_USERNAME=admin
MONGODB_PASSWORD=password
MONGODB_DATABASE=versagraph

# ── LLM Provider ─────────────────────────────────
LLM_PROVIDER=groq                    # Options: "groq" or "ollama"
LLM_MODEL=llama-3.3-70b-versatile    # Model name for the chosen provider
API_KEY_GROQ=gsk_your_api_key_here   # Required if LLM_PROVIDER=groq
API_URL_LLM=http://localhost:11434   # Required if LLM_PROVIDER=ollama
LLM_TEMPERATURE=0.2
```

> **Note:** Ensure the `MONGOBD_USERNAME` and `MONGODB_PASSWORD` in `.env` match the values used in `docker-compose.yml`.

### Running the Application

**Start the FastAPI backend:**

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Start the Gradio frontend** (in a separate terminal):

```bash
python -m src.frontend.gradio_app
```

**Access the application:**

| Service | URL |
|---|---|
| Gradio Web UI | [http://localhost:7860](http://localhost:7860) |
| FastAPI Docs (Swagger) | [http://localhost:8000/docs](http://localhost:8000/docs) |
| LangServe Playground | [http://localhost:8000/chat/playground](http://localhost:8000/chat/playground) |
| Qdrant Dashboard | [http://localhost:6333/dashboard](http://localhost:6333/dashboard) |

---

## 📡 API Reference

### Data Routes — `/data`

#### `POST /data/upload`

Upload one or more documents and associate them with a chat session.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `files` | `UploadFile[]` | ✅ | Files to upload (PDF, DOCX, TXT) |
| `chat_id` | `string` (Form) | ✅ | Target chat session identifier |
| `persona_name` | `string` (Form) | ❌ | Persona name (default: `"General Assistant"`) |
| `persona_instructions` | `string` (Form) | ❌ | System instructions for the AI persona |

<details>
<summary><b>Example Response</b></summary>

```json
{
  "message": "Successfully uploaded 2 files.",
  "uploaded": [
    { "filename": "research_paper.pdf", "file_id": "a1b2c3d4e5f6_research_paper.pdf" },
    { "filename": "notes.txt", "file_id": "g7h8i9j0k1l2_notes.txt" }
  ],
  "failed": []
}
```
</details>

#### `POST /data/process`

Process (chunk, embed, and index) all pending files for a given chat session.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `chat_id` | `string` (JSON) | ✅ | Chat session to process files for |

<details>
<summary><b>Example Response</b></summary>

```json
{
  "message": "Processing complete. Success: 2, Failed: 0",
  "processed": ["a1b2c3d4e5f6_research_paper.pdf", "g7h8i9j0k1l2_notes.txt"],
  "failed": []
}
```
</details>

### Chat Routes — `/chat`

#### `POST /chat/invoke` (LangServe)

Send a message to the RAG chain and receive an AI-generated response with citations.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `input.question` | `string` | ✅ | The user's question |
| `input.chat_id` | `string` | ✅ | Active chat session identifier |
| `input.persona` | `string` | ❌ | Custom persona override |

<details>
<summary><b>Example Request</b></summary>

```json
{
  "input": {
    "question": "What are the key findings in chapter 3?",
    "chat_id": "abc123"
  }
}
```
</details>

#### `GET /chat/history`

Returns a list of all chat session IDs.

#### `GET /chat/history/{chat_id}`

Returns the full message history for a specific chat session.

---

## 📁 Project Structure

```
VersaGraph-RAG-Agent/
├── main.py                          # FastAPI application entry point & lifespan management
├── docker-compose.yml               # Qdrant + MongoDB infrastructure
├── pyproject.toml                   # Project metadata & dependencies
├── .env                             # Environment variables (not committed)
│
├── src/
│   ├── app/
│   │   ├── chains/                  # LangChain RAG pipeline
│   │   │   ├── rag_chain.py         # Full RAG chain assembly (rephrase → retrieve → generate)
│   │   │   ├── retriever.py         # Dual retriever (documents + conversation history)
│   │   │   ├── prompts.py           # System & user prompt templates
│   │   │   ├── memory_manager.py    # Hybrid memory (MongoDB + Qdrant) manager
│   │   │   └── llm/
│   │   │       ├── LLMProvider.py   # Multi-provider LLM factory (Groq / Ollama)
│   │   │       └── LLMProviderEnums.py
│   │   │
│   │   ├── database/
│   │   │   ├── mongo_db/
│   │   │   │   ├── BaseDataModel.py # Abstract base with auto-indexing
│   │   │   │   ├── ChatModel.py     # Chat session CRUD & file registry
│   │   │   │   ├── FileModel.py     # File metadata CRUD
│   │   │   │   ├── MessageModel.py  # Message persistence & retrieval
│   │   │   │   ├── DataBaseEnum.py  # Collection names & file status enums
│   │   │   │   └── schema/
│   │   │   │       ├── Chats.py     # Chat & ChatFile Pydantic models
│   │   │   │       ├── Files.py     # File Pydantic model
│   │   │   │       └── Messages.py  # Message Pydantic model
│   │   │   └── qdrantdb/
│   │   │       └── QdrantdbModel.py # Qdrant collection management, upsert & search
│   │   │
│   │   ├── routes/
│   │   │   ├── chat.py              # Chat endpoints & LangServe registration
│   │   │   ├── data.py              # File upload & processing endpoints
│   │   │   └── schema/
│   │   │       └── ProcessRequest.py
│   │   │
│   │   └── utilities/
│   │       ├── process_file.py      # File validation, storage & metadata extraction
│   │       ├── loader.py            # Multi-format document loading (PDF, DOCX, TXT)
│   │       ├── splitter.py          # Recursive text chunking
│   │       ├── embeder.py           # Ollama-based text embedding
│   │       └── ProcessEnum.py       # Processing signal enums
│   │
│   ├── data/
│   │   └── files/                   # Uploaded file storage directory
│   │
│   ├── frontend/
│   │   └── gradio_app.py            # Gradio web interface
│   │
│   └── helper/
│       └── config.py                # Pydantic Settings with .env integration
```

---

## 🔄 How It Works

### 1. Document Ingestion Pipeline

```
Upload File(s) → Validate (type, size) → Save to Disk → Store Metadata in MongoDB
                                                              │
                                                              ▼
Process Request → Load Document → Split into Chunks → Generate Embeddings → Upsert to Qdrant
                  (PyMuPDF/       (Recursive            (Ollama             (with chat_id
                   Docx2txt/       Character              Embeddings)         filter payload)
                   TextLoader)     Splitter)
```

1. **Upload**: Files are validated against allowed types and size limits, then saved to disk with unique identifiers.
2. **Metadata Tracking**: File records are created in MongoDB with status tracking (`uploaded` → `processing` → `indexed`).
3. **Processing**: Documents are loaded, split into overlapping chunks, embedded into vectors, and stored in Qdrant with `chat_id` filtering metadata.

### 2. RAG Query Pipeline

```
User Question
      │
      ▼
┌─────────────────────┐
│ Fetch Chat History   │──→ MongoDB (last 6 messages)
│ Fetch File Names     │──→ MongoDB (files in session)
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ Rephrase Question    │──→ LLM reformulates with context into standalone query
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ Dual Retrieval       │
│  • Document chunks   │──→ Qdrant (top 10 by similarity, filtered by chat_id)
│  • History memories  │──→ Qdrant (top 2 from conversation history)
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ Generate Answer      │──→ LLM produces cited response using retrieved context
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ Persist Turn         │──→ Save user msg + AI response to MongoDB & Qdrant
└─────────────────────┘
```

### 3. Hybrid Memory System

VersaGraph implements a dual-memory architecture:

- **Short-Term Memory**: The last N messages retrieved from MongoDB, providing immediate conversational context to the LLM.
- **Long-Term Semantic Memory**: All conversation turns are embedded and stored in Qdrant. During retrieval, semantically relevant past exchanges are surfaced alongside document results — enabling the agent to recall relevant information from much earlier in the conversation.

---

## ⚙️ Configuration

All configuration is managed through environment variables via Pydantic Settings (`.env` file).

### File Processing

| Variable | Type | Description |
|---|---|---|
| `FILE_ALLOWED_TYPES` | `list[str]` | Accepted MIME types for upload |
| `FILE_MAX_SIZE_MB` | `int` | Maximum file size in megabytes |
| `FILE_UPLOAD_CHUNK_SIZE` | `int` | Async file write buffer size (bytes) |

### Text Chunking

| Variable | Type | Description |
|---|---|---|
| `CHUNK_SIZE` | `int` | Maximum characters per chunk |
| `CHUNK_OVERLAP` | `int` | Overlap between consecutive chunks |

### Vector Store (Qdrant)

| Variable | Type | Description |
|---|---|---|
| `EMBEDDING_MODEL` | `str` | Ollama embedding model name |
| `EMBED_MODEL_SIZE` | `int` | Embedding vector dimensionality |
| `DISTANCE_METRIC` | `str` | Similarity metric (`Cosine`, `Euclid`, `Dot`) |
| `URL_QDRANT` | `str` | Qdrant server URL |
| `COLLECTION_APP_NAME` | `str` | Collection for document vectors |
| `COLLECTION_CHATS_HISTORY_NAME` | `str` | Collection for conversation history vectors |

### LLM Provider

| Variable | Type | Description |
|---|---|---|
| `LLM_PROVIDER` | `str` | `"groq"` or `"ollama"` |
| `LLM_MODEL` | `str` | Model identifier (e.g., `llama-3.3-70b-versatile`) |
| `API_KEY_GROQ` | `str` | Groq API key (required for Groq provider) |
| `API_URL_LLM` | `str` | Ollama server URL (required for Ollama provider) |
| `LLM_TEMPERATURE` | `float` | Response randomness (0.0 – 1.0) |

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'feat: add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

Please ensure your code follows the existing project structure and includes appropriate documentation.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

```
MIT License • Copyright (c) 2026 Mahmoud El Saeed Mohammed
```

---

<div align="center">

**Built with ❤️ using LangChain, FastAPI, Qdrant, and MongoDB**

</div>
