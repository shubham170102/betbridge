import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = "http://127.0.0.1:8000/api/sportsbooks"
GREETING = """
Welcome to BetBridge!

With this tool, you can:
1. See a list of ongoing sports.
2. Get odds for games happening in a specific sport.
"""

def fetch_sport():
    print("\nFetching the list of sports ongoing...\n")
    response = requests.get(f"{API_URL}/sports")
    if response.status_code == 200:
        sports =  response.json().get("sports", [])
        if sports:
            print(f"Found {len(sports)} ongoing sports:\n")
            for index, sport in enumerate(sports, start=1):
                print(f"{index}. {sport['title']} (Key: {sport['key']})")
            return sports
        else:
            print("No ongoing sports")
    else:
        print("Failed to fetch sports. Try again later.")
    return []



def fetch_odds(sport_key):
    print(f"\nFetching odds for the sport: {sport_key}...\n")
    params = {
        "regions": "us",
        "markets": "h2h,spreads",
        "oddsFormat": "american",
        "dateFormat": "iso"
    }
    response  = requests.get(f"{API_URL}/odds/{sport_key}", params=params)
    if response.status_code == 200:
        odds_data = response.json().get("data", [])
        
        # Debugging: Print the structure of odds_data
        print("Odds Data Structure:", odds_data)

        if isinstance(odds_data, list) and odds_data:
            print(f"Found {len(odds_data)} games with odds:\n")
            for game in odds_data:
                print(f"Game ID: {game.get('id')}")
                print(f"Home Team: {game.get('home_team')}")
                print(f"Away Team: {game.get('away_team')}")
                print(f"Commence Time: {game.get('commence_time')}")
                for bookmaker in game.get("bookmakers", []):
                    print(f"  Bookmaker: {bookmaker.get('title')}")
                    for market in bookmaker.get("markets", []):
                        print(f"    Market: {market.get('key')}")
                        for outcome in market.get("outcomes", []):
                            print(f"      Outcome: {outcome.get('name')}, Price: {outcome.get('price')}")
                print("-" * 50)
        elif isinstance(odds_data, dict):
            print(f"Odds Data: {odds_data}")
        else:
            print("No odds data found for this sport.")
    else:
        print("Failed to fetch odds. Try again later.")


def main():
    print(GREETING)
    while True:
        print("\nWhat would you like to do?")
        print("1. View ongoing sports")
        print("2. Get odds for a specific sport")
        print("3. Exit")
        choice = input("Enter your choice (1/2/3): ").strip()

        if choice == "1":
            sports = fetch_sport()
        elif choice == "2":
            sports = fetch_sport()
            if sports:
                print("\nSelect a sport by entering the corresponding number:")
                try:
                    sport_choice = int(input("Enter the number: ").strip())
                    if 1 <= sport_choice <= len(sports):
                        selected_sport = sports[sport_choice - 1]
                        fetch_odds(selected_sport["key"])
                    else:
                        print("Inavlid Choice")
                except ValueError:
                    print("Invalid input")
        elif choice == "3":
            print("\nThank you for using BetBridge. Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()



            