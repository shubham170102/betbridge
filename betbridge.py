import os
import requests
import time
import csv
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

API_BASE_URL = "http://127.0.0.1:8000/api/sportsbooks"


# Cache storage to reduce API calls and optimize token usage
cache = {"sports": {"data": None, "timestamp": None}}

GREETING = """
Welcome to BetBridge!

With this tool, you can:
1. View ongoing sports.
2. Find arbitrage opportunities across all sports.
3. Find arbitrage opportunities for a specific sport.
4. Get detailed odds for a specific sport.
5. Exit the tool.
"""


def get_sports_with_cache():
    cache_expiry = 3600  # 1-hour cache expiration
    if (
        cache["sports"]["data"]
        and (time.time() - cache["sports"]["timestamp"]) < cache_expiry
    ):
        return cache["sports"]["data"]

    response = requests.get(f"{API_BASE_URL}/sports", timeout=15)
    if response.status_code == 200:
        sports = response.json().get("sports", [])
        cache["sports"] = {"data": sports, "timestamp": time.time()}
        return sports
    else:
        print("Failed to fetch sports.")
        return []


def get_sports():
    response = requests.get(f"{API_BASE_URL}/sports", timeout=15)
    if response.status_code == 200:
        return response.json().get("sports", [])
    else:
        print("Failed to fetch sports.")
        return []


def get_odds(sport_key):
    response = requests.get(
        f"{API_BASE_URL}/odds/{sport_key}",
        params={"markets": "h2h,spreads"},
        timeout=15,
    )
    if response.status_code == 200:
        return response.json().get("odd_data", [])
    else:
        print("Failed to fetch odds.")
        return []


def calculate_arbitrage(odds_data):
    opportunities = []
    for game in odds_data:
        markets = {}
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

        for market_key, outcomes in markets.items():
            best_odds = {}
            for outcome in outcomes:
                name = outcome["outcome_name"]
                if name not in best_odds or outcome["price"] > best_odds[name]["price"]:
                    best_odds[name] = outcome

            implied_prob = {name: 1 / data["price"] for name, data in best_odds.items()}
            total_prob = sum(implied_prob.values())

            if total_prob < 1:
                opportunities.append(
                    {
                        "home_team": game["home_team"],
                        "away_team": game["away_team"],
                        "market": market_key,
                        "profit_percentage": (1 - total_prob) * 100,
                        "bookmakers": best_odds,
                    }
                )

    return opportunities


def convert_to_decimal(price):

    if price > 0:
        return (price / 100) + 1
    else:
        return (100 / abs(price)) + 1


def export_to_csv(opportunities, sport_title):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"arbitrage_opportunities_{sport_title}_{timestamp}.csv"

    with open(filename, "w", newline="") as csvfile:
        fieldnames = [
            "Game",
            "Market",
            "Profit Percentage",
            "Outcome",
            "Bookmaker",
            "Price",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for opp in opportunities:
            for outcome, details in opp["bookmakers"].items():
                writer.writerow(
                    {
                        "Game": f"{opp['home_team']} vs. {opp['away_team']}",
                        "Market": opp["market"],
                        "Profit Percentage": f"{opp['profit_percentage']:.2f}%",
                        "Outcome": outcome,
                        "Bookmaker": details["bookmaker"],
                        "Price": details["price"],
                    }
                )

    print(f"\nResults exported to {filename}")


def display_arbitrage_opportunities(opportunities, sport_title):
    if not opportunities:
        print(f"\nNo arbitrage opportunities found for {sport_title}.")
        return

    print(f"\n=== Arbitrage Opportunities Found for {sport_title} ===\n")
    for opp in opportunities:
        print(f"Game: {opp['home_team']} vs. {opp['away_team']}")
        print(f"Market: {opp['market']}")
        print(f"Profit Percentage: {opp['profit_percentage']:.2f}%")
        for outcome, details in opp["bookmakers"].items():
            print(
                f"  Bet on {outcome} with {details['bookmaker']} at odds {details['price']}"
            )
        print("-" * 50)

    save_choice = (
        input("\nWould you like to export these results to a CSV file? (y/n): ")
        .strip()
        .lower()
    )
    if save_choice == "y":
        export_to_csv(opportunities, sport_title)


def find_arbitrage_for_all_sports():
    sports = get_sports_with_cache()
    if not sports:
        print("No sports to check for arbitrage.")
        return

    min_profit = float(
        input(
            "Enter the minimum profit percentage to display opportunities (default is 0%): "
        )
        or 0
    )
    print("\nSearching for arbitrage opportunities across all sports...\n")
    total_opportunities = 0

    for sport in sports:
        odds_data = get_odds(sport["key"])
        time.sleep(0.5)
        if odds_data:
            opportunities = calculate_arbitrage(odds_data)
            filtered_opps = [
                opp for opp in opportunities if opp["profit_percentage"] >= min_profit
            ]
            if filtered_opps:
                display_arbitrage_opportunities(filtered_opps, sport["title"])
                total_opportunities += len(filtered_opps)

    if total_opportunities == 0:
        print("\nNo arbitrage opportunities found across all sports.")
    else:
        print(f"\nTotal Arbitrage Opportunities Found: {total_opportunities}")


def find_arbitrage_for_specific_sport():
    sports = get_sports_with_cache()
    if not sports:
        print("No sports to check for arbitrage.")
        return

    print("\nSelect a sport by entering the corresponding number:")
    for idx, sport in enumerate(sports, 1):
        print(f"{idx}. {sport['title']} (Key: {sport['key']})")

    try:
        sport_choice = int(input("\nEnter the number: ").strip())
        selected_sport = sports[sport_choice - 1]
    except (ValueError, IndexError):
        print("Invalid input. Please enter a valid number.")
        return

    min_profit = float(
        input(
            "Enter the minimum profit percentage to display opportunities (default is 0%): "
        )
        or 0
    )
    odds_data = get_odds(selected_sport["key"])
    if odds_data:
        opportunities = calculate_arbitrage(odds_data)
        filtered_opps = [
            opp for opp in opportunities if opp["profit_percentage"] >= min_profit
        ]
        display_arbitrage_opportunities(filtered_opps, selected_sport["title"])


def get_detailed_odds_for_sport():
    sports = get_sports_with_cache()
    if not sports:
        print("No sports to check.")
        return

    print("\nSelect a sport by entering the corresponding number:")
    for idx, sport in enumerate(sports, 1):
        print(f"{idx}. {sport['title']} (Key: {sport['key']})")

    try:
        sport_choice = int(input("\nEnter the number: ").strip())
        selected_sport = sports[sport_choice - 1]
    except (ValueError, IndexError):
        print("Invalid input. Please enter a valid number.")
        return

    print(f"\nFetching odds for the sport: {selected_sport['title']}...\n")
    odds_data = get_odds(selected_sport["key"])

    if not odds_data:
        print("No odds available.")
        return

    print("\nFound the following games with odds:\n")
    for game in odds_data:
        print(f"Game ID: {game['id']}")
        print(f"Home Team: {game['home_team']}")
        print(f"Away Team: {game['away_team']}")
        print(f"Commence Time: {game['commence_time']}")
        for bookmaker in game["bookmakers"]:
            print(f"  Bookmaker: {bookmaker['title']}")
            for market in bookmaker["markets"]:
                print(f"    Market: {market['key']}")
                for outcome in market["outcomes"]:
                    print(
                        f"      Outcome: {outcome['name']}, Price: {outcome['price']}"
                    )
        print("-" * 50)


def display_scores(scores_data):
    if not scores_data:
        print("No games found")
        return

    print("\n=== Scores ===\n")
    for game in scores_data:
        commence_time = game["commence_time"]
        formatted_time = datetime.fromisoformat(commence_time.replace("Z", "+00:00"))

        print(f"Game ID: {game['id']}")
        print(f"Sport: {game['sport_title']}")
        print(f"Home Team: {game['home_team']}")
        print(f"Away Team: {game['away_team']}")
        print(f"Start Time: {formatted_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")

        if game["completed"]:
            print("Status: Completed")
            print("Final Scores:")
            for score in game["scores"]:
                print(f"  {score['name']}: {score['score']}")
        elif game["scores"]:
            print("Status: Live")
            print("Current Scores:")
            for score in game["scores"]:
                print(f"  {score['name']}: {score['score']}")
        else:
            print("Status: Upcoming")

        print("-" * 50)


def get_scores_for_sport():
    sports = get_sports_with_cache()
    if not sports:
        print("No sports available to check scores.")
        return

    print("\nSelect a sport to view scores:")
    for idx, sport in enumerate(sports, 1):
        print(f"{idx}. {sport['title']} (Key: {sport['key']})")

    try:
        sport_choice = int(input("\nEnter the number: ").strip())
        selected_sport = sports[sport_choice - 1]
    except (ValueError, IndexError):
        print("Invalid input. Please enter a valid number.")
        return

    days_from = input(
        "Enter the number of days in the past to retrieve scores (1-3, or leave blank for live/upcoming games): "
    ).strip()
    days_from = (
        int(days_from) if days_from.isdigit() and 1 <= int(days_from) <= 3 else 0
    )

    # Ensure parameter names match API documentation
    response = requests.get(
        f"{API_BASE_URL}/scores/{selected_sport['key']}",
        params={
            "apiKey": os.getenv("API_KEY"),
            "daysFrom": days_from,
            "dateFormat": "iso",
        },
        timeout=15,
    )

    if response.status_code == 200:
        scores_data = response.json().get("scores", [])
        display_scores(scores_data)
    else:
        print("Failed to fetch scores.")


def main():
    print(GREETING)
    while True:
        print("\nWhat would you like to do?")
        print("1. View ongoing sports")
        print("2. Find arbitrage opportunities across all sports")
        print("3. Find arbitrage opportunities for a specific sport")
        print("4. Get detailed odds for a specific sport")
        print("5. View scores for a specific sport")
        print("6. Exit")

        choice = input("Enter your choice (1/2/3/4/5/6): ").strip()

        if choice == "1":
            get_sports_with_cache()
        elif choice == "2":
            find_arbitrage_for_all_sports()
        elif choice == "3":
            find_arbitrage_for_specific_sport()
        elif choice == "4":
            get_detailed_odds_for_sport()
        elif choice == "5":
            get_scores_for_sport()
        elif choice == "6":
            print("\nThank you for using BetBridge. Goodbye!")
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 6.")


if __name__ == "__main__":
    main()
