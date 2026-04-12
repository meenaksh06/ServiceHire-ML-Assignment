import operator
from typing import Annotated, Literal, TypedDict, Optional
from pydantic import BaseModel, Field

from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

from rag_pipeline import retrieve_knowledge

# Define the State
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    intent: Optional[Literal["greeting", "product_query", "high_intent"]]
    lead_name: Optional[str]
    lead_email: Optional[str]
    lead_platform: Optional[str]

# Define Intent Classification Model
class IntentClassification(BaseModel):
    intent: Literal["greeting", "product_query", "high_intent"] = Field(
        description="The intent of the user's latest message. "
                    "'greeting' for casual hellos or goodbyes. "
                    "'product_query' for questions about pricing, features, or policies. "
                    "'high_intent' if the user expresses interest in buying, signing up, or trying a plan."
    )

# Define Lead Details Extraction Model
class LeadExtraction(BaseModel):
    name: Optional[str] = Field(description="The user's name if provided. Null if not provided.")
    email: Optional[str] = Field(description="The user's email if provided. Null if not provided.")
    platform: Optional[str] = Field(description="The user's content creator platform (e.g., YouTube, Instagram) if provided. Null if not provided.")

# Mock lead capture tool
def mock_lead_capture(name: str, email: str, platform: str):
    print(f"\n[TOOL EXECUTION] Lead captured successfully: {name}, {email}, {platform}\n")
    return "Lead successfully captured in the system."


def detect_intent_node(state: AgentState):
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    structured_llm = llm.with_structured_output(IntentClassification)
    
    # We only look at the most recent message to determine current intent
    user_msg = state["messages"][-1].content
    # Include some context of previous messages potentially
    prompt = f"Analyze the following user message and context, and determine their intent.\nUser Message: {user_msg}"
    
    result = structured_llm.invoke([HumanMessage(content=prompt)])
    
    return {"intent": result.intent}

def route_intent(state: AgentState) -> Literal["handle_greeting", "handle_rag", "handle_lead"]:
    intent = state.get("intent")
    if intent == "greeting":
        return "handle_greeting"
    elif intent == "product_query":
        return "handle_rag"
    elif intent == "high_intent":
        return "handle_lead"
    else:
        # Default to rag or greeting if parsing failed
        return "handle_greeting"

def handle_greeting_node(state: AgentState):
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    sys_prompt = SystemMessage(content="You are a helpful assistant for AutoStream, an automated video editing SaaS. Give a short, friendly greeting. Do not ask for their email or pitch aggressively yet.")
    response = llm.invoke([sys_prompt] + state["messages"])
    return {"messages": [response]}

def handle_rag_node(state: AgentState):
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    user_msg = state["messages"][-1].content
    context = retrieve_knowledge(user_msg)
    
    sys_prompt = SystemMessage(content=f\"\"\"
    You are a sales assistant for AutoStream. Answer the user's question using ONLY the following context.
    If the context does not contain the answer, politely say you don't have that information.
    Do not make up pricing or features.
    
    Context:
    {context}
    \"\"\")
    
    # We use conversation history and RAG context
    response = llm.invoke([sys_prompt] + state["messages"])
    return {"messages": [response]}

def handle_lead_node(state: AgentState):
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    # Extract details from recent conversation
    extracted_llm = llm.with_structured_output(LeadExtraction)
    
    # Provide the last few messages for extraction context
    recent_messages = state["messages"][-3:]
    conversation_text = "\\n".join([f"{type(m).__name__}: {m.content}" for m in recent_messages])
    
    extraction = extracted_llm.invoke([SystemMessage(content=f"Extract lead details if present in the following conversation:\\n{conversation_text}")])
    
    # Update state with newly found details (keep old ones if not found)
    updates = {}
    name = state.get("lead_name")
    email = state.get("lead_email")
    platform = state.get("lead_platform")
    
    if extraction.name and not name:
        updates["lead_name"] = extraction.name
        name = extraction.name
    if extraction.email and not email:
        updates["lead_email"] = extraction.email
        email = extraction.email
    if extraction.platform and not platform:
        updates["lead_platform"] = extraction.platform
        platform = extraction.platform
        
    missing = []
    if not name: missing.append("name")
    if not email: missing.append("email")
    if not platform: missing.append("creator platform (e.g., YouTube, Instagram, etc.)")
    
    if len(missing) == 0:
        # Execute tool
        tool_resp = mock_lead_capture(name, email, platform)
        response_msg = AIMessage(content=f"Thanks {name}! We've registered your interest for your {platform} content and sent details to {email}. {tool_resp} Our team will be in touch soon!")
        updates["messages"] = [response_msg]
    else:
        # Ask for missing details
        sys_prompt = SystemMessage(content=f"You are qualifying a lead for AutoStream. We are missing the following details: {', '.join(missing)}. Politely ask the user to provide these remaining details in a short message.")
        response_msg = llm.invoke([sys_prompt] + state["messages"])
        updates["messages"] = [response_msg]
        
    return updates

# Build Graph
builder = StateGraph(AgentState)

builder.add_node("detect_intent", detect_intent_node)
builder.add_node("handle_greeting", handle_greeting_node)
builder.add_node("handle_rag", handle_rag_node)
builder.add_node("handle_lead", handle_lead_node)

builder.set_entry_point("detect_intent")
builder.add_conditional_edges("detect_intent", route_intent)
builder.add_edge("handle_greeting", END)
builder.add_edge("handle_rag", END)
builder.add_edge("handle_lead", END)

memory = MemorySaver()
agent_app = builder.compile(checkpointer=memory)
