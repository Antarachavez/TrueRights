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

# Load translated data files if available
_TRANSLATED_DATA = {}
for _lang_code in ['es', 'fr', 'zh']:
    _lang_file = ROOT_DIR / f'data_{_lang_code}.json'
    if _lang_file.exists():
        with open(_lang_file) as _f:
            _TRANSLATED_DATA[_lang_code] = json_module.load(_f)

CATEGORIES = _DATA["categories"]
SCENARIOS = _DATA["scenarios"]
SUBCATEGORY_LEGAL_QUOTES = _DATA["subcategory_legal_quotes"]
SCENARIO_LEGAL_QUOTES = _DATA["scenario_legal_quotes"]
DEFAULT_SCRIPTS = _DATA["default_scripts"]
RESOURCES = _DATA["resources"]
US_STATES = _DATA["us_states"]

def get_data_for_lang(lang):
    """Get the data dict for a given language, falling back to English."""
    if lang and lang != "en" and lang in _TRANSLATED_DATA:
        return _TRANSLATED_DATA[lang]
    return _DATA

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

# Translation map for category/subcategory names
CATEGORY_TRANSLATIONS = {
    "es": {
        "School": "Escuela", "Work": "Trabajo", "Housing": "Vivienda", "Police": "Policía",
        "Online": "En Línea", "Public Spaces": "Espacios Públicos", "Immigration": "Inmigración", "Customer Service": "Servicio al Cliente",
        "Searches & Privacy": "Búsquedas y Privacidad", "Discipline & Suspension": "Disciplina y Suspensión",
        "Attendance": "Asistencia", "Free Speech": "Libertad de Expresión", "Administration": "Administración",
        "Personal Property": "Propiedad Personal", "Grades": "Calificaciones", "Sports": "Deportes",
        "Special Education": "Educación Especial", "Safety": "Seguridad", "Technology": "Tecnología",
        "Pay & Wages": "Pago y Salarios", "Hours & Breaks": "Horas y Descansos", "Workplace Safety": "Seguridad Laboral",
        "Harassment": "Acoso", "Firing & Quitting": "Despido y Renuncia", "Privacy": "Privacidad",
        "Teen Workers": "Trabajadores Menores", "Scheduling": "Horarios", "Tips & Gratuities": "Propinas",
        "Contracts": "Contratos", "Discrimination": "Discriminación",
        "Landlord Entry": "Entrada del Propietario", "Repairs": "Reparaciones", "Eviction": "Desalojo",
        "Security Deposits": "Depósitos de Seguridad", "Lease": "Contrato de Alquiler", "Roommates": "Compañeros de Cuarto",
        "Utilities": "Servicios", "Pets": "Mascotas", "Noise": "Ruido", "Moving": "Mudanza",
        "Being Stopped": "Ser Detenido", "Searches": "Búsquedas", "Arrests": "Arrestos",
        "Your Rights": "Tus Derechos", "Recording Police": "Grabar a la Policía", "Complaints": "Quejas",
        "Minors & Police": "Menores y Policía", "Traffic Stops": "Paradas de Tráfico", "Home & Warrants": "Hogar y Órdenes",
        "Witnesses": "Testigos", "After Arrest": "Después del Arresto",
        "Social Media": "Redes Sociales", "Data Privacy": "Privacidad de Datos", "Online Harassment": "Acoso en Línea",
        "Photos & Images": "Fotos e Imágenes", "Accounts": "Cuentas", "School Devices": "Dispositivos Escolares",
        "Scams": "Estafas", "Gaming": "Videojuegos", "Online Shopping": "Compras en Línea",
        "Copyright": "Derechos de Autor", "AI & Technology": "IA y Tecnología",
        "Filming": "Filmación", "Protests": "Protestas", "Stores": "Tiendas",
        "Transportation": "Transporte", "Parks": "Parques", "Curfew": "Toque de Queda",
        "Malls": "Centros Comerciales", "Events": "Eventos", "Restaurants": "Restaurantes",
        "ID Requirements": "Requisitos de ID", "Being Banned": "Ser Vetado",
        "Documents": "Documentos", "Police & ICE": "Policía e ICE", "Work Rights": "Derechos Laborales",
        "School Rights": "Derechos Escolares", "Travel": "Viaje", "Healthcare": "Salud",
        "Detention": "Detención", "Family": "Familia", "DACA": "DACA", "Raids": "Redadas",
        "Returns": "Devoluciones", "Warranties": "Garantías", "Billing": "Facturación",
        "Debt": "Deudas", "Online Purchases": "Compras en Línea",
    },
    "fr": {
        "School": "École", "Work": "Travail", "Housing": "Logement", "Police": "Police",
        "Online": "En Ligne", "Public Spaces": "Espaces Publics", "Immigration": "Immigration", "Customer Service": "Service Client",
        "Searches & Privacy": "Fouilles et Vie Privée", "Discipline & Suspension": "Discipline et Suspension",
        "Attendance": "Présence", "Free Speech": "Liberté d'Expression", "Administration": "Administration",
        "Personal Property": "Biens Personnels", "Grades": "Notes", "Sports": "Sports",
        "Special Education": "Éducation Spécialisée", "Safety": "Sécurité", "Technology": "Technologie",
        "Pay & Wages": "Salaire et Rémunération", "Hours & Breaks": "Heures et Pauses", "Workplace Safety": "Sécurité au Travail",
        "Harassment": "Harcèlement", "Firing & Quitting": "Licenciement et Démission", "Privacy": "Vie Privée",
        "Teen Workers": "Travailleurs Mineurs", "Scheduling": "Horaires", "Tips & Gratuities": "Pourboires",
        "Contracts": "Contrats", "Discrimination": "Discrimination",
        "Landlord Entry": "Entrée du Propriétaire", "Repairs": "Réparations", "Eviction": "Expulsion",
        "Security Deposits": "Dépôts de Garantie", "Lease": "Bail", "Roommates": "Colocataires",
        "Utilities": "Services", "Pets": "Animaux", "Noise": "Bruit", "Moving": "Déménagement",
        "Being Stopped": "Être Arrêté", "Searches": "Fouilles", "Arrests": "Arrestations",
        "Your Rights": "Vos Droits", "Recording Police": "Filmer la Police", "Complaints": "Plaintes",
        "Minors & Police": "Mineurs et Police", "Traffic Stops": "Contrôles Routiers", "Home & Warrants": "Domicile et Mandats",
        "Witnesses": "Témoins", "After Arrest": "Après l'Arrestation",
        "Social Media": "Réseaux Sociaux", "Data Privacy": "Protection des Données", "Online Harassment": "Harcèlement en Ligne",
        "Photos & Images": "Photos et Images", "Accounts": "Comptes", "School Devices": "Appareils Scolaires",
        "Scams": "Arnaques", "Gaming": "Jeux Vidéo", "Online Shopping": "Achats en Ligne",
        "Copyright": "Droits d'Auteur", "AI & Technology": "IA et Technologie",
        "Filming": "Filmer", "Protests": "Manifestations", "Stores": "Magasins",
        "Transportation": "Transport", "Parks": "Parcs", "Curfew": "Couvre-feu",
        "Malls": "Centres Commerciaux", "Events": "Événements", "Restaurants": "Restaurants",
        "ID Requirements": "Pièces d'Identité", "Being Banned": "Être Banni",
        "Documents": "Documents", "Police & ICE": "Police et ICE", "Work Rights": "Droits au Travail",
        "School Rights": "Droits Scolaires", "Travel": "Voyage", "Healthcare": "Santé",
        "Detention": "Détention", "Family": "Famille", "DACA": "DACA", "Raids": "Raids",
        "Returns": "Retours", "Warranties": "Garanties", "Billing": "Facturation",
        "Debt": "Dettes", "Online Purchases": "Achats en Ligne",
    },
    "zh": {
        "School": "学校", "Work": "工作", "Housing": "住房", "Police": "警察",
        "Online": "网络", "Public Spaces": "公共场所", "Immigration": "移民", "Customer Service": "消费权益",
        "Searches & Privacy": "搜查与隐私", "Discipline & Suspension": "纪律与停学",
        "Attendance": "出勤", "Free Speech": "言论自由", "Administration": "行政管理",
        "Personal Property": "个人财物", "Grades": "成绩", "Sports": "体育运动",
        "Special Education": "特殊教育", "Safety": "安全", "Technology": "科技",
        "Pay & Wages": "薪资", "Hours & Breaks": "工时与休息", "Workplace Safety": "工作场所安全",
        "Harassment": "骚扰", "Firing & Quitting": "解雇与辞职", "Privacy": "隐私",
        "Teen Workers": "未成年工人", "Scheduling": "排班", "Tips & Gratuities": "小费",
        "Contracts": "合同", "Discrimination": "歧视",
        "Landlord Entry": "房东进入", "Repairs": "维修", "Eviction": "驱逐",
        "Security Deposits": "押金", "Lease": "租约", "Roommates": "室友",
        "Utilities": "水电", "Pets": "宠物", "Noise": "噪音", "Moving": "搬家",
        "Being Stopped": "被拦下", "Searches": "搜查", "Arrests": "逮捕",
        "Your Rights": "你的权利", "Recording Police": "录像取证", "Complaints": "投诉",
        "Minors & Police": "未成年与警察", "Traffic Stops": "交通拦截", "Home & Warrants": "住宅与搜查令",
        "Witnesses": "目击者", "After Arrest": "逮捕之后",
        "Social Media": "社交媒体", "Data Privacy": "数据隐私", "Online Harassment": "网络骚扰",
        "Photos & Images": "照片与图像", "Accounts": "账户", "School Devices": "学校设备",
        "Scams": "诈骗", "Gaming": "游戏", "Online Shopping": "网购",
        "Copyright": "版权", "AI & Technology": "AI与科技",
        "Filming": "拍摄", "Protests": "抗议", "Stores": "商店",
        "Transportation": "交通", "Parks": "公园", "Curfew": "宵禁",
        "Malls": "商场", "Events": "活动", "Restaurants": "餐厅",
        "ID Requirements": "身份证件", "Being Banned": "被禁止入内",
        "Documents": "证件", "Police & ICE": "警察与移民局", "Work Rights": "工作权利",
        "School Rights": "受教育权", "Travel": "旅行", "Healthcare": "医疗",
        "Detention": "拘留", "Family": "家庭", "DACA": "DACA", "Raids": "突击搜查",
        "Returns": "退货", "Warranties": "保修", "Billing": "账单",
        "Debt": "债务", "Online Purchases": "网上购物",
    }
}

def translate_categories(categories, lang):
    """Translate category and subcategory names."""
    if lang == "en" or lang not in CATEGORY_TRANSLATIONS:
        return categories
    trans = CATEGORY_TRANSLATIONS[lang]
    result = []
    for cat in categories:
        cat_copy = dict(cat)
        cat_copy["name"] = trans.get(cat["name"], cat["name"])
        cat_copy["description"] = trans.get(cat.get("description", ""), cat.get("description", ""))
        if "subcategories" in cat_copy:
            cat_copy["subcategories"] = [
                {**sub, "name": trans.get(sub["name"], sub["name"])}
                for sub in cat_copy["subcategories"]
            ]
        result.append(cat_copy)
    return result

@api_router.get("/")
async def root():
    return {"message": "True Rights API", "version": "5.0.0"}

@api_router.get("/categories")
async def get_categories(lang: str = "en"):
    return translate_categories(CATEGORIES, lang)

# === Translation endpoint - translates scenario content using AI ===
@api_router.get("/translate/{scenario_id}")
async def translate_scenario(scenario_id: str, lang: str = "en"):
    """Translate a scenario into the requested language. Caches results in MongoDB."""
    if lang == "en":
        # Find original scenario
        for cat_id, subcats in SCENARIOS.items():
            for sub_id, scenarios in subcats.items():
                for s in scenarios:
                    if s["id"] == scenario_id:
                        return s
        raise HTTPException(status_code=404, detail="Scenario not found")

    # Check cache first
    cached = await db.translations.find_one({"scenario_id": scenario_id, "lang": lang})
    if cached:
        cached["_id"] = str(cached["_id"])
        return cached

    # Find original scenario
    original = None
    for cat_id, subcats in SCENARIOS.items():
        for sub_id, scenarios in subcats.items():
            for s in scenarios:
                if s["id"] == scenario_id:
                    original = s
                    break

    if not original:
        raise HTTPException(status_code=404, detail="Scenario not found")

    # Translate using AI
    lang_names = {"es": "Spanish", "fr": "French", "zh": "Mandarin Chinese"}
    target_lang = lang_names.get(lang, "English")

    try:
        from emergentintegrations.llm.chat import chat, UserMessage
        response = await chat(
            api_key=EMERGENT_LLM_KEY,
            model="claude-sonnet-4-20250514",
            messages=[UserMessage(content=f"""Translate this legal rights scenario into {target_lang}. Return ONLY a JSON object with these exact fields translated. Keep the same structure. Do not add commentary.

{{
  "id": "{original['id']}",
  "question": "{original['question']}",
  "short_answer": "{original['short_answer']}",
  "explanation": "{original['explanation']}",
  "script": "{original.get('script', '')}",
  "next_steps": {json_module.dumps(original.get('next_steps', []))}
}}""")]
        )
        import json as j
        text = response.content.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        translated = j.loads(text)
        translated["scenario_id"] = scenario_id
        translated["lang"] = lang
        await db.translations.insert_one(translated)
        translated.pop("_id", None)
        return translated
    except Exception as e:
        # Return original with a translation note if AI fails
        return {**original, "translation_note": f"Translation to {target_lang} unavailable"}

# === Batch translate scenarios for a category ===
@api_router.get("/scenarios/{category_id}/translated")
async def get_translated_scenarios(category_id: str, lang: str = "en"):
    """Get all scenarios for a category, translated if needed."""
    if category_id not in SCENARIOS:
        raise HTTPException(status_code=404, detail="Category not found")

    all_scenarios = []
    for sub_id, scenarios in SCENARIOS[category_id].items():
        for s in scenarios:
            all_scenarios.append(s)

    if lang == "en":
        return all_scenarios

    # Check cache for batch
    cached_ids = set()
    results = []
    async for doc in db.translations.find({"lang": lang, "scenario_id": {"$in": [s["id"] for s in all_scenarios]}}):
        doc["_id"] = str(doc["_id"])
        results.append(doc)
        cached_ids.add(doc["scenario_id"])

    # Return cached + untranslated originals
    for s in all_scenarios:
        if s["id"] not in cached_ids:
            results.append(s)

    return results

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
async def get_scenarios_by_category(category_id: str, lang: str = "en"):
    lang_data = get_data_for_lang(lang)
    scenarios = lang_data["scenarios"]
    if category_id not in scenarios:
        raise HTTPException(status_code=404, detail="Not found")
    all_scenarios = []
    for subcat_id, sc_list in scenarios[category_id].items():
        for s in sc_list:
            sc = s.copy()
            sc["subcategory"] = subcat_id
            sc["category"] = category_id
            all_scenarios.append(sc)
    return all_scenarios

@api_router.get("/scenarios/{category_id}/{subcategory_id}")
async def get_scenarios_by_subcategory(category_id: str, subcategory_id: str, lang: str = "en"):
    lang_data = get_data_for_lang(lang)
    scenarios = lang_data["scenarios"]
    if category_id not in scenarios or subcategory_id not in scenarios[category_id]:
        raise HTTPException(status_code=404, detail="Not found")
    return scenarios[category_id][subcategory_id]

@api_router.get("/scenario/{scenario_id}")
async def get_scenario_detail(scenario_id: str, lang: str = "en"):
    lang_data = get_data_for_lang(lang)
    scenarios = lang_data["scenarios"]
    scenario_legal_quotes = lang_data.get("scenario_legal_quotes", SCENARIO_LEGAL_QUOTES)
    subcategory_legal_quotes = lang_data.get("subcategory_legal_quotes", SUBCATEGORY_LEGAL_QUOTES)
    
    for cat_id, cat_data in scenarios.items():
        for subcat_id, sc_list in cat_data.items():
            for s in sc_list:
                if s["id"] == scenario_id:
                    r = s.copy()
                    r["category"] = cat_id
                    r["subcategory"] = subcat_id
                    if scenario_id in scenario_legal_quotes:
                        r["legal_quotes"] = scenario_legal_quotes[scenario_id]
                    else:
                        import re
                        match = re.match(r"^([a-z]+-[a-z]+)", scenario_id)
                        prefix = match.group(1) if match else scenario_id
                        r["legal_quotes"] = subcategory_legal_quotes.get(prefix, [])
                    return r
    raise HTTPException(status_code=404, detail="Not found")

@api_router.get("/scripts/default")
async def get_default_scripts():
    return DEFAULT_SCRIPTS

@api_router.get("/scripts/by-category")
async def get_scripts_by_category(lang: str = "en"):
    """Return all scripts extracted from scenarios, grouped by category."""
    lang_data = get_data_for_lang(lang)
    categories = lang_data["categories"]
    scenarios = lang_data["scenarios"]
    
    result = {}
    for cat in categories:
        cat_id = cat["id"]
        cat_name = cat["name"]
        cat_icon = cat["icon"]
        cat_color = cat["color"]
        scripts_list = []
        if cat_id in scenarios:
            for subcat_id, sc_list in scenarios[cat_id].items():
                # Find subcategory name
                subcat_name = subcat_id
                for sc in cat.get("subcategories", []):
                    if sc["id"] == subcat_id:
                        subcat_name = sc["name"]
                        break
                for s in sc_list:
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
