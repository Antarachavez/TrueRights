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

# CATEGORIES
CATEGORIES = [
    {"id": "school", "name": "School", "icon": "school", "color": "#3B82F6", "description": "Know your rights at school",
     "subcategories": [
         {"id": "searches", "name": "Searches & Privacy", "icon": "search", "color": "#3B82F6"},
         {"id": "discipline", "name": "Discipline & Suspension", "icon": "warning", "color": "#EF4444"},
         {"id": "attendance", "name": "Attendance & Timing", "icon": "time", "color": "#F59E0B"},
         {"id": "expression", "name": "Free Speech & Expression", "icon": "megaphone", "color": "#8B5CF6"},
         {"id": "administration", "name": "Teachers & Admin", "icon": "people", "color": "#10B981"},
         {"id": "personal", "name": "Personal Items & Dress", "icon": "shirt", "color": "#EC4899"}
     ]},
    {"id": "work", "name": "Work", "icon": "briefcase", "color": "#F97316", "description": "Workplace rights",
     "subcategories": [
         {"id": "pay", "name": "Pay & Wages", "icon": "cash", "color": "#10B981"},
         {"id": "hours", "name": "Hours & Breaks", "icon": "time", "color": "#F97316"},
         {"id": "safety", "name": "Workplace Safety", "icon": "shield-checkmark", "color": "#EF4444"},
         {"id": "harassment", "name": "Harassment", "icon": "alert-circle", "color": "#DC2626"},
         {"id": "firing", "name": "Firing & Quitting", "icon": "exit", "color": "#6B7280"},
         {"id": "privacy", "name": "Privacy at Work", "icon": "eye-off", "color": "#8B5CF6"}
     ]},
    {"id": "housing", "name": "Housing", "icon": "home", "color": "#10B981", "description": "Tenant rights",
     "subcategories": [
         {"id": "entry", "name": "Landlord Entry", "icon": "key", "color": "#F97316"},
         {"id": "repairs", "name": "Repairs & Conditions", "icon": "construct", "color": "#3B82F6"},
         {"id": "eviction", "name": "Eviction & Moving", "icon": "log-out", "color": "#EF4444"},
         {"id": "deposits", "name": "Security Deposits", "icon": "cash", "color": "#10B981"},
         {"id": "lease", "name": "Lease & Rent", "icon": "document-text", "color": "#8B5CF6"},
         {"id": "roommates", "name": "Roommates & Guests", "icon": "people", "color": "#EC4899"}
     ]},
    {"id": "police", "name": "Police", "icon": "shield", "color": "#EF4444", "description": "Police interactions",
     "subcategories": [
         {"id": "stops", "name": "Being Stopped", "icon": "hand-left", "color": "#F97316"},
         {"id": "searches", "name": "Searches", "icon": "search", "color": "#EF4444"},
         {"id": "arrests", "name": "Arrests", "icon": "lock-closed", "color": "#DC2626"},
         {"id": "rights", "name": "Your Rights", "icon": "shield-checkmark", "color": "#3B82F6"},
         {"id": "recording", "name": "Recording Police", "icon": "videocam", "color": "#8B5CF6"},
         {"id": "complaints", "name": "Complaints", "icon": "document-text", "color": "#6B7280"}
     ]},
    {"id": "online", "name": "Online Privacy", "icon": "lock", "color": "#8B5CF6", "description": "Digital safety",
     "subcategories": [
         {"id": "social", "name": "Social Media", "icon": "share-social", "color": "#3B82F6"},
         {"id": "data", "name": "Data & Tracking", "icon": "analytics", "color": "#10B981"},
         {"id": "harassment", "name": "Online Harassment", "icon": "alert-circle", "color": "#EF4444"},
         {"id": "photos", "name": "Photos & Images", "icon": "images", "color": "#EC4899"},
         {"id": "accounts", "name": "Accounts & Security", "icon": "key", "color": "#F97316"},
         {"id": "school-monitoring", "name": "School Monitoring", "icon": "eye", "color": "#6B7280"}
     ]},
    {"id": "public", "name": "Public Spaces", "icon": "map-pin", "color": "#14B8A6", "description": "Public rights",
     "subcategories": [
         {"id": "filming", "name": "Filming & Photos", "icon": "camera", "color": "#3B82F6"},
         {"id": "protests", "name": "Protests", "icon": "megaphone", "color": "#EF4444"},
         {"id": "stores", "name": "Stores & Businesses", "icon": "storefront", "color": "#F97316"},
         {"id": "transport", "name": "Transportation", "icon": "bus", "color": "#10B981"},
         {"id": "parks", "name": "Parks & Streets", "icon": "leaf", "color": "#14B8A6"},
         {"id": "curfew", "name": "Curfews", "icon": "moon", "color": "#8B5CF6"}
     ]}
]

# SCENARIOS - More concise, natural language
SCENARIOS = {
    "school": {
        "searches": [
            {"id": "s1", "question": "Can they search my phone?", "short_answer": "They need a real reason to suspect YOU specifically broke a rule. Ask to call your parents first.", "explanation": "Schools can't just randomly grab phones. They need 'reasonable suspicion' - meaning something specific made them think YOU did something wrong.", "script": "I'd like to call my parent before you search my phone.", "next_steps": ["Stay calm", "Ask why they want to search", "Call a parent", "Write down what happened"]},
            {"id": "s2", "question": "Can they search my locker?", "short_answer": "Probably yes. Most schools own the lockers, so they can check them.", "explanation": "Lockers are usually school property. Your personal stuff inside might have more protection though.", "script": "Can I ask what this is about?", "next_steps": ["Stay calm", "Note who's there", "Tell your parents after"]},
            {"id": "s3", "question": "Can they go through my bag?", "short_answer": "Only if they have a specific reason to suspect you. Not just random bag checks.", "explanation": "Your backpack is your property. They need actual suspicion that YOU broke a rule, not just general searching.", "script": "What rule do you think I broke?", "next_steps": ["Ask why", "Don't consent but don't fight", "Document it"]},
            {"id": "s4", "question": "Can they search my car?", "short_answer": "If it's parked on school property, usually yes. You agreed to it by parking there.", "explanation": "Most parking permits include consent to search. Check what you signed.", "script": "Can I see the parking agreement I signed?", "next_steps": ["Check your permit", "Ask what they're looking for"]},
            {"id": "s5", "question": "Can they strip search me?", "short_answer": "Almost NEVER. This is extreme and usually illegal. Refuse and demand your parents.", "explanation": "The Supreme Court basically said no to this. Schools need crazy strong reasons.", "script": "No. I want my parents and a lawyer NOW.", "next_steps": ["Say no firmly", "Demand parents", "Report this immediately"]},
            {"id": "s6", "question": "Can a teacher look through my texts?", "short_answer": "Not without good reason. Your phone is private property.", "explanation": "Teachers need actual suspicion of rule-breaking, not just curiosity.", "script": "I don't consent to that. Can I call my parent?", "next_steps": ["Don't unlock it", "Ask for a parent", "Stay polite but firm"]},
            {"id": "s7", "question": "What if they find something?", "short_answer": "Depends what it is. Illegal stuff = police. Against rules = school punishment.", "explanation": "Drugs or weapons mean cops. Other stuff is usually just school discipline.", "script": "I'd like to call my parents before we go further.", "next_steps": ["Stay quiet", "Get your parents", "Get a lawyer for serious stuff"]}
        ],
        "discipline": [
            {"id": "d1", "question": "I'm getting suspended. What now?", "short_answer": "You have the right to know the charges and tell your side. Get it in writing.", "explanation": "For short suspensions, they have to tell you what you did and let you respond. Longer ones need formal hearings.", "script": "What exactly am I accused of? I want to explain my side.", "next_steps": ["Ask for specifics", "Tell your version", "Get it in writing", "Involve parents"]},
            {"id": "d2", "question": "Can they expel me?", "short_answer": "Only after a formal hearing where you can defend yourself and bring witnesses.", "explanation": "Expulsion is serious. You get a real hearing, can have a lawyer sometimes, and can appeal.", "script": "I want a formal hearing with my parents present.", "next_steps": ["Request formal hearing", "Bring witnesses", "Consider a lawyer", "Prepare your defense"]},
            {"id": "d3", "question": "Do I have to stay for detention?", "short_answer": "Usually yes, but your parents should be told and you still get bathroom breaks.", "explanation": "Schools can give detention. They should notify parents, especially for after-school.", "script": "Can you make sure my parents know about this?", "next_steps": ["Make sure parents know", "Figure out transportation", "Serve it", "Move on"]},
            {"id": "d4", "question": "Others got lighter punishment. Is that fair?", "short_answer": "Should be consistent. If it seems based on race, gender, etc., that's discrimination.", "explanation": "Schools can't punish you harder because of who you are. Document if you see a pattern.", "script": "I noticed others got different consequences. Can we discuss this?", "next_steps": ["Document similar cases", "Talk to counselor", "File complaint if needed"]},
            {"id": "d5", "question": "Can I appeal?", "short_answer": "Yes. Most schools have an appeals process. Ask for it in writing.", "explanation": "You can usually appeal suspensions, expulsions, and other big decisions.", "script": "I want to appeal. What's the process and deadline?", "next_steps": ["Get the process in writing", "Meet deadlines", "Gather evidence"]},
            {"id": "d6", "question": "Zero tolerance - do I have any rights?", "short_answer": "Yes! You still get to explain what happened. Context matters.", "explanation": "Zero tolerance doesn't mean zero rights. You can still explain circumstances.", "script": "I understand the policy, but can I explain what actually happened?", "next_steps": ["Explain context", "Ask about exceptions", "Involve parents"]},
            {"id": "d7", "question": "They want me to sign something. Should I?", "short_answer": "Read it first. You can ask for time and for parents to review it.", "explanation": "Don't sign anything you don't understand. Take it home if needed.", "script": "I want my parents to read this before I sign anything.", "next_steps": ["Read carefully", "Take it home", "Don't feel pressured"]},
            {"id": "d8", "question": "Can they search me after detention?", "short_answer": "Same rules as always - they need specific suspicion about you.", "explanation": "Detention doesn't give them extra search powers.", "script": "What's the reason for this search?", "next_steps": ["Ask why", "Don't consent unnecessarily", "Document it"]}
        ],
        "attendance": [
            {"id": "a1", "question": "What happens if I'm late a lot?", "short_answer": "Usually starts with warnings, then detention, then bigger consequences.", "explanation": "Schools track tardiness. It escalates: warnings → detention → parent meetings → worse.", "script": "I know I've been late. Can we talk about what's causing it?", "next_steps": ["Be honest", "Ask for help", "Make a plan", "Stick to it"]},
            {"id": "a2", "question": "What's an excused absence?", "short_answer": "Sickness, family emergency, religious holidays, mental health days (in some states).", "explanation": "Policies vary. Usually need a parent note or doctor note. Check your school's rules.", "script": "What documentation do you need?", "next_steps": ["Check school policy", "Get the right paperwork", "Turn it in on time"]},
            {"id": "a3", "question": "Can I leave early?", "short_answer": "Yes, but need parent permission and have to sign out at the office.", "explanation": "Schools are responsible for you. They need to know you're leaving.", "script": "My parent called the office. Where do I sign out?", "next_steps": ["Have parent call", "Go to office", "Sign out properly"]},
            {"id": "a4", "question": "What's truancy and why should I care?", "short_answer": "Too many unexcused absences. Can lead to fines, court, or parents getting in trouble.", "explanation": "States require you to be in school. Skip too much and it becomes a legal issue.", "script": "I'm having attendance issues. Can I talk to a counselor?", "next_steps": ["Talk to counselor", "Figure out what's going on", "Make a plan"]},
            {"id": "a5", "question": "Can I take a mental health day?", "short_answer": "More states allow this now. Check your state law or have a parent excuse you for 'illness.'", "explanation": "Mental health days are becoming recognized. Parents can usually excuse you anyway.", "script": "I need a day for mental health. Can my parent excuse me?", "next_steps": ["Talk to parent", "Check state law", "Get help if it's ongoing"]},
            {"id": "a6", "question": "My parent won't write a note. What do I do?", "short_answer": "Talk to a counselor. There might be bigger issues they can help with.", "explanation": "If you're missing school and parents won't help, counselors can step in.", "script": "I need help with my attendance situation.", "next_steps": ["Talk to counselor", "Be honest about home issues"]},
            {"id": "a7", "question": "Can they call the cops on me for skipping?", "short_answer": "Eventually, yes. Truancy officers exist. Don't let it get that far.", "explanation": "Excessive truancy can involve police and courts. It's serious.", "script": "I know I need to be here more. Can we make a plan?", "next_steps": ["Get help early", "Don't let it escalate"]}
        ],
        "expression": [
            {"id": "e1", "question": "Do I have free speech at school?", "short_answer": "Yes, but limited. Can't substantially disrupt learning or use vulgar language.", "explanation": "Supreme Court says students have rights, but schools can limit disruption.", "script": "I believe this is protected speech. Can we discuss?", "next_steps": ["Keep it peaceful", "Know the limits", "Document if censored unfairly"]},
            {"id": "e2", "question": "Can I organize a protest?", "short_answer": "You can express views, but might face consequences for missing class.", "explanation": "Walkouts are often protected, but you might get marked absent or get detention.", "script": "We want to organize a peaceful demonstration. What are the rules?", "next_steps": ["Know consequences first", "Keep it peaceful", "Have a clear message"]},
            {"id": "e3", "question": "Can I get in trouble for social media posts?", "short_answer": "Off-campus posts are mostly protected now. But threats or major disruptions = trouble.", "explanation": "2021 Supreme Court ruling protects most off-campus speech. Not everything though.", "script": "This was posted off-campus. Why am I being punished?", "next_steps": ["Know the recent law", "Document the post", "Get help if needed"]},
            {"id": "e4", "question": "Can they censor the school newspaper?", "short_answer": "Depends on your state. Some have strong student press protection.", "explanation": "Schools have more control over school-sponsored stuff. Check your state's press laws.", "script": "What's the legal basis for this censorship?", "next_steps": ["Check state press laws", "Contact Student Press Law Center"]},
            {"id": "e5", "question": "Can I wear political clothing?", "short_answer": "Usually yes, unless it's vulgar, promotes drugs, or causes real disruption.", "explanation": "Political messages are generally protected. The Tinker case protected armbands.", "script": "My shirt has a peaceful political message. What rule does it break?", "next_steps": ["Know dress code", "Keep messages appropriate", "Advocate for change"]},
            {"id": "e6", "question": "Can I practice my religion at school?", "short_answer": "YES. You can pray, wear religious items, and discuss your faith.", "explanation": "Schools can't promote religion, but students CAN practice theirs.", "script": "This is my personal religious practice, not the school endorsing it.", "next_steps": ["Know your rights", "Be respectful", "Report discrimination"]},
            {"id": "e7", "question": "Can they stop me from dying my hair?", "short_answer": "Depends on dress code. Can't discriminate against natural hairstyles though.", "explanation": "Some dress codes restrict unnatural colors. CROWN Act protects natural Black hairstyles.", "script": "Can you show me where this is in the dress code?", "next_steps": ["Check the code", "Know anti-discrimination laws"]},
            {"id": "e8", "question": "Can I start a club they don't like?", "short_answer": "If they allow other non-curriculum clubs, they have to treat yours equally.", "explanation": "Schools can't pick and choose which student clubs to allow based on viewpoint.", "script": "Other student clubs exist. Why is ours being treated differently?", "next_steps": ["Document unequal treatment", "Know the Equal Access Act"]}
        ],
        "administration": [
            {"id": "ad1", "question": "Can I fight a grade I think is unfair?", "short_answer": "Yes. Start with the teacher, then department head, then admin.", "explanation": "There's usually a process. Keep records of your work.", "script": "I'd like to discuss my grade. I think there might be an error.", "next_steps": ["Talk to teacher first", "Bring evidence", "Follow chain of command"]},
            {"id": "ad2", "question": "A teacher treats me unfairly. What can I do?", "short_answer": "Document it. Talk to counselor or admin. Involve parents if needed.", "explanation": "Teachers should treat everyone fairly. If it's discriminatory, it's illegal.", "script": "I'm having issues in this class. Can I talk to someone?", "next_steps": ["Document incidents", "Talk to counselor", "Involve parents"]},
            {"id": "ad3", "question": "How do I report bullying?", "short_answer": "Tell a trusted adult - teacher, counselor, admin. Most schools must investigate.", "explanation": "Schools are required to address bullying, especially if it's about race, gender, disability, etc.", "script": "I need to report bullying. I have documentation.", "next_steps": ["Document incidents", "Report to adult", "Follow up"]},
            {"id": "ad4", "question": "I have an IEP/504. School isn't following it.", "short_answer": "They MUST follow it. It's the law. Request an IEP meeting.", "explanation": "IEPs and 504 plans are legal documents. Non-compliance can be reported.", "script": "My IEP says I get [accommodation]. This isn't being provided.", "next_steps": ["Know your plan", "Document non-compliance", "Request meeting", "File complaint if needed"]},
            {"id": "ad5", "question": "Can I see the school counselor?", "short_answer": "Yes. For urgent stuff, you should be able to see them quickly.", "explanation": "Counselors are there to help. You have a right to support.", "script": "I need to talk to a counselor about something important.", "next_steps": ["Ask to see them", "Use 'urgent' if needed", "Know crisis resources"]},
            {"id": "ad6", "question": "Can I see my school records?", "short_answer": "Yes. You and your parents have that right under FERPA.", "explanation": "FERPA gives you the right to access and request corrections to your records.", "script": "I'd like to see my educational records.", "next_steps": ["Submit written request", "Review within 45 days"]}
        ],
        "personal": [
            {"id": "p1", "question": "Can they take my phone all day?", "short_answer": "Many schools do this. Check if it's in the handbook you agreed to.", "explanation": "Schools can restrict phones during class. All-day policies vary.", "script": "When will I get it back? Is it stored securely?", "next_steps": ["Know the policy", "Follow it", "Get it back after"]},
            {"id": "p2", "question": "Is the dress code fair?", "short_answer": "It can't discriminate based on gender, race, or religion.", "explanation": "Dress codes must be applied equally. Sexist or racist enforcement is illegal.", "script": "I'm concerned this rule is applied differently to different groups.", "next_steps": ["Read full code", "Document unequal enforcement"]},
            {"id": "p3", "question": "Can I carry my medication?", "short_answer": "Usually needs documentation. Emergency meds like inhalers/EpiPens often get exceptions.", "explanation": "Most meds go to the nurse. You can often carry emergency ones with paperwork.", "script": "I need to carry my medication. What forms do I need?", "next_steps": ["Get doctor documentation", "Fill out school forms"]},
            {"id": "p4", "question": "Can they tell me how to wear my hair?", "short_answer": "Many states now protect natural hairstyles. Check the CROWN Act.", "explanation": "Schools can't ban braids, locs, twists, etc. That's often discrimination.", "script": "I believe this policy might be discriminatory.", "next_steps": ["Know your state laws", "Cite CROWN Act if applicable"]},
            {"id": "p5", "question": "They won't let me use the bathroom. Is that legal?", "short_answer": "Overly restrictive bathroom policies can be challenged, especially for health reasons.", "explanation": "You have a right to use the bathroom. Extreme restrictions aren't okay.", "script": "I need to use the bathroom and this is affecting my health.", "next_steps": ["Get medical documentation if needed", "Talk to counselor"]},
            {"id": "p6", "question": "What are my rights as an LGBTQ+ student?", "short_answer": "You can be out, form clubs, and should be free from harassment.", "explanation": "LGBTQ+ students are protected from discrimination. Many places recognize chosen names/pronouns.", "script": "I want to be called by my correct name and pronouns.", "next_steps": ["Know your state's protections", "Talk to counselor", "Report discrimination"]}
        ]
    },
    "work": {
        "pay": [
            {"id": "wp1", "question": "Am I getting paid enough?", "short_answer": "Must be at least minimum wage. Check your state - it might be higher than federal.", "explanation": "Federal is $7.25/hr. Many states and cities are higher. Tipped workers have different rules but must still hit minimum.", "script": "Can you show me my hourly rate and any deductions?", "next_steps": ["Check your state's minimum", "Review pay stubs", "Report violations"]},
            {"id": "wp2", "question": "Can they make me work off the clock?", "short_answer": "NO. If you're hourly, every minute of work must be paid.", "explanation": "Working 'off the clock' is illegal. Before shift, after shift, through breaks - all counts.", "script": "I want to make sure I'm clocking all my time.", "next_steps": ["Track your hours", "Document unpaid time", "Report to labor dept"]},
            {"id": "wp3", "question": "When do I get overtime?", "short_answer": "Over 40 hours/week = time and a half. Some states have daily overtime too.", "explanation": "Non-exempt workers get 1.5x pay after 40 hours. Salary doesn't automatically mean no overtime.", "script": "I worked over 40 hours. Will I get overtime pay?", "next_steps": ["Track hours", "Know if you're exempt", "Check state laws"]},
            {"id": "wp4", "question": "Can they take money from my check?", "short_answer": "Only taxes and stuff you agreed to in writing. Can't drop you below minimum wage.", "explanation": "Employers need written consent for most deductions. Uniforms, shortages - usually need your okay.", "script": "What's this deduction? I didn't authorize it.", "next_steps": ["Review stubs", "Ask about deductions", "Report illegal ones"]},
            {"id": "wp5", "question": "Can my boss take my tips?", "short_answer": "No. Tips are yours. Managers usually can't take from tip pools either.", "explanation": "Tip pooling with other workers can be okay. But your boss keeping tips? Illegal.", "script": "How exactly are tips distributed here?", "next_steps": ["Know tip laws", "Track your tips", "Report violations"]},
            {"id": "wp6", "question": "My paycheck bounced. Now what?", "short_answer": "This is illegal. They owe you the money plus often penalties.", "explanation": "Employers must pay for work done. Bounced checks can get them in serious trouble.", "script": "My check didn't clear. When will I get my money?", "next_steps": ["Document it", "Notify in writing", "File wage complaint"]},
            {"id": "wp7", "question": "I'm paid less than coworkers doing the same job.", "short_answer": "If it's because of your race, gender, etc., that's illegal discrimination.", "explanation": "Equal pay laws exist. Different pay for same work based on protected characteristics = illegal.", "script": "I'd like to understand how pay is determined.", "next_steps": ["Document differences", "Ask HR", "File complaint if discriminatory"]},
            {"id": "wp8", "question": "Can they pay me less because I'm young?", "short_answer": "There's a lower 'youth minimum wage' in some places for the first 90 days only.", "explanation": "After 90 days, same minimum wage applies. Check your state's rules.", "script": "How long does the training wage apply?", "next_steps": ["Know the rules", "Track your days", "Ask after 90 days"]}
        ],
        "hours": [
            {"id": "wh1", "question": "Do I get breaks?", "short_answer": "Depends on state. Many require meal and rest breaks for longer shifts.", "explanation": "Federal law doesn't require breaks, but many states do. Minors usually get more.", "script": "What's the break policy here?", "next_steps": ["Look up state law", "Check company policy", "Document denied breaks"]},
            {"id": "wh2", "question": "Can they change my schedule last minute?", "short_answer": "Usually yes, unless you're in a city with predictive scheduling laws.", "explanation": "Most workers don't have schedule protection. Some cities require advance notice.", "script": "What's the policy on schedule changes?", "next_steps": ["Check local laws", "Ask about notice policy"]},
            {"id": "wh3", "question": "Can I refuse overtime?", "short_answer": "Usually they can require it, but they MUST pay you time and a half.", "explanation": "Most places can mandate overtime. You must be paid for it though.", "script": "I can work overtime. Can you confirm the rate?", "next_steps": ["Know your rights", "Get paid properly"]},
            {"id": "wh4", "question": "They want me to stay late. Do I get paid?", "short_answer": "Yes. All time worked must be paid. Clock out when you ACTUALLY leave.", "explanation": "If they require you to stay, it's work time. Period.", "script": "I'll clock out when I actually leave, right?", "next_steps": ["Clock all time", "Document late stays"]},
            {"id": "wh5", "question": "How many hours can I work as a minor?", "short_answer": "Limited. Usually 3hrs on school days, 18hrs in school week for under 16.", "explanation": "Strict limits exist for workers under 18. Varies by age and school schedule.", "script": "Can you verify my hours are legal for my age?", "next_steps": ["Know state rules", "Track hours", "Speak up if exceeded"]},
            {"id": "wh6", "question": "Can they schedule me during school?", "short_answer": "Not during school hours if you're required to be there.", "explanation": "School comes first. Employers can't schedule you during class.", "script": "I can't work during school hours.", "next_steps": ["Give your school schedule", "Stand firm"]},
            {"id": "wh7", "question": "I worked through lunch. Do I get paid?", "short_answer": "Yes. If you worked, you get paid. Even if you were 'supposed' to be on break.", "explanation": "Working through a break = paid time. Can't be denied.", "script": "I worked through my break. I'm logging that time.", "next_steps": ["Log the time", "Document it"]}
        ],
        "safety": [
            {"id": "ws1", "question": "This place seems unsafe. What can I do?", "short_answer": "Report it. You can even file anonymous OSHA complaints.", "explanation": "OSHA requires safe workplaces. You're protected from retaliation for reporting.", "script": "I'm concerned about a safety issue.", "next_steps": ["Document it", "Report to supervisor", "File OSHA complaint if ignored"]},
            {"id": "ws2", "question": "I got hurt at work. Now what?", "short_answer": "Report it immediately. You might qualify for workers' comp.", "explanation": "Workers' comp covers medical bills and lost wages. Don't need to prove fault.", "script": "I got injured at work. I need to report this.", "next_steps": ["Report immediately", "Get medical care", "File workers' comp"]},
            {"id": "ws3", "question": "Do they have to give me safety gear?", "short_answer": "Yes. Employers must provide and pay for required safety equipment.", "explanation": "OSHA requires employers to give you PPE free of charge.", "script": "I need proper safety equipment for this job.", "next_steps": ["Request it", "Document the request", "Report if denied"]},
            {"id": "ws4", "question": "Can I refuse dangerous work?", "short_answer": "Only if there's immediate serious danger and no other option.", "explanation": "Limited right to refuse. Danger must be immediate and you must have tried other ways.", "script": "This seems dangerous. Can we discuss safety measures?", "next_steps": ["Explain concerns", "Ask for alternatives", "Document everything"]},
            {"id": "ws5", "question": "They're not following COVID/health rules.", "short_answer": "Report to OSHA or your local health department.", "explanation": "Employers must follow health guidelines. Violations are reportable.", "script": "I'm concerned about health protocols here.", "next_steps": ["Document violations", "Report to OSHA or health dept"]}
        ],
        "harassment": [
            {"id": "wha1", "question": "What counts as sexual harassment?", "short_answer": "Unwanted sexual comments, touching, requests for dates, quid pro quo.", "explanation": "Anything unwelcome and sexual that affects your job or creates a hostile environment.", "script": "I need to report harassment.", "next_steps": ["Document incidents", "Report to HR", "File EEOC complaint"]},
            {"id": "wha2", "question": "I'm being treated differently because of who I am.", "short_answer": "Discrimination based on race, gender, religion, etc. is illegal.", "explanation": "Protected characteristics: race, color, religion, sex, national origin, age, disability, and more.", "script": "I'm concerned about discriminatory treatment.", "next_steps": ["Document everything", "Report to HR", "File EEOC complaint"]},
            {"id": "wha3", "question": "What's a hostile work environment?", "short_answer": "When harassment is so bad or constant that it makes work impossible.", "explanation": "Not one bad joke. It's ongoing patterns or extreme single incidents.", "script": "The ongoing behavior is affecting my ability to work.", "next_steps": ["Keep detailed records", "Report to management", "File complaint"]},
            {"id": "wha4", "question": "Can they punish me for reporting?", "short_answer": "No. Retaliation is illegal.", "explanation": "Can't fire, demote, or punish you for reporting harassment, even if complaint doesn't pan out.", "script": "I'm concerned about retaliation.", "next_steps": ["Document any changes", "Report retaliation too"]},
            {"id": "wha5", "question": "HR isn't helping. Now what?", "short_answer": "File with the EEOC or your state's civil rights agency.", "explanation": "If internal complaints fail, government agencies can investigate.", "script": "I'd like to file an external complaint.", "next_steps": ["File with EEOC", "Consider a lawyer"]}
        ],
        "firing": [
            {"id": "wf1", "question": "Can they fire me for no reason?", "short_answer": "In most states, yes. But not for illegal reasons like discrimination.", "explanation": "Most workers are 'at-will.' Either side can end it. But illegal reasons (discrimination, retaliation) are still illegal.", "script": "Can I get the reason for termination in writing?", "next_steps": ["Ask for written reason", "Check for illegal reasons", "File complaint if needed"]},
            {"id": "wf2", "question": "When do I get my last paycheck?", "short_answer": "Depends on state. Some say immediately, others say next regular payday.", "explanation": "State laws vary. All owed wages must be paid.", "script": "When will I receive my final pay?", "next_steps": ["Know state law", "Verify amount", "File complaint if unpaid"]},
            {"id": "wf3", "question": "Can I get unemployment?", "short_answer": "Usually yes if you're fired (not for serious misconduct) or laid off.", "explanation": "Quitting usually doesn't qualify unless you had good cause.", "script": "I'm applying for unemployment. Can I get my separation info?", "next_steps": ["Apply quickly", "Appeal if denied"]},
            {"id": "wf4", "question": "Do I have to give two weeks notice?", "short_answer": "Usually no, it's just polite. But check your contract.", "explanation": "Two weeks is courtesy, not law. Some contracts may require notice.", "script": "I'm resigning effective [date].", "next_steps": ["Check contract", "Give notice if possible"]},
            {"id": "wf5", "question": "They want me to sign something when I leave.", "short_answer": "Read it carefully. You might be giving up rights. Take time to review.", "explanation": "Severance agreements often waive your right to sue. Understand before signing.", "script": "I'd like time to review this before signing.", "next_steps": ["Read carefully", "Consider a lawyer", "Don't feel rushed"]}
        ],
        "privacy": [
            {"id": "wpr1", "question": "Can they read my work emails?", "short_answer": "Yes. Work email = work property. Don't use it for personal stuff.", "explanation": "Anything on company systems can be monitored. Use personal devices for private matters.", "script": "I understand work email is monitored.", "next_steps": ["Don't expect privacy", "Use personal devices for personal stuff"]},
            {"id": "wpr2", "question": "Can they drug test me?", "short_answer": "Often yes for hiring. Random testing varies by state and job.", "explanation": "Rules vary. Safety-sensitive jobs have more testing. Some states protect off-duty marijuana use.", "script": "What's the drug testing policy?", "next_steps": ["Know state laws", "Understand the policy"]},
            {"id": "wpr3", "question": "Can I be fired for social media posts?", "short_answer": "Often yes. But discussing wages or working conditions is usually protected.", "explanation": "Private employers can fire for posts. But talking about work conditions = often protected.", "script": "What social media activities affect employment?", "next_steps": ["Know what's protected", "Be careful online"]},
            {"id": "wpr4", "question": "Can they check my criminal record?", "short_answer": "Yes, but many places limit WHEN they can ask. 'Ban the box' laws help.", "explanation": "Many states make employers wait until later to ask about criminal history.", "script": "How is criminal history considered in hiring?", "next_steps": ["Know your state's laws", "Be honest when asked"]}
        ]
    },
    "housing": {
        "entry": [
            {"id": "he1", "question": "Can my landlord just walk in?", "short_answer": "No. Most places require 24-48 hours notice. Emergencies only exception.", "explanation": "You have the right to 'quiet enjoyment.' They can't just show up.", "script": "I need proper notice before any entry.", "next_steps": ["Check state law", "Review lease", "Send written request"]},
            {"id": "he2", "question": "What counts as an emergency?", "short_answer": "Fire, flooding, gas leak. NOT routine stuff or wanting to 'check.'", "explanation": "Real emergencies only. A repair that can wait isn't an emergency.", "script": "This doesn't seem like an emergency. I'd like notice.", "next_steps": ["Know what's really emergency", "Document any entry"]},
            {"id": "he3", "question": "Can I change my locks?", "short_answer": "Usually yes, but you may have to give landlord a key.", "explanation": "You can change locks for safety. Check your lease. DV victims often have extra protections.", "script": "I'd like to change locks for safety. What's the process?", "next_steps": ["Check lease", "Give key if required"]},
            {"id": "he4", "question": "They keep showing my apartment to people.", "short_answer": "They can show it with proper notice, but you can request reasonable times.", "explanation": "Landlords can show to prospective tenants/buyers. But must give notice.", "script": "Can we schedule showings at convenient times?", "next_steps": ["Know notice requirements", "Request reasonable times"]}
        ],
        "repairs": [
            {"id": "hr1", "question": "Landlord won't fix stuff. What now?", "short_answer": "Put request in writing. You may be able to withhold rent or fix it yourself.", "explanation": "Landlords must keep places livable. Document everything.", "script": "I reported this on [date]. Can you give me a repair timeline in writing?", "next_steps": ["Request in writing", "Take photos", "Know state options"]},
            {"id": "hr2", "question": "No heat or hot water!", "short_answer": "This is an emergency. They must fix it fast or face consequences.", "explanation": "Heat and hot water are basic requirements. This is urgent.", "script": "No heat/hot water is an emergency. I need this fixed within 24 hours.", "next_steps": ["Report immediately", "Document", "Call code enforcement"]},
            {"id": "hr3", "question": "There's mold or bugs.", "short_answer": "Usually landlord's problem. Document it and report in writing.", "explanation": "Mold and pests are typically landlord responsibility.", "script": "I'm reporting a mold/pest issue. This is a health hazard.", "next_steps": ["Take photos", "Report in writing", "See doctor if needed"]},
            {"id": "hr4", "question": "Can they evict me for asking for repairs?", "short_answer": "No. That's illegal retaliation.", "explanation": "Landlords can't punish you for requesting repairs or calling code enforcement.", "script": "I'm documenting this as exercising my legal tenant rights.", "next_steps": ["Document timeline", "Report retaliation"]}
        ],
        "eviction": [
            {"id": "hev1", "question": "Can they kick me out right now?", "short_answer": "No. Eviction requires legal process, notice, usually court.", "explanation": "They can't just force you out. There's a legal process.", "script": "I need to see the formal eviction notice.", "next_steps": ["Don't leave without process", "Know notice requirements", "Get legal help"]},
            {"id": "hev2", "question": "How much notice do I get?", "short_answer": "Varies by reason and state. Usually 3-30 days before court.", "explanation": "Non-payment: usually 3-14 days. Other reasons: 14-30 days. No-cause: 30-60 days.", "script": "What's the timeline for this?", "next_steps": ["Read notice carefully", "Note deadline", "Respond in time"]},
            {"id": "hev3", "question": "They locked me out or shut off utilities!", "short_answer": "ILLEGAL. Call police and sue them.", "explanation": "Landlords can't lock you out, take your stuff, or shut off utilities. It's a crime.", "script": "This is an illegal lockout. I'm calling police.", "next_steps": ["Call police", "Document everything", "Sue them"]},
            {"id": "hev4", "question": "Will eviction show on my record?", "short_answer": "Court filings are public. Even cases you win might show up.", "explanation": "Eviction records can appear on tenant screening. Some states allow sealing.", "script": "How will this affect my record?", "next_steps": ["Try to settle", "Get case dismissed if possible", "Know sealing laws"]}
        ],
        "deposits": [
            {"id": "hd1", "question": "When do I get my deposit back?", "short_answer": "Usually 14-30 days after moving out. Must include itemized list.", "explanation": "State laws set deadlines. They must list any deductions with receipts.", "script": "I've moved out. When will I get my deposit and itemized list?", "next_steps": ["Give forwarding address", "Document condition at move-out"]},
            {"id": "hd2", "question": "They're keeping it for normal wear and tear.", "short_answer": "That's not allowed. Normal wear can't be deducted.", "explanation": "Faded paint, worn carpet = normal. Holes, stains = damage.", "script": "These charges are for normal wear and tear. I'm disputing them.", "next_steps": ["Document everything", "Dispute in writing", "Sue in small claims"]},
            {"id": "hd3", "question": "How much can they charge upfront?", "short_answer": "Many states cap deposits at 1-2 months rent.", "explanation": "Check your state's limits on security and pet deposits.", "script": "Does this deposit comply with state limits?", "next_steps": ["Know state limits", "Get receipts"]}
        ],
        "lease": [
            {"id": "hl1", "question": "Can I break my lease early?", "short_answer": "You might owe money, but landlords must try to re-rent.", "explanation": "Breaking lease has consequences, but they can't just let it sit empty and charge you.", "script": "I need to break my lease. What are my options?", "next_steps": ["Read lease", "Give notice", "Know mitigation rules"]},
            {"id": "hl2", "question": "Can they raise my rent?", "short_answer": "Not during lease. After, they need proper notice. Rent control may apply.", "explanation": "During lease = usually fixed. After = can raise with notice.", "script": "What's the process for rent increases?", "next_steps": ["Check lease", "Know notice requirements", "Check for rent control"]},
            {"id": "hl3", "question": "My lease has weird terms. Are they legal?", "short_answer": "Illegal terms are unenforceable. You can't sign away your rights.", "explanation": "Terms like 'landlord not responsible for anything' usually aren't enforceable.", "script": "I don't think this term is legal.", "next_steps": ["Know tenant rights", "Consult legal aid"]}
        ],
        "roommates": [
            {"id": "hro1", "question": "Roommate bailed. Am I stuck paying everything?", "short_answer": "If you're both on the lease, landlord can go after either of you for full rent.", "explanation": "Joint and several liability means either roommate can be held responsible for all.", "script": "My roommate left. What are my options?", "next_steps": ["Talk to landlord", "Find replacement", "Get things in writing"]},
            {"id": "hro2", "question": "Can I sublet or get a roommate?", "short_answer": "Check your lease. Usually need landlord permission.", "explanation": "Most leases require approval for new occupants or subletters.", "script": "What's the process for adding a roommate?", "next_steps": ["Read lease", "Get written permission"]},
            {"id": "hro3", "question": "Can landlord limit my guests?", "short_answer": "Some limits on long-term guests are okay. Can't ban normal visitors.", "explanation": "Overnight guests for 7-14 days usually fine. Living there = different.", "script": "What's the guest policy?", "next_steps": ["Know the limits", "Consider adding to lease if permanent"]}
        ]
    },
    "police": {
        "stops": [
            {"id": "ps1", "question": "Cops stopped me walking. What do I do?", "short_answer": "Stay calm. Hands visible. Ask if you're free to go.", "explanation": "You can ask if you're detained. If not, you can leave. Don't run.", "script": "Am I free to go or am I being detained?", "next_steps": ["Stay calm", "Hands visible", "Ask if free to go", "Don't run"]},
            {"id": "ps2", "question": "What about traffic stops?", "short_answer": "Pull over safely. Hands on wheel. Give license/registration when asked.", "explanation": "Pull over, turn off car, hands visible, announce movements.", "script": "I'm reaching for my license in my [location].", "next_steps": ["Pull over safely", "Stay calm", "Hands on wheel"]},
            {"id": "ps3", "question": "Can I walk away?", "short_answer": "Ask if you're detained. If no, leave calmly. Never run.", "explanation": "If they have 'reasonable suspicion,' they can briefly detain you.", "script": "Am I being detained? If not, I'm leaving.", "next_steps": ["Ask clearly", "Wait for answer", "Leave calmly if free"]},
            {"id": "ps4", "question": "Do I have to give my name?", "short_answer": "In most states, yes if detained. Other questions? You can stay silent.", "explanation": "Most states require name when lawfully detained. Nothing else though.", "script": "I'll give my name. I'm staying silent on other questions.", "next_steps": ["Know your state's law", "Give name if required"]}
        ],
        "searches": [
            {"id": "pse1", "question": "Can they search me?", "short_answer": "Pat-down for weapons needs reasonable suspicion. Full search needs more.", "explanation": "Quick frisk for weapons if they think you're armed. Full search = probable cause, consent, or arrest.", "script": "I don't consent to a search.", "next_steps": ["Say you don't consent", "Don't resist physically"]},
            {"id": "pse2", "question": "Can they search my car?", "short_answer": "They need probable cause, consent, or warrant. Say you don't consent.", "explanation": "Smell drugs, see contraband = probable cause. You can always refuse consent.", "script": "I don't consent to a search of my car.", "next_steps": ["Don't consent", "Don't unlock/open", "Stay polite"]},
            {"id": "pse3", "question": "Can they go through my phone?", "short_answer": "NO. Supreme Court says they need a warrant. Don't unlock it.", "explanation": "Phones require warrants. Don't unlock it, give passwords, or use face/fingerprint.", "script": "I don't consent to searching my phone. Show me a warrant.", "next_steps": ["Don't unlock", "Don't give password", "Ask for warrant"]},
            {"id": "pse4", "question": "Can they search my house?", "short_answer": "Need warrant, consent, or emergency. Don't let them in.", "explanation": "Your home has strong protection. Don't invite them in.", "script": "I don't consent. Please show a warrant.", "next_steps": ["Don't invite in", "Step outside to talk", "Ask for warrant"]},
            {"id": "pse5", "question": "What about drug dogs?", "short_answer": "Can't extend a stop just to bring dogs. If already there, sniff is allowed.", "explanation": "They can't hold you longer than normal stop to wait for K-9.", "script": "Is this stop taking longer than necessary?", "next_steps": ["Know the limits", "Challenge in court"]}
        ],
        "arrests": [
            {"id": "pa1", "question": "I'm being arrested. What now?", "short_answer": "Don't resist. Say 'I want a lawyer' and 'I'm staying silent.'", "explanation": "Even if arrest is wrong, don't fight. Challenge it in court.", "script": "I'm not resisting. I want a lawyer. I'm staying silent.", "next_steps": ["Don't resist", "Ask for lawyer", "Stay quiet"]},
            {"id": "pa2", "question": "What are Miranda rights?", "short_answer": "Right to silence and right to lawyer before questioning.", "explanation": "After arrest, they must read these before questioning. Invoke them.", "script": "I'm invoking my right to remain silent and I want a lawyer.", "next_steps": ["Remember these rights", "Invoke clearly", "Stop talking"]},
            {"id": "pa3", "question": "Do I get a phone call?", "short_answer": "Yes. Usually within reasonable time after arrest.", "explanation": "You can call lawyer and family. Timing varies.", "script": "I'd like to make my phone call.", "next_steps": ["Ask for call", "Call lawyer first"]},
            {"id": "pa4", "question": "How does bail work?", "short_answer": "Money to get out before trial. Pay full amount (returned later) or use bondsman (10% fee).", "explanation": "Amount depends on charge and your situation.", "script": "I'd like a bail hearing.", "next_steps": ["Ask about bail", "Contact family", "Show up to court"]}
        ],
        "rights": [
            {"id": "pr1", "question": "What's the right to remain silent?", "short_answer": "You don't have to answer questions. Can't be used against you.", "explanation": "Fifth Amendment. You can refuse to answer. Just say it clearly.", "script": "I'm exercising my right to remain silent.", "next_steps": ["State it clearly", "Stop talking"]},
            {"id": "pr2", "question": "When can I have a lawyer?", "short_answer": "Before and during any questioning. If you can't afford one, you get one free.", "explanation": "Once you ask for a lawyer, questioning must stop.", "script": "I want a lawyer before answering anything.", "next_steps": ["Ask immediately", "Don't waive this right"]},
            {"id": "pr3", "question": "What if they arrested me unfairly?", "short_answer": "Don't resist. Document everything. Challenge it in court.", "explanation": "Fighting makes it worse. Get justice through the legal system.", "script": "I believe this is unlawful but I'm not resisting. I want a lawyer.", "next_steps": ["Don't resist", "Document", "Get lawyer", "File complaint"]}
        ],
        "recording": [
            {"id": "pre1", "question": "Can I record police?", "short_answer": "Yes. In public, from a safe distance, without interfering.", "explanation": "First Amendment protects this. Stay back and don't get in the way.", "script": "I'm recording from a safe distance without interfering.", "next_steps": ["Keep distance", "Don't interfere", "Back up video"]},
            {"id": "pre2", "question": "Can they make me delete it?", "short_answer": "No. That's illegal. Don't unlock your phone for them.", "explanation": "They can't legally make you delete recordings.", "script": "I don't consent to deleting recordings or unlocking my phone.", "next_steps": ["Don't delete", "Don't unlock"]}
        ],
        "complaints": [
            {"id": "pc1", "question": "How do I file a complaint?", "short_answer": "Internal affairs, civilian review board, or DOJ for serious stuff.", "explanation": "Most departments have complaint processes. Document everything first.", "script": "I want to file a formal complaint.", "next_steps": ["Document everything", "File written complaint", "Keep copies"]},
            {"id": "pc2", "question": "Can I sue the police?", "short_answer": "Yes for civil rights violations, but it's hard. Get a lawyer.", "explanation": "Section 1983 lawsuits exist. Police have some immunity. It's complicated.", "script": "I want to talk to a civil rights attorney.", "next_steps": ["Document everything", "Find lawyer", "Know time limits"]}
        ]
    },
    "online": {
        "social": [
            {"id": "os1", "question": "Who can see my posts?", "short_answer": "Check privacy settings. But anyone who sees can screenshot.", "explanation": "Settings control direct viewing. Nothing is truly private.", "script": "Where are my privacy settings?", "next_steps": ["Check settings", "Audit regularly"]},
            {"id": "os2", "question": "Can I really delete something?", "short_answer": "From the platform, yes. But screenshots and copies may exist.", "explanation": "The internet is forever. Think before posting.", "script": "How do I delete this?", "next_steps": ["Delete from platform", "Know copies may exist"]},
            {"id": "os3", "question": "Someone hacked my account.", "short_answer": "Change passwords, enable 2FA, report to platform, warn contacts.", "explanation": "Act fast. Secure everything.", "script": "My account was hacked. I need help.", "next_steps": ["Change passwords", "Enable 2FA", "Report", "Warn friends"]},
            {"id": "os4", "question": "Someone's pretending to be me online.", "short_answer": "Report to platform. It violates terms of service.", "explanation": "Most platforms have impersonation reporting.", "script": "I need to report a fake account.", "next_steps": ["Report to platform", "Document it"]}
        ],
        "data": [
            {"id": "od1", "question": "What data do apps collect?", "short_answer": "Usually a lot: location, browsing, purchases, messages.", "explanation": "Read privacy policies. They're long but tell you what's collected.", "script": "What data do you collect about me?", "next_steps": ["Read privacy policies", "Check settings"]},
            {"id": "od2", "question": "Can I get my data deleted?", "short_answer": "Yes in some states (like California). Many companies offer it anyway.", "explanation": "CCPA and similar laws give deletion rights.", "script": "I want to request deletion of my data.", "next_steps": ["Find deletion option", "Submit request"]}
        ],
        "harassment": [
            {"id": "oh1", "question": "Someone's cyberbullying me.", "short_answer": "Screenshot, block, report. If threats, tell an adult and maybe police.", "explanation": "Document everything. Get help for serious stuff.", "script": "I'm being cyberbullied and I have documentation.", "next_steps": ["Screenshot", "Block", "Report", "Tell trusted adult"]},
            {"id": "oh2", "question": "Someone posted my personal info (doxxing).", "short_answer": "Report for removal. Call police if there are threats.", "explanation": "Doxxing can be dangerous. Take it seriously.", "script": "My info was posted without consent. Remove it.", "next_steps": ["Report for removal", "Police if threats", "Secure accounts"]},
            {"id": "oh3", "question": "I got threats online.", "short_answer": "Take it seriously. Screenshot, report, contact police.", "explanation": "Online threats can be crimes. Document everything.", "script": "I've received threats. Reporting to police.", "next_steps": ["Screenshot", "Report", "Contact police"]}
        ],
        "photos": [
            {"id": "op1", "question": "Someone posted my photo without asking.", "short_answer": "In public, usually legal. For harassment or profit, you may have recourse.", "explanation": "Public photos are generally okay. Intimate images have special protections.", "script": "This photo was used harmfully. I need it removed.", "next_steps": ["Report to platform", "Check laws"]},
            {"id": "op2", "question": "Someone shared intimate images of me.", "short_answer": "This is illegal in most states. Report to platform AND police.", "explanation": "'Revenge porn' is illegal. Get help.", "script": "Intimate images shared without consent. This is illegal.", "next_steps": ["Report to platform", "Contact police", "Call Cyber Civil Rights Initiative"]}
        ],
        "accounts": [
            {"id": "oa1", "question": "Can school/parents demand my passwords?", "short_answer": "Parents often can for minors. Schools usually can't for personal accounts.", "explanation": "Parents have authority over kids' accounts. Schools can access school accounts, not personal.", "script": "Why is my password being requested?", "next_steps": ["Understand who's asking", "Protect personal accounts"]},
            {"id": "oa2", "question": "How do I make my accounts secure?", "short_answer": "Strong unique passwords, 2FA, watch for phishing.", "explanation": "Use different passwords. Turn on two-factor. Don't click sketchy links.", "script": "How do I enable two-factor?", "next_steps": ["Use password manager", "Enable 2FA", "Watch for scams"]}
        ],
        "school-monitoring": [
            {"id": "osm1", "question": "Can school see what I do on school devices?", "short_answer": "YES. Everything. Don't expect privacy on school stuff.", "explanation": "School devices are fully monitored. Never use for personal things.", "script": "I'll use my personal device for personal stuff.", "next_steps": ["Don't use for private things", "Use personal devices"]},
            {"id": "osm2", "question": "Can they track me at home?", "short_answer": "If using school device or logged into school accounts, probably yes.", "explanation": "Monitoring software works everywhere. School accounts may also track.", "script": "I'll log out of school accounts at home.", "next_steps": ["Use personal device at home", "Log out of school accounts"]}
        ]
    },
    "public": {
        "filming": [
            {"id": "pf1", "question": "Can I take photos on the street?", "short_answer": "Yes. Public places = no expectation of privacy.", "explanation": "Photography in public is generally legal.", "script": "I'm in a public space.", "next_steps": ["Stay in public areas", "Be respectful"]},
            {"id": "pf2", "question": "Can I film cops?", "short_answer": "Yes. It's your First Amendment right. Keep safe distance, don't interfere.", "explanation": "Recording police is protected. Just stay back.", "script": "I'm exercising my right to record police.", "next_steps": ["Keep distance", "Don't interfere", "Back up footage"]},
            {"id": "pf3", "question": "Can I film in stores?", "short_answer": "Only with permission. Private property, their rules.", "explanation": "Businesses can ban photography. If asked to stop, do it or leave.", "script": "Am I allowed to take photos here?", "next_steps": ["Ask permission", "Leave if asked"]}
        ],
        "protests": [
            {"id": "pp1", "question": "What are my rights at protests?", "short_answer": "First Amendment protects peaceful assembly. Know the limits.", "explanation": "You can protest peacefully. Don't block traffic or trespass.", "script": "I'm exercising my right to peaceful assembly.", "next_steps": ["Stay peaceful", "Know permit rules", "Document if rights violated"]},
            {"id": "pp2", "question": "Do I need a permit?", "short_answer": "Large organized events often yes. Small spontaneous groups usually no.", "explanation": "Check local rules. Sidewalk gatherings usually fine.", "script": "What are the permit requirements?", "next_steps": ["Check local rules", "Apply if needed"]},
            {"id": "pp3", "question": "What if I'm arrested at a protest?", "short_answer": "Don't resist. Say 'I want a lawyer' and stay silent.", "explanation": "May be charged with trespassing or disorderly conduct.", "script": "I'm not resisting. I want a lawyer. Staying silent.", "next_steps": ["Don't resist", "Ask for lawyer"]}
        ],
        "stores": [
            {"id": "pst1", "question": "Can a store hold me for shoplifting?", "short_answer": "Briefly, if they have reasonable belief. Must be reasonable.", "explanation": "'Shopkeeper's privilege' allows brief detention with good reason.", "script": "I haven't taken anything. Call police if you think I have.", "next_steps": ["Stay calm", "Don't run", "Ask for manager"]},
            {"id": "pst2", "question": "Can they check my bag?", "short_answer": "They can ask. You can usually refuse, but they might ban you.", "explanation": "Bag checks are usually voluntary unless you agreed (like membership stores).", "script": "Is this required or can I decline?", "next_steps": ["Ask if required", "Comply or leave"]},
            {"id": "pst3", "question": "Can they kick me out?", "short_answer": "Yes for most reasons. But not discrimination.", "explanation": "Private businesses can refuse service. Can't discriminate based on race, etc.", "script": "May I ask why?", "next_steps": ["Leave if asked", "Note if discriminatory"]}
        ],
        "transport": [
            {"id": "pt1", "question": "What about public transit?", "short_answer": "It's public but agencies set rules. Pay your fare.", "explanation": "Transit can have rules. Police can be called for violations.", "script": "What are the rules here?", "next_steps": ["Pay fare", "Follow rules"]},
            {"id": "pt2", "question": "Rights in Uber/Lyft?", "short_answer": "It's a private car. Driver can end rides. Report safety issues.", "explanation": "Drivers can set rules. Use app safety features.", "script": "I feel unsafe. I'm ending this ride.", "next_steps": ["Use safety features", "Report issues"]},
            {"id": "pt3", "question": "Airport searches?", "short_answer": "You consent by entering security. Can opt out of body scanner for pat-down.", "explanation": "Airport searches are allowed because you choose to fly.", "script": "I'd like to opt out of the body scanner.", "next_steps": ["Know you'll be searched", "Arrive early"]}
        ],
        "parks": [
            {"id": "pk1", "question": "What can I do in parks?", "short_answer": "Varies by park. Check posted rules about hours, alcohol, fires.", "explanation": "Public parks have rules. Common: close at dusk, no alcohol.", "script": "What activities are allowed here?", "next_steps": ["Check rules", "Know hours"]},
            {"id": "pk2", "question": "Can I sleep outside?", "short_answer": "Laws vary. Many ban it, but courts limit enforcement when no shelters available.", "explanation": "Anti-camping laws exist but are being challenged.", "script": "Are there shelter resources available?", "next_steps": ["Know local laws", "Find shelter resources"]}
        ],
        "curfew": [
            {"id": "cu1", "question": "Are youth curfews legal?", "short_answer": "Many cities have them with exceptions for work, school events, emergencies.", "explanation": "Curfews are common but have exceptions. Know them.", "script": "I'm heading home from [work/event/with parent].", "next_steps": ["Know your city's curfew", "Know exceptions", "Carry ID"]},
            {"id": "cu2", "question": "Can I be arrested for loitering?", "short_answer": "Vague loitering laws often unconstitutional. Specific activities may be illegal.", "explanation": "General 'loitering' is hard to enforce. Blocking sidewalks is different.", "script": "What specifically am I accused of?", "next_steps": ["Ask what law violated", "Move along if asked"]}
        ]
    }
}

DEFAULT_SCRIPTS = [
    {"id": "ds1", "title": "Don't Consent to Search", "content": "I don't consent to a search.", "category": "general"},
    {"id": "ds2", "title": "Get It in Writing", "content": "Can you explain that in writing?", "category": "general"},
    {"id": "ds3", "title": "Call for Help", "content": "I'd like to contact my parent, guardian, or lawyer.", "category": "general"},
    {"id": "ds4", "title": "Not Comfortable", "content": "I'm not comfortable answering without support.", "category": "general"},
    {"id": "ds5", "title": "Am I Detained?", "content": "Am I free to go or am I being detained?", "category": "police"},
    {"id": "ds6", "title": "Stay Silent", "content": "I'm staying silent. I want a lawyer.", "category": "police"},
    {"id": "ds7", "title": "Phone Protected", "content": "I don't consent to searching my phone.", "category": "police"},
    {"id": "ds8", "title": "Recording", "content": "I'm recording from a safe distance.", "category": "police"},
    {"id": "ds9", "title": "Log Hours", "content": "I want to make sure all my time is logged.", "category": "work"},
    {"id": "ds10", "title": "Need Break", "content": "I need my required break.", "category": "work"},
    {"id": "ds11", "title": "Entry Notice", "content": "I need proper notice before you enter.", "category": "housing"},
    {"id": "ds12", "title": "Repairs in Writing", "content": "I'm reporting this in writing. When will it be fixed?", "category": "housing"}
]

RESOURCES = [
    {"category": "Emergency", "items": [
        {"name": "911", "contact": "911", "description": "Immediate emergencies"},
        {"name": "Crisis Text", "contact": "Text HOME to 741741", "description": "24/7 crisis support"},
        {"name": "988", "contact": "988", "description": "Suicide & mental health crisis"}
    ]},
    {"category": "Legal Help", "items": [
        {"name": "ACLU", "contact": "aclu.org", "description": "Civil liberties help"},
        {"name": "LawHelp", "contact": "lawhelp.org", "description": "Free legal aid by state"},
        {"name": "Legal Aid", "contact": "lsc.gov", "description": "Find free lawyers"}
    ]},
    {"category": "Youth Support", "items": [
        {"name": "Boys Town", "contact": "1-800-448-3000", "description": "24/7 teen help"},
        {"name": "Teen Line", "contact": "1-800-852-8336", "description": "Teens helping teens"},
        {"name": "Trevor Project", "contact": "1-866-488-7386", "description": "LGBTQ+ crisis support"}
    ]},
    {"category": "Work Rights", "items": [
        {"name": "DOL", "contact": "dol.gov", "description": "Workplace rights"},
        {"name": "OSHA", "contact": "1-800-321-OSHA", "description": "Safety issues"},
        {"name": "Wage Help", "contact": "1-866-487-9243", "description": "Wage theft"}
    ]},
    {"category": "Housing", "items": [
        {"name": "HUD", "contact": "hud.gov", "description": "Housing rights"},
        {"name": "Rent Help", "contact": "consumerfinance.gov/renthelp", "description": "Rental assistance"}
    ]},
    {"category": "Online Safety", "items": [
        {"name": "Cyber Civil Rights", "contact": "cybercivilrights.org", "description": "Image abuse help"},
        {"name": "FBI IC3", "contact": "ic3.gov", "description": "Report internet crime"}
    ]}
]

US_STATES = ["Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming", "District of Columbia"]

# Routes
@api_router.get("/")
async def root():
    return {"message": "Know Your Rights API", "version": "3.0.0"}

@api_router.get("/categories")
async def get_categories():
    return CATEGORIES

@api_router.get("/scenarios/{category_id}")
async def get_scenarios_by_category(category_id: str):
    if category_id not in SCENARIOS:
        raise HTTPException(status_code=404, detail="Category not found")
    all_scenarios = []
    for subcategory_id, scenarios in SCENARIOS[category_id].items():
        for scenario in scenarios:
            scenario_copy = scenario.copy()
            scenario_copy["subcategory"] = subcategory_id
            scenario_copy["category"] = category_id
            all_scenarios.append(scenario_copy)
    return all_scenarios

@api_router.get("/scenarios/{category_id}/{subcategory_id}")
async def get_scenarios_by_subcategory(category_id: str, subcategory_id: str):
    if category_id not in SCENARIOS or subcategory_id not in SCENARIOS[category_id]:
        raise HTTPException(status_code=404, detail="Not found")
    return SCENARIOS[category_id][subcategory_id]

@api_router.get("/scenario/{scenario_id}")
async def get_scenario_detail(scenario_id: str):
    for cat_id, category_data in SCENARIOS.items():
        for subcat_id, scenarios in category_data.items():
            for scenario in scenarios:
                if scenario["id"] == scenario_id:
                    result = scenario.copy()
                    result["category"] = cat_id
                    result["subcategory"] = subcat_id
                    return result
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
    
    state_ctx = f" User is in {request.user_state}." if request.user_state else " State unknown - give general US guidance, mention laws vary."
    
    system = f"""You help teens understand their rights. Keep it SHORT and REAL - no corporate speak.

RULES:
- 2-3 short paragraphs MAX
- Talk like a helpful older friend, not a textbook
- NEVER say you're a lawyer
- Always say "get real legal help for serious stuff"
- Be supportive, not preachy

{state_ctx}

Topics: school, work, housing, cops, online privacy, public spaces. This is info, not legal advice."""

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
