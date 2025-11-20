"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List

# Core investigator-friendly schemas for the anti-fraud case management app

class Case(BaseModel):
    """
    Case records created when investigating a username.
    Collection name: "case"
    """
    username: str = Field(..., description="Instagram username under investigation")
    allegations: Optional[str] = Field(None, description="Summary of suspected fraud/scam behavior")
    reporter_name: Optional[str] = Field(None, description="Reporter/Victim name (if provided with consent)")
    reporter_contact: Optional[str] = Field(None, description="Reporter/Victim contact (email/phone) with consent")
    status: str = Field("open", description="Case status: open, in_review, closed")
    risk_score: Optional[int] = Field(None, ge=0, le=100, description="Optional risk score 0-100 based on evidence")
    notes: Optional[str] = Field(None, description="Investigator notes")

class Evidence(BaseModel):
    """
    Evidence items linked to a case.
    Collection name: "evidence"
    """
    case_id: str = Field(..., description="Associated case document id")
    type: str = Field(..., description="Type of evidence: screenshot, link, payment_proof, chat_log, other")
    url: Optional[str] = Field(None, description="URL to evidence (if hosted)")
    description: Optional[str] = Field(None, description="Short description/context")

# Example schemas (kept for reference but not used by the app UI)
class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")
