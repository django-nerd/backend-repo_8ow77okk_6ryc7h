"""
Database Schemas for Cutty

Each Pydantic model maps to a MongoDB collection with the lowercase class name.
Example: User -> "user"
"""
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr, HttpUrl
from datetime import datetime

# Core user profile
class User(BaseModel):
    name: str = Field(..., description="Display name")
    email: EmailStr = Field(..., description="Email address")
    bio: Optional[str] = Field(None, description="Short bio")
    avatar_url: Optional[HttpUrl] = Field(None, description="Profile image URL")
    badges: List[str] = Field(default_factory=list, description="Earned badges")

# Community post
class Post(BaseModel):
    user_id: str = Field(..., description="Author user id")
    caption: str = Field(..., description="Post caption")
    image_url: Optional[HttpUrl] = Field(None, description="Optional photo")
    hashtags: List[str] = Field(default_factory=list, description="Hashtags like #FirstBloom")
    stage: Optional[str] = Field(None, description="Seedling | Growing | Blooming")
    cheers: int = Field(0, ge=0, description="Number of cheers")

class Comment(BaseModel):
    post_id: str = Field(..., description="Related post id")
    user_id: str = Field(..., description="Author user id")
    text: str = Field(..., min_length=1)

class Event(BaseModel):
    title: str
    season: str = Field(..., description="Spring | Summer | Autumn | Winter")
    description: str
    hashtag: Optional[str] = None
    date: Optional[datetime] = None
    location: Optional[str] = None

class Product(BaseModel):
    title: str
    description: Optional[str] = None
    price: float = Field(..., ge=0)
    image_url: Optional[HttpUrl] = None
    in_stock: bool = True

class NewsletterSignup(BaseModel):
    email: EmailStr
    name: Optional[str] = None

class ContactMessage(BaseModel):
    name: str
    email: EmailStr
    message: str

