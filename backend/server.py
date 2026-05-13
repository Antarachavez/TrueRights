from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Optional
import uuid
from datetime import datetime
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Load data from JSON file
import json as json_module
with open(ROOT_DIR / 'data.json') as _f:
    _DATA = json_module.load(_f)

CATEGORIES = _DATA["categories"]
SCENARIOS = _DATA["scenarios"]
SUBCATEGORY_LEGAL_QUOTES = _DATA["subcategory_legal_quotes"]
SCENARIO_LEGAL_QUOTES = _DATA["scenario_legal_quotes"]
DEFAULT_SCRIPTS = _DATA["default_scripts"]
RESOURCES = _DATA["resources"]
US_STATES = _DATA["us_states"]

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')

app = FastAPI()
api_router = APIRouter(prefix="/api")

# Models
class UserPreferences(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    device_id: str
    state: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    onboarding_completed: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class UserPreferencesCreate(BaseModel):
    device_id: str
    state: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    onboarding_completed: bool = False

class SavedScript(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    device_id: str
    title: str
    content: str
    category: str
    saved_at: datetime = Field(default_factory=datetime.utcnow)

class SavedScriptCreate(BaseModel):
    device_id: str
    title: str
    content: str
    category: str

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    device_id: str
    session_id: str
    role: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ChatRequest(BaseModel):
    device_id: str
    session_id: str
    message: str
    user_state: Optional[str] = None

class GenerateScenarioRequest(BaseModel):
    question: str
    category: str = "general"
    device_id: str = ""

class EmergencyNote(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    device_id: str
    content: str
    event_time: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)

class EmergencyNoteCreate(BaseModel):
    device_id: str
    content: str
    event_time: datetime

class SMSRequest(BaseModel):
    to_phone: str
    message: str
    from_name: str

# Data loaded from data.json above

# ROUTES
@api_router.get("/")
async def root():
    return {"message": "True Rights API", "version": "5.0.0"}

@api_router.get("/categories")
async def get_categories():
    return CATEGORIES

# === AI-Generated Scenario Routes (must be before parameterized routes) ===

@api_router.post("/scenarios/generate")
async def generate_scenario(request: GenerateScenarioRequest):
    """Use AI to generate a scenario for a question not in the pre-loaded data."""
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="AI not configured")

    # Check if already generated before
    existing = await db.generated_scenarios.find_one({
        "question": {"$regex": f"^{request.question.strip()}$", "$options": "i"}
    })
    if existing:
        existing["_id"] = str(existing["_id"])
        return existing

    # Find category name for context
    cat_name = request.category
    for c in CATEGORIES:
        if c["id"] == request.category:
            cat_name = c["name"]
            break

    system = f"""You generate structured rights information for teens. Category: {cat_name}.
Return ONLY valid JSON (no markdown, no backticks) with this exact structure:
{{
  "short_answer": "1-2 sentence direct answer",
  "explanation": "2-3 paragraph plain English explanation. Be real and direct, not corporate.",
  "next_steps": ["Step 1", "Step 2", "Step 3", "Step 4"],
  "legal_quotes": [
    {{"source": "Law name and citation", "text": "Exact or close quote from the law", "type": "Constitution|Supreme Court|Federal Law|State Law"}},
    {{"source": "Another law", "text": "Quote", "type": "type"}}
  ]
}}
Rules:
- short_answer: Direct, teen-friendly, 1-2 sentences max
- explanation: Concise, real talk. No legalese. Like an older friend explaining.
- next_steps: 3-5 practical action items
- legal_quotes: 1-3 REAL laws, amendments, or court cases. Use actual citations.
- NEVER make up fake laws. If unsure, cite the most relevant Constitutional amendment.
- This is educational info, NOT legal advice."""

    try:
        import json as json_module
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"kyr-gen-{uuid.uuid4()}",
            system_message=system
        ).with_model("anthropic", "claude-sonnet-4-5-20250929")

        response = await chat.send_message(
            UserMessage(text=f"Generate rights info for this question: {request.question}")
        )

        # Parse the JSON response - clean up markdown if present
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        parsed = json_module.loads(cleaned)

        # Build the generated scenario document
        gen_id = f"gen-{uuid.uuid4().hex[:8]}"
        scenario_doc = {
            "id": gen_id,
            "question": request.question.strip(),
            "short_answer": parsed.get("short_answer", ""),
            "explanation": parsed.get("explanation", ""),
            "script": "",
            "next_steps": parsed.get("next_steps", []),
            "legal_quotes": parsed.get("legal_quotes", []),
            "category": request.category,
            "category_name": cat_name,
            "generated": True,
            "generated_at": datetime.utcnow().isoformat(),
            "device_id": request.device_id,
        }

        await db.generated_scenarios.insert_one(scenario_doc.copy())
        return scenario_doc

    except Exception as e:
        logging.error(f"Generate error: {e}")
        raise HTTPException(status_code=500, detail="AI generation failed")


@api_router.get("/scenarios/generated/{category_id}")
async def get_generated_scenarios(category_id: str):
    """Get all AI-generated scenarios for a category."""
    scenarios = await db.generated_scenarios.find(
        {"category": category_id}
    ).sort("generated_at", -1).to_list(100)
    for s in scenarios:
        s["_id"] = str(s["_id"])
    return scenarios


@api_router.get("/scenarios/generated")
async def get_all_generated_scenarios():
    """Get all AI-generated scenarios."""
    scenarios = await db.generated_scenarios.find().sort("generated_at", -1).to_list(200)
    for s in scenarios:
        s["_id"] = str(s["_id"])
    return scenarios


@api_router.get("/scenario/generated/{scenario_id}")
async def get_generated_scenario_detail(scenario_id: str):
    """Get a specific AI-generated scenario."""
    scenario = await db.generated_scenarios.find_one({"id": scenario_id})
    if not scenario:
        raise HTTPException(status_code=404, detail="Not found")
    scenario["_id"] = str(scenario["_id"])
    return scenario


@api_router.get("/scenarios/search-all/{query}")
async def search_all_scenarios(query: str):
    """Search across both pre-loaded and AI-generated scenarios."""
    results = []
    q = query.lower().strip()

    for cat_id, cat_data in SCENARIOS.items():
        for subcat_id, scenarios in cat_data.items():
            for s in scenarios:
                if q in s["question"].lower() or q in s["short_answer"].lower():
                    r = s.copy()
                    r["category"] = cat_id
                    r["subcategory"] = subcat_id
                    r["generated"] = False
                    results.append(r)

    generated = await db.generated_scenarios.find({
        "$or": [
            {"question": {"$regex": q, "$options": "i"}},
            {"short_answer": {"$regex": q, "$options": "i"}},
        ]
    }).to_list(50)
    for g in generated:
        g["_id"] = str(g["_id"])
        g["generated"] = True
        results.append(g)

    return results

# === Pre-loaded scenario routes ===

@api_router.get("/scenarios/{category_id}")
async def get_scenarios_by_category(category_id: str):
    if category_id not in SCENARIOS:
        raise HTTPException(status_code=404, detail="Not found")
    all_scenarios = []
    for subcat_id, scenarios in SCENARIOS[category_id].items():
        for s in scenarios:
            sc = s.copy()
            sc["subcategory"] = subcat_id
            sc["category"] = category_id
            all_scenarios.append(sc)
    return all_scenarios

@api_router.get("/scenarios/{category_id}/{subcategory_id}")
async def get_scenarios_by_subcategory(category_id: str, subcategory_id: str):
    if category_id not in SCENARIOS or subcategory_id not in SCENARIOS[category_id]:
        raise HTTPException(status_code=404, detail="Not found")
    return SCENARIOS[category_id][subcategory_id]

@api_router.get("/scenario/{scenario_id}")
async def get_scenario_detail(scenario_id: str):
    for cat_id, cat_data in SCENARIOS.items():
        for subcat_id, scenarios in cat_data.items():
            for s in scenarios:
                if s["id"] == scenario_id:
                    r = s.copy()
                    r["category"] = cat_id
                    r["subcategory"] = subcat_id
                    # Look up legal quotes: specific override first, then subcategory
                    if scenario_id in SCENARIO_LEGAL_QUOTES:
                        r["legal_quotes"] = SCENARIO_LEGAL_QUOTES[scenario_id]
                    else:
                        # Find matching subcategory prefix
                        prefix = "-".join(scenario_id.rsplit("-", 1)[0].split("-")[:2]) if "-" in scenario_id else scenario_id
                        # Try prefix match (e.g. "sch-s" from "sch-s1")
                        import re
                        sid = scenario_id
                        match = re.match(r"^([a-z]+-[a-z]+)", sid)
                        if match:
                            prefix = match.group(1)
                        r["legal_quotes"] = SUBCATEGORY_LEGAL_QUOTES.get(prefix, [])
                    return r
    raise HTTPException(status_code=404, detail="Not found")

@api_router.get("/scripts/default")
async def get_default_scripts():
    return DEFAULT_SCRIPTS

@api_router.get("/scripts/by-category")
async def get_scripts_by_category():
    """Return all scripts extracted from scenarios, grouped by category."""
    result = {}
    for cat in CATEGORIES:
        cat_id = cat["id"]
        cat_name = cat["name"]
        cat_icon = cat["icon"]
        cat_color = cat["color"]
        scripts_list = []
        if cat_id in SCENARIOS:
            for subcat_id, scenarios in SCENARIOS[cat_id].items():
                # Find subcategory name
                subcat_name = subcat_id
                for sc in cat.get("subcategories", []):
                    if sc["id"] == subcat_id:
                        subcat_name = sc["name"]
                        break
                for s in scenarios:
                    if s.get("script"):
                        scripts_list.append({
                            "id": s["id"],
                            "title": s.get("question", "Script"),
                            "content": s["script"],
                            "category": cat_id,
                            "category_name": cat_name,
                            "subcategory": subcat_id,
                            "subcategory_name": subcat_name,
                        })
        result[cat_id] = {
            "name": cat_name,
            "icon": cat_icon,
            "color": cat_color,
            "scripts": scripts_list,
            "count": len(scripts_list),
        }
    return result

@api_router.get("/resources")
async def get_resources():
    return RESOURCES

@api_router.get("/states")
async def get_states():
    return US_STATES

@api_router.post("/preferences", response_model=UserPreferences)
async def create_or_update_preferences(input: UserPreferencesCreate):
    existing = await db.preferences.find_one({"device_id": input.device_id})
    if existing:
        await db.preferences.update_one({"device_id": input.device_id}, {"$set": {**input.dict(), "updated_at": datetime.utcnow()}})
        updated = await db.preferences.find_one({"device_id": input.device_id})
        return UserPreferences(**updated)
    prefs = UserPreferences(**input.dict())
    await db.preferences.insert_one(prefs.dict())
    return prefs

@api_router.get("/preferences/{device_id}")
async def get_preferences(device_id: str):
    prefs = await db.preferences.find_one({"device_id": device_id})
    return UserPreferences(**prefs) if prefs else None

@api_router.post("/scripts/saved", response_model=SavedScript)
async def save_script(input: SavedScriptCreate):
    script = SavedScript(**input.dict())
    await db.saved_scripts.insert_one(script.dict())
    return script

@api_router.get("/scripts/saved/{device_id}")
async def get_saved_scripts(device_id: str):
    scripts = await db.saved_scripts.find({"device_id": device_id}).to_list(100)
    return [SavedScript(**s) for s in scripts]

@api_router.delete("/scripts/saved/{script_id}")
async def delete_saved_script(script_id: str):
    result = await db.saved_scripts.delete_one({"id": script_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Not found")
    return {"message": "Deleted"}

@api_router.post("/emergency/notes", response_model=EmergencyNote)
async def create_emergency_note(input: EmergencyNoteCreate):
    note = EmergencyNote(**input.dict())
    await db.emergency_notes.insert_one(note.dict())
    return note

@api_router.get("/emergency/notes/{device_id}")
async def get_emergency_notes(device_id: str):
    notes = await db.emergency_notes.find({"device_id": device_id}).sort("created_at", -1).to_list(100)
    return [EmergencyNote(**n) for n in notes]

@api_router.post("/sms/send")
async def send_sms(request: SMSRequest):
    logging.info(f"[MOCKED SMS] To: {request.to_phone}")
    return {"success": True, "mocked": True}

@api_router.post("/chat")
async def chat_with_ai(request: ChatRequest):
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="AI not configured")
    await db.chat_messages.insert_one(ChatMessage(device_id=request.device_id, session_id=request.session_id, role="user", content=request.message).dict())
    history = await db.chat_messages.find({"device_id": request.device_id, "session_id": request.session_id}).sort("timestamp", 1).to_list(20)
    state_ctx = f" User is in {request.user_state}." if request.user_state else " State unknown - give general US guidance."
    system = f"""You help teens understand their rights. Keep it SHORT and REAL - no corporate speak. 2-3 paragraphs MAX. Talk like a helpful older friend. NEVER say you're a lawyer. Always say 'get real legal help for serious stuff.'{state_ctx} Topics: school, work, housing, cops, online, public, immigration, consumer rights. This is info, not legal advice."""
    try:
        chat = LlmChat(api_key=EMERGENT_LLM_KEY, session_id=f"kyr-{request.session_id}", system_message=system).with_model("anthropic", "claude-sonnet-4-5-20250929")
        context = "\n".join([f"{'User' if m['role']=='user' else 'You'}: {m['content']}" for m in history[-10:]])
        response = await chat.send_message(UserMessage(text=f"Chat:\n{context}\n\nNew: {request.message}"))
        await db.chat_messages.insert_one(ChatMessage(device_id=request.device_id, session_id=request.session_id, role="assistant", content=response).dict())
        return {"response": response, "session_id": request.session_id}
    except Exception as e:
        logging.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="AI failed")

@api_router.get("/chat/history/{device_id}/{session_id}")
async def get_chat_history(device_id: str, session_id: str):
    messages = await db.chat_messages.find({"device_id": device_id, "session_id": session_id}).sort("timestamp", 1).to_list(100)
    return [ChatMessage(**m) for m in messages]

@api_router.delete("/chat/history/{device_id}")
async def clear_chat_history(device_id: str):
    await db.chat_messages.delete_many({"device_id": device_id})
    return {"message": "Cleared"}

app.include_router(api_router)
app.add_middleware(CORSMiddleware, allow_credentials=True, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
logging.basicConfig(level=logging.INFO)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
