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

# ========================
# COMPREHENSIVE DATA
# ========================

CATEGORIES = [
    {
        "id": "school",
        "name": "School",
        "icon": "school",
        "color": "#3B82F6",
        "description": "Know your rights at school",
        "subcategories": [
            {"id": "searches", "name": "Searches & Privacy", "icon": "search", "color": "#3B82F6"},
            {"id": "discipline", "name": "Discipline & Suspension", "icon": "warning", "color": "#EF4444"},
            {"id": "attendance", "name": "Attendance & Timing", "icon": "time", "color": "#F59E0B"},
            {"id": "expression", "name": "Free Speech & Expression", "icon": "megaphone", "color": "#8B5CF6"},
            {"id": "administration", "name": "Teachers & Administration", "icon": "people", "color": "#10B981"},
            {"id": "personal", "name": "Personal Items & Dress", "icon": "shirt", "color": "#EC4899"}
        ]
    },
    {
        "id": "work",
        "name": "Work",
        "icon": "briefcase",
        "color": "#F97316",
        "description": "Workplace rights and protections",
        "subcategories": [
            {"id": "pay", "name": "Pay & Wages", "icon": "cash", "color": "#10B981"},
            {"id": "hours", "name": "Hours & Breaks", "icon": "time", "color": "#F97316"},
            {"id": "safety", "name": "Workplace Safety", "icon": "shield-checkmark", "color": "#EF4444"},
            {"id": "harassment", "name": "Harassment & Discrimination", "icon": "alert-circle", "color": "#DC2626"},
            {"id": "firing", "name": "Firing & Quitting", "icon": "exit", "color": "#6B7280"},
            {"id": "privacy", "name": "Privacy at Work", "icon": "eye-off", "color": "#8B5CF6"}
        ]
    },
    {
        "id": "housing",
        "name": "Housing",
        "icon": "home",
        "color": "#10B981",
        "description": "Tenant and renter rights",
        "subcategories": [
            {"id": "entry", "name": "Landlord Entry", "icon": "key", "color": "#F97316"},
            {"id": "repairs", "name": "Repairs & Conditions", "icon": "construct", "color": "#3B82F6"},
            {"id": "eviction", "name": "Eviction & Moving", "icon": "log-out", "color": "#EF4444"},
            {"id": "deposits", "name": "Security Deposits", "icon": "cash", "color": "#10B981"},
            {"id": "lease", "name": "Lease & Rent", "icon": "document-text", "color": "#8B5CF6"},
            {"id": "roommates", "name": "Roommates & Guests", "icon": "people", "color": "#EC4899"}
        ]
    },
    {
        "id": "police",
        "name": "Police Interaction",
        "icon": "shield",
        "color": "#EF4444",
        "description": "Know your rights with law enforcement",
        "subcategories": [
            {"id": "stops", "name": "Being Stopped", "icon": "hand-left", "color": "#F97316"},
            {"id": "searches", "name": "Searches", "icon": "search", "color": "#EF4444"},
            {"id": "arrests", "name": "Arrests & Detention", "icon": "lock-closed", "color": "#DC2626"},
            {"id": "rights", "name": "Your Rights", "icon": "shield-checkmark", "color": "#3B82F6"},
            {"id": "recording", "name": "Recording Police", "icon": "videocam", "color": "#8B5CF6"},
            {"id": "complaints", "name": "Complaints & Misconduct", "icon": "document-text", "color": "#6B7280"}
        ]
    },
    {
        "id": "online",
        "name": "Online Privacy",
        "icon": "lock",
        "color": "#8B5CF6",
        "description": "Digital privacy and safety",
        "subcategories": [
            {"id": "social", "name": "Social Media", "icon": "share-social", "color": "#3B82F6"},
            {"id": "data", "name": "Data & Tracking", "icon": "analytics", "color": "#10B981"},
            {"id": "harassment", "name": "Online Harassment", "icon": "alert-circle", "color": "#EF4444"},
            {"id": "photos", "name": "Photos & Images", "icon": "images", "color": "#EC4899"},
            {"id": "accounts", "name": "Accounts & Passwords", "icon": "key", "color": "#F97316"},
            {"id": "school-monitoring", "name": "School Monitoring", "icon": "eye", "color": "#6B7280"}
        ]
    },
    {
        "id": "public",
        "name": "Public Spaces",
        "icon": "map-pin",
        "color": "#14B8A6",
        "description": "Rights in public areas",
        "subcategories": [
            {"id": "filming", "name": "Photography & Filming", "icon": "camera", "color": "#3B82F6"},
            {"id": "protests", "name": "Protests & Assembly", "icon": "megaphone", "color": "#EF4444"},
            {"id": "stores", "name": "Stores & Businesses", "icon": "storefront", "color": "#F97316"},
            {"id": "transport", "name": "Transportation", "icon": "bus", "color": "#10B981"},
            {"id": "parks", "name": "Parks & Public Property", "icon": "leaf", "color": "#14B8A6"},
            {"id": "curfew", "name": "Curfews & Loitering", "icon": "moon", "color": "#8B5CF6"}
        ]
    }
]

# ========================
# COMPREHENSIVE SCENARIOS
# ========================

SCENARIOS = {
    # ==================== SCHOOL ====================
    "school": {
        "searches": [
            {
                "id": "school-phone-search",
                "question": "Can my school search my phone?",
                "short_answer": "They need reasonable suspicion. You can ask to call a parent first.",
                "explanation": "Schools need 'reasonable suspicion' you broke a rule before searching your phone. They can't randomly search everyone's phones. The search should be related to what they suspect.",
                "script": "I'd like to speak with my parent/guardian before allowing a search of my personal device.",
                "next_steps": ["Stay calm and be respectful", "Ask why they want to search", "Request to call a parent", "Document what happened"]
            },
            {
                "id": "school-locker-search",
                "question": "Can my school search my locker?",
                "short_answer": "Usually yes. Lockers are typically school property.",
                "explanation": "Most schools own the lockers and can search them. However, your personal belongings inside may have more protection. Check your student handbook for the policy.",
                "script": "I understand you need to check. May I ask what prompted this search?",
                "next_steps": ["Cooperate calmly", "Note any witnesses", "Ask for the policy in writing", "Tell a parent afterward"]
            },
            {
                "id": "school-bag-search",
                "question": "Can they search my backpack or purse?",
                "short_answer": "Only with reasonable suspicion that you broke a specific rule.",
                "explanation": "Your personal bags have more privacy protection than lockers. They need a real reason to suspect you specifically, not just a general search of everyone.",
                "script": "Can you tell me what specific rule I'm suspected of breaking before searching my personal belongings?",
                "next_steps": ["Ask for the specific reason", "Stay calm", "Don't consent but don't resist physically", "Document everything"]
            },
            {
                "id": "school-car-search",
                "question": "Can school search my car in the parking lot?",
                "short_answer": "Generally yes, if parked on school property. You agreed to this by parking there.",
                "explanation": "Most schools require you to consent to vehicle searches as a condition of parking on campus. Check your parking permit agreement.",
                "script": "I'd like to understand what led to this search. Can I see the parking policy I signed?",
                "next_steps": ["Review your parking agreement", "Ask about suspicion", "Have a witness present", "Document the search"]
            },
            {
                "id": "school-strip-search",
                "question": "Can school officials strip search me?",
                "short_answer": "Almost never. This is extremely rare and requires very serious circumstances.",
                "explanation": "Strip searches by school officials are almost always unconstitutional. The Supreme Court ruled schools need VERY strong reasons and must protect your dignity.",
                "script": "I do not consent to this. I want to call my parents and a lawyer immediately.",
                "next_steps": ["Firmly say no", "Demand to call parents", "This is serious - get legal help", "File a complaint"]
            }
        ],
        "discipline": [
            {
                "id": "school-suspension-process",
                "question": "What happens if I'm suspended?",
                "short_answer": "You should get notice of charges and a chance to explain your side.",
                "explanation": "For short suspensions (under 10 days), you're entitled to know what you're accused of and explain your side. Longer suspensions require more formal hearings.",
                "script": "I'd like to understand exactly what I'm being accused of and share my side of the story.",
                "next_steps": ["Listen to the charges", "Ask for evidence", "Tell your side calmly", "Get everything in writing"]
            },
            {
                "id": "school-expulsion",
                "question": "Can they expel me? What are my rights?",
                "short_answer": "Expulsion requires a formal hearing where you can present your case.",
                "explanation": "Expulsion is serious. You have the right to a hearing, to bring witnesses, sometimes to have a lawyer, and to appeal the decision.",
                "script": "I'd like to request a formal hearing and understand the appeals process.",
                "next_steps": ["Request formal hearing", "Gather witnesses", "Consider getting a lawyer", "Prepare your defense"]
            },
            {
                "id": "school-detention-rights",
                "question": "Do I have to stay for detention?",
                "short_answer": "Generally yes, but parents should be notified and you can't miss essential needs.",
                "explanation": "Schools can require detention, but they should notify parents, especially for after-school detention. You should still be able to eat, use restroom, etc.",
                "script": "I understand I have detention. Can you make sure my parents are notified about the time?",
                "next_steps": ["Confirm parents know", "Ask about transportation", "Complete the detention", "Learn from the situation"]
            },
            {
                "id": "school-punishment-fairness",
                "question": "Is my punishment fair compared to others?",
                "short_answer": "Punishments should be consistent. Discrimination is illegal.",
                "explanation": "Schools can't punish you more harshly because of race, gender, disability, or other protected characteristics. If you notice a pattern of unfairness, document it.",
                "script": "I'm concerned this punishment isn't consistent with how similar situations are handled. Can we discuss this?",
                "next_steps": ["Document similar cases", "Compare punishments", "Talk to counselor", "File complaint if needed"]
            },
            {
                "id": "school-appeal-decision",
                "question": "Can I appeal a school decision?",
                "short_answer": "Yes, most schools have an appeals process for serious decisions.",
                "explanation": "You can usually appeal suspensions, expulsions, and other major decisions. Ask for the appeals process in writing and follow it carefully.",
                "script": "I'd like to appeal this decision. Can you provide me with the appeals process and timeline?",
                "next_steps": ["Get process in writing", "Meet all deadlines", "Gather supporting evidence", "Consider getting help"]
            },
            {
                "id": "school-zero-tolerance",
                "question": "What if my school has a 'zero tolerance' policy?",
                "short_answer": "You still have due process rights, even with zero tolerance policies.",
                "explanation": "Zero tolerance doesn't mean zero rights. You're still entitled to explain your side and the punishment should fit what actually happened.",
                "script": "I understand the policy, but I'd like the opportunity to explain the circumstances of what happened.",
                "next_steps": ["Explain the context", "Ask about exceptions", "Involve parents", "Appeal if unfair"]
            }
        ],
        "attendance": [
            {
                "id": "school-late-consequences",
                "question": "What can happen if I'm late to school?",
                "short_answer": "Consequences vary but usually start small and increase with repeated tardiness.",
                "explanation": "Schools track tardiness. Consequences typically escalate from warnings to detention to parent meetings. Excessive tardiness can affect grades or lead to truancy issues.",
                "script": "I know I've been late. Can we discuss what's causing it and find a solution?",
                "next_steps": ["Be honest about reasons", "Ask about accommodations", "Set up a plan", "Follow through"]
            },
            {
                "id": "school-absence-excuses",
                "question": "What counts as an excused absence?",
                "short_answer": "Illness, family emergencies, religious observances, and sometimes mental health days.",
                "explanation": "Policies vary by school and state. Generally: illness (with parent note or doctor note), family emergencies, religious holidays, and court appearances are excused.",
                "script": "I need to be absent for [reason]. What documentation do you need for an excused absence?",
                "next_steps": ["Check school policy", "Get proper documentation", "Submit in time", "Make up missed work"]
            },
            {
                "id": "school-leave-early",
                "question": "Can I leave school early?",
                "short_answer": "Usually only with parent permission and signing out through the office.",
                "explanation": "Schools are responsible for you during school hours. Leaving requires parent/guardian permission, usually a note or call to the office.",
                "script": "I need to leave early today. My parent has contacted the office. What's the sign-out process?",
                "next_steps": ["Have parent notify school", "Go to the office", "Sign out properly", "Get any missed assignments"]
            },
            {
                "id": "school-truancy-laws",
                "question": "What happens if I skip school a lot?",
                "short_answer": "Truancy can lead to school consequences, parent fines, or even court involvement.",
                "explanation": "States have compulsory attendance laws. Excessive absences can trigger truancy proceedings, which may involve social workers, fines for parents, or juvenile court.",
                "script": "I'm struggling with attendance. Can I meet with a counselor to discuss what's going on and get help?",
                "next_steps": ["Talk to a counselor", "Address underlying issues", "Create attendance plan", "Know your state's laws"]
            },
            {
                "id": "school-mental-health-days",
                "question": "Can I take a mental health day?",
                "short_answer": "Some states now allow mental health as an excused absence.",
                "explanation": "More states are recognizing mental health days as valid absences. Check your state law and school policy. Even where not official, parents can often excuse you for 'illness.'",
                "script": "I'm not doing well mentally and need a day to recover. Can my parent excuse me for health reasons?",
                "next_steps": ["Talk to your parent", "Check state/school policy", "Get proper documentation", "Seek help if ongoing"]
            }
        ],
        "expression": [
            {
                "id": "school-free-speech",
                "question": "Do I have free speech at school?",
                "short_answer": "Yes, but it's more limited than outside school. Can't substantially disrupt learning.",
                "explanation": "The Supreme Court said students don't 'shed their constitutional rights at the schoolhouse gate.' But speech that substantially disrupts school can be limited.",
                "script": "I believe this is protected expression that isn't disrupting school. Can we discuss why it's being restricted?",
                "next_steps": ["Stay peaceful", "Understand the limits", "Document restrictions", "Seek help if censored unfairly"]
            },
            {
                "id": "school-protest-rights",
                "question": "Can I organize a protest at school?",
                "short_answer": "You can express views, but schools may regulate time, place, and manner.",
                "explanation": "Walkouts and protests are often protected, but you may face consequences for missing class. Schools can require protests happen during non-class time.",
                "script": "We'd like to organize a peaceful demonstration. What are the guidelines for doing this appropriately?",
                "next_steps": ["Know consequences first", "Keep it peaceful", "Consider timing", "Have clear message"]
            },
            {
                "id": "school-social-media",
                "question": "Can I get in trouble for social media posts?",
                "short_answer": "Usually no for off-campus posts, unless they cause substantial disruption at school.",
                "explanation": "Recent Supreme Court ruling (2021) limits schools' ability to punish off-campus speech. But threats, severe bullying, or posts causing major disruption can still have consequences.",
                "script": "This was posted off-campus and doesn't disrupt school. Why am I being disciplined for it?",
                "next_steps": ["Know the recent law", "Document the post", "Get legal help if needed", "Be careful online anyway"]
            },
            {
                "id": "school-newspaper-censorship",
                "question": "Can the school censor the student newspaper?",
                "short_answer": "It depends on whether it's a 'public forum' and your state's laws.",
                "explanation": "Schools have more control over school-sponsored publications. But many states have laws protecting student press freedom. Know your state's Student Press Law.",
                "script": "Is our publication considered a public forum? I'd like to understand why this content is being restricted.",
                "next_steps": ["Check state press laws", "Document censorship", "Contact Student Press Law Center", "Know your publication type"]
            },
            {
                "id": "school-clothing-message",
                "question": "Can I wear clothing with political messages?",
                "short_answer": "Generally yes, unless it's vulgar, promotes drugs, or substantially disrupts school.",
                "explanation": "The Tinker case protected students wearing black armbands. Political messages are usually protected unless they cause real disruption or contain unprotected content.",
                "script": "My clothing has a peaceful political message. Can you explain what school policy it violates?",
                "next_steps": ["Know dress code", "Keep messages appropriate", "Document any restrictions", "Advocate for change"]
            },
            {
                "id": "school-religious-expression",
                "question": "Can I express my religion at school?",
                "short_answer": "Yes! Students can pray, wear religious items, and discuss faith.",
                "explanation": "Schools can't promote religion, but students CAN practice their faith. You can pray, wear religious clothing/symbols, form religious clubs, and discuss beliefs.",
                "script": "I believe this is protected religious expression. The school isn't endorsing it - I'm personally practicing my faith.",
                "next_steps": ["Know your rights", "Be respectful of others", "Join or form religious club", "Report discrimination"]
            }
        ],
        "administration": [
            {
                "id": "school-grade-dispute",
                "question": "Can I dispute a grade I think is unfair?",
                "short_answer": "Yes, there's usually a process to discuss and appeal grades.",
                "explanation": "Start by talking to the teacher. If unresolved, go to the department head, then administration. Keep records of your work and communications.",
                "script": "I'd like to discuss my grade on this assignment. I believe there may have been an error or I'd like to understand the grading better.",
                "next_steps": ["Talk to teacher first", "Bring evidence", "Follow chain of command", "Document everything"]
            },
            {
                "id": "school-teacher-conflict",
                "question": "What if a teacher treats me unfairly?",
                "short_answer": "Document incidents, talk to counselor or administrator, and involve parents if needed.",
                "explanation": "Teachers should treat all students fairly. If you experience unfair treatment, especially if discriminatory, report it through proper channels.",
                "script": "I'm experiencing some difficulties in this class and would like to discuss them with a counselor or administrator.",
                "next_steps": ["Document specific incidents", "Talk to counselor", "Involve parents", "File formal complaint if needed"]
            },
            {
                "id": "school-bullying-report",
                "question": "How do I report bullying?",
                "short_answer": "Tell an adult you trust - teacher, counselor, or administrator. Most schools must investigate.",
                "explanation": "Schools are required to address bullying, especially if based on race, disability, sex, or other protected characteristics. Keep records and follow up.",
                "script": "I need to report bullying. I have documentation and I'd like to understand the investigation process.",
                "next_steps": ["Document incidents", "Report to trusted adult", "Follow up on investigation", "Seek support"]
            },
            {
                "id": "school-iep-rights",
                "question": "What are my rights with an IEP or 504 plan?",
                "short_answer": "Schools MUST follow your plan. You have strong legal protections.",
                "explanation": "IEPs and 504 plans are legal documents. Schools must provide the accommodations listed. If they don't, you can file complaints with the district or federal government.",
                "script": "I have an IEP/504 plan that requires [accommodation]. This isn't being provided. How can we fix this?",
                "next_steps": ["Know your plan", "Document non-compliance", "Request IEP meeting", "File complaint if needed"]
            },
            {
                "id": "school-counselor-access",
                "question": "Can I see the school counselor whenever I want?",
                "short_answer": "Generally yes, especially for urgent issues. You have a right to mental health support.",
                "explanation": "Counselors are there to help. For urgent issues, you should be able to see them quickly. For ongoing support, there may be a scheduling system.",
                "script": "I need to speak with a counselor about something important. Is one available now or when can I schedule?",
                "next_steps": ["Ask to see counselor", "Use urgent words if needed", "Follow up", "Know crisis resources"]
            },
            {
                "id": "school-records-access",
                "question": "Can I see my school records?",
                "short_answer": "Yes, you and your parents have the right to see and request changes to your records.",
                "explanation": "Under FERPA, parents (and students 18+) can review educational records, request corrections, and control who sees them.",
                "script": "I'd like to review my educational records. What's the process for requesting access?",
                "next_steps": ["Submit written request", "Review within 45 days", "Request corrections if needed", "Know your FERPA rights"]
            }
        ],
        "personal": [
            {
                "id": "school-phone-use",
                "question": "Can school take my phone during the day?",
                "short_answer": "Many schools can restrict phone use during class, but complete confiscation policies vary.",
                "explanation": "Schools can set phone policies for educational reasons. Some collect phones at start of day, others just ban use during class. Check your school's specific policy.",
                "script": "I understand the phone policy. When will my phone be returned and is it stored securely?",
                "next_steps": ["Know school policy", "Follow the rules", "Ask about secure storage", "Retrieve promptly"]
            },
            {
                "id": "school-dress-code",
                "question": "Is my school's dress code legal?",
                "short_answer": "Dress codes are generally legal, but can't discriminate based on gender, race, or religion.",
                "explanation": "Schools can have dress codes, but they can't target specific groups unfairly, must allow religious expression, and shouldn't be sexist.",
                "script": "I'm concerned this dress code rule is being applied unfairly or may be discriminatory. Can we discuss this?",
                "next_steps": ["Read the full code", "Document unequal enforcement", "Advocate for change", "File complaint if discriminatory"]
            },
            {
                "id": "school-medication",
                "question": "Can I carry my own medication?",
                "short_answer": "Usually only with proper documentation. Some exceptions for emergency meds like inhalers or EpiPens.",
                "explanation": "Schools typically require medications be kept in the nurse's office. Exceptions often exist for emergency medications. Check your school's policy.",
                "script": "I need to carry my medication for medical reasons. What paperwork is required to allow this?",
                "next_steps": ["Get doctor documentation", "Complete school forms", "Know where nurse is", "Train on emergency meds"]
            },
            {
                "id": "school-hair-rules",
                "question": "Can school dictate my hairstyle?",
                "short_answer": "Increasingly, laws protect natural hairstyles. Discrimination based on hair is often illegal.",
                "explanation": "The CROWN Act and similar laws in many states protect natural hairstyles associated with race. Schools can't ban braids, locs, twists, etc.",
                "script": "I believe policies restricting my natural hairstyle may be discriminatory. Can we discuss this?",
                "next_steps": ["Know your state's laws", "Document the policy", "Cite CROWN Act if applicable", "File complaint if needed"]
            },
            {
                "id": "school-bathroom-access",
                "question": "What are my bathroom access rights?",
                "short_answer": "You have a right to use the bathroom. Restrictive policies can be challenged.",
                "explanation": "While schools can have hall pass systems, overly restrictive bathroom policies can be challenged, especially if they affect health. Trans students have rights to appropriate bathrooms too.",
                "script": "I need to use the bathroom and it's affecting my health/learning. Can we discuss reasonable access?",
                "next_steps": ["Know the policy", "Get medical documentation if needed", "Talk to counselor", "File complaint if denied"]
            },
            {
                "id": "school-gender-identity",
                "question": "What are my rights as an LGBTQ+ student?",
                "short_answer": "You have rights to express your identity, form clubs, and be free from harassment.",
                "explanation": "LGBTQ+ students are protected from discrimination and harassment. You can form GSA clubs, be out, and be called by your chosen name/pronouns in many places.",
                "script": "I want to be addressed by my correct name and pronouns. What steps do I need to take?",
                "next_steps": ["Know your state's protections", "Talk to counselor", "Update records if possible", "Report discrimination"]
            }
        ]
    },
    
    # ==================== WORK ====================
    "work": {
        "pay": [
            {
                "id": "work-minimum-wage",
                "question": "Am I being paid enough?",
                "short_answer": "You must be paid at least minimum wage (federal or state, whichever is higher).",
                "explanation": "Federal minimum is $7.25/hr, but many states/cities are higher. Some exceptions exist for tipped workers, but total must equal minimum wage.",
                "script": "Can you clarify my hourly rate and any deductions? I want to make sure I'm receiving proper wages.",
                "next_steps": ["Check your state's minimum wage", "Review your pay stubs", "Calculate your hours", "Report violations"]
            },
            {
                "id": "work-unpaid-time",
                "question": "Can my boss make me work off the clock?",
                "short_answer": "No. If you're hourly, you must be paid for ALL time worked.",
                "explanation": "Working 'off the clock' is illegal for hourly workers. This includes time before/after shifts, working through breaks, or any tasks for the employer.",
                "script": "I want to make sure I'm logging all my work hours correctly. Can you clarify the policy on clock-in times?",
                "next_steps": ["Track all your hours", "Document unpaid time", "Ask for policy in writing", "Report to labor department"]
            },
            {
                "id": "work-overtime-pay",
                "question": "When do I get overtime pay?",
                "short_answer": "Non-exempt workers get overtime (1.5x) after 40 hours per week.",
                "explanation": "Federal law requires overtime pay for non-exempt workers over 40 hours/week. Some states require daily overtime too. Salary doesn't automatically mean no overtime.",
                "script": "I've worked over 40 hours this week. Can you confirm overtime will be included in my pay?",
                "next_steps": ["Track hours carefully", "Know if you're exempt", "Check state laws", "Ask about overtime policy"]
            },
            {
                "id": "work-paycheck-deductions",
                "question": "Can my boss take money from my paycheck?",
                "short_answer": "Only with your written permission or as required by law (taxes, etc.).",
                "explanation": "Employers can deduct taxes and court-ordered amounts. Other deductions (uniforms, shortages) usually require written consent and can't drop you below minimum wage.",
                "script": "I noticed a deduction I didn't authorize. Can you explain what this is and provide documentation?",
                "next_steps": ["Review pay stubs", "Ask about deductions", "Get authorization in writing", "Report illegal deductions"]
            },
            {
                "id": "work-tips",
                "question": "Can my employer take my tips?",
                "short_answer": "No, tips belong to you. Tip pooling rules vary by state.",
                "explanation": "Employers cannot keep your tips. Tip pooling (sharing with other staff) is allowed in some situations. Managers generally can't participate in tip pools.",
                "script": "I'd like to understand the tip policy here. How are tips distributed and who participates in the pool?",
                "next_steps": ["Know your state's tip laws", "Track your tips", "Document any violations", "Report to labor department"]
            },
            {
                "id": "work-bounced-paycheck",
                "question": "What if my paycheck bounces?",
                "short_answer": "This is illegal. Your employer must pay you for work performed.",
                "explanation": "Employers must pay wages earned. Bounced paychecks may entitle you to additional penalties. Document everything and file a complaint.",
                "script": "My paycheck did not clear. When will I receive my wages and any associated fees?",
                "next_steps": ["Document the bounced check", "Notify employer in writing", "File wage complaint", "Consider legal action"]
            }
        ],
        "hours": [
            {
                "id": "work-break-rights",
                "question": "Am I entitled to breaks?",
                "short_answer": "It depends on your state. Many states require meal and rest breaks.",
                "explanation": "Federal law doesn't require breaks, but many states do. Common: 10-min break every 4 hours, 30-min meal break for 6+ hour shifts. Know your state's law.",
                "script": "I'd like to understand my break schedule. What does our policy say about rest and meal breaks?",
                "next_steps": ["Look up state break laws", "Check company policy", "Document denied breaks", "Report violations"]
            },
            {
                "id": "work-schedule-changes",
                "question": "Can my boss change my schedule last minute?",
                "short_answer": "Usually yes, unless you have a contract or work in a city with predictive scheduling laws.",
                "explanation": "Most workers are 'at-will' and schedules can change. But some cities require advance notice of schedules. Check if predictive scheduling laws apply to you.",
                "script": "I received very short notice about this schedule change. What is the policy on schedule changes?",
                "next_steps": ["Check for local laws", "Ask about notice policy", "Document changes", "Advocate for better policies"]
            },
            {
                "id": "work-refuse-overtime",
                "question": "Can I refuse to work overtime?",
                "short_answer": "Usually your employer can require overtime, but you must be paid for it.",
                "explanation": "In most cases, employers can mandate overtime. However, you must be paid overtime rates. Some exceptions exist for certain industries or union contracts.",
                "script": "I understand overtime may be required. Can you confirm the overtime rate and if there are any limits on required overtime?",
                "next_steps": ["Know your rights", "Ensure proper pay", "Check union contract", "Document excessive hours"]
            },
            {
                "id": "work-closing-shift",
                "question": "Can I be made to stay late after my shift ends?",
                "short_answer": "You must be paid for all time worked, including staying late.",
                "explanation": "If your employer requires you to stay, you must be paid. Clock out when you actually leave, not your scheduled end time.",
                "script": "I need to stay late tonight. I'll make sure to clock out when I actually leave. Is that correct?",
                "next_steps": ["Always clock all time", "Document late stays", "Know overtime rules", "Report unpaid time"]
            },
            {
                "id": "work-minor-hours",
                "question": "How many hours can I work as a minor?",
                "short_answer": "Strict limits exist. Generally 3 hrs on school days, 18 hrs in school week for under 16.",
                "explanation": "Federal and state laws limit hours for workers under 18. Rules differ by age and whether school is in session. Know your specific limits.",
                "script": "I want to make sure my schedule complies with labor laws for minors. Can you verify my hours?",
                "next_steps": ["Know your state's rules", "Track your hours", "Speak up if exceeded", "Report violations"]
            }
        ],
        "safety": [
            {
                "id": "work-unsafe-conditions",
                "question": "What if my workplace is unsafe?",
                "short_answer": "You have the right to a safe workplace. Report hazards and refuse extremely dangerous work.",
                "explanation": "OSHA requires employers to provide safe conditions. You can report hazards anonymously and cannot be retaliated against for reporting.",
                "script": "I'm concerned about a safety issue. Who should I report this to, and how is it documented?",
                "next_steps": ["Document the hazard", "Report to supervisor", "File OSHA complaint if ignored", "Know your rights against retaliation"]
            },
            {
                "id": "work-injury",
                "question": "What if I get hurt at work?",
                "short_answer": "Report it immediately. You may be entitled to workers' compensation.",
                "explanation": "Report injuries right away, even if minor. Workers' comp covers medical bills and lost wages. You don't have to prove your employer was at fault.",
                "script": "I was injured at work. I need to report this and understand the workers' compensation process.",
                "next_steps": ["Report immediately", "Get medical care", "Document everything", "File workers' comp claim"]
            },
            {
                "id": "work-protective-equipment",
                "question": "Who pays for safety equipment?",
                "short_answer": "Employers must provide and pay for required safety equipment.",
                "explanation": "OSHA requires employers to provide personal protective equipment (PPE) free of charge. This includes gloves, goggles, hard hats, etc.",
                "script": "I need proper safety equipment for this job. When will this be provided?",
                "next_steps": ["Request needed equipment", "Document the request", "Know what's required", "Report if denied"]
            },
            {
                "id": "work-dangerous-task",
                "question": "Can I refuse a dangerous task?",
                "short_answer": "You can refuse work that poses imminent danger with no reasonable alternative.",
                "explanation": "You have limited rights to refuse dangerous work. The danger must be immediate and serious, and you must have tried to get it fixed first.",
                "script": "I believe this task poses serious danger and I'd like to discuss alternatives or safety measures.",
                "next_steps": ["Explain your concerns", "Ask for alternatives", "Document the situation", "Know your rights"]
            }
        ],
        "harassment": [
            {
                "id": "work-sexual-harassment",
                "question": "What is sexual harassment?",
                "short_answer": "Unwelcome sexual advances, requests for favors, or conduct of a sexual nature that affects your job.",
                "explanation": "Sexual harassment includes unwanted touching, comments, jokes, requests for dates after saying no, quid pro quo ('do this or else'), and hostile environment.",
                "script": "I need to report harassment. What is the process for filing a complaint and what protections do I have?",
                "next_steps": ["Document incidents", "Report to HR", "File EEOC complaint", "Know anti-retaliation laws"]
            },
            {
                "id": "work-discrimination",
                "question": "What if I'm treated differently because of who I am?",
                "short_answer": "Discrimination based on protected characteristics is illegal.",
                "explanation": "You're protected from discrimination based on race, color, religion, sex, national origin, age (40+), disability, and in many places sexual orientation and gender identity.",
                "script": "I'm concerned about discriminatory treatment. I'd like to file a formal complaint.",
                "next_steps": ["Document everything", "Report to HR", "File EEOC complaint", "Know your state's protections"]
            },
            {
                "id": "work-hostile-environment",
                "question": "What makes a 'hostile work environment'?",
                "short_answer": "Severe or pervasive harassment that makes it hard to do your job.",
                "explanation": "A hostile environment is created by harassment so severe or frequent that it interferes with your work. One bad joke isn't enough; ongoing patterns or extreme incidents are.",
                "script": "The ongoing behavior I'm experiencing is affecting my ability to work. I need to report this.",
                "next_steps": ["Keep detailed records", "Report to management", "File formal complaint", "Consult with attorney"]
            },
            {
                "id": "work-retaliation",
                "question": "Can I be punished for reporting harassment?",
                "short_answer": "No. Retaliation for reporting is illegal.",
                "explanation": "It's illegal to fire, demote, or punish someone for reporting harassment or discrimination, even if the complaint doesn't pan out.",
                "script": "I'm concerned about potential retaliation for my complaint. What protections are in place?",
                "next_steps": ["Document any changes", "Report retaliation too", "File with EEOC", "Know it's illegal"]
            }
        ],
        "firing": [
            {
                "id": "work-wrongful-termination",
                "question": "Can I be fired for any reason?",
                "short_answer": "In most states, yes ('at-will'), but not for illegal reasons like discrimination or retaliation.",
                "explanation": "Most workers are 'at-will,' meaning either party can end employment. But firing for discrimination, retaliation, or refusing to break the law is illegal.",
                "script": "I'd like to understand why I'm being terminated and receive documentation of the reason.",
                "next_steps": ["Ask for reason in writing", "Review for illegal reasons", "File complaint if discriminatory", "Apply for unemployment"]
            },
            {
                "id": "work-final-paycheck",
                "question": "When do I get my final paycheck?",
                "short_answer": "Depends on state law. Some require immediate payment, others by next regular payday.",
                "explanation": "State laws vary. Some require final pay within 24-72 hours. Others allow until the next regular payday. Owed wages must always be paid.",
                "script": "When will I receive my final paycheck, including any unused vacation time?",
                "next_steps": ["Know state law", "Get it in writing", "Verify all wages included", "File complaint if unpaid"]
            },
            {
                "id": "work-unemployment",
                "question": "Can I get unemployment if I'm fired?",
                "short_answer": "Usually yes, unless fired for serious misconduct.",
                "explanation": "You can generally get unemployment if laid off or fired for performance. Fired for theft, violence, or gross misconduct may disqualify you.",
                "script": "I'd like to apply for unemployment benefits. Can you provide my separation information?",
                "next_steps": ["Apply quickly", "Document your separation", "Appeal if denied", "Know what disqualifies you"]
            },
            {
                "id": "work-quitting-notice",
                "question": "Do I have to give two weeks notice?",
                "short_answer": "Usually no, it's just a courtesy. But check your contract.",
                "explanation": "Two weeks notice is professional courtesy, not legal requirement for most workers. But some contracts may require it.",
                "script": "I'm submitting my resignation. My last day will be [date]. What is the process for transitioning my duties?",
                "next_steps": ["Check your contract", "Give notice if possible", "Get job reference", "Confirm final pay"]
            }
        ],
        "privacy": [
            {
                "id": "work-email-monitoring",
                "question": "Can my boss read my work emails?",
                "short_answer": "Yes, employers generally can monitor company email and devices.",
                "explanation": "Emails sent on company systems are usually not private. Assume anything on work devices can be seen. Use personal devices/email for private matters.",
                "script": "I'd like to understand the company's policy on email and device monitoring.",
                "next_steps": ["Read the policy", "Use personal devices for personal stuff", "Don't expect privacy", "Be professional"]
            },
            {
                "id": "work-drug-test",
                "question": "Can I be drug tested?",
                "short_answer": "Often yes, especially for hiring or safety-sensitive jobs. Laws vary by state.",
                "explanation": "Drug testing laws vary. Many employers can test during hiring. Random testing is more restricted. Some states have protections for marijuana use.",
                "script": "I'd like to understand the drug testing policy, including what's tested for and the process.",
                "next_steps": ["Know state laws", "Ask about policy", "Know your rights", "Be aware of implications"]
            },
            {
                "id": "work-social-media-firing",
                "question": "Can I be fired for social media posts?",
                "short_answer": "Often yes, especially for posts that affect the company. Some activities are protected.",
                "explanation": "Private employers can usually fire for social media posts. But discussing wages, working conditions, or union activity is often protected.",
                "script": "I'd like to understand which of my social media activities might affect my employment.",
                "next_steps": ["Know what's protected", "Review company policy", "Be careful online", "Know NLRA protections"]
            },
            {
                "id": "work-background-check",
                "question": "Can employers check my criminal history?",
                "short_answer": "Usually yes, but 'ban the box' laws limit when they can ask and consider it.",
                "explanation": "Many places have 'ban the box' laws requiring employers to wait until later in hiring to ask about criminal history. They must also consider if it's relevant to the job.",
                "script": "I'd like to understand how criminal history is considered in hiring decisions here.",
                "next_steps": ["Know your state's laws", "Be honest when asked", "Explain rehabilitation", "Know your rights"]
            }
        ]
    },
    
    # ==================== HOUSING ====================
    "housing": {
        "entry": [
            {
                "id": "housing-notice-required",
                "question": "Can my landlord enter without notice?",
                "short_answer": "Usually no. Most states require 24-48 hours notice except for emergencies.",
                "explanation": "Tenants have a right to 'quiet enjoyment.' Landlords must give advance notice (often 24-48 hours) before entering, except for true emergencies.",
                "script": "I'd appreciate proper notice before any entry as required by law. Can we agree on how that will work?",
                "next_steps": ["Check state/local law", "Review lease", "Document unauthorized entries", "Send written request"]
            },
            {
                "id": "housing-emergency-entry",
                "question": "What counts as an emergency entry?",
                "short_answer": "Fire, flooding, gas leak, or other immediate dangers. Not routine matters.",
                "explanation": "True emergencies that risk life or property damage. A repair that can wait is not an emergency. Your landlord wanting to 'check' something is not an emergency.",
                "script": "I don't believe this situation qualifies as an emergency. I'd like proper notice for non-emergency entry.",
                "next_steps": ["Know what's truly emergency", "Document any entry", "Report abuse", "Assert your rights"]
            },
            {
                "id": "housing-change-locks",
                "question": "Can I change my locks?",
                "short_answer": "Usually yes, but you may need to provide the landlord a key. Check your lease.",
                "explanation": "You generally can change locks for safety, but may need to give landlord a copy. Some leases prohibit it. For domestic violence, special protections often apply.",
                "script": "I'd like to change my locks for safety reasons. What is the policy and do I need to provide a key?",
                "next_steps": ["Check your lease", "Provide key if required", "Document safety concerns", "Know DV protections"]
            },
            {
                "id": "housing-showing-apartment",
                "question": "Can landlord show my apartment while I live there?",
                "short_answer": "Yes, but with proper notice. You don't have to be there.",
                "explanation": "Landlords can show your unit to prospective tenants or buyers, but must give proper notice. You can request reasonable times.",
                "script": "I'm happy to accommodate showings with proper notice. Can we agree on reasonable times?",
                "next_steps": ["Know notice requirements", "Suggest convenient times", "Secure valuables", "Document excessive showings"]
            }
        ],
        "repairs": [
            {
                "id": "housing-repair-request",
                "question": "My landlord won't fix something. What can I do?",
                "short_answer": "Put requests in writing. You may have options like rent withholding or repair-and-deduct.",
                "explanation": "Landlords must maintain habitable conditions. Document requests in writing. If ignored, you may have legal remedies depending on your state.",
                "script": "I've reported this issue on [date]. Can you provide a timeline for repairs? I'd like this in writing.",
                "next_steps": ["Request in writing", "Document with photos", "Know your state's options", "Contact code enforcement"]
            },
            {
                "id": "housing-heat-hot-water",
                "question": "I have no heat or hot water. What are my rights?",
                "short_answer": "This is a habitability issue. Landlord must fix it quickly or face legal consequences.",
                "explanation": "Heat and hot water are basic requirements. Landlords must repair quickly. You may be able to withhold rent, repair yourself, or stay elsewhere at landlord's expense.",
                "script": "The lack of heat/hot water is a habitability emergency. I need this fixed within 24 hours.",
                "next_steps": ["Report immediately", "Document everything", "Know emergency options", "Contact code enforcement"]
            },
            {
                "id": "housing-mold-pests",
                "question": "What about mold or pest infestations?",
                "short_answer": "Landlords are usually responsible for addressing mold and pests.",
                "explanation": "Most mold and pest issues are landlord responsibility, especially if caused by building issues. Document the problem and report it in writing.",
                "script": "I'm reporting a mold/pest problem that needs to be addressed. This may be a health hazard.",
                "next_steps": ["Document with photos", "Report in writing", "Request professional treatment", "See a doctor if needed"]
            },
            {
                "id": "housing-retaliation-repairs",
                "question": "Can I be evicted for requesting repairs?",
                "short_answer": "No. Retaliating against tenants for requesting repairs is illegal.",
                "explanation": "Landlords cannot evict you, raise rent, or reduce services because you requested repairs or complained to housing authorities.",
                "script": "I'm concerned about retaliation for my repair requests. I want to document that I'm exercising my legal rights.",
                "next_steps": ["Document timeline", "Report any changes", "Know it's illegal", "File complaint if retaliated against"]
            }
        ],
        "eviction": [
            {
                "id": "housing-eviction-process",
                "question": "Can I be kicked out immediately?",
                "short_answer": "No. Eviction requires legal process with notice and often court involvement.",
                "explanation": "Landlords cannot force you out without legal eviction process. This includes proper notice, and usually a court hearing where you can defend yourself.",
                "script": "I'd like to understand the formal eviction process. Can I receive any notices in writing?",
                "next_steps": ["Don't leave without process", "Know notice requirements", "Respond to court papers", "Get legal help"]
            },
            {
                "id": "housing-eviction-notice",
                "question": "How much notice is required before eviction?",
                "short_answer": "Varies by reason and state. Usually 3-30 days notice before court action.",
                "explanation": "Non-payment usually requires 3-14 days. Lease violations often 14-30 days. No-cause (where allowed) typically 30-60 days.",
                "script": "I received an eviction notice. I'd like to understand my rights and timeline for responding.",
                "next_steps": ["Read notice carefully", "Note the deadline", "Respond in time", "Seek legal help"]
            },
            {
                "id": "housing-illegal-lockout",
                "question": "What if landlord locks me out or shuts off utilities?",
                "short_answer": "This is illegal 'self-help' eviction. You can call police and sue.",
                "explanation": "Landlords cannot lock you out, remove your belongings, or shut off utilities to force you out. This is illegal and you can take legal action.",
                "script": "This is an illegal lockout. I'm calling the police and documenting this for legal action.",
                "next_steps": ["Call police", "Document everything", "Contact legal aid", "File lawsuit"]
            },
            {
                "id": "housing-eviction-record",
                "question": "Will an eviction show on my record?",
                "short_answer": "Court filings are public. Even cases you win may appear on screening reports.",
                "explanation": "Eviction court records can appear on tenant screening reports. Some states allow sealing of records if you win or case is dismissed.",
                "script": "I'd like to understand how this will affect my rental history and if the record can be sealed.",
                "next_steps": ["Try to settle", "Get case dismissed if possible", "Know sealing laws", "Explain to future landlords"]
            }
        ],
        "deposits": [
            {
                "id": "housing-deposit-return",
                "question": "When do I get my security deposit back?",
                "short_answer": "Usually 14-30 days after moving out. Landlord must itemize any deductions.",
                "explanation": "State laws set deadlines for returning deposits (usually 14-30 days). Landlords must provide itemized list of deductions with receipts.",
                "script": "I've moved out and left my forwarding address. When will I receive my deposit and itemized list?",
                "next_steps": ["Provide forwarding address", "Document condition at move-out", "Know state deadline", "Demand if not received"]
            },
            {
                "id": "housing-unfair-deductions",
                "question": "Can they keep my deposit for normal wear and tear?",
                "short_answer": "No. Normal wear and tear cannot be deducted from your deposit.",
                "explanation": "Faded paint, worn carpet, and minor scuffs are normal wear. Holes in walls, stains, and damage beyond normal use can be deducted.",
                "script": "I believe these deductions are for normal wear and tear, not damage. I'm disputing these charges.",
                "next_steps": ["Document everything at move-out", "Know what's normal wear", "Dispute in writing", "Sue in small claims"]
            },
            {
                "id": "housing-deposit-limit",
                "question": "How much can landlord charge for deposit?",
                "short_answer": "Many states limit deposits to 1-2 months rent.",
                "explanation": "State laws often cap security deposits. Some also limit pet deposits and other fees. Know your state's limits.",
                "script": "I want to verify that the deposit amount complies with state law. What is the total being charged?",
                "next_steps": ["Know state limits", "Get receipt", "Check for illegal fees", "Report violations"]
            }
        ],
        "lease": [
            {
                "id": "housing-break-lease",
                "question": "Can I break my lease early?",
                "short_answer": "You may owe rent, but landlords must try to re-rent. Some exceptions apply.",
                "explanation": "Breaking a lease may have financial consequences, but landlords must mitigate damages by trying to re-rent. Special rules for military, DV, and uninhabitable conditions.",
                "script": "I need to break my lease. What are my options and what will I owe?",
                "next_steps": ["Read lease terms", "Give proper notice", "Know mitigation rules", "Look for special protections"]
            },
            {
                "id": "housing-rent-increase",
                "question": "Can landlord raise my rent?",
                "short_answer": "Usually only after lease ends or with proper notice. Rent control may apply.",
                "explanation": "During a lease, rent is usually fixed. After, landlords can raise it with proper notice. Some areas have rent control limiting increases.",
                "script": "I'd like to understand the process and limits for rent increases here.",
                "next_steps": ["Check your lease", "Know notice requirements", "Research rent control", "Negotiate if possible"]
            },
            {
                "id": "housing-lease-renewal",
                "question": "Do I have to renew my lease?",
                "short_answer": "No. You can leave at end of lease with proper notice, or go month-to-month.",
                "explanation": "At lease end, you can renew, go month-to-month, or move out with proper notice. Check your lease for any auto-renewal clauses.",
                "script": "My lease is ending. What are my options and what notice do I need to give?",
                "next_steps": ["Give proper notice", "Know auto-renewal terms", "Negotiate new terms", "Plan ahead"]
            },
            {
                "id": "housing-illegal-lease-terms",
                "question": "What if my lease has illegal terms?",
                "short_answer": "Illegal lease terms are unenforceable. Your rights under law can't be waived.",
                "explanation": "You can't sign away tenant rights. Terms like 'no repairs' or 'landlord not liable' are usually unenforceable. Know your rights.",
                "script": "I believe this lease term may not be enforceable. Can you clarify the legal basis for this?",
                "next_steps": ["Know tenant rights", "Identify illegal terms", "Consult legal aid", "Don't be intimidated"]
            }
        ],
        "roommates": [
            {
                "id": "housing-roommate-leave",
                "question": "What if my roommate moves out?",
                "short_answer": "You may be responsible for full rent if you're both on the lease.",
                "explanation": "If both names are on the lease, you're usually 'jointly and severally liable' - either can be held responsible for full rent. Talk to landlord about options.",
                "script": "My roommate is moving out. What are my options for the lease and finding a replacement?",
                "next_steps": ["Check lease terms", "Talk to landlord", "Find replacement", "Get things in writing"]
            },
            {
                "id": "housing-subletting",
                "question": "Can I sublet or get a roommate?",
                "short_answer": "Usually only with landlord permission. Check your lease.",
                "explanation": "Most leases require landlord approval for subletting or adding occupants. Some cities have laws requiring landlords to approve reasonable requests.",
                "script": "I'd like to add a roommate/sublet. What is the process for getting approval?",
                "next_steps": ["Read lease terms", "Get written permission", "Know local laws", "Screen subletters carefully"]
            },
            {
                "id": "housing-guest-restrictions",
                "question": "Can landlord limit my guests?",
                "short_answer": "Some limits on long-term guests are allowed, but can't ban visitors entirely.",
                "explanation": "Leases can limit how long guests can stay (often 7-14 consecutive days). But landlords can't ban normal visitors or monitor your social life.",
                "script": "I'd like to understand the guest policy. How long can visitors stay?",
                "next_steps": ["Know the limits", "Don't have guests 'live' there", "Protect your rights", "Consider adding to lease"]
            }
        ]
    },
    
    # ==================== POLICE ====================
    "police": {
        "stops": [
            {
                "id": "police-on-foot",
                "question": "What do I do if stopped by police on foot?",
                "short_answer": "Stay calm, keep hands visible, ask if you're free to go.",
                "explanation": "You may ask 'Am I being detained or am I free to go?' If detained, you can remain silent except for providing identification in most states.",
                "script": "I want to be respectful, officer. Am I free to go, or am I being detained?",
                "next_steps": ["Stay calm", "Keep hands visible", "Ask if you can leave", "Don't run"]
            },
            {
                "id": "police-traffic-stop",
                "question": "What do I do during a traffic stop?",
                "short_answer": "Pull over safely, hands on wheel, provide license and registration when asked.",
                "explanation": "Pull over safely, turn off car, hands on steering wheel, turn on interior light at night. Provide license, registration, insurance when asked.",
                "script": "I'll provide my license and registration. I'm reaching into my [location] now.",
                "next_steps": ["Pull over safely", "Stay calm", "Hands on wheel", "Announce movements"]
            },
            {
                "id": "police-walking-away",
                "question": "Can I walk away from police?",
                "short_answer": "Ask if you're being detained. If no, you can leave. Don't run.",
                "explanation": "If police have 'reasonable suspicion' of a crime, they can briefly detain you. If you're not being detained, you're free to leave. Never run.",
                "script": "Am I being detained? If not, I'd like to leave now.",
                "next_steps": ["Ask clearly", "Wait for answer", "Leave calmly if free", "Don't argue if detained"]
            },
            {
                "id": "police-identify-yourself",
                "question": "Do I have to identify myself?",
                "short_answer": "In most states, yes if detained. But you don't have to answer other questions.",
                "explanation": "Most states have 'stop and identify' laws. You usually must give your name if lawfully detained. You don't have to answer other questions.",
                "script": "I'll provide my name. I'm exercising my right to remain silent for other questions.",
                "next_steps": ["Know your state's law", "Provide name if required", "Stay silent otherwise", "Be polite"]
            }
        ],
        "searches": [
            {
                "id": "police-search-person",
                "question": "Can police search my body/clothes?",
                "short_answer": "They can pat down for weapons if they have reason to believe you're armed. Full searches need more.",
                "explanation": "A 'Terry frisk' for weapons requires reasonable suspicion you're armed. Full searches need probable cause, consent, or arrest.",
                "script": "I do not consent to a search.",
                "next_steps": ["State clearly you don't consent", "Don't physically resist", "Remember what happens", "Challenge in court later"]
            },
            {
                "id": "police-search-car",
                "question": "Can police search my car?",
                "short_answer": "They need probable cause, consent, or a warrant. You can decline consent.",
                "explanation": "Police can search your car if they smell drugs, see contraband in plain view, or arrest you. You can always say you don't consent.",
                "script": "I don't consent to a search of my vehicle.",
                "next_steps": ["Don't consent", "Don't unlock/open things", "Stay polite", "Document everything later"]
            },
            {
                "id": "police-search-phone",
                "question": "Can police search my phone?",
                "short_answer": "No, they need a warrant to search your phone. Don't unlock it for them.",
                "explanation": "Supreme Court ruled police need a warrant to search phones. You don't have to unlock it, provide passwords, or use biometrics. Assert your rights.",
                "script": "I do not consent to a search of my phone. I'd like to see a warrant.",
                "next_steps": ["Don't unlock phone", "Ask for warrant", "Don't provide passwords", "Be polite but firm"]
            },
            {
                "id": "police-search-home",
                "question": "Can police search my home?",
                "short_answer": "Generally no without a warrant. You don't have to let them in.",
                "explanation": "Police need a warrant, your consent, or very limited emergency exceptions to enter and search your home. You can say no.",
                "script": "I do not consent to a search. Please provide a warrant.",
                "next_steps": ["Don't invite them in", "Ask for warrant", "Step outside to talk", "Call a lawyer if arrested"]
            },
            {
                "id": "police-drug-dogs",
                "question": "What about police dogs sniffing my car?",
                "short_answer": "They can't extend a traffic stop just to bring dogs. Dogs can sniff without consent if already there.",
                "explanation": "Police can't hold you longer than a normal stop just to wait for drug dogs. But if dogs are already there, a sniff isn't considered a 'search.'",
                "script": "Am I being detained? Is this stop taking longer than necessary for a traffic violation?",
                "next_steps": ["Know the limits", "Ask about the delay", "Don't consent to searches", "Challenge in court"]
            }
        ],
        "arrests": [
            {
                "id": "police-being-arrested",
                "question": "What do I do if I'm being arrested?",
                "short_answer": "Don't resist. Say you want a lawyer. Stay silent.",
                "explanation": "Don't resist arrest, even if you think it's wrong. Clearly say 'I want a lawyer' and 'I'm invoking my right to remain silent.' Challenge it in court.",
                "script": "I'm not resisting. I want a lawyer. I'm invoking my right to remain silent.",
                "next_steps": ["Don't resist", "Ask for lawyer immediately", "Stay silent", "Remember details for later"]
            },
            {
                "id": "police-miranda-rights",
                "question": "What are Miranda rights?",
                "short_answer": "Right to remain silent and right to a lawyer before questioning.",
                "explanation": "After arrest, police must read you Miranda rights before questioning. Anything you say can be used against you. You can invoke these rights at any time.",
                "script": "I'm invoking my right to remain silent and my right to a lawyer.",
                "next_steps": ["Remember these rights", "Invoke them clearly", "Stop answering questions", "Wait for lawyer"]
            },
            {
                "id": "police-phone-call",
                "question": "Do I get a phone call?",
                "short_answer": "Yes, you have the right to make phone calls after arrest, usually within a reasonable time.",
                "explanation": "You typically have the right to make calls to a lawyer, family, or to arrange bail. The exact timing varies by jurisdiction.",
                "script": "I'd like to make my phone call to contact a lawyer and notify my family.",
                "next_steps": ["Ask for your call", "Call a lawyer first", "Notify family", "Be patient"]
            },
            {
                "id": "police-bail",
                "question": "How does bail work?",
                "short_answer": "Bail is money to get released before trial. Amount depends on the charge and your situation.",
                "explanation": "Bail lets you leave jail while awaiting trial. Amount varies. You may pay full amount (returned if you show up) or use a bail bondsman (10% fee).",
                "script": "I'd like to request a bail hearing and understand my options for release.",
                "next_steps": ["Ask about bail amount", "Contact family for help", "Consider bondsman", "Show up to all court dates"]
            }
        ],
        "rights": [
            {
                "id": "police-remain-silent",
                "question": "What is the right to remain silent?",
                "short_answer": "You don't have to answer questions. This can't be used against you.",
                "explanation": "The Fifth Amendment protects you from self-incrimination. You can refuse to answer questions from police. Clearly invoke this right.",
                "script": "I'm exercising my Fifth Amendment right to remain silent.",
                "next_steps": ["State it clearly", "Stop talking", "Repeat if necessary", "Wait for lawyer"]
            },
            {
                "id": "police-right-to-lawyer",
                "question": "When can I have a lawyer?",
                "short_answer": "You can have a lawyer before and during any questioning. If you can't afford one, one will be provided.",
                "explanation": "You have the right to an attorney. If you can't afford one, a public defender will be assigned. Once you ask for a lawyer, questioning must stop.",
                "script": "I want a lawyer present before answering any questions.",
                "next_steps": ["Ask immediately", "Repeat if needed", "Don't answer until lawyer arrives", "Don't waive this right"]
            },
            {
                "id": "police-false-arrest",
                "question": "What if I'm arrested unfairly?",
                "short_answer": "Don't resist. Document everything. Challenge it in court and possibly file a complaint.",
                "explanation": "Resisting makes things worse, even if arrest is illegal. Document everything, get a lawyer, challenge in court, and file a complaint afterward.",
                "script": "I believe this arrest is unlawful but I will not resist. I want a lawyer.",
                "next_steps": ["Don't resist", "Document everything", "Get a lawyer", "File complaint later"]
            },
            {
                "id": "police-excessive-force",
                "question": "What if police use excessive force?",
                "short_answer": "Don't resist. Document everything. Get medical attention. File a complaint.",
                "explanation": "Resisting may escalate the situation. Afterward, photograph injuries, get medical records, file a complaint, and consider a lawsuit.",
                "script": "I'm not resisting. Please stop.",
                "next_steps": ["Don't resist", "Document injuries", "Get medical care", "File complaint"]
            }
        ],
        "recording": [
            {
                "id": "police-record-police",
                "question": "Can I record police?",
                "short_answer": "Yes, in public places from a safe distance that doesn't interfere.",
                "explanation": "You have a First Amendment right to record police in public. Stay at a safe distance and don't interfere with their duties.",
                "script": "I'm recording from a safe distance and not interfering.",
                "next_steps": ["Keep safe distance", "Don't interfere", "Keep recording", "Back up the video"]
            },
            {
                "id": "police-delete-recording",
                "question": "Can police make me delete recordings?",
                "short_answer": "No. Demanding you delete recordings is illegal. Don't unlock your phone.",
                "explanation": "Police cannot legally require you to delete recordings. Don't unlock your phone or show them how to delete it.",
                "script": "I do not consent to deleting my recordings or unlocking my phone.",
                "next_steps": ["Don't delete", "Don't unlock phone", "Stay calm", "Report if pressured"]
            },
            {
                "id": "police-witness-recording",
                "question": "Can I record police interacting with others?",
                "short_answer": "Yes, you can record police interacting with others in public.",
                "explanation": "Bystanders have the right to record police actions in public. Keep a safe distance and don't interfere.",
                "script": "I'm a bystander exercising my right to record public activity.",
                "next_steps": ["Keep recording", "Stay safe", "Don't interfere", "Share if needed"]
            }
        ],
        "complaints": [
            {
                "id": "police-file-complaint",
                "question": "How do I file a complaint against police?",
                "short_answer": "File with internal affairs, civilian review board, or the DOJ for serious violations.",
                "explanation": "Most departments have internal affairs or citizen complaint processes. Many cities have civilian review boards. For civil rights violations, contact the DOJ.",
                "script": "I'd like to file a formal complaint. What is the process and timeline?",
                "next_steps": ["Document everything", "File written complaint", "Keep copies", "Follow up"]
            },
            {
                "id": "police-lawsuit",
                "question": "Can I sue the police?",
                "short_answer": "Yes, you can sue for civil rights violations, but it's difficult. Get a lawyer.",
                "explanation": "You can sue under Section 1983 for civil rights violations. It's complex and police have some immunity. Consult a civil rights attorney.",
                "script": "I'd like to consult with a civil rights attorney about my options.",
                "next_steps": ["Document everything", "Find civil rights lawyer", "Know time limits", "Understand difficulty"]
            }
        ]
    },
    
    # ==================== ONLINE ====================
    "online": {
        "social": [
            {
                "id": "online-social-privacy",
                "question": "Who can see what I post?",
                "short_answer": "Check privacy settings. Even 'private' posts can be screenshotted and shared.",
                "explanation": "Privacy settings control who sees posts directly, but anyone who can see them can screenshot and share. Nothing online is truly private.",
                "script": "I'd like to review my privacy settings. Where can I find these options?",
                "next_steps": ["Review privacy settings", "Know nothing is truly private", "Be careful what you post", "Audit regularly"]
            },
            {
                "id": "online-delete-posts",
                "question": "Can I really delete something online?",
                "short_answer": "You can delete from the platform, but copies may exist. The internet is forever.",
                "explanation": "Deleting removes it from the platform, but screenshots, archives, and copies may still exist. Think before you post.",
                "script": "I need to delete this content. Where is the option and will it be permanently removed?",
                "next_steps": ["Delete from platform", "Know copies may exist", "Request removal from Google", "Learn from it"]
            },
            {
                "id": "online-account-hacked",
                "question": "What if my social media is hacked?",
                "short_answer": "Change passwords, enable 2FA, report to platform, warn contacts.",
                "explanation": "Immediately change passwords on all accounts, enable two-factor authentication, report to the platform, and warn your contacts.",
                "script": "My account was hacked. I need to report this and secure my account.",
                "next_steps": ["Change passwords", "Enable 2FA", "Report to platform", "Warn contacts"]
            },
            {
                "id": "online-impersonation",
                "question": "Someone is impersonating me online. What can I do?",
                "short_answer": "Report to the platform. This violates most terms of service.",
                "explanation": "Most platforms have impersonation reporting. You can also contact law enforcement if they're committing fraud or harassment.",
                "script": "I need to report a fake account impersonating me. How do I do this?",
                "next_steps": ["Report to platform", "Document the account", "Warn friends", "Contact police if serious"]
            }
        ],
        "data": [
            {
                "id": "online-data-collection",
                "question": "What data do companies collect about me?",
                "short_answer": "A lot: location, browsing, purchases, messages, contacts. Check privacy policies.",
                "explanation": "Companies collect extensive data including location, searches, purchases, and device info. Privacy policies explain what they collect and how.",
                "script": "Can you tell me what data you collect about me and how I can access it?",
                "next_steps": ["Read privacy policies", "Check data settings", "Request your data", "Limit what you share"]
            },
            {
                "id": "online-data-deletion",
                "question": "Can I get my data deleted?",
                "short_answer": "Yes, some laws (like CCPA) give you the right to request deletion.",
                "explanation": "California's CCPA and other laws give you the right to request data deletion. Many companies offer this even if not legally required.",
                "script": "I'd like to request deletion of my personal data under applicable privacy laws.",
                "next_steps": ["Find deletion request option", "Submit formal request", "Follow up", "Know your state's laws"]
            },
            {
                "id": "online-ad-tracking",
                "question": "How do I stop being tracked for ads?",
                "short_answer": "Use privacy settings, ad blockers, and opt-out of personalized ads.",
                "explanation": "Adjust privacy settings on devices and apps, use browser privacy features, and opt out of personalized advertising where available.",
                "script": "I want to opt out of personalized advertising. Where can I change these settings?",
                "next_steps": ["Check phone settings", "Adjust app permissions", "Use privacy browsers", "Install blockers"]
            }
        ],
        "harassment": [
            {
                "id": "online-cyberbullying",
                "question": "What can I do about cyberbullying?",
                "short_answer": "Document, block, report to platform. If threats, involve police and adults.",
                "explanation": "Screenshot evidence, block the bully, report to the platform. If there are threats, tell a trusted adult and potentially police.",
                "script": "I'm experiencing cyberbullying and need to report it. I have documentation.",
                "next_steps": ["Screenshot everything", "Block the person", "Report to platform", "Tell trusted adult"]
            },
            {
                "id": "online-doxxing",
                "question": "What if someone posts my personal info (doxxing)?",
                "short_answer": "Report to platform for removal. Contact police if threats are involved.",
                "explanation": "Doxxing can enable harassment or danger. Report to the platform for removal. If there are threats or danger, contact police.",
                "script": "My personal information was posted without consent. I need this removed immediately.",
                "next_steps": ["Report for removal", "Document everything", "Contact police if threats", "Secure accounts"]
            },
            {
                "id": "online-death-threats",
                "question": "What if I receive online threats?",
                "short_answer": "Take them seriously. Screenshot, report to platform, contact police.",
                "explanation": "Online threats can be crimes. Document everything, report to the platform, and contact police, especially if threats are specific.",
                "script": "I've received threats online. I'm reporting to the platform and police.",
                "next_steps": ["Screenshot evidence", "Report to platform", "Contact police", "Increase security"]
            }
        ],
        "photos": [
            {
                "id": "online-photo-consent",
                "question": "Can someone post my photo without permission?",
                "short_answer": "Generally yes in public places. But some uses (commercial, harassment) may be restricted.",
                "explanation": "In public, people can photograph you. But using your image commercially or for harassment may violate laws. Intimate images have special protections.",
                "script": "This photo was used without my consent in a harmful way. I need it removed.",
                "next_steps": ["Report to platform", "Document the use", "Check state laws", "Consider legal action"]
            },
            {
                "id": "online-intimate-images",
                "question": "Someone shared intimate images of me without consent.",
                "short_answer": "This is illegal in most states. Report to platform and police. Get help.",
                "explanation": "Non-consensual intimate images ('revenge porn') are illegal in most states. Report to police, the platform, and organizations like CCRI.",
                "script": "Intimate images were shared without my consent. This is illegal and I need help getting them removed.",
                "next_steps": ["Report to platform", "Contact police", "Reach out to CCRI", "Don't blame yourself"]
            },
            {
                "id": "online-sexting-minors",
                "question": "What are the risks of sexting as a minor?",
                "short_answer": "Creating, sharing, or possessing intimate images of minors can be illegal, even of yourself.",
                "explanation": "Sexting involving anyone under 18 can potentially involve child pornography laws, even if you're the subject. This is serious.",
                "script": "I need help with a situation involving inappropriate images. I'm under 18 and need to talk to someone.",
                "next_steps": ["Talk to trusted adult", "Don't share images", "Know the legal risks", "Get help if pressured"]
            }
        ],
        "accounts": [
            {
                "id": "online-password-demand",
                "question": "Can my parents/school demand my passwords?",
                "short_answer": "Parents often can. Schools usually can't demand personal account passwords.",
                "explanation": "Parents have authority over minor children's accounts. Schools can access school accounts but generally can't demand personal passwords.",
                "script": "I'd like to understand why my password is being requested and what it will be used for.",
                "next_steps": ["Know who's asking", "Understand the reason", "Know your rights", "Protect personal accounts"]
            },
            {
                "id": "online-employer-social-media",
                "question": "Can employers ask for my social media passwords?",
                "short_answer": "In many states, no. Laws protect against employers demanding personal passwords.",
                "explanation": "Many states have laws prohibiting employers from demanding personal social media passwords. Know your state's protections.",
                "script": "I don't believe I'm required to provide my personal social media passwords. What is the legal basis for this request?",
                "next_steps": ["Know your state's law", "Politely decline if protected", "Keep professional online", "Consult lawyer if pressured"]
            },
            {
                "id": "online-two-factor",
                "question": "How do I make my accounts more secure?",
                "short_answer": "Use strong unique passwords, enable 2FA, watch for phishing.",
                "explanation": "Use different strong passwords for each account, enable two-factor authentication, and be careful of phishing attempts.",
                "script": "I want to secure my accounts. How do I enable two-factor authentication?",
                "next_steps": ["Use password manager", "Enable 2FA everywhere", "Watch for phishing", "Check for breaches"]
            }
        ],
        "school-monitoring": [
            {
                "id": "online-school-devices",
                "question": "Can school see what I do on school devices?",
                "short_answer": "Yes. School devices are fully monitored. Don't expect privacy.",
                "explanation": "Schools can monitor everything on school devices - websites, apps, messages. Never use school devices for personal, private activities.",
                "script": "I understand school devices are monitored. I'm using my personal device for personal activities.",
                "next_steps": ["Don't use for private stuff", "Use personal devices", "Know you're watched", "Be appropriate"]
            },
            {
                "id": "online-home-wifi",
                "question": "Can school track me when I'm at home?",
                "short_answer": "If using school device or logged into school accounts, yes they may be able to.",
                "explanation": "School monitoring software on school devices works everywhere. Being logged into school accounts may also allow some tracking.",
                "script": "I'm concerned about monitoring at home. I'll use personal devices for personal activities.",
                "next_steps": ["Use personal device at home", "Log out of school accounts", "Know what's monitored", "Separate school/personal"]
            }
        ]
    },
    
    # ==================== PUBLIC SPACES ====================
    "public": {
        "filming": [
            {
                "id": "public-photo-street",
                "question": "Can I photograph people on the street?",
                "short_answer": "Generally yes. In public, there's no expectation of privacy.",
                "explanation": "Photography in public places is generally legal. People in public don't have an expectation of privacy. Private property is different.",
                "script": "I'm photographing in a public space where there's no expectation of privacy.",
                "next_steps": ["Stay in public areas", "Be respectful", "Know property boundaries", "Commercial use may differ"]
            },
            {
                "id": "public-film-police",
                "question": "Can I film police in public?",
                "short_answer": "Yes. Recording police in public is a First Amendment right.",
                "explanation": "You have the right to record police in public. Keep a safe distance and don't interfere with their duties.",
                "script": "I'm exercising my First Amendment right to record police activity in public.",
                "next_steps": ["Keep safe distance", "Don't interfere", "Back up footage", "Know your rights"]
            },
            {
                "id": "public-private-property",
                "question": "Can I film in stores and businesses?",
                "short_answer": "Only with permission. Private property owners set their own rules.",
                "explanation": "Businesses can prohibit photography on their property. If asked to stop or leave, you should comply or risk trespassing charges.",
                "script": "I understand this is private property. Am I allowed to photograph here?",
                "next_steps": ["Ask permission", "Respect 'no photos' policies", "Leave if asked", "Public areas only otherwise"]
            }
        ],
        "protests": [
            {
                "id": "public-protest-rights",
                "question": "What are my rights at a protest?",
                "short_answer": "You have First Amendment rights to peaceful assembly. Know the limits.",
                "explanation": "You can protest peacefully in public. Some restrictions on time, place, and manner may apply. Don't block traffic or trespass.",
                "script": "I'm exercising my First Amendment right to peaceful assembly.",
                "next_steps": ["Stay peaceful", "Know permit rules", "Follow lawful orders", "Document if rights violated"]
            },
            {
                "id": "public-protest-permit",
                "question": "Do I need a permit to protest?",
                "short_answer": "For large, organized events, often yes. Small spontaneous gatherings usually don't.",
                "explanation": "Large demonstrations often need permits. Spontaneous, small groups on public sidewalks usually don't. Know local rules.",
                "script": "I'd like to understand the permit requirements for public demonstrations.",
                "next_steps": ["Check local rules", "Apply if needed", "Small groups often okay", "Know your rights"]
            },
            {
                "id": "public-arrested-protest",
                "question": "What if I'm arrested at a protest?",
                "short_answer": "Stay calm, don't resist, invoke your right to remain silent and to a lawyer.",
                "explanation": "If arrested, don't resist. Clearly invoke your rights. You may be charged with trespassing or disorderly conduct.",
                "script": "I'm not resisting. I want a lawyer. I'm invoking my right to remain silent.",
                "next_steps": ["Don't resist", "Give name only", "Ask for lawyer", "Document later"]
            },
            {
                "id": "public-counter-protesters",
                "question": "What about counter-protesters?",
                "short_answer": "They have the same rights. Police should keep groups separated.",
                "explanation": "Counter-protesters have First Amendment rights too. Police should maintain separation. Don't engage in violence.",
                "script": "I'm here to peacefully exercise my rights. I'm not engaging with counter-protesters.",
                "next_steps": ["Don't engage", "Stay peaceful", "Let police handle issues", "Document if needed"]
            }
        ],
        "stores": [
            {
                "id": "public-store-detention",
                "question": "Can a store detain me for suspected shoplifting?",
                "short_answer": "Briefly, yes, if they have reasonable grounds. It must be reasonable in manner and time.",
                "explanation": "'Shopkeeper's privilege' allows brief detention if they reasonably believe theft occurred. Can't use excessive force or hold too long.",
                "script": "I haven't taken anything. If you believe I have, please call the police to resolve this.",
                "next_steps": ["Stay calm", "Don't run", "Ask for manager", "Request police if needed"]
            },
            {
                "id": "public-bag-check",
                "question": "Can stores check my bag?",
                "short_answer": "They can ask. You can usually refuse, but they may ban you from the store.",
                "explanation": "Bag checks are usually voluntary unless you agreed to them (like at Costco with membership). Stores can refuse service if you decline.",
                "script": "Is this bag check required, or can I decline? I haven't purchased anything yet.",
                "next_steps": ["Ask if required", "Check if you agreed to it", "Comply or leave", "Know store policy"]
            },
            {
                "id": "public-asked-to-leave",
                "question": "Can a business ask me to leave?",
                "short_answer": "Yes, businesses can refuse service for most reasons (but not discrimination).",
                "explanation": "Private businesses can ask people to leave for many reasons, including no reason. They cannot discriminate based on protected characteristics.",
                "script": "I understand I'm being asked to leave. May I ask why?",
                "next_steps": ["Leave if asked", "Ask reason politely", "Note if discriminatory", "File complaint if discrimination"]
            }
        ],
        "transport": [
            {
                "id": "public-bus-train",
                "question": "What are my rights on public transit?",
                "short_answer": "Public transit is public, but agencies can set rules. Pay your fare.",
                "explanation": "Transit agencies can set reasonable rules about conduct. Police can be called for fare evasion or disruptions. You generally can be photographed.",
                "script": "I'd like to understand the rules for this transit system.",
                "next_steps": ["Pay your fare", "Follow rules", "Be respectful", "Know your stop"]
            },
            {
                "id": "public-rideshare",
                "question": "What are my rights in an Uber/Lyft?",
                "short_answer": "You're in a private vehicle. The driver can set rules. Report safety issues.",
                "explanation": "Rideshares are private vehicles. Drivers can end rides for safety. You can report issues to the company. Know emergency features in apps.",
                "script": "I feel unsafe. I'm ending this ride and reporting to the company.",
                "next_steps": ["Use app safety features", "End ride if unsafe", "Report to company", "Know emergency options"]
            },
            {
                "id": "public-airport-rights",
                "question": "What about searches at airports?",
                "short_answer": "You consent to search by entering security. You can opt out of body scanners for pat-downs.",
                "explanation": "Airport security searches are permitted because you consent by choosing to fly. You can request pat-down instead of body scanner.",
                "script": "I'd like to opt out of the body scanner and receive a pat-down instead.",
                "next_steps": ["Know you'll be searched", "Opt out if preferred", "Don't joke about threats", "Arrive early"]
            }
        ],
        "parks": [
            {
                "id": "public-park-rules",
                "question": "What can I do in public parks?",
                "short_answer": "Parks have rules about hours, activities, and permits. Check posted rules.",
                "explanation": "Public parks are public property, but have rules. Common restrictions: hours (often close at dusk), alcohol, fires, overnight camping.",
                "script": "I want to make sure I'm following park rules. What activities are allowed here?",
                "next_steps": ["Check posted rules", "Know hours", "Get permits if needed", "Be respectful"]
            },
            {
                "id": "public-sleeping-outside",
                "question": "Can I sleep in public places?",
                "short_answer": "Laws vary widely. Many places ban camping or sleeping in public. Some courts have limited enforcement.",
                "explanation": "Anti-camping laws exist but recent court decisions limit enforcement when shelters are full. Know local rules and available resources.",
                "script": "I need somewhere safe to be. Are there resources or shelters available?",
                "next_steps": ["Know local laws", "Find shelter resources", "Know your rights", "Seek help"]
            }
        ],
        "curfew": [
            {
                "id": "public-curfew-laws",
                "question": "Are curfews for minors legal?",
                "short_answer": "Many cities have youth curfews, but there are exceptions and some legal challenges.",
                "explanation": "Youth curfews are common but often have exceptions for work, emergencies, school events, or being with a parent. Some have been challenged as unconstitutional.",
                "script": "I'm aware of the curfew. I'm heading home from [work/school event/with parent].",
                "next_steps": ["Know your city's curfew", "Know the exceptions", "Have explanation ready", "Carry ID/work badge"]
            },
            {
                "id": "public-loitering-laws",
                "question": "Can I be arrested for 'loitering'?",
                "short_answer": "Vague loitering laws have been struck down, but some specific laws remain.",
                "explanation": "General 'loitering' laws are often unconstitutional. But laws against specific activities (blocking sidewalks, drug loitering) may be valid.",
                "script": "I'm not blocking anyone or doing anything illegal. What specifically am I being accused of?",
                "next_steps": ["Ask what law you're violating", "Move along if asked", "Know your rights", "Don't argue"]
            }
        ]
    }
}

DEFAULT_SCRIPTS = [
    {"id": "script-no-search", "title": "Declining a Search", "content": "I do not consent to a search.", "category": "general"},
    {"id": "script-policy-writing", "title": "Request Policy in Writing", "content": "Can you please explain the policy in writing?", "category": "general"},
    {"id": "script-contact-support", "title": "Request Support", "content": "I would like to contact a parent, guardian, or lawyer.", "category": "general"},
    {"id": "script-uncomfortable", "title": "Decline to Answer", "content": "I am not comfortable answering that without support.", "category": "general"},
    {"id": "script-free-to-go", "title": "Ask if Detained", "content": "Am I free to go, or am I being detained?", "category": "police"},
    {"id": "script-remain-silent", "title": "Invoke Right to Silence", "content": "I am exercising my right to remain silent. I would like a lawyer.", "category": "police"},
    {"id": "script-no-consent-phone", "title": "Protect Your Phone", "content": "I do not consent to a search of my phone.", "category": "police"},
    {"id": "script-recording", "title": "Assert Recording Rights", "content": "I am recording from a safe distance and not interfering.", "category": "police"},
    {"id": "script-work-hours", "title": "Confirm Work Hours", "content": "I want to make sure I'm logging all my work hours correctly.", "category": "work"},
    {"id": "script-break-request", "title": "Request Break", "content": "I need to take my required break. When should I go?", "category": "work"},
    {"id": "script-landlord-notice", "title": "Request Entry Notice", "content": "I'd appreciate proper notice before any entry as required by law.", "category": "housing"},
    {"id": "script-repair-request", "title": "Request Repairs", "content": "I'm reporting this issue in writing. Can you provide a timeline for repairs?", "category": "housing"}
]

RESOURCES = [
    {
        "category": "Emergency Hotlines",
        "items": [
            {"name": "National Emergency", "contact": "911", "description": "For immediate emergencies"},
            {"name": "Crisis Text Line", "contact": "Text HOME to 741741", "description": "Free 24/7 crisis support via text"},
            {"name": "National Suicide Prevention", "contact": "988", "description": "24/7 mental health crisis support"},
            {"name": "National Domestic Violence", "contact": "1-800-799-7233", "description": "Help for domestic violence"}
        ]
    },
    {
        "category": "Legal Aid",
        "items": [
            {"name": "Legal Services Corporation", "contact": "lsc.gov", "description": "Find free legal aid in your area"},
            {"name": "ACLU", "contact": "aclu.org", "description": "Civil liberties information and help"},
            {"name": "LawHelp.org", "contact": "lawhelp.org", "description": "Free legal help by state"},
            {"name": "National Legal Aid", "contact": "nlada.org", "description": "Directory of legal aid organizations"}
        ]
    },
    {
        "category": "Youth Support",
        "items": [
            {"name": "Boys Town Hotline", "contact": "1-800-448-3000", "description": "24/7 help for teens and parents"},
            {"name": "Teen Line", "contact": "1-800-852-8336", "description": "Teens helping teens"},
            {"name": "The Trevor Project", "contact": "1-866-488-7386", "description": "LGBTQ+ youth crisis support"},
            {"name": "StopBullying.gov", "contact": "stopbullying.gov", "description": "Anti-bullying resources"}
        ]
    },
    {
        "category": "Worker Rights",
        "items": [
            {"name": "Department of Labor", "contact": "dol.gov", "description": "Federal workplace rights info"},
            {"name": "OSHA", "contact": "1-800-321-OSHA", "description": "Workplace safety concerns"},
            {"name": "EEOC", "contact": "eeoc.gov", "description": "Employment discrimination help"},
            {"name": "Wage & Hour Division", "contact": "1-866-487-9243", "description": "Wage theft and hour violations"}
        ]
    },
    {
        "category": "Housing Help",
        "items": [
            {"name": "HUD", "contact": "hud.gov", "description": "Housing rights and assistance"},
            {"name": "National Housing Law Project", "contact": "nhlp.org", "description": "Tenant rights resources"},
            {"name": "Rent Help", "contact": "consumerfinance.gov/renthelp", "description": "Rental assistance programs"},
            {"name": "Eviction Lab", "contact": "evictionlab.org", "description": "Eviction data and resources"}
        ]
    },
    {
        "category": "Online Safety",
        "items": [
            {"name": "Cyber Civil Rights Initiative", "contact": "cybercivilrights.org", "description": "Non-consensual image help"},
            {"name": "StaySafeOnline", "contact": "staysafeonline.org", "description": "Online safety resources"},
            {"name": "Identity Theft Resource", "contact": "idtheftcenter.org", "description": "Identity theft help"},
            {"name": "FBI Internet Crime", "contact": "ic3.gov", "description": "Report internet crimes"}
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
    return {"message": "Know Your Rights API", "version": "2.0.0"}

@api_router.get("/categories")
async def get_categories():
    return CATEGORIES

@api_router.get("/category/{category_id}/subcategories")
async def get_subcategories(category_id: str):
    for cat in CATEGORIES:
        if cat["id"] == category_id:
            return {"category": cat, "subcategories": cat.get("subcategories", [])}
    raise HTTPException(status_code=404, detail="Category not found")

@api_router.get("/scenarios/{category_id}")
async def get_scenarios_by_category(category_id: str):
    """Get all scenarios for a category (flattened from subcategories)"""
    if category_id not in SCENARIOS:
        raise HTTPException(status_code=404, detail="Category not found")
    
    all_scenarios = []
    category_data = SCENARIOS[category_id]
    for subcategory_id, scenarios in category_data.items():
        for scenario in scenarios:
            scenario_copy = scenario.copy()
            scenario_copy["subcategory"] = subcategory_id
            all_scenarios.append(scenario_copy)
    return all_scenarios

@api_router.get("/scenarios/{category_id}/{subcategory_id}")
async def get_scenarios_by_subcategory(category_id: str, subcategory_id: str):
    """Get scenarios for a specific subcategory"""
    if category_id not in SCENARIOS:
        raise HTTPException(status_code=404, detail="Category not found")
    if subcategory_id not in SCENARIOS[category_id]:
        raise HTTPException(status_code=404, detail="Subcategory not found")
    return SCENARIOS[category_id][subcategory_id]

@api_router.get("/scenario/{scenario_id}")
async def get_scenario_detail(scenario_id: str):
    for category_data in SCENARIOS.values():
        for subcategory_scenarios in category_data.values():
            for scenario in subcategory_scenarios:
                if scenario["id"] == scenario_id:
                    return scenario
    raise HTTPException(status_code=404, detail="Scenario not found")

@api_router.get("/scripts/default")
async def get_default_scripts():
    return DEFAULT_SCRIPTS

@api_router.get("/resources")
async def get_resources():
    return RESOURCES

@api_router.get("/states")
async def get_states():
    return US_STATES

# User Preferences
@api_router.post("/preferences", response_model=UserPreferences)
async def create_or_update_preferences(input: UserPreferencesCreate):
    existing = await db.preferences.find_one({"device_id": input.device_id})
    if existing:
        update_data = {**input.dict(), "updated_at": datetime.utcnow()}
        await db.preferences.update_one({"device_id": input.device_id}, {"$set": update_data})
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
    logging.info(f"[MOCKED SMS] To: {request.to_phone}, From: {request.from_name}, Message: {request.message}")
    return {"success": True, "mocked": True, "message": "SMS would be sent in production"}

# AI Chat
@api_router.post("/chat")
async def chat_with_ai(request: ChatRequest):
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="AI service not configured")
    
    user_msg = ChatMessage(device_id=request.device_id, session_id=request.session_id, role="user", content=request.message)
    await db.chat_messages.insert_one(user_msg.dict())
    
    history = await db.chat_messages.find({"device_id": request.device_id, "session_id": request.session_id}).sort("timestamp", 1).to_list(20)
    
    state_context = f" The user is in {request.user_state}." if request.user_state else " The user's state is unknown, so provide general U.S. guidance and mention that laws vary by state."
    
    system_message = f"""You are a helpful rights education assistant for the "Know Your Rights" app. Help teens and young adults understand their basic rights in everyday situations.

RULES:
1. Keep answers SHORT and CLEAR - 2-3 paragraphs max
2. Use PLAIN language a teenager would understand
3. NEVER pretend to be a lawyer or give official legal advice
4. Always encourage seeking qualified help for serious legal issues
5. Focus on educational guidance, practical scripts, and next steps
6. Be supportive and non-judgmental
7. If unclear, ask what situation or setting applies

{state_context}

Topics: School rights, work rights, housing, police interactions, online privacy, public spaces.

Remember: You're helping people who may be stressed. Be calm, clear, and helpful. This is educational info, NOT legal advice."""

    try:
        chat = LlmChat(api_key=EMERGENT_LLM_KEY, session_id=f"kyr-{request.session_id}", system_message=system_message).with_model("anthropic", "claude-sonnet-4-5-20250929")
        
        context = ""
        for msg in history[-10:]:
            role = "User" if msg["role"] == "user" else "Assistant"
            context += f"{role}: {msg['content']}\n"
        
        full_message = f"Previous conversation:\n{context}\n\nUser's new question: {request.message}"
        response = await chat.send_message(UserMessage(text=full_message))
        
        assistant_msg = ChatMessage(device_id=request.device_id, session_id=request.session_id, role="assistant", content=response)
        await db.chat_messages.insert_one(assistant_msg.dict())
        
        return {"response": response, "session_id": request.session_id}
    except Exception as e:
        logging.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get AI response")

@api_router.get("/chat/history/{device_id}/{session_id}")
async def get_chat_history(device_id: str, session_id: str):
    messages = await db.chat_messages.find({"device_id": device_id, "session_id": session_id}).sort("timestamp", 1).to_list(100)
    return [ChatMessage(**m) for m in messages]

@api_router.delete("/chat/history/{device_id}")
async def clear_chat_history(device_id: str):
    await db.chat_messages.delete_many({"device_id": device_id})
    return {"message": "Chat history cleared"}

app.include_router(api_router)

app.add_middleware(CORSMiddleware, allow_credentials=True, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
