# AutoStream Social-to-Lead Agent

An agentic AI workflow built for AutoStream to classify user intent, answer product questions via RAG, and autonomously capture leads using LangGraph, Python, and a sophisticated React Frontend.

## How to run the project locally

1. **Clone the repository** and navigate to the directory.
2. **Setup the Python Environment** (Backend):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Configure API Keys**: Copy `.env.example` to `.env` and add your `OPENAI_API_KEY`.
4. **Start the Backend server**:
   ```bash
   uvicorn app:app --host 127.0.0.1 --port 8000
   ```
5. **Start the Frontend UI**:
   Open a new terminal and navigate to the `/frontend` directory:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
6. Open your browser to the local URL (usually `http://127.0.0.1:5173/`).

## Architecture Explanation

This application utilizes a decoupled architecture featuring a **React (Vite)** frontend and a **FastAPI** backend that wraps a **LangGraph state machine**. LangGraph was chosen because conversational agent workflows require cyclic execution and memory retention that standard linear chains (like LCEL) cannot easily provide. By defining the agent as a finite state machine (`AgentState`), we can persistently store the conversation history alongside custom variables like `intent` and missing lead details (`lead_name`, `lead_email`, `lead_platform`).

When a user sends a message, it enters the `detect_intent` node, where `gpt-4o-mini` uses structured output to classify the message. Based on this intent, conditional edges route the execution flow. A product query triggers the RAG node (utilizing ChromaDB and OpenAI Embeddings), while high-intent triggers a specialized lead qualification node that dynamically checks the `AgentState` for missing fields. Importantly, running this loop inside a native Python API rather than a hosted service allows us to seamlessly trigger the local `mock_lead_capture` tool when the state constraints are met, providing robust error handling and exposing live execution traces directly to the sophisticated React UI in real-time.

## WhatsApp Deployment Integration

To integrate this sophisticated LangGraph agent with WhatsApp using Webhooks, the architecture would look like this:
1. **Meta App Setup**: Create an application in the Meta Developer Portal and subscribe to WhatsApp Cloud API Webhooks.
2. **Webhook Endpoint Mapping**: Extend the existing FastAPI backend with a new `GET /webhook` route (to handle Meta's verification challenge) and a `POST /webhook` route to receive real-time messages.
3. **State Checkpointer Adaptation**: Instead of generating a random `thread_id` locally, the system will use the user's WhatsApp Phone Number (`WaId`) as the `thread_id` in LangGraph's checkpointer. This guarantees state memory across entirely asynchronous WhatsApp interactions.
4. **Response Delivery**: Once LangGraph finishes processing its node execution (RAG query, asking for missing lead details, etc.), it outputs a string. The FastAPI endpoint will push that string payload securely back to the WhatsApp API to deliver the final response to the user's phone.
