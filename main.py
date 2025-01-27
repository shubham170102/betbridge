from fastapi import FastAPI
from routes.oddsapi import router as sportsbooks_router

app = FastAPI()

# Include the routes
app.include_router(sportsbooks_router, prefix="/api/sportsbooks")

@app.get("/")
def root():
    return {"message": "Sports Betting API is running!"}
