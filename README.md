# AutoStream Social-to-Lead Conversational Agent

## Overview

This repository contains an advanced conversational agent workflow developed for AutoStream. The system is designed to seamlessly classify user intent, answer product-related queries via Retrieval-Augmented Generation (RAG), and autonomously capture and qualify leads. The architecture leverages LangGraph for complex state management, Python (FastAPI) for robust backend execution, and React (Vite) for a professional, responsive frontend application.

## Prerequisites

Ensure the following dependencies are installed prior to deployment:
- Python 3.9+ 
- Node.js (v18 or higher)
- NPM or standard package manager

## Local Setup and Installation

### 1. Backend Configuration (FastAPI & LangGraph)

1. Clone the repository and navigate to the project root directory.
2. Initialize and activate a Python virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install the required Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment variables by duplicating `.env.example` to `.env` and supplying a valid OpenAI API key:
   ```env
   OPENAI_API_KEY=your_api_key_here
   ```
5. Start the underlying FastAPI backend server:
   ```bash
   uvicorn app:app --host 127.0.0.1 --port 8000
   ```

### 2. Frontend Configuration (React & Vite)

1. Open a secondary terminal instance and navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install the necessary Node packages:
   ```bash
   npm install
   ```
3. Boot the local development server:
   ```bash
   npm run dev
   ```
4. Access the web interface via a standard browser routing to `http://127.0.0.1:5173/`.

## Architecture Overview

The application utilizes a decoupled, modern architecture:
- **Frontend Layer**: Built using React and Vite. It communicates asynchronously with the backend API to render real-time state updates and manage conversational interface mechanics.
- **Backend Layer & State Management**: The core logic is powered by a FastAPI layer wrapping a LangGraph state machine. LangGraph enables persistent cyclical execution and conversation memory. Through the `AgentState` paradigm, the server accurately tracks intent categorization and parses missing lead parameters (`lead_name`, `lead_email`, `lead_platform`) across multi-turn interactions.
- **Intent Routing & RAG Execution**: Initial user input passes through a node executing an LLM-driven structured output parse. Based on classification, traffic routes either to a ChromaDB-backed RAG instance for product inquiries or to a qualification node that iteratively extracts entities for the final `mock_lead_capture` trigger.

## Deployment Integration: WhatsApp Webhook Strategy

Deploying this LangGraph agent to external asynchronous messaging platforms such as WhatsApp requires the following infrastructural modifications:

1. **Meta Application Configuration**: Register the application in the Meta Developer Portal and subscribe the webhook endpoint to WhatsApp Cloud API events.
2. **Endpoint Restructuring**: Expose `GET /webhook` to validate Meta verification challenges and `POST /webhook` to serialize incoming payload events.
3. **Checkpointer Memory Management**: Map the incoming WhatsApp User ID (`WaId`) to the `thread_id` within the LangGraph checkpointer. This assures decoupled, persistent memory allocation per individual interacting over WhatsApp.
4. **Asynchronous Dispatch**: Upon completion of the LangGraph execution cycle, the payload is directed to an outbound API call routing securely to Meta's message delivery endpoint, thereby closing the communication loop automatically.
