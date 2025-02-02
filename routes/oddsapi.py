from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from db import SessionLocal, Sport, init_db, Odds, Bookmaker
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
                    existing_sport = (
                        db.query(Sport).filter(Sport.sport_key == sport["key"]).first()
                    )
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
    regions: str = Query(
        "us", description="Comma-separated list of regions (e.g., us, uk, au)"
    ),
    markets: str = Query(
        "h2h",
        description="Comma-separated list of markets (e.g., h2h, spreads, totals)",
    ),
    odds_formats: str = Query(
        "american", description="Odds format (e.g., american, decimal)"
    ),
    date_format: str = Query("iso", description="Date format (e.g., iso, unix)"),
):
    try:
        # Check if the sport exists
        sport = db.query(Sport).filter(Sport.sport_key == sport_key).first()
        if not sport:
            raise HTTPException(
                status_code=404, detail=f"Sport key '{sport_key}' not found."
            )

        # Fetch odds data from the API
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
                arbitrage_opportunities = arbitrage_calculation(odds_data)
                for game in odds_data:
                    # Insert into Odds table
                    existing_odds = (
                        db.query(Odds).filter(Odds.game_id == game.get("id")).first()
                    )
                    if not existing_odds:
                        new_odds = Odds(
                            game_id=game.get("id"),
                            sport_key=sport_key,
                            home_team=game.get("home_team"),
                            away_team=game.get("away_team"),
                            commence_time=game.get("commence_time"),
                        )
                        db.add(new_odds)
                        db.commit()
                        db.refresh(new_odds)

                        # Insert bookmakers data
                        for bookmaker in game.get("bookmakers", []):
                            for market in bookmaker.get("markets", []):
                                for outcome in market.get("outcomes", []):
                                    new_bookmaker = Bookmaker(
                                        odds_id=new_odds.id,
                                        bookmaker_key=bookmaker.get("key"),
                                        bookmaker_title=bookmaker.get("title"),
                                        last_update=bookmaker.get("last_update"),
                                        market_type=market.get("key"),
                                        market_outcome_name=outcome.get("name"),
                                        market_outcome_price=outcome.get("price"),
                                        market_point=outcome.get("point"),
                                    )
                                    db.add(new_bookmaker)

                db.commit()
                return {
                    "success": True,
                    "sport": sport_key,
                    "regions": regions,
                    "markets": markets,
                    "odd_data": odds_data,
                    "arbitrage_opportunities": arbitrage_opportunities,
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


@router.get("/scores/{sport_key}")
async def get_scores(
    sport_key: str,
    db: Session = Depends(get_db),
    days_from: int = Query(None, description="Number of days from which to retrieve completed games."),
    date_format: str = Query("iso", description="Date format (e.g., iso, unix)"),
):
    try:
        # Construct the request URL
        url = f"{SPORTS_LIST_URL}/{sport_key}/scores"
        
        # Prepare query parameters
        params = {"apiKey": API_KEY, "dateFormat": date_format}
        if days_from is not None:
            params["daysFrom"] = days_from

        # Make the API request
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()

            if response.status_code == 200:
                score_data = response.json()
                return {
                    "success": True,
                    "sport": sport_key,
                    "days_from": days_from,
                    "scores": score_data,
                }
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to fetch scores from the external API",
                )
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



def arbitrage_calculation(odd_data):
    opportunities = []

    for game in odd_data:
        markets = {}

        # Iterate through bookmakers and extract market information
        for bookmaker in game.get("bookmakers", []):
            for market in bookmaker.get("markets", []):
                market_key = market["key"]
                if market_key not in markets:
                    markets[market_key] = []

                for outcome in market.get("outcomes", []):
                    price = outcome["price"]
                    decimal_price = convert_to_decimal(price)
                    markets[market_key].append(
                        {
                            "bookmaker": bookmaker["title"],
                            "outcome_name": outcome["name"],
                            "price": decimal_price,
                        }
                    )

        # Check arbitrage for each market
        for market_key, outcomes in markets.items():
            best_odds = {}
            for outcome in outcomes:
                name = outcome["outcome_name"]
                if name not in best_odds or outcome["price"] > best_odds[name]["price"]:
                    best_odds[name] = outcome

            # Calculate implied probabilities
            implied_prob = {name: 1 / data["price"] for name, data in best_odds.items()}
            total_prob = sum(implied_prob.values())

            # If total probability is less than 1, it's an arbitrage opportunity
            if total_prob < 1:
                opportunities.append(
                    {
                        "game_id": game["id"],
                        "market": market_key,
                        "profit_percentage": (1 - total_prob) * 100,
                        "best_odds": best_odds,
                    }
                )

    return opportunities


def convert_to_decimal(price):
    """Converts American odds to decimal odds."""
    if price > 0:
        return (price / 100) + 1
    else:
        return (100 / abs(price)) + 1
