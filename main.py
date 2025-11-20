import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from bson.objectid import ObjectId

app = FastAPI(title="Investigation Case Manager", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database helpers
try:
    from database import db, create_document, get_documents
except Exception:
    db = None
    def create_document(*args, **kwargs):
        raise Exception("Database not available")
    def get_documents(*args, **kwargs):
        raise Exception("Database not available")

# Schemas
from schemas import Case as CaseSchema, Evidence as EvidenceSchema

# Request models
class CaseCreate(BaseModel):
    username: str
    allegations: Optional[str] = None
    reporter_name: Optional[str] = None
    reporter_contact: Optional[str] = None

class CaseUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    risk_score: Optional[int] = Field(None, ge=0, le=100)

class EvidenceCreate(BaseModel):
    case_id: str
    type: str
    url: Optional[str] = None
    description: Optional[str] = None

# Utilities

def as_str_id(doc: dict):
    doc = dict(doc)
    if doc.get("_id"):
        doc["id"] = str(doc.pop("_id"))
    return doc

@app.get("/")
async def root():
    return {"message": "Investigation Case Manager API running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        from database import db as _db
        if _db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = _db.name if hasattr(_db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = _db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
        response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
        response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

# Cases
@app.post("/api/cases")
def create_case(payload: CaseCreate):
    data = CaseSchema(**payload.model_dump())
    case_id = create_document("case", data)
    return {"id": case_id}

@app.get("/api/cases")
def list_cases(username: Optional[str] = None, status: Optional[str] = None, limit: int = 50):
    filter_q = {}
    if username:
        filter_q["username"] = username
    if status:
        filter_q["status"] = status
    docs = get_documents("case", filter_q, limit)
    return [as_str_id(d) for d in docs]

@app.get("/api/cases/{case_id}")
def get_case(case_id: str):
    if db is None:
        raise HTTPException(500, "Database not available")
    doc = db["case"].find_one({"_id": ObjectId(case_id)})
    if not doc:
        raise HTTPException(404, "Case not found")
    return as_str_id(doc)

@app.patch("/api/cases/{case_id}")
def update_case(case_id: str, payload: CaseUpdate):
    if db is None:
        raise HTTPException(500, "Database not available")
    updates = {k: v for k, v in payload.model_dump(exclude_none=True).items()}
    if not updates:
        return {"updated": False}
    res = db["case"].update_one({"_id": ObjectId(case_id)}, {"$set": updates})
    if res.matched_count == 0:
        raise HTTPException(404, "Case not found")
    return {"updated": True}

# Evidence
@app.post("/api/evidence")
def add_evidence(payload: EvidenceCreate):
    # Ensure case exists
    if db is None:
        raise HTTPException(500, "Database not available")
    case = db["case"].find_one({"_id": ObjectId(payload.case_id)})
    if not case:
        raise HTTPException(404, "Case not found")
    data = EvidenceSchema(**payload.model_dump())
    evidence_id = create_document("evidence", data)
    return {"id": evidence_id}

@app.get("/api/cases/{case_id}/evidence")
def list_evidence(case_id: str, limit: int = 200):
    docs = get_documents("evidence", {"case_id": case_id}, limit)
    return [as_str_id(d) for d in docs]

# Public profile lookups (public info only). No private stories or bypassing auth.
class PublicProfileResponse(BaseModel):
    username: str
    full_name: Optional[str] = None
    bio: Optional[str] = None
    external_url: Optional[str] = None
    is_private: Optional[bool] = None

@app.get("/api/lookup/{username}", response_model=PublicProfileResponse)
def public_lookup(username: str):
    # Placeholder for public metadata via allowed methods only. No scraping of private data.
    # For demo, return structure with minimal fields. In a real deployment, integrate approved APIs.
    return PublicProfileResponse(
        username=username,
        full_name=None,
        bio=None,
        external_url=None,
        is_private=True
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
