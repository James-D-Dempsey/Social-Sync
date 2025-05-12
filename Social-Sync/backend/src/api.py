from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from recommender import get_recommendations
from db_connector import get_user_id, fetch_recommendations, add_user

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,   #very litterally allowed anything that connects to this server access
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserIn(BaseModel):
    tag: str

@app.post("/users/", status_code=201)
async def create_user(u: UserIn):
    try:
        add_user(u.tag)
        return {"status": "ok", "tag": u.tag}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/recommend/{tag}")
async def recommend(tag: str):
    try:
        recs = get_recommendations(tag)
        return {"recommendations": recs}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/users/{spotify_id}/recommendations/refresh")
def refresh_recs(spotify_id: str, top_n: int = 20, pop_cutoff: int = 30):
    """Force‑generate & store fresh recs for this user."""
    recs = get_recommendations(spotify_id, popularity_cutoff=pop_cutoff, top_n=top_n)
    return {"status": "ok", "count": len(recs), "recs": recs}


@app.get("/users/{spotify_id}/recommendations")
def get_cached_recs(spotify_id: str, limit: int = 20):
    """
    Just read back whatever is in Recommendations table.
    """
    uid = get_user_id(spotify_id)
    recs = fetch_recommendations(uid, limit=limit)
    if not recs:
        recs = refresh_recs(spotify_id, top_n=limit)["recs"]
    return recs