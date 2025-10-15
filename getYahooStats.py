import requests
import json
import os
import math
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from jinja2 import Environment, FileSystemLoader, select_autoescape

# from yahooToken import YAHOO_TOKEN

def detemrine_last_completed_week(season_start: datetime):
    """
    given the season start date return the last completed week of nfl football.
    weeks end after mnday night football is completed.
    """
    delta = datetime.now() - season_start

    last_completed_week = math.floor(delta.days/7)

    return last_completed_week

def get_teams_response(token, league_id):
    url = f"https://fantasysports.yahooapis.com/fantasy/v2/league/{league_id}/teams;out=stats?format=json"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    return response.json()


def get_teams_response_for_week(token, team_id, league_id, week):
    url = f"https://fantasysports.yahooapis.com/fantasy/v2/team/{league_id}.t.{team_id}/stats;type=week;week={week}?format=json"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    return response.json()


def parse_team_ids(json_response):
    """
    Parse team IDs from Yahoo Fantasy Sports JSON response.

    Args:
        json_response (dict): The JSON response from Yahoo Fantasy Sports API

    Returns:
        list: List of team IDs as strings
    """
    team_ids = []

    try:
        teams_data = json_response["fantasy_content"]["league"][1]["teams"]

        # Iterate through teams (indices 0-11 for 12 teams)
        for team_index in range(12):  # Based on "count": 12 in the JSON
            if str(team_index) in teams_data:
                team_info = teams_data[str(team_index)]["team"][0][1]
                team_id = team_info["team_id"]
                team_ids.append(team_id)

    except (KeyError, IndexError, TypeError) as e:
        print(f"Error parsing team IDs: {e}")
        return []

    return team_ids


def parse_team_names_and_ids(json_response):
    """
    Parse team names and IDs from Yahoo Fantasy Sports JSON response.

    Args:
        json_response (dict): The JSON response from Yahoo Fantasy Sports API

    Returns:
        list: List of tuples containing (team_id, team_name)
    """
    teams_info = []

    try:
        teams_data = json_response["fantasy_content"]["league"][1]["teams"]

        # Iterate through teams (indices 0-11 for 12 teams)
        for team_index in range(12):  # Based on "count": 12 in the JSON
            if str(team_index) in teams_data:
                team_info = teams_data[str(team_index)]["team"][0]
                team_id = team_info[1]["team_id"]
                team_name = team_info[2]["name"]
                teams_info.append((team_id, team_name))

    except (KeyError, IndexError, TypeError) as e:
        print(f"Error parsing team info: {e}")
        return []

    return teams_info


def parse_team_points_total(weekly_stats_response):
    """
    Parse team points total from Yahoo Fantasy Sports weekly stats response.

    Args:
        weekly_stats_response (dict): The JSON response from the weekly stats API

    Returns:
        float: The total points scored by the team for that week
    """
    try:
        # Navigate to the team points in the JSON structure
        # The structure is: fantasy_content -> team -> [1] -> team_points -> total
        team_points_data = weekly_stats_response["fantasy_content"]["team"][1][
            "team_points"
        ]
        total_points = float(team_points_data["total"])
        return total_points

    except (KeyError, IndexError, TypeError, ValueError) as e:
        print(f"Error parsing team points total: {e}")
        return 0.0


def parse_team_name_from_weekly_stats(weekly_stats_response):
    """
    Parse team name from Yahoo Fantasy Sports weekly stats response.

    Args:
        weekly_stats_response (dict): The JSON response from the weekly stats API

    Returns:
        str: The team name
    """
    try:
        # Navigate to the team name in the JSON structure
        team_info = weekly_stats_response["fantasy_content"]["team"][0][2]
        team_name = team_info["name"]
        return team_name

    except (KeyError, IndexError, TypeError) as e:
        print(f"Error parsing team name: {e}")
        return "Unknown Team"


def get_team_weekly_score(token, team_id, league_id, week):
    """
    Get team name, weekly score, and projected points in one function call.

    Args:
        token (str): Yahoo API token
        team_id (str): Team ID
        league_id (str): League ID
        week (int): Week number

    Returns:
        tuple: (team_name, points_total, projected_points)
    """
    response = get_teams_response_for_week(token, team_id, league_id, week)
    team_name = parse_team_name_from_weekly_stats(response)
    points_total = parse_team_points_total(response)
    projected_points = parse_team_projected_points(response)
    return team_name, points_total, projected_points


# make request to get a list of all teams
# https://fantasysports.yahooapis.com/fantasy/v2/league/{{curr_league_id}}/teams;out=stats?format=json

# Get token from environment variable
YAHOO_TOKEN = os.getenv("YAHOO_TOKEN")
SEASON_START = datetime(2025, 9, 2, 2)

if not YAHOO_TOKEN:
    print("Error: YAHOO_TOKEN environment variable not set!")
    print("Please set your Yahoo API token as an environment variable:")
    print("export YAHOO_TOKEN='your_token_here'")
    exit(1)

league_id = "461.l.632073"
teams_response = get_teams_response(YAHOO_TOKEN, league_id)
teams_and_names = parse_team_names_and_ids(teams_response)

last_completed_week = detemrine_last_completed_week(SEASON_START)
print(f'Last completed week is {last_completed_week}')
# teams_scores = [s
#     ["team_id", "team_name", "week", "point"]
# ]
teams_scores = []
# Example: Get weekly stats for the first team
for team in teams_and_names:
    for week in range(1, last_completed_week + 1):
        teams_response_for_week = get_teams_response_for_week(
            YAHOO_TOKEN, team[0], league_id, week
        )
        team_points = parse_team_points_total(teams_response_for_week)
        teams_scores.append([team[0], team[1], week, team_points])


# Sort the list by points (index 3) in descending order (highest first)
teams_scores_sorted = sorted(teams_scores, key=lambda x: x[3], reverse=True)


def generate_html_report(teams_scores_sorted, teams_response):
    """Render HTML using Jinja2 template with top 5 and worst 5 (completed weeks)."""
    # Determine current week from league response if available; fallback to max week in data
    current_week = None
    try:
        league_meta = teams_response["fantasy_content"]["league"][0]
        if isinstance(league_meta, dict) and "current_week" in league_meta:
            current_week = int(league_meta["current_week"])  # may be str
    except Exception:
        current_week = None

    if current_week is None:
        try:
            current_week = max(week for _, _, week, _ in teams_scores_sorted)
        except ValueError:
            current_week = 1

    # Build top 5 list of dicts
    top_5_raw = teams_scores_sorted[:5]
    top_5 = [
        {"team_id": t[0], "team_name": t[1], "week": t[2], "points": float(t[3])}
        for t in top_5_raw
    ]

    # Completed weeks only for worst 5
    completed_scores = [s for s in teams_scores_sorted if s[2] <= current_week]
    worst_5_raw = sorted(completed_scores, key=lambda x: x[3])[:5]
    worst_5 = [
        {"team_id": t[0], "team_name": t[1], "week": t[2], "points": float(t[3])}
        for t in worst_5_raw
    ]

    env = Environment(
        loader=FileSystemLoader("templates"),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("index.html.j2")
    html = template.render(top_5=top_5, worst_5=worst_5)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("HTML report generated: index.html")


# Generate the HTML report
generate_html_report(teams_scores_sorted, teams_response)
