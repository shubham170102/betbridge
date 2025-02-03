from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.oddsapi import router as sportsbooks_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the routes
app.include_router(sportsbooks_router, prefix="/api/sportsbooks")


@app.get("/")
def root():
    return {"message": "Sports Betting API is running!"}
