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

# CATEGORIES - Now with 8 main categories
CATEGORIES = [
    {"id": "school", "name": "School", "icon": "school", "color": "#7DD3FC", "description": "Know your rights at school",
     "subcategories": [
         {"id": "searches", "name": "Searches & Privacy", "icon": "search", "color": "#3B82F6"},
         {"id": "discipline", "name": "Discipline & Suspension", "icon": "warning", "color": "#EF4444"},
         {"id": "attendance", "name": "Attendance", "icon": "time", "color": "#F59E0B"},
         {"id": "expression", "name": "Free Speech", "icon": "megaphone", "color": "#8B5CF6"},
         {"id": "administration", "name": "Teachers & Admin", "icon": "people", "color": "#10B981"},
         {"id": "personal", "name": "Personal Items", "icon": "shirt", "color": "#EC4899"},
         {"id": "grades", "name": "Grades & Testing", "icon": "document-text", "color": "#14B8A6"},
         {"id": "sports", "name": "Sports & Activities", "icon": "football", "color": "#F97316"},
         {"id": "special-ed", "name": "Special Education", "icon": "accessibility", "color": "#6366F1"},
         {"id": "safety", "name": "Safety & Health", "icon": "medkit", "color": "#DC2626"},
         {"id": "technology", "name": "Technology", "icon": "laptop", "color": "#0EA5E9"}
     ]},
    {"id": "work", "name": "Work", "icon": "briefcase", "color": "#FCA5A5", "description": "Workplace rights",
     "subcategories": [
         {"id": "pay", "name": "Pay & Wages", "icon": "cash", "color": "#10B981"},
         {"id": "hours", "name": "Hours & Breaks", "icon": "time", "color": "#F97316"},
         {"id": "safety", "name": "Safety", "icon": "shield-checkmark", "color": "#EF4444"},
         {"id": "harassment", "name": "Harassment", "icon": "alert-circle", "color": "#DC2626"},
         {"id": "firing", "name": "Firing & Quitting", "icon": "exit", "color": "#6B7280"},
         {"id": "privacy", "name": "Privacy", "icon": "eye-off", "color": "#8B5CF6"},
         {"id": "minors", "name": "Teen Workers", "icon": "person", "color": "#3B82F6"},
         {"id": "scheduling", "name": "Scheduling", "icon": "calendar", "color": "#14B8A6"},
         {"id": "tips", "name": "Tips & Commission", "icon": "wallet", "color": "#F59E0B"},
         {"id": "contracts", "name": "Contracts", "icon": "document-text", "color": "#6366F1"},
         {"id": "discrimination", "name": "Discrimination", "icon": "ban", "color": "#EC4899"}
     ]},
    {"id": "housing", "name": "Housing", "icon": "home", "color": "#86EFAC", "description": "Tenant rights",
     "subcategories": [
         {"id": "entry", "name": "Landlord Entry", "icon": "key", "color": "#F97316"},
         {"id": "repairs", "name": "Repairs", "icon": "construct", "color": "#3B82F6"},
         {"id": "eviction", "name": "Eviction", "icon": "log-out", "color": "#EF4444"},
         {"id": "deposits", "name": "Deposits", "icon": "cash", "color": "#10B981"},
         {"id": "lease", "name": "Lease & Rent", "icon": "document-text", "color": "#8B5CF6"},
         {"id": "roommates", "name": "Roommates", "icon": "people", "color": "#EC4899"},
         {"id": "utilities", "name": "Utilities", "icon": "flash", "color": "#F59E0B"},
         {"id": "pets", "name": "Pets", "icon": "paw", "color": "#14B8A6"},
         {"id": "noise", "name": "Noise & Neighbors", "icon": "volume-high", "color": "#6366F1"},
         {"id": "discrimination", "name": "Discrimination", "icon": "ban", "color": "#DC2626"},
         {"id": "moving", "name": "Moving Out", "icon": "car", "color": "#0EA5E9"}
     ]},
    {"id": "police", "name": "Police", "icon": "shield", "color": "#FDA4AF", "description": "Police interactions",
     "subcategories": [
         {"id": "stops", "name": "Being Stopped", "icon": "hand-left", "color": "#F97316"},
         {"id": "searches", "name": "Searches", "icon": "search", "color": "#EF4444"},
         {"id": "arrests", "name": "Arrests", "icon": "lock-closed", "color": "#DC2626"},
         {"id": "rights", "name": "Your Rights", "icon": "shield-checkmark", "color": "#3B82F6"},
         {"id": "recording", "name": "Recording", "icon": "videocam", "color": "#8B5CF6"},
         {"id": "complaints", "name": "Complaints", "icon": "document-text", "color": "#6B7280"},
         {"id": "minors", "name": "Minors & Police", "icon": "person", "color": "#10B981"},
         {"id": "traffic", "name": "Traffic Stops", "icon": "car", "color": "#F59E0B"},
         {"id": "home", "name": "Police at Home", "icon": "home", "color": "#14B8A6"},
         {"id": "witnesses", "name": "Being a Witness", "icon": "eye", "color": "#6366F1"},
         {"id": "after", "name": "After Arrest", "icon": "time", "color": "#EC4899"}
     ]},
    {"id": "online", "name": "Online", "icon": "lock", "color": "#C4B5FD", "description": "Digital safety",
     "subcategories": [
         {"id": "social", "name": "Social Media", "icon": "share-social", "color": "#3B82F6"},
         {"id": "data", "name": "Data & Tracking", "icon": "analytics", "color": "#10B981"},
         {"id": "harassment", "name": "Harassment", "icon": "alert-circle", "color": "#EF4444"},
         {"id": "photos", "name": "Photos & Images", "icon": "images", "color": "#EC4899"},
         {"id": "accounts", "name": "Accounts", "icon": "key", "color": "#F97316"},
         {"id": "school-monitoring", "name": "School Devices", "icon": "eye", "color": "#6B7280"},
         {"id": "scams", "name": "Scams & Fraud", "icon": "warning", "color": "#DC2626"},
         {"id": "gaming", "name": "Gaming", "icon": "game-controller", "color": "#8B5CF6"},
         {"id": "shopping", "name": "Online Shopping", "icon": "cart", "color": "#14B8A6"},
         {"id": "copyright", "name": "Copyright", "icon": "document", "color": "#6366F1"},
         {"id": "ai", "name": "AI & Deepfakes", "icon": "hardware-chip", "color": "#0EA5E9"}
     ]},
    {"id": "public", "name": "Public Spaces", "icon": "map-pin", "color": "#6EE7B7", "description": "Public rights",
     "subcategories": [
         {"id": "filming", "name": "Filming", "icon": "camera", "color": "#3B82F6"},
         {"id": "protests", "name": "Protests", "icon": "megaphone", "color": "#EF4444"},
         {"id": "stores", "name": "Stores", "icon": "storefront", "color": "#F97316"},
         {"id": "transport", "name": "Transportation", "icon": "bus", "color": "#10B981"},
         {"id": "parks", "name": "Parks", "icon": "leaf", "color": "#14B8A6"},
         {"id": "curfew", "name": "Curfews", "icon": "moon", "color": "#8B5CF6"},
         {"id": "malls", "name": "Malls & Shopping", "icon": "bag", "color": "#EC4899"},
         {"id": "events", "name": "Events & Concerts", "icon": "musical-notes", "color": "#6366F1"},
         {"id": "restaurants", "name": "Restaurants", "icon": "restaurant", "color": "#F59E0B"},
         {"id": "id", "name": "ID Requirements", "icon": "card", "color": "#DC2626"},
         {"id": "banned", "name": "Being Banned", "icon": "ban", "color": "#6B7280"}
     ]},
    {"id": "immigration", "name": "Immigration", "icon": "globe", "color": "#67E8F9", "description": "Immigration rights",
     "subcategories": [
         {"id": "documents", "name": "Documents", "icon": "document-text", "color": "#3B82F6"},
         {"id": "police", "name": "Police & ICE", "icon": "shield", "color": "#EF4444"},
         {"id": "work", "name": "Work Rights", "icon": "briefcase", "color": "#F97316"},
         {"id": "school", "name": "School Rights", "icon": "school", "color": "#10B981"},
         {"id": "travel", "name": "Travel", "icon": "airplane", "color": "#8B5CF6"},
         {"id": "healthcare", "name": "Healthcare", "icon": "medkit", "color": "#EC4899"},
         {"id": "housing", "name": "Housing", "icon": "home", "color": "#14B8A6"},
         {"id": "detention", "name": "Detention", "icon": "lock-closed", "color": "#DC2626"},
         {"id": "family", "name": "Family", "icon": "people", "color": "#6366F1"},
         {"id": "daca", "name": "DACA", "icon": "ribbon", "color": "#F59E0B"},
         {"id": "raids", "name": "Raids & Checkpoints", "icon": "warning", "color": "#6B7280"}
     ]},
    {"id": "consumer", "name": "Customer Service", "icon": "cart", "color": "#FDBA74", "description": "Consumer rights",
     "subcategories": [
         {"id": "returns", "name": "Returns & Refunds", "icon": "refresh", "color": "#10B981"},
         {"id": "warranties", "name": "Warranties", "icon": "shield-checkmark", "color": "#3B82F6"},
         {"id": "scams", "name": "Scams", "icon": "warning", "color": "#EF4444"},
         {"id": "billing", "name": "Billing Disputes", "icon": "card", "color": "#F97316"},
         {"id": "complaints", "name": "Complaints", "icon": "megaphone", "color": "#8B5CF6"},
         {"id": "contracts", "name": "Contracts & Subscriptions", "icon": "document-text", "color": "#6366F1"},
         {"id": "debt", "name": "Debt Collection", "icon": "cash", "color": "#DC2626"},
         {"id": "privacy", "name": "Privacy & Data", "icon": "lock-closed", "color": "#14B8A6"},
         {"id": "discrimination", "name": "Discrimination", "icon": "ban", "color": "#EC4899"},
         {"id": "repairs", "name": "Repairs & Services", "icon": "construct", "color": "#F59E0B"},
         {"id": "online", "name": "Online Purchases", "icon": "globe", "color": "#0EA5E9"}
     ]}
]

# MASSIVE SCENARIOS DATABASE
SCENARIOS = {
    "school": {
        "searches": [
            {"id": "sch-s1", "question": "Can they search my phone?", "short_answer": "They need a real reason to suspect YOU broke a rule. Ask to call your parents first.", "explanation": "Schools can't randomly grab phones. They need specific suspicion about you.", "script": "I'd like to call my parent before any search.", "next_steps": ["Stay calm", "Ask why", "Call parent", "Document it"]},
            {"id": "sch-s2", "question": "Can they search my locker?", "short_answer": "Probably yes. Most schools own lockers.", "explanation": "Lockers are usually school property.", "script": "Can I ask what this is about?", "next_steps": ["Stay calm", "Note witnesses", "Tell parents"]},
            {"id": "sch-s3", "question": "Can they go through my bag?", "short_answer": "Only with specific suspicion about you, not random checks.", "explanation": "Your backpack is your property.", "script": "What rule am I suspected of breaking?", "next_steps": ["Ask why", "Don't resist", "Document"]},
            {"id": "sch-s4", "question": "Can they search my car?", "short_answer": "If parked at school, usually yes - you agreed by parking there.", "explanation": "Check your parking permit.", "script": "Can I see the parking policy?", "next_steps": ["Check permit", "Ask reason"]},
            {"id": "sch-s5", "question": "Can they strip search me?", "short_answer": "Almost NEVER. Refuse and demand parents immediately.", "explanation": "Supreme Court basically banned this.", "script": "No. I want my parents and a lawyer NOW.", "next_steps": ["Say no", "Demand parents", "Report"]},
            {"id": "sch-s6", "question": "Can a teacher read my texts?", "short_answer": "Not without good reason. Your phone is private.", "explanation": "Teachers need actual suspicion.", "script": "I don't consent. Can I call my parent?", "next_steps": ["Don't unlock", "Ask for parent"]},
            {"id": "sch-s7", "question": "Can they make me empty my pockets?", "short_answer": "They need reasonable suspicion first.", "explanation": "Can't just randomly search everyone.", "script": "What's the reason for this?", "next_steps": ["Ask why", "Stay calm"]},
            {"id": "sch-s8", "question": "Can they use metal detectors?", "short_answer": "Yes, if everyone goes through them. Random selection is trickier.", "explanation": "General screening is usually okay.", "script": "Is everyone being screened?", "next_steps": ["Comply if general", "Ask if targeted"]}
        ],
        "discipline": [
            {"id": "sch-d1", "question": "I'm getting suspended. What now?", "short_answer": "You have the right to know charges and tell your side.", "explanation": "Short suspensions need basic due process.", "script": "What exactly am I accused of?", "next_steps": ["Ask specifics", "Tell your side", "Get it in writing"]},
            {"id": "sch-d2", "question": "Can they expel me?", "short_answer": "Only after a formal hearing where you can defend yourself.", "explanation": "Expulsion is serious - you get a real hearing.", "script": "I want a formal hearing.", "next_steps": ["Request hearing", "Bring witnesses", "Get lawyer"]},
            {"id": "sch-d3", "question": "Do I have to stay for detention?", "short_answer": "Usually yes, but parents should be notified.", "explanation": "Schools can give detention.", "script": "Can you notify my parents?", "next_steps": ["Confirm parents know", "Serve it"]},
            {"id": "sch-d4", "question": "Others got lighter punishment. Fair?", "short_answer": "Should be consistent. If it's about race/gender, that's discrimination.", "explanation": "Can't punish you harder because of who you are.", "script": "Others got different consequences. Can we discuss?", "next_steps": ["Document", "Talk to counselor"]},
            {"id": "sch-d5", "question": "Can I appeal?", "short_answer": "Yes. Most schools have appeals.", "explanation": "Big decisions can be appealed.", "script": "What's the appeals process?", "next_steps": ["Get process", "Meet deadlines"]},
            {"id": "sch-d6", "question": "Zero tolerance - any rights?", "short_answer": "Yes! You still get to explain what happened.", "explanation": "Zero tolerance doesn't mean zero rights.", "script": "Can I explain the circumstances?", "next_steps": ["Explain context", "Involve parents"]},
            {"id": "sch-d7", "question": "They want me to sign something.", "short_answer": "Read it first. Take it home if needed.", "explanation": "Don't sign what you don't understand.", "script": "I want my parents to see this first.", "next_steps": ["Read carefully", "Take home"]},
            {"id": "sch-d8", "question": "Can they call the cops on me?", "short_answer": "For serious stuff, yes. Schools can involve police.", "explanation": "Crimes can involve police.", "script": "I want a lawyer before talking to police.", "next_steps": ["Stay silent", "Get lawyer"]}
        ],
        "attendance": [
            {"id": "sch-a1", "question": "What if I'm late a lot?", "short_answer": "Usually warnings, then detention, then bigger problems.", "explanation": "Tardiness escalates.", "script": "Can we talk about what's causing this?", "next_steps": ["Be honest", "Get help"]},
            {"id": "sch-a2", "question": "What's excused absence?", "short_answer": "Sickness, emergency, religious holiday, mental health (some states).", "explanation": "Need documentation usually.", "script": "What paperwork do you need?", "next_steps": ["Check policy", "Get docs"]},
            {"id": "sch-a3", "question": "Can I leave early?", "short_answer": "Yes with parent permission and signing out.", "explanation": "Schools need to know.", "script": "My parent called. Where do I sign out?", "next_steps": ["Have parent call", "Sign out"]},
            {"id": "sch-a4", "question": "What's truancy?", "short_answer": "Too many unexcused absences. Can lead to court.", "explanation": "It's a legal issue.", "script": "I need help with attendance.", "next_steps": ["Talk to counselor", "Make plan"]},
            {"id": "sch-a5", "question": "Mental health day?", "short_answer": "More states allow this now.", "explanation": "Mental health is real health.", "script": "Can my parent excuse me for health?", "next_steps": ["Check state law", "Get help if ongoing"]},
            {"id": "sch-a6", "question": "Parent won't write note?", "short_answer": "Talk to counselor. There might be bigger issues.", "explanation": "Counselors can help.", "script": "I need help with my situation.", "next_steps": ["Talk to counselor"]}
        ],
        "expression": [
            {"id": "sch-e1", "question": "Do I have free speech?", "short_answer": "Yes, but limited. Can't disrupt learning.", "explanation": "Students have rights but with limits.", "script": "Is this protected speech?", "next_steps": ["Keep peaceful", "Know limits"]},
            {"id": "sch-e2", "question": "Can I protest?", "short_answer": "You can express views but might get marked absent.", "explanation": "Walkouts are protected but have consequences.", "script": "What are the rules for demonstrations?", "next_steps": ["Know consequences", "Stay peaceful"]},
            {"id": "sch-e3", "question": "Trouble for social media?", "short_answer": "Off-campus posts mostly protected now. Threats = trouble.", "explanation": "2021 Supreme Court ruling helps.", "script": "This was off-campus. Why punishment?", "next_steps": ["Know the law", "Document"]},
            {"id": "sch-e4", "question": "Political clothing?", "short_answer": "Usually yes unless vulgar or causing disruption.", "explanation": "Political messages are generally protected.", "script": "What rule does my shirt break?", "next_steps": ["Know dress code"]},
            {"id": "sch-e5", "question": "Practice religion at school?", "short_answer": "YES. You can pray and wear religious items.", "explanation": "Students can practice their faith.", "script": "This is my personal religious practice.", "next_steps": ["Know rights", "Report discrimination"]},
            {"id": "sch-e6", "question": "Can I start a controversial club?", "short_answer": "If other clubs exist, yours should be treated equally.", "explanation": "Can't discriminate by viewpoint.", "script": "Why is our club different?", "next_steps": ["Document unequal treatment"]}
        ],
        "administration": [
            {"id": "sch-ad1", "question": "Fight unfair grade?",  "short_answer": "Yes. Teacher → department → admin.", "explanation": "There's a process.", "script": "Can we discuss this grade?", "next_steps": ["Talk to teacher", "Bring evidence"]},
            {"id": "sch-ad2", "question": "Teacher treats me unfairly?", "short_answer": "Document it. Talk to counselor.", "explanation": "Teachers should be fair.", "script": "I'm having issues. Can I talk to someone?", "next_steps": ["Document", "Talk to counselor"]},
            {"id": "sch-ad3", "question": "Report bullying?", "short_answer": "Tell trusted adult. Schools must investigate.", "explanation": "Schools are required to address bullying.", "script": "I need to report bullying.", "next_steps": ["Document", "Report", "Follow up"]},
            {"id": "sch-ad4", "question": "IEP/504 not being followed?", "short_answer": "They MUST follow it. It's law.", "explanation": "These are legal documents.", "script": "My IEP requires this. It's not provided.", "next_steps": ["Know your plan", "Request meeting"]},
            {"id": "sch-ad5", "question": "See school counselor?", "short_answer": "Yes. Urgent issues should be seen quickly.", "explanation": "Counselors are there to help.", "script": "I need to talk to someone.", "next_steps": ["Ask to see them"]}
        ],
        "personal": [
            {"id": "sch-p1", "question": "Take my phone all day?", "short_answer": "Many schools do this. Check handbook.", "explanation": "Schools can restrict phones.", "script": "When do I get it back?", "next_steps": ["Know policy"]},
            {"id": "sch-p2", "question": "Dress code fair?", "short_answer": "Can't discriminate by gender, race, religion.", "explanation": "Must be applied equally.", "script": "Is this applied to everyone equally?", "next_steps": ["Document unequal enforcement"]},
            {"id": "sch-p3", "question": "Carry medication?", "short_answer": "Usually needs paperwork. Emergency meds often allowed.", "explanation": "Most meds go to nurse.", "script": "What forms do I need?", "next_steps": ["Get doctor note"]},
            {"id": "sch-p4", "question": "Hair rules?", "short_answer": "Natural hairstyles protected in many states.", "explanation": "CROWN Act protects Black hairstyles.", "script": "This might be discriminatory.", "next_steps": ["Know state laws"]},
            {"id": "sch-p5", "question": "Bathroom access?", "short_answer": "Overly restrictive policies can be challenged.", "explanation": "You have basic needs.", "script": "This is affecting my health.", "next_steps": ["Get medical docs if needed"]},
            {"id": "sch-p6", "question": "LGBTQ+ rights?", "short_answer": "Can be out, form clubs, free from harassment.", "explanation": "Protected from discrimination.", "script": "I want my correct name/pronouns.", "next_steps": ["Know protections", "Report issues"]}
        ],
        "grades": [
            {"id": "sch-g1", "question": "Grade changed without telling me?", "short_answer": "You should be notified of grade changes.", "explanation": "Transparency matters.", "script": "Why was my grade changed?", "next_steps": ["Ask for explanation", "Document"]},
            {"id": "sch-g2", "question": "Failed for attendance?", "short_answer": "Usually allowed but check policy for exceptions.", "explanation": "Many schools have attendance policies.", "script": "Are there exceptions to this policy?", "next_steps": ["Check policy", "Appeal if unfair"]},
            {"id": "sch-g3", "question": "Extra credit refused?", "short_answer": "Teachers don't have to offer it.", "explanation": "Extra credit is optional.", "script": "Are there other ways to improve?", "next_steps": ["Ask about alternatives"]},
            {"id": "sch-g4", "question": "Accused of cheating unfairly?", "short_answer": "You should get to explain before punishment.", "explanation": "Due process applies.", "script": "Can I explain what happened?", "next_steps": ["Defend yourself", "Get evidence"]},
            {"id": "sch-g5", "question": "Test accommodations denied?", "short_answer": "If you have IEP/504, they must provide them.", "explanation": "Legal requirement.", "script": "My plan requires this accommodation.", "next_steps": ["Show documentation", "Request meeting"]}
        ],
        "sports": [
            {"id": "sch-sp1", "question": "Cut from team unfairly?", "short_answer": "Coaches have discretion, but can't discriminate.", "explanation": "Fair tryouts required.", "script": "Can you explain the selection criteria?", "next_steps": ["Ask for criteria", "Document if discriminatory"]},
            {"id": "sch-sp2", "question": "Benched for no reason?", "short_answer": "Coaches decide playing time. Unless it's discrimination.", "explanation": "Playing time isn't guaranteed.", "script": "Can we discuss what I need to improve?", "next_steps": ["Ask for feedback"]},
            {"id": "sch-sp3", "question": "Forced to play injured?", "short_answer": "Never required. Your health comes first.", "explanation": "Safety is priority.", "script": "I'm injured and can't play safely.", "next_steps": ["Get medical note", "Don't risk health"]},
            {"id": "sch-sp4", "question": "Hazing on the team?", "short_answer": "Illegal in most states. Report it.", "explanation": "Hazing is abuse.", "script": "I need to report hazing.", "next_steps": ["Report to admin", "Tell parents"]},
            {"id": "sch-sp5", "question": "Drug testing for sports?", "short_answer": "Schools can require it for athletes.", "explanation": "Athletes have less privacy here.", "script": "What's the testing policy?", "next_steps": ["Know the rules"]}
        ],
        "special-ed": [
            {"id": "sch-se1", "question": "How do I get an IEP?", "short_answer": "Request evaluation in writing. School must respond.", "explanation": "You have the right to be evaluated.", "script": "I'm requesting a special education evaluation.", "next_steps": ["Request in writing", "Keep copies"]},
            {"id": "sch-se2", "question": "School won't evaluate me?", "short_answer": "They must respond to requests. File complaint if ignored.", "explanation": "Legal requirement to respond.", "script": "I requested evaluation on [date]. What's the status?", "next_steps": ["Follow up in writing", "File complaint"]},
            {"id": "sch-se3", "question": "IEP not being followed?", "short_answer": "Document it. Request IEP meeting.", "explanation": "They must follow the plan.", "script": "My IEP says X but I'm not getting it.", "next_steps": ["Document", "Request meeting"]},
            {"id": "sch-se4", "question": "Want different services?", "short_answer": "Request IEP meeting to discuss changes.", "explanation": "You can request changes.", "script": "I'd like to discuss my services.", "next_steps": ["Request meeting", "Bring suggestions"]},
            {"id": "sch-se5", "question": "Graduation requirements different?", "short_answer": "IEP can modify requirements.", "explanation": "Accommodations can apply to graduation.", "script": "What are my graduation options?", "next_steps": ["Discuss at IEP meeting"]}
        ],
        "safety": [
            {"id": "sch-sf1", "question": "Report unsafe conditions?", "short_answer": "Tell admin, parent, or report to district.", "explanation": "Schools must be safe.", "script": "I'm concerned about safety.", "next_steps": ["Report to admin", "Tell parents"]},
            {"id": "sch-sf2", "question": "Can they give me medicine?", "short_answer": "Only with parent permission and proper forms.", "explanation": "Medical consent required.", "script": "I need parent permission for that.", "next_steps": ["Have parents sign forms"]},
            {"id": "sch-sf3", "question": "Someone has a weapon?", "short_answer": "Tell an adult IMMEDIATELY.", "explanation": "Safety first.", "script": "Someone has something dangerous.", "next_steps": ["Tell adult now", "Don't confront them"]},
            {"id": "sch-sf4", "question": "Feeling unsafe at school?", "short_answer": "Tell counselor, parent, or trusted adult.", "explanation": "You deserve to feel safe.", "script": "I don't feel safe.", "next_steps": ["Talk to someone", "Make safety plan"]}
        ],
        "technology": [
            {"id": "sch-t1", "question": "School see everything on school device?", "short_answer": "YES. Everything. Don't expect privacy.", "explanation": "School devices are monitored.", "script": "I'll use personal device for personal stuff.", "next_steps": ["Don't use for private things"]},
            {"id": "sch-t2", "question": "Track me at home?", "short_answer": "If using school device or logged in, probably yes.", "explanation": "Monitoring software works everywhere.", "script": "I'll log out at home.", "next_steps": ["Use personal devices at home"]},
            {"id": "sch-t3", "question": "Blocked website I need?", "short_answer": "Ask teacher or tech support to unblock for education.", "explanation": "Educational needs should be met.", "script": "I need this site for homework.", "next_steps": ["Ask teacher"]},
            {"id": "sch-t4", "question": "Accused of hacking?", "short_answer": "Serious accusation. Get parents and maybe lawyer.", "explanation": "Can have legal consequences.", "script": "I want my parents here.", "next_steps": ["Don't admit anything", "Get parents"]}
        ]
    },
    "work": {
        "pay": [
            {"id": "wrk-p1", "question": "Am I getting minimum wage?", "short_answer": "Check your state - might be higher than federal $7.25.", "explanation": "State rates often higher.", "script": "What's my exact hourly rate?", "next_steps": ["Check state minimum", "Review stubs"]},
            {"id": "wrk-p2", "question": "Working off the clock?", "short_answer": "Illegal if you're hourly. All work time must be paid.", "explanation": "Every minute counts.", "script": "I want to clock all my time.", "next_steps": ["Track hours", "Report violations"]},
            {"id": "wrk-p3", "question": "When's overtime?", "short_answer": "Over 40 hrs/week = 1.5x pay.", "explanation": "Non-exempt workers get overtime.", "script": "Will I get overtime for this?", "next_steps": ["Track hours", "Know if exempt"]},
            {"id": "wrk-p4", "question": "Deductions from paycheck?", "short_answer": "Only taxes and stuff you agreed to in writing.", "explanation": "Need written consent for most.", "script": "What's this deduction?", "next_steps": ["Review stubs", "Report illegal ones"]},
            {"id": "wrk-p5", "question": "Tips being taken?", "short_answer": "Illegal. Tips are yours.", "explanation": "Managers can't take tips.", "script": "How are tips distributed?", "next_steps": ["Know tip laws", "Report violations"]},
            {"id": "wrk-p6", "question": "Paycheck bounced?", "short_answer": "Illegal. They owe you plus penalties.", "explanation": "Must pay for work done.", "script": "When will I get my money?", "next_steps": ["Document", "File complaint"]},
            {"id": "wrk-p7", "question": "Paid less than coworkers?", "short_answer": "If it's discrimination, that's illegal.", "explanation": "Equal pay laws exist.", "script": "How is pay determined?", "next_steps": ["Document", "Ask HR"]},
            {"id": "wrk-p8", "question": "Commission not paid?", "short_answer": "Must pay earned commission per agreement.", "explanation": "Check your agreement.", "script": "What's the commission calculation?", "next_steps": ["Review agreement", "Document sales"]}
        ],
        "hours": [
            {"id": "wrk-h1", "question": "Do I get breaks?", "short_answer": "Depends on state. Many require meal and rest breaks.", "explanation": "Federal doesn't require, states often do.", "script": "What's the break policy?", "next_steps": ["Check state law"]},
            {"id": "wrk-h2", "question": "Last minute schedule change?", "short_answer": "Usually legal unless you have predictive scheduling laws.", "explanation": "Most workers don't have protection.", "script": "What's the schedule change policy?", "next_steps": ["Check local laws"]},
            {"id": "wrk-h3", "question": "Refuse overtime?", "short_answer": "Usually they can require it, but must pay you.", "explanation": "Overtime often mandatory.", "script": "What's the overtime rate?", "next_steps": ["Get paid properly"]},
            {"id": "wrk-h4", "question": "Stay late without pay?", "short_answer": "All time worked must be paid.", "explanation": "If required to stay, it's work time.", "script": "I'll clock out when I actually leave.", "next_steps": ["Clock all time"]},
            {"id": "wrk-h5", "question": "Hours as a minor?", "short_answer": "Limited by law. Usually 3 hrs on school days.", "explanation": "Strict rules for under 18.", "script": "Are my hours legal?", "next_steps": ["Know state rules"]},
            {"id": "wrk-h6", "question": "Scheduled during school?", "short_answer": "Can't work during required school hours.", "explanation": "School comes first.", "script": "I can't work during school.", "next_steps": ["Give school schedule"]}
        ],
        "safety": [
            {"id": "wrk-sf1", "question": "Unsafe workplace?", "short_answer": "Report it. OSHA complaints can be anonymous.", "explanation": "You have right to safe work.", "script": "I'm concerned about safety.", "next_steps": ["Document", "File OSHA complaint"]},
            {"id": "wrk-sf2", "question": "Hurt at work?", "short_answer": "Report immediately. Workers' comp covers you.", "explanation": "Don't need to prove fault.", "script": "I got injured at work.", "next_steps": ["Report", "Get medical care"]},
            {"id": "wrk-sf3", "question": "Who pays for safety gear?", "short_answer": "Employer must provide it free.", "explanation": "OSHA requires this.", "script": "I need safety equipment.", "next_steps": ["Request it"]},
            {"id": "wrk-sf4", "question": "Refuse dangerous work?", "short_answer": "Only if immediate serious danger.", "explanation": "Limited right to refuse.", "script": "This seems dangerous.", "next_steps": ["Explain concerns"]}
        ],
        "harassment": [
            {"id": "wrk-hr1", "question": "Sexual harassment?", "short_answer": "Unwanted sexual conduct is illegal.", "explanation": "Report it.", "script": "I need to report harassment.", "next_steps": ["Document", "Report to HR"]},
            {"id": "wrk-hr2", "question": "Treated differently because of who I am?", "short_answer": "Discrimination based on protected traits is illegal.", "explanation": "Many characteristics protected.", "script": "I'm concerned about discrimination.", "next_steps": ["Document", "Report"]},
            {"id": "wrk-hr3", "question": "Punished for reporting?", "short_answer": "Retaliation is illegal.", "explanation": "Can't punish you for reporting.", "script": "I'm worried about retaliation.", "next_steps": ["Document changes", "Report retaliation"]},
            {"id": "wrk-hr4", "question": "HR not helping?", "short_answer": "File with EEOC.", "explanation": "Government can investigate.", "script": "I want to file external complaint.", "next_steps": ["File EEOC complaint"]}
        ],
        "firing": [
            {"id": "wrk-f1", "question": "Fired for no reason?", "short_answer": "Usually legal unless discriminatory.", "explanation": "Most states are at-will.", "script": "Can I get termination reason in writing?", "next_steps": ["Get written reason"]},
            {"id": "wrk-f2", "question": "Final paycheck?", "short_answer": "Depends on state. Some say immediately.", "explanation": "State laws vary.", "script": "When do I get final pay?", "next_steps": ["Know state law"]},
            {"id": "wrk-f3", "question": "Unemployment?", "short_answer": "Usually yes if fired (not for misconduct).", "explanation": "Apply quickly.", "script": "I'm applying for unemployment.", "next_steps": ["Apply fast"]},
            {"id": "wrk-f4", "question": "Two weeks notice required?", "short_answer": "Usually no, just polite.", "explanation": "Check your contract.", "script": "I'm resigning effective [date].", "next_steps": ["Check contract"]},
            {"id": "wrk-f5", "question": "Sign something when leaving?", "short_answer": "Read carefully. Might give up rights.", "explanation": "Don't rush.", "script": "I need time to review this.", "next_steps": ["Read carefully", "Get lawyer maybe"]}
        ],
        "privacy": [
            {"id": "wrk-pr1", "question": "Read my work emails?", "short_answer": "Yes. Work email = work property.", "explanation": "No privacy on work systems.", "script": "I understand email is monitored.", "next_steps": ["Use personal for personal"]},
            {"id": "wrk-pr2", "question": "Drug test me?", "short_answer": "Often yes, especially for hiring.", "explanation": "Rules vary by state.", "script": "What's the policy?", "next_steps": ["Know state laws"]},
            {"id": "wrk-pr3", "question": "Fired for social media?", "short_answer": "Often yes. But discussing work conditions is protected.", "explanation": "Some speech protected.", "script": "What posts affect employment?", "next_steps": ["Be careful online"]}
        ],
        "minors": [
            {"id": "wrk-m1", "question": "What jobs can I do as a teen?", "short_answer": "Depends on age. Some jobs banned for under 18.", "explanation": "Hazardous work restricted.", "script": "What am I allowed to do at my age?", "next_steps": ["Know restrictions"]},
            {"id": "wrk-m2", "question": "Work late on school night?", "short_answer": "Limited hours during school week.", "explanation": "Usually can't work past certain time.", "script": "What are my hour limits?", "next_steps": ["Know the rules"]},
            {"id": "wrk-m3", "question": "Work permit needed?", "short_answer": "Many states require work permits for minors.", "explanation": "Get from school usually.", "script": "How do I get a work permit?", "next_steps": ["Ask school"]},
            {"id": "wrk-m4", "question": "Boss making me do dangerous stuff?", "short_answer": "Minors have extra protections from hazardous work.", "explanation": "Some tasks banned for minors.", "script": "I don't think I'm allowed to do this.", "next_steps": ["Know restrictions", "Report"]}
        ],
        "scheduling": [
            {"id": "wrk-sc1", "question": "On call without pay?", "short_answer": "If you must stay available, you might need to be paid.", "explanation": "Depends on restrictions.", "script": "What are the on-call rules?", "next_steps": ["Know the policy"]},
            {"id": "wrk-sc2", "question": "Shift cancelled last minute?", "short_answer": "Some places have 'show up pay' laws.", "explanation": "Check local laws.", "script": "Is there pay for cancelled shifts?", "next_steps": ["Check local rules"]},
            {"id": "wrk-sc3", "question": "Too many hours?", "short_answer": "No federal cap but must be paid. Minors have limits.", "explanation": "Must pay for all hours.", "script": "I'm working too many hours.", "next_steps": ["Track hours"]},
            {"id": "wrk-sc4", "question": "Need day off they won't give?", "short_answer": "No law requires time off except FMLA for family/medical.", "explanation": "Depends on circumstances.", "script": "I need this day off for [reason].", "next_steps": ["Ask about policies"]}
        ],
        "tips": [
            {"id": "wrk-tp1", "question": "Tip pooling?", "short_answer": "Okay with other tipped workers. Managers usually can't take.", "explanation": "Must follow rules.", "script": "Who's in the tip pool?", "next_steps": ["Know the rules"]},
            {"id": "wrk-tp2", "question": "Credit card tips?", "short_answer": "Must give you full tip amount. Small processing fee sometimes okay.", "explanation": "Tips are yours.", "script": "When do I get card tips?", "next_steps": ["Track tips"]},
            {"id": "wrk-tp3", "question": "Making less than minimum with tips?", "short_answer": "Employer must make up difference to minimum wage.", "explanation": "Must hit minimum total.", "script": "I'm not making minimum wage.", "next_steps": ["Track wages and tips"]}
        ],
        "contracts": [
            {"id": "wrk-c1", "question": "Non-compete agreement?", "short_answer": "Many states limit or ban them, especially for low-wage workers.", "explanation": "May not be enforceable.", "script": "Is this enforceable in our state?", "next_steps": ["Check state law"]},
            {"id": "wrk-c2", "question": "Signed something I didn't understand?", "short_answer": "You're usually bound. Get lawyer to review.", "explanation": "Read before signing.", "script": "Can I get a copy of what I signed?", "next_steps": ["Get copy", "Review"]},
            {"id": "wrk-c3", "question": "Job different than promised?", "short_answer": "Verbal promises hard to enforce. Check written agreement.", "explanation": "Get important stuff in writing.", "script": "This wasn't what was described.", "next_steps": ["Document", "Ask HR"]}
        ],
        "discrimination": [
            {"id": "wrk-ds1", "question": "Not hired because of age?", "short_answer": "Age discrimination illegal for 40+. Younger workers less protected.", "explanation": "Laws protect older workers more.", "script": "Why wasn't I selected?", "next_steps": ["Ask for reason"]},
            {"id": "wrk-ds2", "question": "Pregnancy discrimination?", "short_answer": "Illegal. Must treat like other medical conditions.", "explanation": "Protected status.", "script": "I need pregnancy accommodations.", "next_steps": ["Request accommodations"]},
            {"id": "wrk-ds3", "question": "Accent discrimination?", "short_answer": "Illegal if based on national origin.", "explanation": "National origin protected.", "script": "I'm being treated differently.", "next_steps": ["Document", "Report"]}
        ]
    },
    "housing": {
        "entry": [
            {"id": "hsg-e1", "question": "Landlord just walk in?", "short_answer": "No. Need 24-48 hours notice except emergencies.", "explanation": "Right to quiet enjoyment.", "script": "I need proper notice.", "next_steps": ["Check state law"]},
            {"id": "hsg-e2", "question": "What's emergency?", "short_answer": "Fire, flood, gas leak. NOT routine stuff.", "explanation": "Real emergencies only.", "script": "This doesn't seem like emergency.", "next_steps": ["Know what qualifies"]},
            {"id": "hsg-e3", "question": "Change locks?", "short_answer": "Usually yes but might need to give landlord key.", "explanation": "Check lease.", "script": "I want to change locks for safety.", "next_steps": ["Check lease"]},
            {"id": "hsg-e4", "question": "Too many showings?", "short_answer": "Can ask for reasonable limits.", "explanation": "Must give notice.", "script": "Can we limit showing times?", "next_steps": ["Request reasonable schedule"]}
        ],
        "repairs": [
            {"id": "hsg-r1", "question": "Won't fix stuff?", "short_answer": "Put in writing. May have legal options.", "explanation": "Landlord must maintain habitability.", "script": "When will this be fixed?", "next_steps": ["Request in writing"]},
            {"id": "hsg-r2", "question": "No heat or hot water?", "short_answer": "Emergency. Must fix fast.", "explanation": "Basic requirements.", "script": "This is an emergency.", "next_steps": ["Report", "Call code enforcement"]},
            {"id": "hsg-r3", "question": "Mold or bugs?", "short_answer": "Usually landlord's problem.", "explanation": "Document and report.", "script": "I'm reporting a health hazard.", "next_steps": ["Take photos", "Report"]}
        ],
        "eviction": [
            {"id": "hsg-ev1", "question": "Kicked out immediately?", "short_answer": "No. Legal process required.", "explanation": "Can't force you out.", "script": "I need formal notice.", "next_steps": ["Don't leave without process"]},
            {"id": "hsg-ev2", "question": "How much notice?", "short_answer": "Varies by state and reason. Usually 3-30 days.", "explanation": "Depends on circumstances.", "script": "What's the timeline?", "next_steps": ["Read notice carefully"]},
            {"id": "hsg-ev3", "question": "Locked out?", "short_answer": "ILLEGAL. Call police.", "explanation": "Self-help eviction banned.", "script": "This is illegal lockout.", "next_steps": ["Call police", "Sue them"]}
        ],
        "deposits": [
            {"id": "hsg-d1", "question": "When get deposit back?", "short_answer": "Usually 14-30 days with itemized list.", "explanation": "State sets deadline.", "script": "When do I get deposit?", "next_steps": ["Give forwarding address"]},
            {"id": "hsg-d2", "question": "Keeping for normal wear?", "short_answer": "Not allowed. Normal wear isn't damage.", "explanation": "Faded paint is normal.", "script": "These are normal wear.", "next_steps": ["Dispute in writing"]},
            {"id": "hsg-d3", "question": "Deposit too high?", "short_answer": "Many states cap at 1-2 months.", "explanation": "Check state limits.", "script": "Is this within legal limits?", "next_steps": ["Know state rules"]}
        ],
        "lease": [
            {"id": "hsg-l1", "question": "Break lease early?", "short_answer": "May owe money but landlord must try to re-rent.", "explanation": "Mitigation required.", "script": "What are my options?", "next_steps": ["Read lease", "Give notice"]},
            {"id": "hsg-l2", "question": "Raise rent during lease?", "short_answer": "Usually no. After lease, need proper notice.", "explanation": "During lease = fixed.", "script": "What's the rent increase process?", "next_steps": ["Check lease"]}
        ],
        "roommates": [
            {"id": "hsg-rm1", "question": "Roommate bailed?", "short_answer": "If both on lease, either can be liable for all.", "explanation": "Joint liability.", "script": "My roommate left. Options?", "next_steps": ["Talk to landlord"]},
            {"id": "hsg-rm2", "question": "Can I sublet?", "short_answer": "Check lease. Usually need permission.", "explanation": "Most require approval.", "script": "What's the process to sublet?", "next_steps": ["Read lease", "Get permission"]}
        ],
        "utilities": [
            {"id": "hsg-u1", "question": "Landlord shut off utilities?", "short_answer": "ILLEGAL in most places.", "explanation": "Can't cut utilities to force you out.", "script": "This is illegal.", "next_steps": ["Call police", "Report"]},
            {"id": "hsg-u2", "question": "Who pays utilities?", "short_answer": "Check lease. Should be clear.", "explanation": "Lease should specify.", "script": "What utilities am I responsible for?", "next_steps": ["Check lease"]},
            {"id": "hsg-u3", "question": "Bill seems too high?", "short_answer": "Can request sub-metering or audit.", "explanation": "Should be fair.", "script": "Can we verify these charges?", "next_steps": ["Request breakdown"]}
        ],
        "pets": [
            {"id": "hsg-pt1", "question": "Pet deposit too high?", "short_answer": "Some states limit pet deposits.", "explanation": "Check state rules.", "script": "Is this within legal limits?", "next_steps": ["Know state rules"]},
            {"id": "hsg-pt2", "question": "Service animal fees?", "short_answer": "Can't charge extra for service animals.", "explanation": "Service animals aren't pets legally.", "script": "This is a service animal.", "next_steps": ["Provide documentation"]},
            {"id": "hsg-pt3", "question": "Changed pet policy?", "short_answer": "Can't change during lease usually.", "explanation": "Lease terms apply.", "script": "My lease allows this.", "next_steps": ["Show lease"]}
        ],
        "noise": [
            {"id": "hsg-n1", "question": "Neighbors too loud?", "short_answer": "Complain to landlord. May be lease violation.", "explanation": "Right to quiet enjoyment.", "script": "The noise is unreasonable.", "next_steps": ["Document incidents", "Complain"]},
            {"id": "hsg-n2", "question": "Accused of being too loud?", "short_answer": "Know quiet hours. Reasonable noise is allowed.", "explanation": "Normal living noise is okay.", "script": "What specific noise violated rules?", "next_steps": ["Know quiet hours"]}
        ],
        "discrimination": [
            {"id": "hsg-ds1", "question": "Denied because of kids?", "short_answer": "Familial status is protected. Usually illegal.", "explanation": "Can't discriminate against families.", "script": "Is this because I have children?", "next_steps": ["Document", "Report to HUD"]},
            {"id": "hsg-ds2", "question": "Denied for race/religion?", "short_answer": "Illegal. Fair Housing Act.", "explanation": "Many characteristics protected.", "script": "Why was I denied?", "next_steps": ["Get reason in writing", "Report"]}
        ],
        "moving": [
            {"id": "hsg-mv1", "question": "How much notice to move out?", "short_answer": "Usually 30 days. Check lease.", "explanation": "Give proper notice.", "script": "What notice is required?", "next_steps": ["Check lease", "Give written notice"]},
            {"id": "hsg-mv2", "question": "Cleaning required?", "short_answer": "Usually must leave reasonably clean.", "explanation": "Normal cleaning expected.", "script": "What cleaning is expected?", "next_steps": ["Take photos", "Clean reasonably"]},
            {"id": "hsg-mv3", "question": "Stuff left behind?", "short_answer": "Landlord may be able to dispose of it.", "explanation": "Take everything.", "script": "I need more time to get my things.", "next_steps": ["Get extension if needed"]}
        ]
    },
    "police": {
        "stops": [
            {"id": "pol-st1", "question": "Stopped walking?", "short_answer": "Stay calm. Hands visible. Ask if free to go.", "explanation": "Can ask if detained.", "script": "Am I free to go?", "next_steps": ["Stay calm", "Don't run"]},
            {"id": "pol-st2", "question": "Have to give name?", "short_answer": "Usually yes if detained. Other questions optional.", "explanation": "Most states require ID when detained.", "script": "I'll give my name. I'm staying silent otherwise.", "next_steps": ["Know state law"]},
            {"id": "pol-st3", "question": "Can I walk away?", "short_answer": "Ask if detained. If no, leave calmly.", "explanation": "Never run.", "script": "Am I being detained?", "next_steps": ["Ask clearly", "Leave if free"]}
        ],
        "searches": [
            {"id": "pol-se1", "question": "Search my body?", "short_answer": "Pat-down for weapons needs suspicion. Full search needs more.", "explanation": "Say you don't consent.", "script": "I don't consent to a search.", "next_steps": ["Don't consent", "Don't resist"]},
            {"id": "pol-se2", "question": "Search my car?", "short_answer": "Need probable cause or consent. Say no.", "explanation": "You can refuse consent.", "script": "I don't consent.", "next_steps": ["Don't consent", "Stay polite"]},
            {"id": "pol-se3", "question": "Search phone?", "short_answer": "NO. Need warrant. Don't unlock it.", "explanation": "Supreme Court says warrant required.", "script": "Show me a warrant.", "next_steps": ["Don't unlock", "Don't give password"]},
            {"id": "pol-se4", "question": "Search home?", "short_answer": "Need warrant. Don't let them in.", "explanation": "Strong home protection.", "script": "I don't consent. Show warrant.", "next_steps": ["Step outside", "Ask for warrant"]}
        ],
        "arrests": [
            {"id": "pol-ar1", "question": "Being arrested?", "short_answer": "Don't resist. Say 'lawyer' and 'silent.'", "explanation": "Fight it in court.", "script": "I want a lawyer. I'm staying silent.", "next_steps": ["Don't resist", "Stay quiet"]},
            {"id": "pol-ar2", "question": "Miranda rights?", "short_answer": "Right to silence and lawyer.", "explanation": "Invoke them clearly.", "script": "I invoke my rights.", "next_steps": ["Say it clearly", "Stop talking"]},
            {"id": "pol-ar3", "question": "Phone call?", "short_answer": "Yes, usually within reasonable time.", "explanation": "You get to call.", "script": "I want my phone call.", "next_steps": ["Call lawyer first"]}
        ],
        "rights": [
            {"id": "pol-rt1", "question": "Right to remain silent?", "short_answer": "Yes. You don't have to answer questions.", "explanation": "Fifth Amendment.", "script": "I'm exercising my right to remain silent.", "next_steps": ["Say it clearly", "Stop talking"]},
            {"id": "pol-rt2", "question": "Right to lawyer?", "short_answer": "Before and during questioning. Free if you can't afford.", "explanation": "Questioning must stop when you ask.", "script": "I want a lawyer.", "next_steps": ["Ask immediately"]}
        ],
        "recording": [
            {"id": "pol-rc1", "question": "Can I record police?", "short_answer": "Yes in public. Safe distance, don't interfere.", "explanation": "First Amendment right.", "script": "I'm recording from safe distance.", "next_steps": ["Stay back", "Back up video"]},
            {"id": "pol-rc2", "question": "Make me delete?", "short_answer": "No. That's illegal.", "explanation": "Don't delete.", "script": "I don't consent to deleting.", "next_steps": ["Don't delete", "Don't unlock"]}
        ],
        "complaints": [
            {"id": "pol-cm1", "question": "File complaint?", "short_answer": "Internal affairs or civilian review board.", "explanation": "Document everything first.", "script": "I want to file complaint.", "next_steps": ["Document", "File in writing"]},
            {"id": "pol-cm2", "question": "Sue police?", "short_answer": "Possible for civil rights violations. Get lawyer.", "explanation": "It's hard but possible.", "script": "I want to talk to civil rights attorney.", "next_steps": ["Get lawyer"]}
        ],
        "minors": [
            {"id": "pol-mn1", "question": "Questioned without parents?", "short_answer": "You can ask for parents. Rules vary.", "explanation": "Minors have some extra protections.", "script": "I want my parents here.", "next_steps": ["Ask for parents", "Stay silent"]},
            {"id": "pol-mn2", "question": "Curfew violation?", "short_answer": "May get ticket or taken to parents.", "explanation": "Usually not serious.", "script": "I was heading home.", "next_steps": ["Be honest", "Know exceptions"]},
            {"id": "pol-mn3", "question": "Juvenile record?", "short_answer": "Often sealed at 18. Ask lawyer.", "explanation": "May not follow you.", "script": "What happens to this record?", "next_steps": ["Ask about sealing"]}
        ],
        "traffic": [
            {"id": "pol-tr1", "question": "Pulled over?", "short_answer": "Pull over safely. Hands on wheel. Be polite.", "explanation": "Stay calm.", "script": "I'm reaching for my license.", "next_steps": ["Hands visible", "Announce movements"]},
            {"id": "pol-tr2", "question": "Have to get out of car?", "short_answer": "If they order you out, yes.", "explanation": "Legal order to exit.", "script": "Okay, I'm getting out.", "next_steps": ["Comply calmly"]},
            {"id": "pol-tr3", "question": "Sobriety test?", "short_answer": "Can refuse field tests. Chemical test refusal has consequences.", "explanation": "Implied consent laws.", "script": "What are consequences of refusing?", "next_steps": ["Know state rules"]}
        ],
        "home": [
            {"id": "pol-hm1", "question": "Police at my door?", "short_answer": "Don't have to open. Talk through door.", "explanation": "Your home is protected.", "script": "How can I help you?", "next_steps": ["Don't open", "Ask for warrant"]},
            {"id": "pol-hm2", "question": "They have warrant?", "short_answer": "Ask to see it. Check name, address, what they can search.", "explanation": "Verify it's valid.", "script": "Let me see the warrant.", "next_steps": ["Check details", "Watch what they search"]},
            {"id": "pol-hm3", "question": "Came in without warrant?", "short_answer": "Say you don't consent. Document everything.", "explanation": "May be illegal search.", "script": "I don't consent to this.", "next_steps": ["Don't consent", "Get lawyer"]}
        ],
        "witnesses": [
            {"id": "pol-wt1", "question": "Have to talk as witness?", "short_answer": "Generally yes, but can have lawyer.", "explanation": "Witnesses usually must cooperate.", "script": "Can I have a lawyer present?", "next_steps": ["Ask for lawyer if nervous"]},
            {"id": "pol-wt2", "question": "Subpoenaed?", "short_answer": "Must appear. Can be held in contempt otherwise.", "explanation": "Court orders are mandatory.", "script": "I received a subpoena.", "next_steps": ["Show up", "Get lawyer if needed"]}
        ],
        "after": [
            {"id": "pol-af1", "question": "How does bail work?", "short_answer": "Money to get out before trial.", "explanation": "Pay full or use bondsman.", "script": "I'd like a bail hearing.", "next_steps": ["Ask about bail"]},
            {"id": "pol-af2", "question": "Public defender?", "short_answer": "Free if you can't afford lawyer.", "explanation": "Right to counsel.", "script": "I need a public defender.", "next_steps": ["Request one"]},
            {"id": "pol-af3", "question": "What happens at arraignment?", "short_answer": "Hear charges, enter plea.", "explanation": "Usually plead not guilty.", "script": "I plead not guilty.", "next_steps": ["Get lawyer first"]}
        ]
    },
    "online": {
        "social": [
            {"id": "onl-so1", "question": "Who sees my posts?", "short_answer": "Check settings. Anyone can screenshot.", "explanation": "Nothing truly private.", "script": "Where are privacy settings?", "next_steps": ["Check settings"]},
            {"id": "onl-so2", "question": "Delete something?", "short_answer": "From platform yes. Copies may exist.", "explanation": "Internet is forever.", "script": "How do I delete this?", "next_steps": ["Delete from platform"]},
            {"id": "onl-so3", "question": "Account hacked?", "short_answer": "Change passwords, enable 2FA, report.", "explanation": "Act fast.", "script": "My account was hacked.", "next_steps": ["Change passwords", "Enable 2FA"]}
        ],
        "data": [
            {"id": "onl-dt1", "question": "What data do apps collect?", "short_answer": "Usually a lot. Check privacy policy.", "explanation": "Location, browsing, contacts...", "script": "What do you collect?", "next_steps": ["Read policies"]},
            {"id": "onl-dt2", "question": "Get my data deleted?", "short_answer": "Yes in some states.", "explanation": "CCPA and similar laws.", "script": "I want my data deleted.", "next_steps": ["Submit request"]}
        ],
        "harassment": [
            {"id": "onl-hr1", "question": "Cyberbullied?", "short_answer": "Screenshot, block, report. Threats = police.", "explanation": "Document everything.", "script": "I'm being cyberbullied.", "next_steps": ["Screenshot", "Block", "Report"]},
            {"id": "onl-hr2", "question": "Doxxed?", "short_answer": "Report for removal. Police if threats.", "explanation": "Take it seriously.", "script": "My info was posted.", "next_steps": ["Report", "Police if threats"]},
            {"id": "onl-hr3", "question": "Online threats?", "short_answer": "Screenshot. Report. Police.", "explanation": "Threats can be crimes.", "script": "I've received threats.", "next_steps": ["Screenshot", "Report", "Police"]}
        ],
        "photos": [
            {"id": "onl-ph1", "question": "Photo posted without consent?", "short_answer": "In public usually legal. Harassment/profit different.", "explanation": "Context matters.", "script": "This was used harmfully.", "next_steps": ["Report to platform"]},
            {"id": "onl-ph2", "question": "Intimate images shared?", "short_answer": "Illegal in most states. Report to platform AND police.", "explanation": "'Revenge porn' is crime.", "script": "This is illegal.", "next_steps": ["Report platform", "Contact police"]}
        ],
        "accounts": [
            {"id": "onl-ac1", "question": "Parents/school want password?", "short_answer": "Parents often can for minors. Schools usually can't for personal.", "explanation": "Depends who's asking.", "script": "Why do you need this?", "next_steps": ["Protect personal accounts"]},
            {"id": "onl-ac2", "question": "Make accounts secure?", "short_answer": "Strong passwords, 2FA, watch for phishing.", "explanation": "Use different passwords.", "script": "How do I enable 2FA?", "next_steps": ["Enable 2FA everywhere"]}
        ],
        "school-monitoring": [
            {"id": "onl-sm1", "question": "School see school device?", "short_answer": "YES. Everything.", "explanation": "Fully monitored.", "script": "I'll use personal for personal.", "next_steps": ["Don't use for private"]},
            {"id": "onl-sm2", "question": "Track me at home?", "short_answer": "If using school device, probably.", "explanation": "Monitoring works everywhere.", "script": "I'll log out at home.", "next_steps": ["Use personal at home"]}
        ],
        "scams": [
            {"id": "onl-sc1", "question": "Think I got scammed?", "short_answer": "Report to FTC. Contact bank. Change passwords.", "explanation": "Act fast to limit damage.", "script": "I need to report a scam.", "next_steps": ["Report to FTC", "Contact bank"]},
            {"id": "onl-sc2", "question": "Phishing email?", "short_answer": "Don't click. Report. Delete.", "explanation": "Never give info to suspicious emails.", "script": "This looks fake.", "next_steps": ["Don't click", "Report"]},
            {"id": "onl-sc3", "question": "Gave scammer my info?", "short_answer": "Change passwords. Freeze credit. Monitor accounts.", "explanation": "Minimize damage.", "script": "I accidentally gave info.", "next_steps": ["Change passwords", "Freeze credit"]}
        ],
        "gaming": [
            {"id": "onl-gm1", "question": "In-game harassment?", "short_answer": "Report to platform. Block. Save evidence.", "explanation": "Platforms have rules.", "script": "I need to report harassment.", "next_steps": ["Report", "Block"]},
            {"id": "onl-gm2", "question": "Scammed in game trade?", "short_answer": "Report to platform. May not get stuff back.", "explanation": "Virtual items hard to recover.", "script": "I was scammed in a trade.", "next_steps": ["Report to game"]},
            {"id": "onl-gm3", "question": "Account banned unfairly?", "short_answer": "Appeal through platform process.", "explanation": "Platforms have appeal options.", "script": "I want to appeal this ban.", "next_steps": ["Follow appeal process"]}
        ],
        "shopping": [
            {"id": "onl-sh1", "question": "Package never arrived?", "short_answer": "Contact seller. File dispute with payment method.", "explanation": "Document everything.", "script": "My order never arrived.", "next_steps": ["Contact seller", "Dispute charge"]},
            {"id": "onl-sh2", "question": "Received wrong item?", "short_answer": "Contact seller. Usually must accept return.", "explanation": "You get what you ordered.", "script": "This isn't what I ordered.", "next_steps": ["Contact seller", "Document"]}
        ],
        "copyright": [
            {"id": "onl-cp1", "question": "Use someone's music/art?", "short_answer": "Need permission or must be fair use.", "explanation": "Copyright protects creators.", "script": "Can I use this?", "next_steps": ["Ask permission", "Check if fair use"]},
            {"id": "onl-cp2", "question": "Someone stole my content?", "short_answer": "File DMCA takedown with platform.", "explanation": "You have rights to your work.", "script": "My content was stolen.", "next_steps": ["File DMCA"]}
        ],
        "ai": [
            {"id": "onl-ai1", "question": "Deepfake of me?", "short_answer": "Many states have laws against this. Report to platform.", "explanation": "Increasingly illegal.", "script": "There's a fake video/image of me.", "next_steps": ["Report platform", "Check state law"]},
            {"id": "onl-ai2", "question": "AI using my likeness?", "short_answer": "Emerging legal area. Document and consult lawyer.", "explanation": "Laws developing.", "script": "AI is using my face/voice.", "next_steps": ["Document", "Consult lawyer"]}
        ]
    },
    "public": {
        "filming": [
            {"id": "pub-fl1", "question": "Photos on street?", "short_answer": "Yes. No expectation of privacy in public.", "explanation": "Public photography legal.", "script": "I'm in a public space.", "next_steps": ["Be respectful"]},
            {"id": "pub-fl2", "question": "Film police?", "short_answer": "Yes. First Amendment. Safe distance.", "explanation": "Recording is protected.", "script": "I'm exercising my right to record.", "next_steps": ["Keep distance", "Back up"]}
        ],
        "protests": [
            {"id": "pub-pr1", "question": "Rights at protests?", "short_answer": "First Amendment protects peaceful assembly.", "explanation": "Know the limits.", "script": "I'm exercising my rights.", "next_steps": ["Stay peaceful"]},
            {"id": "pub-pr2", "question": "Need permit?", "short_answer": "Large events often yes. Small groups usually no.", "explanation": "Check local rules.", "script": "What are permit requirements?", "next_steps": ["Check rules"]},
            {"id": "pub-pr3", "question": "Arrested at protest?", "short_answer": "Don't resist. Lawyer. Silent.", "explanation": "Challenge in court.", "script": "I want a lawyer.", "next_steps": ["Don't resist"]}
        ],
        "stores": [
            {"id": "pub-st1", "question": "Detained for shoplifting?", "short_answer": "Briefly if reasonable belief.", "explanation": "Shopkeeper's privilege.", "script": "I haven't taken anything.", "next_steps": ["Stay calm"]},
            {"id": "pub-st2", "question": "Check my bag?", "short_answer": "They ask. You can usually refuse but might get banned.", "explanation": "Usually voluntary.", "script": "Is this required?", "next_steps": ["Ask if required"]}
        ],
        "transport": [
            {"id": "pub-tr1", "question": "Public transit rules?", "short_answer": "Agencies set rules. Pay fare.", "explanation": "Follow rules.", "script": "What are the rules?", "next_steps": ["Pay fare"]},
            {"id": "pub-tr2", "question": "Uber/Lyft rights?", "short_answer": "Private car. Driver can end ride.", "explanation": "Use safety features.", "script": "I feel unsafe.", "next_steps": ["End ride", "Report"]}
        ],
        "parks": [
            {"id": "pub-pk1", "question": "Park rules?", "short_answer": "Check posted rules. Hours, alcohol, etc.", "explanation": "Parks have rules.", "script": "What's allowed here?", "next_steps": ["Check rules"]},
            {"id": "pub-pk2", "question": "Sleep outside?", "short_answer": "Laws vary. Being challenged where no shelter available.", "explanation": "Evolving area.", "script": "Where can I get help?", "next_steps": ["Find shelter resources"]}
        ],
        "curfew": [
            {"id": "pub-cf1", "question": "Youth curfew?", "short_answer": "Many cities have them with exceptions.", "explanation": "Know exceptions.", "script": "I'm heading home from work.", "next_steps": ["Know exceptions"]},
            {"id": "pub-cf2", "question": "Loitering?", "short_answer": "Vague laws often unconstitutional.", "explanation": "Can ask what you're accused of.", "script": "What am I accused of?", "next_steps": ["Ask specifically"]}
        ],
        "malls": [
            {"id": "pub-ml1", "question": "Kicked out of mall?", "short_answer": "Private property. They can ask you to leave.", "explanation": "But not for discrimination.", "script": "Why am I being asked to leave?", "next_steps": ["Ask reason"]},
            {"id": "pub-ml2", "question": "Mall security search me?", "short_answer": "Usually need consent. They're not police.", "explanation": "Private security has limits.", "script": "I don't consent to a search.", "next_steps": ["Don't consent"]}
        ],
        "events": [
            {"id": "pub-ev1", "question": "Bag check at concert?", "short_answer": "Condition of entry. You agree by entering.", "explanation": "Private venue rules.", "script": "What's the bag policy?", "next_steps": ["Know policy"]},
            {"id": "pub-ev2", "question": "Kicked out of event?", "short_answer": "Private venues can remove you.", "explanation": "But not for discrimination.", "script": "Why am I being removed?", "next_steps": ["Ask reason"]}
        ],
        "restaurants": [
            {"id": "pub-rs1", "question": "Refused service?", "short_answer": "Legal unless discrimination.", "explanation": "Private business rights.", "script": "Is this discrimination?", "next_steps": ["Document if discriminatory"]},
            {"id": "pub-rs2", "question": "Charged for things I didn't order?", "short_answer": "Only pay for what you ordered.", "explanation": "Dispute errors.", "script": "I didn't order this.", "next_steps": ["Dispute charge"]}
        ],
        "id": [
            {"id": "pub-id1", "question": "Have to show ID?", "short_answer": "To police if detained. Others usually no.", "explanation": "Limited requirement.", "script": "Am I required to show ID?", "next_steps": ["Know when required"]},
            {"id": "pub-id2", "question": "Bouncer wants ID?", "short_answer": "Their policy. Can deny entry.", "explanation": "Private business.", "script": "What ID do you accept?", "next_steps": ["Show if you want entry"]}
        ],
        "banned": [
            {"id": "pub-bn1", "question": "Banned from store?", "short_answer": "Private property. They can ban you.", "explanation": "Unless discrimination.", "script": "Why am I banned?", "next_steps": ["Get reason"]},
            {"id": "pub-bn2", "question": "Trespassing if return?", "short_answer": "Yes, you can be arrested.", "explanation": "Respect bans.", "script": "Is there an appeal process?", "next_steps": ["Ask about appeal"]}
        ]
    },
    "immigration": {
        "documents": [
            {"id": "imm-dc1", "question": "Have to carry papers?", "short_answer": "Should have some form of ID. Depends on status.", "explanation": "Rules vary by status.", "script": "What documentation do I need?", "next_steps": ["Know your requirements"]},
            {"id": "imm-dc2", "question": "Lost my documents?", "short_answer": "Request replacement from USCIS.", "explanation": "File replacement forms.", "script": "How do I replace lost documents?", "next_steps": ["Contact USCIS"]},
            {"id": "imm-dc3", "question": "Expired documents?", "short_answer": "Renew before expiration if possible.", "explanation": "Don't let them lapse.", "script": "How do I renew?", "next_steps": ["Apply for renewal"]}
        ],
        "police": [
            {"id": "imm-pl1", "question": "Police ask immigration status?", "short_answer": "In many places, local police can't ask. You don't have to answer.", "explanation": "Know your jurisdiction.", "script": "Am I required to answer?", "next_steps": ["Know local policies", "Stay silent if unsure"]},
            {"id": "imm-pl2", "question": "ICE wants to talk?", "short_answer": "You have right to remain silent and ask for lawyer.", "explanation": "ICE isn't regular police.", "script": "I'm staying silent. I want a lawyer.", "next_steps": ["Don't answer questions", "Get lawyer"]},
            {"id": "imm-pl3", "question": "Stopped by ICE?", "short_answer": "Ask if free to go. Don't sign anything. Get lawyer.", "explanation": "You have rights.", "script": "Am I free to go?", "next_steps": ["Ask if detained", "Stay silent", "Lawyer"]},
            {"id": "imm-pl4", "question": "ICE at my door?", "short_answer": "Don't have to open. Ask for warrant through door.", "explanation": "They need judicial warrant to enter.", "script": "Do you have a warrant signed by a judge?", "next_steps": ["Don't open", "Check warrant"]}
        ],
        "work": [
            {"id": "imm-wk1", "question": "Can I work?", "short_answer": "Depends on your status. Some visas allow, some don't.", "explanation": "Know your authorization.", "script": "What work am I authorized for?", "next_steps": ["Check your status"]},
            {"id": "imm-wk2", "question": "Employer threats about status?", "short_answer": "Using immigration to threaten is illegal.", "explanation": "Protected from retaliation.", "script": "That threat is illegal.", "next_steps": ["Document", "Report"]},
            {"id": "imm-wk3", "question": "Work visa issues?", "short_answer": "Contact immigration lawyer immediately.", "explanation": "Time-sensitive.", "script": "I need immigration lawyer.", "next_steps": ["Get lawyer fast"]},
            {"id": "imm-wk4", "question": "Paid less because of status?", "short_answer": "Illegal. Labor laws protect everyone.", "explanation": "Same wage protections apply.", "script": "I should get equal pay.", "next_steps": ["Document", "Report to DOL"]}
        ],
        "school": [
            {"id": "imm-sc1", "question": "Can I go to public school?", "short_answer": "YES. All kids can attend K-12 regardless of status.", "explanation": "Plyler v. Doe protects this.", "script": "My child has a right to education.", "next_steps": ["Enroll normally"]},
            {"id": "imm-sc2", "question": "School asking immigration status?", "short_answer": "They shouldn't. It's not relevant for enrollment.", "explanation": "Schools can't require this.", "script": "Why is this being asked?", "next_steps": ["You don't have to answer"]},
            {"id": "imm-sc3", "question": "College as undocumented?", "short_answer": "Possible. Many schools accept. In-state tuition varies.", "explanation": "Options exist.", "script": "What are my options?", "next_steps": ["Research schools", "Ask about policies"]},
            {"id": "imm-sc4", "question": "Financial aid for undocumented?", "short_answer": "No federal. Some states and private aid available.", "explanation": "Limited but exists.", "script": "What aid can I access?", "next_steps": ["Check state programs", "Private scholarships"]}
        ],
        "travel": [
            {"id": "imm-tv1", "question": "Travel within US?", "short_answer": "Generally yes, but checkpoints exist near borders.", "explanation": "Know the risks.", "script": "What should I expect?", "next_steps": ["Know checkpoint locations"]},
            {"id": "imm-tv2", "question": "Travel outside US?", "short_answer": "Risky depending on status. May not be able to return.", "explanation": "Consult lawyer first.", "script": "What are the risks?", "next_steps": ["Talk to lawyer"]},
            {"id": "imm-tv3", "question": "Airport questions?", "short_answer": "You have some rights but CBP has broad authority.", "explanation": "Borders are different.", "script": "I'd like to speak to a lawyer.", "next_steps": ["Know border rules"]}
        ],
        "healthcare": [
            {"id": "imm-hc1", "question": "Get medical care?", "short_answer": "Emergency rooms must treat everyone.", "explanation": "EMTALA applies to all.", "script": "I need emergency care.", "next_steps": ["Get emergency care"]},
            {"id": "imm-hc2", "question": "Health insurance?", "short_answer": "Options vary by status and state.", "explanation": "Some programs available.", "script": "What programs can I access?", "next_steps": ["Check state programs"]},
            {"id": "imm-hc3", "question": "Hospital reporting status?", "short_answer": "Generally no. Medical privacy applies.", "explanation": "HIPAA protects you.", "script": "Is my information private?", "next_steps": ["Know your privacy rights"]}
        ],
        "housing": [
            {"id": "imm-hs1", "question": "Rent an apartment?", "short_answer": "Landlords can't discriminate based on citizenship.", "explanation": "Fair Housing protects you.", "script": "Why was I denied?", "next_steps": ["Document if discriminated"]},
            {"id": "imm-hs2", "question": "Landlord threatening to call ICE?", "short_answer": "Often illegal retaliation.", "explanation": "Can't use immigration to threaten.", "script": "That threat is illegal.", "next_steps": ["Document", "Report"]}
        ],
        "detention": [
            {"id": "imm-dt1", "question": "Detained by ICE?", "short_answer": "You have rights. Don't sign anything. Get lawyer.", "explanation": "Stay silent and ask for lawyer.", "script": "I want a lawyer.", "next_steps": ["Stay silent", "Get lawyer"]},
            {"id": "imm-dt2", "question": "Detained family member?", "short_answer": "Contact immigration lawyer immediately.", "explanation": "Time is critical.", "script": "I need to find a lawyer.", "next_steps": ["Call immigration lawyer", "Contact family hotline"]},
            {"id": "imm-dt3", "question": "Rights in detention?", "short_answer": "Right to lawyer, phone calls, medical care.", "explanation": "Rights exist in detention.", "script": "I want to call a lawyer.", "next_steps": ["Assert rights"]}
        ],
        "family": [
            {"id": "imm-fm1", "question": "Sponsor family?", "short_answer": "Depends on your status and their relationship.", "explanation": "Complex rules.", "script": "How do I sponsor family?", "next_steps": ["Consult lawyer"]},
            {"id": "imm-fm2", "question": "Child born here?", "short_answer": "Child is US citizen. Doesn't automatically change your status.", "explanation": "Child is citizen at birth.", "script": "What are my child's rights?", "next_steps": ["Know child's citizenship"]},
            {"id": "imm-fm3", "question": "Family separation?", "short_answer": "Contact immigration lawyer and advocacy groups.", "explanation": "Help exists.", "script": "My family was separated.", "next_steps": ["Get legal help", "Contact advocacy groups"]}
        ],
        "daca": [
            {"id": "imm-da1", "question": "What is DACA?", "short_answer": "Program for people brought to US as kids. Protects from deportation.", "explanation": "Work permit and protection.", "script": "Am I eligible for DACA?", "next_steps": ["Check eligibility"]},
            {"id": "imm-da2", "question": "DACA renewal?", "short_answer": "Renew 150-120 days before expiration.", "explanation": "Don't let it lapse.", "script": "How do I renew?", "next_steps": ["Apply in time"]},
            {"id": "imm-da3", "question": "DACA expired?", "short_answer": "Check current policy. Rules change.", "explanation": "Consult lawyer.", "script": "What are my options?", "next_steps": ["Talk to lawyer"]}
        ],
        "raids": [
            {"id": "imm-rd1", "question": "ICE raid at work?", "short_answer": "Stay calm. Know your rights. Don't run.", "explanation": "Running makes things worse.", "script": "I'm staying silent.", "next_steps": ["Stay calm", "Stay silent"]},
            {"id": "imm-rd2", "question": "Checkpoint stopped?", "short_answer": "Answer citizenship question. Can stay silent otherwise.", "explanation": "Limited questioning at checkpoints.", "script": "Am I free to go?", "next_steps": ["Answer briefly", "Don't consent to search"]},
            {"id": "imm-rd3", "question": "Prepare for raid?", "short_answer": "Have emergency plan. Know lawyer contact. Have power of attorney for kids.", "explanation": "Be prepared.", "script": "What should I prepare?", "next_steps": ["Make plan", "Prepare documents"]}
        ]
    },
    "consumer": {
        "returns": [
            {"id": "con-rt1", "question": "Store won't take return?", "short_answer": "Check posted policy. They set their own rules.", "explanation": "No law requires returns.", "script": "What's your return policy?", "next_steps": ["Check policy", "Dispute with card"]},
            {"id": "con-rt2", "question": "No receipt?", "short_answer": "Many stores can look up purchases. Policy varies.", "explanation": "Ask about options.", "script": "Can you look up my purchase?", "next_steps": ["Ask about alternatives"]},
            {"id": "con-rt3", "question": "Final sale item broken?", "short_answer": "Defective items often still covered even if 'final sale.'", "explanation": "Defects are different.", "script": "This item was defective.", "next_steps": ["Argue defect", "Dispute charge"]},
            {"id": "con-rt4", "question": "Store credit only?", "short_answer": "Policy can specify credit only. Check before buying.", "explanation": "Their policy.", "script": "Can I get cash back?", "next_steps": ["Check policy"]}
        ],
        "warranties": [
            {"id": "con-wr1", "question": "Warranty denied?", "short_answer": "Check warranty terms. File complaint if wrongly denied.", "explanation": "Know what's covered.", "script": "This should be covered.", "next_steps": ["Check terms", "Escalate"]},
            {"id": "con-wr2", "question": "Extended warranty worth it?", "short_answer": "Often no. Credit cards sometimes include protection.", "explanation": "Do the math.", "script": "What does this cover exactly?", "next_steps": ["Read fine print", "Check card benefits"]},
            {"id": "con-wr3", "question": "Voided warranty?", "short_answer": "Must be for valid reason. FTC has right to repair rules.", "explanation": "Check if legitimate.", "script": "Why is my warranty voided?", "next_steps": ["Get explanation", "File complaint"]},
            {"id": "con-wr4", "question": "Implied warranty?", "short_answer": "Even without written warranty, products must work basically.", "explanation": "Basic protection exists.", "script": "This doesn't work as expected.", "next_steps": ["Demand fix or refund"]}
        ],
        "scams": [
            {"id": "con-sc1", "question": "Got scammed?", "short_answer": "Report to FTC. Dispute charges. Change passwords.", "explanation": "Act fast.", "script": "I need to report fraud.", "next_steps": ["Report FTC", "Dispute charges"]},
            {"id": "con-sc2", "question": "Fake product?", "short_answer": "Report to platform and FTC. Dispute charge.", "explanation": "Counterfeits are illegal.", "script": "This is counterfeit.", "next_steps": ["Report", "Dispute"]},
            {"id": "con-sc3", "question": "Prize scam?", "short_answer": "Real prizes don't require payment. It's a scam.", "explanation": "Never pay to collect.", "script": "This is a scam.", "next_steps": ["Don't pay", "Report"]},
            {"id": "con-sc4", "question": "Identify theft?", "short_answer": "Freeze credit. Report to FTC. File police report.", "explanation": "Act immediately.", "script": "My identity was stolen.", "next_steps": ["Freeze credit", "Report to FTC"]}
        ],
        "billing": [
            {"id": "con-bl1", "question": "Wrong charge on card?", "short_answer": "Dispute with card company within 60 days.", "explanation": "You have dispute rights.", "script": "I'm disputing this charge.", "next_steps": ["Dispute with card"]},
            {"id": "con-bl2", "question": "Charged twice?", "short_answer": "Contact merchant first. Then dispute with card.", "explanation": "Document everything.", "script": "I was double charged.", "next_steps": ["Contact merchant", "Dispute"]},
            {"id": "con-bl3", "question": "Charged for cancelled service?", "short_answer": "Dispute charge. Show cancellation proof.", "explanation": "Keep cancellation records.", "script": "I cancelled this service.", "next_steps": ["Show proof", "Dispute"]},
            {"id": "con-bl4", "question": "Hidden fees?", "short_answer": "May be able to challenge. Check FTC junk fee rules.", "explanation": "New rules against hidden fees.", "script": "This fee wasn't disclosed.", "next_steps": ["Complain", "Dispute"]}
        ],
        "complaints": [
            {"id": "con-cm1", "question": "Company won't help?", "short_answer": "Escalate to supervisor. Then file complaints.", "explanation": "Multiple options.", "script": "I'd like to speak to a supervisor.", "next_steps": ["Escalate", "File complaints"]},
            {"id": "con-cm2", "question": "Where to complain?", "short_answer": "BBB, FTC, state AG, CFPB for financial.", "explanation": "Multiple agencies.", "script": "I'm filing a complaint.", "next_steps": ["Choose right agency"]},
            {"id": "con-cm3", "question": "Small claims court?", "short_answer": "For smaller amounts. No lawyer needed.", "explanation": "DIY court option.", "script": "I'm taking this to small claims.", "next_steps": ["Check amount limits", "File claim"]},
            {"id": "con-cm4", "question": "Social media complaining?", "short_answer": "Often gets response. Be factual.", "explanation": "Companies watch social.", "script": "I'm posting about this.", "next_steps": ["Be truthful", "Document"]}
        ],
        "contracts": [
            {"id": "con-ct1", "question": "Cancel subscription?", "short_answer": "FTC click-to-cancel rule helps. Companies must make it easy.", "explanation": "Should be simple.", "script": "How do I cancel?", "next_steps": ["Follow process", "Document"]},
            {"id": "con-ct2", "question": "Contract auto-renewed?", "short_answer": "They must notify. Check for opt-out.", "explanation": "Should give notice.", "script": "I didn't agree to renewal.", "next_steps": ["Check notification", "Dispute"]},
            {"id": "con-ct3", "question": "Signed bad contract?", "short_answer": "Usually stuck. Some cooling off periods exist.", "explanation": "Read before signing.", "script": "What are my options?", "next_steps": ["Check for cooling off", "Negotiate"]},
            {"id": "con-ct4", "question": "Gym won't let me cancel?", "short_answer": "Many states have gym cancellation laws.", "explanation": "Check state rules.", "script": "I'm legally entitled to cancel.", "next_steps": ["Check state law", "Send certified letter"]}
        ],
        "debt": [
            {"id": "con-db1", "question": "Debt collector rights?", "short_answer": "They have limits. Can't harass, lie, or call at bad times.", "explanation": "FDCPA protects you.", "script": "Don't call again. Send in writing.", "next_steps": ["Know your rights"]},
            {"id": "con-db2", "question": "Debt not mine?", "short_answer": "Dispute in writing within 30 days.", "explanation": "They must verify.", "script": "I dispute this debt.", "next_steps": ["Dispute in writing"]},
            {"id": "con-db3", "question": "Statute of limitations?", "short_answer": "Old debt may be time-barred. Varies by state.", "explanation": "Check if collectible.", "script": "Is this within statute of limitations?", "next_steps": ["Check state law"]},
            {"id": "con-db4", "question": "Being sued for debt?", "short_answer": "Don't ignore. Respond to lawsuit or get default judgment.", "explanation": "Must respond.", "script": "I need to respond to this.", "next_steps": ["Don't ignore", "Get help"]}
        ],
        "privacy": [
            {"id": "con-pv1", "question": "Company sold my data?", "short_answer": "Some states let you opt out. Check privacy settings.", "explanation": "Rights expanding.", "script": "I want to opt out of data sharing.", "next_steps": ["Check state law", "Submit opt out"]},
            {"id": "con-pv2", "question": "Stop spam calls?", "short_answer": "Register on Do Not Call. Report violations.", "explanation": "Some protection.", "script": "Stop calling me.", "next_steps": ["Register Do Not Call", "Report"]},
            {"id": "con-pv3", "question": "Data breach notification?", "short_answer": "Companies must notify. Take steps to protect yourself.", "explanation": "They must tell you.", "script": "What data was exposed?", "next_steps": ["Freeze credit", "Change passwords"]}
        ],
        "discrimination": [
            {"id": "con-ds1", "question": "Refused service because of who I am?", "short_answer": "Discrimination in public accommodations is illegal.", "explanation": "Protected from discrimination.", "script": "Is this discrimination?", "next_steps": ["Document", "File complaint"]},
            {"id": "con-ds2", "question": "Followed in store?", "short_answer": "Racial profiling may be illegal. Document and report.", "explanation": "May be discrimination.", "script": "Why am I being followed?", "next_steps": ["Document", "Complain"]}
        ],
        "repairs": [
            {"id": "con-rp1", "question": "Bad repair job?", "short_answer": "They should fix it right. Complain and get another opinion.", "explanation": "Entitled to proper work.", "script": "This wasn't done correctly.", "next_steps": ["Demand fix", "Get second opinion"]},
            {"id": "con-rp2", "question": "Charged more than estimate?", "short_answer": "Should authorize changes. Minor increases okay, major need approval.", "explanation": "Estimates are estimates.", "script": "I only authorized the estimate amount.", "next_steps": ["Dispute excess", "Pay estimate"]},
            {"id": "con-rp3", "question": "Car held hostage for payment?", "short_answer": "Mechanics can hold car for unpaid work (mechanic's lien).", "explanation": "Legal in most cases.", "script": "What exactly am I being charged for?", "next_steps": ["Get itemized bill", "Dispute if wrong"]}
        ],
        "online": [
            {"id": "con-on1", "question": "Package never came?", "short_answer": "Contact seller. Then dispute charge.", "explanation": "Document everything.", "script": "My order never arrived.", "next_steps": ["Contact seller", "Dispute"]},
            {"id": "con-on2", "question": "Different from description?", "short_answer": "Return or dispute. Item must match listing.", "explanation": "Must be as described.", "script": "This isn't what was shown.", "next_steps": ["Return", "Dispute"]},
            {"id": "con-on3", "question": "Third party seller scam?", "short_answer": "Report to platform. Dispute charge. A-to-z guarantee if Amazon.", "explanation": "Platform protections exist.", "script": "Seller scammed me.", "next_steps": ["Report to platform", "Dispute"]}
        ]
    }
}

DEFAULT_SCRIPTS = [
    {"id": "ds1", "title": "Don't Consent", "content": "I don't consent to a search.", "category": "general"},
    {"id": "ds2", "title": "In Writing", "content": "Can I get that in writing?", "category": "general"},
    {"id": "ds3", "title": "Call Parent", "content": "I want to call my parent.", "category": "general"},
    {"id": "ds4", "title": "Lawyer", "content": "I want a lawyer.", "category": "police"},
    {"id": "ds5", "title": "Stay Silent", "content": "I'm staying silent.", "category": "police"},
    {"id": "ds6", "title": "Am I Detained?", "content": "Am I free to go?", "category": "police"},
    {"id": "ds7", "title": "Warrant", "content": "Do you have a warrant?", "category": "police"},
    {"id": "ds8", "title": "ICE Rights", "content": "I don't consent. I want a lawyer.", "category": "immigration"}
]

RESOURCES = [
    {"category": "Emergency", "items": [
        {"name": "911", "contact": "911", "description": "Emergencies"},
        {"name": "Crisis Text", "contact": "Text HOME to 741741", "description": "24/7 crisis support"},
        {"name": "988", "contact": "988", "description": "Mental health crisis"}
    ]},
    {"category": "Legal", "items": [
        {"name": "ACLU", "contact": "aclu.org", "description": "Civil liberties"},
        {"name": "LawHelp", "contact": "lawhelp.org", "description": "Free legal aid"},
        {"name": "Legal Aid", "contact": "lsc.gov", "description": "Find lawyers"}
    ]},
    {"category": "Youth", "items": [
        {"name": "Boys Town", "contact": "1-800-448-3000", "description": "Teen help"},
        {"name": "Trevor Project", "contact": "1-866-488-7386", "description": "LGBTQ+ support"}
    ]},
    {"category": "Immigration", "items": [
        {"name": "RAICES", "contact": "raicestexas.org", "description": "Immigration legal"},
        {"name": "NILC", "contact": "nilc.org", "description": "Immigrant rights"},
        {"name": "United We Dream", "contact": "unitedwedream.org", "description": "Undocumented youth"}
    ]},
    {"category": "Consumer", "items": [
        {"name": "FTC", "contact": "ftc.gov", "description": "Report scams"},
        {"name": "CFPB", "contact": "consumerfinance.gov", "description": "Financial complaints"},
        {"name": "BBB", "contact": "bbb.org", "description": "Business complaints"}
    ]}
]

US_STATES = ["Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming", "District of Columbia"]

# ROUTES
@api_router.get("/")
async def root():
    return {"message": "Know Your Rights API", "version": "4.0.0"}

@api_router.get("/categories")
async def get_categories():
    return CATEGORIES

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
