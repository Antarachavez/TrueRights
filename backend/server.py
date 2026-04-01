from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Emergent LLM Key
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')

# Create the main app
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ========================
# MODELS
# ========================

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
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ChatRequest(BaseModel):
    device_id: str
    session_id: str
    message: str
    user_state: Optional[str] = None

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

# ========================
# SAMPLE DATA
# ========================

CATEGORIES = [
    {
        "id": "school",
        "name": "School",
        "icon": "school",
        "color": "#3B82F6",
        "description": "Know your rights at school"
    },
    {
        "id": "work",
        "name": "Work",
        "icon": "briefcase",
        "color": "#F97316",
        "description": "Workplace rights and protections"
    },
    {
        "id": "housing",
        "name": "Housing",
        "icon": "home",
        "color": "#10B981",
        "description": "Tenant and renter rights"
    },
    {
        "id": "police",
        "name": "Police Interaction",
        "icon": "shield",
        "color": "#EF4444",
        "description": "Know your rights with law enforcement"
    },
    {
        "id": "online",
        "name": "Online Privacy",
        "icon": "lock",
        "color": "#8B5CF6",
        "description": "Digital privacy and safety"
    },
    {
        "id": "public",
        "name": "Public Spaces",
        "icon": "map-pin",
        "color": "#14B8A6",
        "description": "Rights in public areas"
    }
]

SCENARIOS = {
    "school": [
        {
            "id": "school-phone-search",
            "category": "school",
            "question": "Can my school search my phone?",
            "short_answer": "Usually, they need reasonable suspicion. You can politely decline.",
            "explanation": "Schools have some authority to search students, but they generally need 'reasonable suspicion' that you've broken a rule. Random searches of phones are often not allowed. Private schools may have different rules based on their policies.",
            "script": "I'd like to speak with my parent/guardian before allowing a search of my personal device.",
            "next_steps": [
                "Stay calm and be respectful",
                "Ask why they want to search your phone",
                "Request to call a parent or guardian",
                "Document what happened afterward"
            ]
        },
        {
            "id": "school-locker-search",
            "question": "Can my school search my locker?",
            "category": "school",
            "short_answer": "Usually yes. School lockers are typically school property.",
            "explanation": "Most schools consider lockers to be school property, so they can often search them without your permission. However, they usually still need some reason to suspect a rule violation.",
            "script": "I understand you need to check. May I ask what prompted this search?",
            "next_steps": [
                "Cooperate calmly",
                "Remember you can ask questions respectfully",
                "Note any witnesses present",
                "Talk to a parent afterward"
            ]
        },
        {
            "id": "school-speech",
            "question": "Can I express my opinions at school?",
            "category": "school",
            "short_answer": "Yes, but with some limits on disruption.",
            "explanation": "Students have First Amendment rights, but schools can limit speech that substantially disrupts learning or violates others' rights. Peaceful, non-disruptive expression is generally protected.",
            "script": "I believe I have the right to express my views peacefully. Can we discuss what's acceptable?",
            "next_steps": [
                "Choose appropriate times and places",
                "Keep expression peaceful and respectful",
                "Know your school's specific policies",
                "Consider talking to a counselor if you feel your rights are violated"
            ]
        }
    ],
    "work": [
        {
            "id": "work-unpaid-time",
            "question": "Can my boss make me work unpaid extra time?",
            "category": "work",
            "short_answer": "No. If you're hourly (non-exempt), you must be paid for all time worked.",
            "explanation": "Under federal law (FLSA), hourly workers must be paid for all hours worked, including overtime. 'Off the clock' work is illegal. Salaried exempt employees have different rules.",
            "script": "I want to make sure I'm logging all my work hours correctly. Can you help me understand the policy?",
            "next_steps": [
                "Keep records of your hours worked",
                "Ask for written policies about overtime",
                "Contact your state labor department if unpaid work continues",
                "Consider speaking with HR"
            ]
        },
        {
            "id": "work-breaks",
            "question": "Am I entitled to breaks at work?",
            "category": "work",
            "short_answer": "It depends on your state. Many states require breaks for shifts over a certain length.",
            "explanation": "Federal law doesn't require breaks, but many states do. If you're a minor, you usually have stronger break protections. Check your state's specific labor laws.",
            "script": "I'd like to understand my break schedule. What does our policy say about rest and meal breaks?",
            "next_steps": [
                "Look up your state's break laws",
                "Ask HR or your manager about break policies",
                "Document if breaks are denied",
                "Contact your state labor board if needed"
            ]
        },
        {
            "id": "work-discrimination",
            "question": "What if I'm treated unfairly because of who I am?",
            "category": "work",
            "short_answer": "Discrimination based on protected characteristics is illegal.",
            "explanation": "Federal and state laws protect against discrimination based on race, color, religion, sex, national origin, age, disability, and more. Some states also protect LGBTQ+ workers.",
            "script": "I'm concerned about how I'm being treated. Can you tell me how to file a formal concern or complaint?",
            "next_steps": [
                "Document specific incidents with dates and witnesses",
                "Report to HR or a supervisor",
                "File a complaint with the EEOC if needed",
                "Seek legal advice for serious situations"
            ]
        }
    ],
    "housing": [
        {
            "id": "housing-entry",
            "question": "Can my landlord enter without notice?",
            "category": "housing",
            "short_answer": "Usually no. Most states require 24-48 hours notice except for emergencies.",
            "explanation": "Tenants have a right to 'quiet enjoyment' of their home. Landlords typically must give advance notice (often 24-48 hours) before entering, except in true emergencies like flooding or fire.",
            "script": "I'd appreciate advance notice before any entry as required by law. Can we agree on how that will work?",
            "next_steps": [
                "Check your lease for entry provisions",
                "Look up your state's notice requirements",
                "Document any unauthorized entries",
                "Send a written request for proper notice"
            ]
        },
        {
            "id": "housing-repairs",
            "question": "What if my landlord won't fix things?",
            "category": "housing",
            "short_answer": "You have a right to a habitable home. There are legal remedies.",
            "explanation": "Landlords must maintain 'habitability' - working plumbing, heat, electricity, and safety features. If they don't, you may have options like rent withholding or repair-and-deduct, depending on your state.",
            "script": "I've reported this issue on [date]. Can you provide a timeline for repairs? I'd like this in writing.",
            "next_steps": [
                "Put repair requests in writing",
                "Document problems with photos and dates",
                "Check local tenant rights organizations",
                "Contact housing code enforcement if needed"
            ]
        },
        {
            "id": "housing-eviction",
            "question": "Can I be kicked out immediately?",
            "category": "housing",
            "short_answer": "No. Eviction requires a legal process with notice and court involvement.",
            "explanation": "Landlords cannot force you out without going through legal eviction proceedings. This includes proper notice periods and often a court hearing where you can present your side.",
            "script": "I'd like to understand the formal process. Can I receive any notices in writing?",
            "next_steps": [
                "Don't leave just because asked verbally",
                "Know your state's eviction notice requirements",
                "Respond to any court summons",
                "Seek help from legal aid immediately"
            ]
        }
    ],
    "police": [
        {
            "id": "police-stop",
            "question": "What should I do if stopped by police?",
            "category": "police",
            "short_answer": "Stay calm, keep hands visible, and know you have rights.",
            "explanation": "You have the right to remain silent and the right to refuse searches. However, staying calm and being polite helps keep everyone safe. You must provide ID if asked in most states.",
            "script": "I want to be respectful, officer. Am I free to go, or am I being detained?",
            "next_steps": [
                "Stay calm and keep hands visible",
                "You can ask if you're free to leave",
                "You can decline to answer questions beyond ID",
                "Document everything afterward"
            ]
        },
        {
            "id": "police-search",
            "question": "Can police search me or my car?",
            "category": "police",
            "short_answer": "You can refuse consent. They need probable cause or a warrant for most searches.",
            "explanation": "Police generally need your consent, probable cause, or a warrant to search. You can clearly but politely say you don't consent. This doesn't guarantee they won't search, but it preserves your rights.",
            "script": "I do not consent to a search. Am I free to go?",
            "next_steps": [
                "Clearly state you don't consent",
                "Don't physically resist if they proceed",
                "Remember what happens for later",
                "Contact a lawyer if your rights were violated"
            ]
        },
        {
            "id": "police-questions",
            "question": "Do I have to answer police questions?",
            "category": "police",
            "short_answer": "You have the right to remain silent, except for identifying yourself.",
            "explanation": "The Fifth Amendment protects your right to remain silent. You typically must provide your name if asked, but you don't have to answer other questions without a lawyer present.",
            "script": "I'm choosing to remain silent. I'd like to speak with a lawyer before answering questions.",
            "next_steps": [
                "Clearly invoke your right to silence",
                "Ask for a lawyer if detained",
                "Stay calm and don't argue",
                "Document everything later"
            ]
        }
    ],
    "online": [
        {
            "id": "online-data",
            "question": "Can companies collect my data without asking?",
            "category": "online",
            "short_answer": "They usually disclose it in privacy policies. Some states give you more control.",
            "explanation": "Companies typically can collect data if disclosed in their privacy policy. However, some states like California give you rights to know what's collected and request deletion.",
            "script": "Can you tell me what data you collect about me and how I can request its deletion?",
            "next_steps": [
                "Read privacy policies (especially data sections)",
                "Check your state's privacy laws",
                "Use privacy settings in apps",
                "Consider data minimization practices"
            ]
        },
        {
            "id": "online-harassment",
            "question": "What can I do about online harassment?",
            "category": "online",
            "short_answer": "Document everything, report to platforms, and contact authorities if threats are made.",
            "explanation": "Online harassment can violate platform rules and sometimes laws. Serious threats may be criminal. Document everything, use platform reporting tools, and involve authorities for credible threats.",
            "script": "I need to report harassment. Can you direct me to your platform's safety team?",
            "next_steps": [
                "Screenshot and save all evidence",
                "Use platform reporting features",
                "Block the harasser",
                "Contact police for credible threats"
            ]
        },
        {
            "id": "online-images",
            "question": "Someone shared my photos without permission. What can I do?",
            "category": "online",
            "short_answer": "This may violate laws, especially for intimate images. Report and seek help.",
            "explanation": "Non-consensual sharing of intimate images is illegal in many states. Even non-intimate images may violate terms of service. Platforms have removal processes, and legal remedies may exist.",
            "script": "I need to report an image that was shared without my consent. This is urgent.",
            "next_steps": [
                "Document the post before it's removed",
                "Report through platform safety features",
                "Check if revenge porn laws apply in your state",
                "Contact the Cyber Civil Rights Initiative for support"
            ]
        }
    ],
    "public": [
        {
            "id": "public-filming",
            "question": "Can I film in public spaces?",
            "category": "public",
            "short_answer": "Generally yes. Public spaces have no expectation of privacy.",
            "explanation": "In public spaces, you generally have the right to photograph or film. This includes filming police (from a safe distance). Private property rules may differ.",
            "script": "I'm recording from a public space where there's no expectation of privacy.",
            "next_steps": [
                "Stay in clearly public areas",
                "Don't interfere with police or emergency work",
                "Know that private property has different rules",
                "Respect requests in private spaces"
            ]
        },
        {
            "id": "public-protest",
            "question": "What are my rights at a protest?",
            "category": "public",
            "short_answer": "You have First Amendment rights to peaceful protest in public spaces.",
            "explanation": "The Constitution protects peaceful assembly and protest. However, permits may be required for large gatherings, and blocking traffic or private property may lead to issues.",
            "script": "I'm exercising my First Amendment right to peaceful assembly.",
            "next_steps": [
                "Know the local permit requirements",
                "Stay on public property",
                "Keep the protest peaceful",
                "Know your exit routes"
            ]
        },
        {
            "id": "public-store",
            "question": "Can a store detain me if they think I shoplifted?",
            "category": "public",
            "short_answer": "In most states, yes, briefly, if they have reasonable grounds.",
            "explanation": "Many states have 'shopkeeper's privilege' laws allowing brief detention if there's reasonable belief of theft. However, the detention must be reasonable in length and manner.",
            "script": "I haven't taken anything. If you believe I have, please call the police so we can resolve this properly.",
            "next_steps": [
                "Stay calm and don't run",
                "Ask to see a manager",
                "Request police if the situation escalates",
                "Get contact info for witnesses"
            ]
        }
    ]
}

DEFAULT_SCRIPTS = [
    {
        "id": "script-no-search",
        "title": "Declining a Search",
        "content": "I do not consent to a search.",
        "category": "general"
    },
    {
        "id": "script-policy-writing",
        "title": "Request Policy in Writing",
        "content": "Can you please explain the policy in writing?",
        "category": "general"
    },
    {
        "id": "script-contact-support",
        "title": "Request Support",
        "content": "I would like to contact a parent, guardian, or lawyer.",
        "category": "general"
    },
    {
        "id": "script-uncomfortable",
        "title": "Decline to Answer",
        "content": "I am not comfortable answering that without support.",
        "category": "general"
    },
    {
        "id": "script-free-to-go",
        "title": "Ask if Detained",
        "content": "Am I free to go, or am I being detained?",
        "category": "police"
    },
    {
        "id": "script-remain-silent",
        "title": "Invoke Right to Silence",
        "content": "I am exercising my right to remain silent. I would like a lawyer.",
        "category": "police"
    }
]

RESOURCES = [
    {
        "category": "Emergency Hotlines",
        "items": [
            {"name": "National Emergency", "contact": "911", "description": "For immediate emergencies"},
            {"name": "Crisis Text Line", "contact": "Text HOME to 741741", "description": "Free 24/7 crisis support via text"},
            {"name": "National Suicide Prevention", "contact": "988", "description": "24/7 mental health crisis support"}
        ]
    },
    {
        "category": "Legal Aid",
        "items": [
            {"name": "Legal Services Corporation", "contact": "lsc.gov", "description": "Find free legal aid in your area"},
            {"name": "ACLU", "contact": "aclu.org", "description": "Civil liberties information and help"},
            {"name": "LawHelp.org", "contact": "lawhelp.org", "description": "Free legal help by state"}
        ]
    },
    {
        "category": "Youth Support",
        "items": [
            {"name": "Boys Town Hotline", "contact": "1-800-448-3000", "description": "24/7 help for teens and parents"},
            {"name": "Teen Line", "contact": "1-800-852-8336", "description": "Teens helping teens"},
            {"name": "The Trevor Project", "contact": "1-866-488-7386", "description": "LGBTQ+ youth crisis support"}
        ]
    },
    {
        "category": "Worker Rights",
        "items": [
            {"name": "Department of Labor", "contact": "dol.gov", "description": "Federal workplace rights info"},
            {"name": "OSHA", "contact": "1-800-321-OSHA", "description": "Workplace safety concerns"},
            {"name": "EEOC", "contact": "eeoc.gov", "description": "Employment discrimination help"}
        ]
    },
    {
        "category": "Housing Help",
        "items": [
            {"name": "HUD", "contact": "hud.gov", "description": "Housing rights and assistance"},
            {"name": "National Housing Law Project", "contact": "nhlp.org", "description": "Tenant rights resources"},
            {"name": "Local Tenant Unions", "contact": "Search online", "description": "Community housing support"}
        ]
    }
]

US_STATES = [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut",
    "Delaware", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa",
    "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan",
    "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire",
    "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio",
    "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
    "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia",
    "Wisconsin", "Wyoming", "District of Columbia"
]

# ========================
# ROUTES
# ========================

@api_router.get("/")
async def root():
    return {"message": "Know Your Rights API", "version": "1.0.0"}

# Categories
@api_router.get("/categories")
async def get_categories():
    return CATEGORIES

# Scenarios
@api_router.get("/scenarios/{category_id}")
async def get_scenarios_by_category(category_id: str):
    if category_id not in SCENARIOS:
        raise HTTPException(status_code=404, detail="Category not found")
    return SCENARIOS[category_id]

@api_router.get("/scenario/{scenario_id}")
async def get_scenario_detail(scenario_id: str):
    for category_scenarios in SCENARIOS.values():
        for scenario in category_scenarios:
            if scenario["id"] == scenario_id:
                return scenario
    raise HTTPException(status_code=404, detail="Scenario not found")

# Default Scripts
@api_router.get("/scripts/default")
async def get_default_scripts():
    return DEFAULT_SCRIPTS

# Resources
@api_router.get("/resources")
async def get_resources():
    return RESOURCES

# States
@api_router.get("/states")
async def get_states():
    return US_STATES

# User Preferences
@api_router.post("/preferences", response_model=UserPreferences)
async def create_or_update_preferences(input: UserPreferencesCreate):
    existing = await db.preferences.find_one({"device_id": input.device_id})
    
    if existing:
        update_data = {**input.dict(), "updated_at": datetime.utcnow()}
        await db.preferences.update_one(
            {"device_id": input.device_id},
            {"$set": update_data}
        )
        updated = await db.preferences.find_one({"device_id": input.device_id})
        return UserPreferences(**updated)
    else:
        prefs = UserPreferences(**input.dict())
        await db.preferences.insert_one(prefs.dict())
        return prefs

@api_router.get("/preferences/{device_id}")
async def get_preferences(device_id: str):
    prefs = await db.preferences.find_one({"device_id": device_id})
    if prefs:
        return UserPreferences(**prefs)
    return None

# Saved Scripts
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
        raise HTTPException(status_code=404, detail="Script not found")
    return {"message": "Script deleted"}

# Emergency Notes
@api_router.post("/emergency/notes", response_model=EmergencyNote)
async def create_emergency_note(input: EmergencyNoteCreate):
    note = EmergencyNote(**input.dict())
    await db.emergency_notes.insert_one(note.dict())
    return note

@api_router.get("/emergency/notes/{device_id}")
async def get_emergency_notes(device_id: str):
    notes = await db.emergency_notes.find({"device_id": device_id}).sort("created_at", -1).to_list(100)
    return [EmergencyNote(**n) for n in notes]

# SMS (MOCKED)
@api_router.post("/sms/send")
async def send_sms(request: SMSRequest):
    """MOCKED SMS endpoint - in production, integrate Twilio"""
    logging.info(f"[MOCKED SMS] To: {request.to_phone}, From: {request.from_name}, Message: {request.message}")
    return {
        "success": True,
        "mocked": True,
        "message": "SMS would be sent in production",
        "details": {
            "to": request.to_phone,
            "from_name": request.from_name,
            "body": request.message
        }
    }

# AI Chat
@api_router.post("/chat")
async def chat_with_ai(request: ChatRequest):
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="AI service not configured")
    
    # Save user message
    user_msg = ChatMessage(
        device_id=request.device_id,
        session_id=request.session_id,
        role="user",
        content=request.message
    )
    await db.chat_messages.insert_one(user_msg.dict())
    
    # Get chat history for context
    history = await db.chat_messages.find({
        "device_id": request.device_id,
        "session_id": request.session_id
    }).sort("timestamp", 1).to_list(20)
    
    state_context = f" The user is in {request.user_state}." if request.user_state else " The user's state is unknown, so provide general U.S. guidance and mention that laws vary by state."
    
    system_message = f"""You are a helpful rights education assistant for the "Know Your Rights" app. Your purpose is to help teens and young adults understand their basic rights in everyday situations.

IMPORTANT RULES:
1. Keep answers SHORT and CLEAR - 2-3 paragraphs maximum
2. Use PLAIN language that a teenager would understand
3. NEVER pretend to be a lawyer or give official legal advice
4. Always encourage seeking qualified help for serious legal issues
5. Focus on educational guidance, practical scripts, and next steps
6. If the question is unclear, ask what situation or setting applies
7. Always remind users that this is educational information, not legal advice
8. Be supportive and non-judgmental
9. If a question isn't about rights, politely redirect to rights-related topics

{state_context}

Common topics you help with:
- School rights (searches, speech, privacy)
- Work rights (pay, breaks, discrimination)
- Housing rights (tenant protections, landlord rules)
- Police interactions (searches, silence, detention)
- Online privacy (data, harassment)
- Public spaces (filming, protests)

Remember: You're helping people who may be stressed or scared. Be calm, clear, and helpful."""

    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"kyr-{request.session_id}",
            system_message=system_message
        ).with_model("anthropic", "claude-sonnet-4-5-20250929")
        
        # Build context from history
        context = ""
        for msg in history[-10:]:  # Last 10 messages
            role = "User" if msg["role"] == "user" else "Assistant"
            context += f"{role}: {msg['content']}\n"
        
        full_message = f"Previous conversation:\n{context}\n\nUser's new question: {request.message}"
        
        user_message = UserMessage(text=full_message)
        response = await chat.send_message(user_message)
        
        # Save assistant response
        assistant_msg = ChatMessage(
            device_id=request.device_id,
            session_id=request.session_id,
            role="assistant",
            content=response
        )
        await db.chat_messages.insert_one(assistant_msg.dict())
        
        return {"response": response, "session_id": request.session_id}
        
    except Exception as e:
        logging.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get AI response")

@api_router.get("/chat/history/{device_id}/{session_id}")
async def get_chat_history(device_id: str, session_id: str):
    messages = await db.chat_messages.find({
        "device_id": device_id,
        "session_id": session_id
    }).sort("timestamp", 1).to_list(100)
    return [ChatMessage(**m) for m in messages]

@api_router.delete("/chat/history/{device_id}")
async def clear_chat_history(device_id: str):
    await db.chat_messages.delete_many({"device_id": device_id})
    return {"message": "Chat history cleared"}

# Include the router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
