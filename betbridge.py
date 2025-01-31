import os
import requests
import time
import csv
from dotenv import load_dotenv

load_dotenv()

API_URL = "http://127.0.0.1:8000/api/sportsbooks"
GREETING = """
Welcome to BetBridge!

With this tool, you can:
1. View ongoing sports.
2. Find arbitrage opportunities across all sports.
3. Exit the tool.
"""

def fetch_sport():
    print("\nFetching the list of sports ongoing...\n")
    response = requests.get(f"{API_URL}/sports", timeout=15)
    if response.status_code == 200:
        sports = response.json().get("sports", [])
        if sports:
            print(f"Found {len(sports)} ongoing sports:\n")
            for index, sport in enumerate(sports, start=1):
                print(f"{index}. {sport['title']} (Key: {sport['key']})")
            return sports
        else:
            print("No ongoing sports found.")
    else:
        print("Failed to fetch sports. Try again later.")
    return []

def fetch_odds_for_sport(sport_key):
    print(f"\nFetching odds for the sport: {sport_key}...\n")
    params = {
        "regions": "us",
        "markets": "h2h,spreads",
        "oddsFormat": "american",
        "dateFormat": "iso",
    }
    try:
        response = requests.get(f"{API_URL}/odds/{sport_key}", params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        return data.get("arbitrage_opportunities", [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching odds for {sport_key}: {e}")
        return []

def export_to_csv(opportunities):
    filename = "arbitrage_opportunities.csv"
    with open(filename, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Sport", "Game ID", "Market", "Profit Percentage", "Outcome", "Bookmaker", "Price"])
        for sport, sport_opps in opportunities.items():
            for opp in sport_opps:
                for name, data in opp["best_odds"].items():
                    writer.writerow([
                        sport, opp["game_id"], opp["market"], f"{opp['profit_percentage']:.2f}%",
                        name, data["bookmaker"], data["price"]
                    ])
    print(f"\nOpportunities exported to {filename}")

def find_arbitrage_opportunities():
    sports = fetch_sport()
    if not sports:
        print("No sports to check for arbitrage.")
        return

    try:
        min_profit = float(input("Enter the minimum profit percentage to display opportunities (default is 0%): ") or 0)
    except ValueError:
        min_profit = 0

    print("\nSearching for arbitrage opportunities across all sports...\n")
    total_opportunities = 0
    opportunities_by_sport = {}
    errors = 0

    for index, sport in enumerate(sports, start=1):
        print(f"Processing sport {index}/{len(sports)}: {sport['title']}...")
        arbitrage_opportunities = fetch_odds_for_sport(sport["key"])
        time.sleep(0.5)

        if arbitrage_opportunities:
            filtered_opportunities = [opp for opp in arbitrage_opportunities if opp['profit_percentage'] >= min_profit]

            if filtered_opportunities:
                print(f"\n=== Arbitrage Opportunities Found for {sport['title']} ===\n")
                opportunities_by_sport[sport["title"]] = filtered_opportunities

                for opportunity in filtered_opportunities:
                    print(f"Game ID: {opportunity['game_id']}")
                    print(f"Market: {opportunity['market']}")
                    print(f"Profit Percentage: {opportunity['profit_percentage']:.2f}%")
                    print("Best Odds:")
                    for name, data in opportunity["best_odds"].items():
                        print(
                            f"  Outcome: {name}, Bookmaker: {data['bookmaker']}, Price: {data['price']}"
                        )
                    print("-" * 50)

                total_opportunities += len(filtered_opportunities)
        else:
            errors += 1

    if total_opportunities == 0:
        print("\nNo arbitrage opportunities found across all sports.")
    else:
        print(f"\nTotal Arbitrage Opportunities Found: {total_opportunities}")
        print("\nSummary of Arbitrage Opportunities by Sport:")
        for sport, sport_opps in opportunities_by_sport.items():
            print(f"- {sport}: {len(sport_opps)} opportunities found")

    print(f"\n{errors} sports had errors fetching odds.")
    
    export_choice = input("\nWould you like to export the results to a CSV file? (yes/no): ").strip().lower()
    if export_choice == "yes":
        export_to_csv(opportunities_by_sport)

def main():
    print(GREETING)
    while True:
        print("\nWhat would you like to do?")
        print("1. View ongoing sports")
        print("2. Find arbitrage opportunities across all sports")
        print("3. Exit")
        choice = input("Enter your choice (1/2/3): ").strip()

        if choice == "1":
            fetch_sport()
        elif choice == "2":
            find_arbitrage_opportunities()
        elif choice == "3":
            print("\nThank you for using BetBridge. Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()
