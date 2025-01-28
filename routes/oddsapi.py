from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from db import SessionLocal, Sport, init_db
import httpx
from dotenv import load_dotenv
import os

load_dotenv()

router = APIRouter()
API_KEY = os.getenv("API_KEY")
SPORTS_LIST_URL = "https://api.the-odds-api.com/v4/sports"

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize the database
init_db()

@router.get("/sports")
async def get_sports(db: Session = Depends(get_db)):
    try:
        # Construct the API request URL
        url = f"{SPORTS_LIST_URL}"
        params = {
            "apiKey": API_KEY,
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()

            if response.status_code == 200:
                sports = response.json()

                # Store sports data in the database
                for sport in sports:
                    existing_sport = db.query(Sport).filter(Sport.sport_key == sport["key"]).first()
                    if not existing_sport:
                        # Extract individual fields from the API response
                        new_sport = Sport(
                            sport_key=sport["key"],
                            group_name=sport.get("group"),
                            title=sport.get("title"),
                            description=sport.get("description"),
                            active=sport.get("active", False),
                            has_outrights=sport.get("has_outrights", False),
                        )
                        db.add(new_sport)

                db.commit()

                return {
                    "success": True,
                    "count": len(sports),
                    "sports": sports,
                    "stored_keys": [sport["key"] for sport in sports],
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to fetch sports. Status code: {response.status_code}",
                }
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/odds/{sport_key}")
async def get_odds(
    sport_key: str,
    db: Session = Depends(get_db),
    regions: str = Query("us", description="Comma-separated list of regions (e.g., us, uk, au)"),
    markets: str = Query("h2h", description="Comma-separated list of markets (e.g., h2h, spreads, totals)"),
    odds_formats: str = Query("american", description="Odds format (e.g., american, decimal)"),
    date_format: str = Query("iso", description="Date format (e.g., iso, unix)")
):
    try:
        sport = db.query(Sport).filter(Sport.sport_key == sport_key).first()
        if not sport:
            raise HTTPException(status_code=404, detail="Sport key '{sport_key}' not found")
        
        # Construct the API request URL
        url = f"{SPORTS_LIST_URL}/{sport_key}/odds"
        params = {
            "apiKey": API_KEY,
            "regions": regions,
            "markets": markets,
            "oddsFormat": odds_formats,
            "dateFormat": date_format,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            if response.status_code == 200:
                odds_data = response.json()
                return {
                    "success": True,
                    "sport": sport_key,
                    "regions": regions,
                    "markets": markets,
                    "data": odds_data,
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to fetch odds. Status code: {response.status_code}",
                }
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))