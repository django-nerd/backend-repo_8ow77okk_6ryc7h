import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson.objectid import ObjectId

from database import db, create_document, get_documents
from schemas import User, Post, Comment, Event, Product, NewsletterSignup, ContactMessage

app = FastAPI(title="Cutty – Grow Happiness Together")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helpers

def to_str_id(docs):
    for d in docs:
        if isinstance(d.get("_id"), ObjectId):
            d["id"] = str(d.pop("_id"))
    return docs

# Root
@app.get("/")
async def root():
    return {"message": "Cutty API running", "status": "ok"}

# Schema endpoint for viewer
@app.get("/schema")
async def schema():
    return {
        "user": User.model_json_schema(),
        "post": Post.model_json_schema(),
        "comment": Comment.model_json_schema(),
        "event": Event.model_json_schema(),
        "product": Product.model_json_schema(),
        "newslettersignup": NewsletterSignup.model_json_schema(),
        "contactmessage": ContactMessage.model_json_schema(),
    }

# Demo/seed routes
@app.get("/seed")
async def seed_demo():
    """Insert a few demo documents if collections are empty"""
    if db is None:
        raise HTTPException(500, "Database not available")

    created = {}

    if db["product"].count_documents({}) == 0:
        for p in [
            {"title": "The Cutty Box", "description": "DIY Dahlia kit with soil, pot, fertilizer, and mini greenhouse.", "price": 12.95, "image_url": "https://cdn.discordapp.com/attachments/692077531272052768/1440123736064917534/image0.jpg?ex=691d033e&is=691bb1be&hm=aab8d25f1609bb5aafae87cf0d0ab5f4e9fdfa113989b6cfd786be0c943eff79&", "in_stock": True},
            {"title": "Refill Kit", "description": "Soil + nutrients refill to keep growing.", "price": 12.0, "image_url": "https://images.unsplash.com/photo-1589998059171-988d887df646?q=80&w=1200&auto=format&fit=crop", "in_stock": True},
        ]:
            create_document("product", p)
        created["product"] = 2

    if db["event"].count_documents({}) == 0:
        for e in [
            {"title": "Spring Start", "season": "Spring", "description": "Kickoff your growth journey", "hashtag": "#SpringStart"},
            {"title": "Summer Bloom", "season": "Summer", "description": "Share blooms and smiles", "hashtag": "#SummerBloom"},
        ]:
            create_document("event", e)
        created["event"] = 2

    if db["post"].count_documents({}) == 0:
        # Insert both demo posts
        demo_posts = [
            {
                "user_id": "Maya",
                "caption": "Day 7 – first sprout! Feeling calmer already.",
                "image_url": "https://images.unsplash.com/photo-1495640452828-3df6795cf69b?q=80&w=1600&auto=format&fit=crop",
                "stage": "Seedling",
                "hashtags": ["#SpringStart", "#FirstSprout"],
                "cheers": 12,
            },
            {
                "user_id": "You",
                "caption": "Today’s progress with my Cutty plant — Stage: Growing. Two new leaves unfurled and the stem looks stronger. Gave it a gentle morning mist and rotated it toward the light. Felt a small spark of joy seeing that tiny change. Anyone else seeing this stage now?",
                "image_url": "https://images.unsplash.com/photo-1446071103084-c257b5f70672?q=80&w=1600&auto=format&fit=crop",
                "stage": "Growing",
                "hashtags": ["#MindfulMoment", "#CuttyProgress"],
                "cheers": 18,
            },
        ]
        for post in demo_posts:
            create_document("post", post)
        created["post"] = len(demo_posts)

    return {"seeded": created}

# Public fetch routes
@app.get("/products")
async def list_products():
    items = get_documents("product")
    items = to_str_id(items)
    # Normalize: ensure current price and imagery reflect latest decisions
    for it in items:
        if str(it.get("title", "")).lower().strip() == "the cutty box":
            it["price"] = 12.95
            it["image_url"] = "https://cdn.discordapp.com/attachments/692077531272052768/1440123736064917534/image0.jpg?ex=691d033e&is=691bb1be&hm=aab8d25f1609bb5aafae87cf0d0ab5f4e9fdfa113989b6cfd786be0c943eff79&"
        if str(it.get("title", "")).lower().strip() == "refill kit":
            it.setdefault("image_url", "https://images.unsplash.com/photo-1589998059171-988d887df646?q=80&w=1200&auto=format&fit=crop")
    return items

@app.get("/events")
async def list_events():
    items = get_documents("event")
    return to_str_id(items)

# Community demo (updated to plant-growing post first)
@app.get("/community/demo")
async def community_demo():
    return [
        {
            "id": "1",
            "user": {"name": "You", "avatar_url": None},
            "image_url": "https://images.unsplash.com/photo-1446071103084-c257b5f70672?q=80&w=1600&auto=format&fit=crop",
            "caption": "Today’s progress with my Cutty plant — Stage: Growing. Two new leaves unfurled and the stem looks stronger. Gave it a gentle morning mist and rotated it toward the light. Felt a small spark of joy seeing that tiny change. Anyone else seeing this stage now?",
            "stage": "Growing",
            "hashtags": ["#MindfulMoment", "#CuttyProgress"],
            "cheers": 18,
            "comments": [
                {"user": "Leo", "text": "Love the gentle misting routine 🌿"}
            ]
        },
        {
            "id": "2",
            "user": {"name": "Maya", "avatar_url": None},
            "image_url": "https://images.unsplash.com/photo-1495640452828-3df6795cf69b?q=80&w=1600&auto=format&fit=crop",
            "caption": "Day 7 – first sprout! Feeling calmer already.",
            "stage": "Seedling",
            "hashtags": ["#SpringStart", "#FirstSprout"],
            "cheers": 12,
            "comments": [
                {"user": "Ava", "text": "Sprout squad! 🌱"}
            ]
        }
    ]

# Community persistent API
class CreatePost(BaseModel):
    name: str
    caption: str
    image_url: Optional[str] = None
    hashtags: Optional[List[str]] = []
    stage: Optional[str] = None

class CreateComment(BaseModel):
    name: str
    text: str

@app.get("/community/posts")
async def community_posts():
    if db is None:
        return []
    posts = list(db["post"].find({}, sort=[("_id", -1)]))
    # Prioritize the custom demo post (You + Growing) at the top
    for p in posts:
        p["_priority"] = 1 if (str(p.get("user_id", "")).lower() == "you" and str(p.get("stage", "")).lower() == "growing") else 0
        ca = p.get("created_at")
        p["_created_str"] = ca.isoformat() if hasattr(ca, "isoformat") else str(ca or "")
    posts.sort(key=lambda x: (x.get("_priority", 0), x.get("_created_str", "")), reverse=True)
    to_str_id(posts)
    # attach comments for each post (latest 5)
    for p in posts:
        pid = p.get("id")
        comments = list(db["comment"].find({"post_id": pid}, sort=[("_id", -1)], limit=5))
        to_str_id(comments)
        p["comments"] = [{"id": c.get("id"), "user_id": c.get("user_id"), "text": c.get("text")} for c in comments]
        p.pop("_priority", None)
        p.pop("_created_str", None)
    return posts

@app.post("/community/posts")
async def create_post(data: CreatePost):
    payload = {
        "user_id": data.name.strip() or "guest",
        "caption": data.caption,
        "image_url": data.image_url,
        "hashtags": data.hashtags or [],
        "stage": data.stage,
        "cheers": 0,
    }
    doc_id = create_document("post", payload)
    return {"id": doc_id, "ok": True}

@app.post("/community/posts/{post_id}/cheer")
async def cheer_post(post_id: str):
    if db is None:
        raise HTTPException(500, "Database not available")
    r = db["post"].find_one_and_update({"_id": ObjectId(post_id) if ObjectId.is_valid(post_id) else post_id}, {"$inc": {"cheers": 1}}, return_document=True)
    if not r:
        raise HTTPException(404, "Post not found")
    if isinstance(r.get("_id"), ObjectId):
        r["id"] = str(r.pop("_id"))
    return {"ok": True, "cheers": r.get("cheers", 0), "id": r.get("id")}

@app.get("/community/posts/{post_id}/comments")
async def list_comments(post_id: str):
    items = get_documents("comment", filter_dict={"post_id": post_id})
    return to_str_id(items)

@app.post("/community/posts/{post_id}/comments")
async def add_comment(post_id: str, data: CreateComment):
    payload = {"post_id": post_id, "user_id": data.name.strip() or "guest", "text": data.text}
    doc_id = create_document("comment", payload)
    return {"id": doc_id, "ok": True}

# Maintenance utilities to help manage demo data
@app.post("/community/reset-demo")
async def reset_demo_posts():
    if db is None:
        raise HTTPException(500, "Database not available")
    db["comment"].delete_many({})
    db["post"].delete_many({})
    demo_posts = [
        {
            "user_id": "Maya",
            "caption": "Day 7 – first sprout! Feeling calmer already.",
            "image_url": "https://images.unsplash.com/photo-1495640452828-3df6795cf69b?q=80&w=1600&auto=format&fit=crop",
            "stage": "Seedling",
            "hashtags": ["#SpringStart", "#FirstSprout"],
            "cheers": 12,
        },
        {
            "user_id": "You",
            "caption": "Today’s progress with my Cutty plant — Stage: Growing. Two new leaves unfurled and the stem looks stronger. Gave it a gentle morning mist and rotated it toward the light. Felt a small spark of joy seeing that tiny change. Anyone else seeing this stage now?",
            "image_url": "https://images.unsplash.com/photo-1446071103084-c257b5f70672?q=80&w=1600&auto=format&fit=crop",
            "stage": "Growing",
            "hashtags": ["#MindfulMoment", "#CuttyProgress"],
            "cheers": 18,
        },
    ]
    for p in demo_posts:
        create_document("post", p)
    return {"ok": True, "reset": 2}

@app.post("/community/purge-unwanted")
async def purge_unwanted_posts():
    if db is None:
        raise HTTPException(500, "Database not available")
    # Remove any legacy demo posts that match old captions like "Repotted today" or mention "soil smell"
    res = db["post"].delete_many({
        "$or": [
            {"caption": {"$regex": "^Repotted", "$options": "i"}},
            {"caption": {"$regex": "Repotted today", "$options": "i"}},
            {"caption": {"$regex": "soil smell", "$options": "i"}},
        ]
    })
    return {"ok": True, "deleted": getattr(res, 'deleted_count', 0)}

# Simple create endpoints for newsletter/contact
@app.post("/newsletter")
async def newsletter(signup: NewsletterSignup):
    doc_id = create_document("newslettersignup", signup)
    return {"id": doc_id, "ok": True}

@app.post("/contact")
async def contact(message: ContactMessage):
    doc_id = create_document("contactmessage", message)
    return {"id": doc_id, "ok": True}

# Health
@app.get("/test")
async def test_database():
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
            response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
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
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
