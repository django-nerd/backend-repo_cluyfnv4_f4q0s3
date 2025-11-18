import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr
from database import create_document, get_documents, db
from schemas import ProductApp as ProductAppSchema, Inquiry as InquirySchema

app = FastAPI(title="Oboloi API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Response models
class ProductOut(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    name: str
    tagline: str
    description: str
    link: Optional[str] = None
    image: Optional[str] = None
    tags: List[str] = []
    pricing: Optional[str] = None

    class Config:
        populate_by_name = True


class InquiryIn(BaseModel):
    name: str
    email: EmailStr
    company: Optional[str] = None
    message: str


@app.get("/")
def read_root():
    return {"message": "Oboloi backend running"}


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/products", response_model=List[ProductOut])
def list_products():
    """Return all product apps. If none exist, seed a few demo entries for the landing page."""
    try:
        items = get_documents("productapp")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Seed with sample data if empty
    if not items:
        samples: List[ProductAppSchema] = [
            ProductAppSchema(
                name="Nimbus Desk",
                tagline="Task management that feels weightless",
                description="A beautifully minimal task manager with real-time collaboration and calendar sync.",
                link="https://example.com/nimbus",
                image="https://images.unsplash.com/photo-1555099962-4199c345e5dd?q=80&w=1200&auto=format&fit=crop",
                tags=["SaaS", "Productivity", "Collaboration"],
                pricing="Freemium"
            ),
            ProductAppSchema(
                name="Pulse Analytics",
                tagline="Product analytics for lean teams",
                description="Event tracking, funnels, and retention without the bloat. Privacy-first by default.",
                link="https://example.com/pulse",
                image="https://images.unsplash.com/photo-1556157382-97eda2d62296?q=80&w=1200&auto=format&fit=crop",
                tags=["Analytics", "Privacy", "SaaS"],
                pricing="Starts at $19/mo"
            ),
            ProductAppSchema(
                name="Relay Support",
                tagline="Shared inbox that actually scales",
                description="Manage email, chat, and social in one place. Powered by AI-assisted responses.",
                link="https://example.com/relay",
                image="https://images.unsplash.com/photo-1558655146-d09347e92766?q=80&w=1200&auto=format&fit=crop",
                tags=["Support", "AI", "Inbox"],
                pricing="$29/agent/mo"
            ),
        ]
        for s in samples:
            try:
                create_document("productapp", s)
            except Exception:
                pass
        items = get_documents("productapp")

    # Convert ObjectId to string for _id
    for item in items:
        if item.get("_id") is not None:
            item["_id"] = str(item["_id"])
    return items


@app.post("/api/inquiries")
def create_inquiry(payload: InquiryIn):
    try:
        # Validate with schema, then insert
        schema_obj = InquirySchema(**payload.model_dump())
        inserted_id = create_document("inquiry", schema_obj)
        return {"status": "ok", "id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = getattr(db, "name", "✅ Connected")
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
