from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from agent import agent_app
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    thread_id: str

class ChatResponse(BaseModel):
    message: str
    intent: str
    missing_fields: list[str]
    is_lead_captured: bool
    platform: str | None
    name: str | None
    email: str | None

@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    # Setup configuration for the LangGraph checkpointer (MemorySaver)
    config = {"configurable": {"thread_id": req.thread_id}}
    input_message = HumanMessage(content=req.message)
    
    # Run the graph and stream outputs
    events = agent_app.stream({"messages": [input_message]}, config=config, stream_mode="values")
    
    final_state = None
    for event in events:
        final_state = event
        
    last_message = final_state["messages"][-1].content
    intent = final_state.get("intent", "greeting")
    
    name = final_state.get("lead_name")
    email = final_state.get("lead_email")
    platform = final_state.get("lead_platform")
    
    missing_fields = []
    if not name: missing_fields.append("name")
    if not email: missing_fields.append("email")
    if not platform: missing_fields.append("platform")
    
    is_lead_captured = (intent == "high_intent") and (len(missing_fields) == 0)
    
    return ChatResponse(
        message=last_message,
        intent=intent,
        missing_fields=missing_fields,
        is_lead_captured=is_lead_captured,
        platform=platform,
        name=name,
        email=email
    )
