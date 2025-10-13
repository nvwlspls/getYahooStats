import requests
import json

import YAHOO_TOKEN from yahooToken.py

def get_teams_response(token, league_id):
    url = f"https://fantasysports.yahooapis.com/fantasy/v2/league/{league_id}/teams;out=stats?format=json"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers=headers)
    return response.json()

def get_teams_response_for_week(token, team_id, league_id, week):
    url = f"https://fantasysports.yahooapis.com/fantasy/v2/team/{league_id}.t.{team_id}/stats;type=week;week={week}?format=json"
    headers = {
        "Authorization": f"Bearer {token}"
    }
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
        team_points_data = weekly_stats_response["fantasy_content"]["team"][1]["team_points"]
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

# TOKEN = os.getenv("YAHOO_TOKEN")
league_id = "461.l.632073"
teams_response = get_teams_response(YAHOO_TOKEN, league_id)
teams_and_names = parse_team_names_and_ids(teams_response)
# print(teams_and_names)


# teams_scores = [s
#     ["team_id", "team_name", "week", "point"]
# ]
teams_scores = []
# Example: Get weekly stats for the first team
for team in teams_and_names:
    for week in range(1, 18):
        teams_response_for_week = get_teams_response_for_week(TOKEN, team[0], league_id, week)
        team_points = parse_team_points_total(teams_response_for_week)
        teams_scores.append([team[0],team[1], week, team_points])


# Sort the list by points (index 3) in descending order (highest first)
teams_scores_sorted = sorted(teams_scores, key=lambda x: x[3], reverse=True)

def generate_html_report(teams_scores_sorted):
    """Generate HTML file with top 5 scores, featuring prominent top score."""
    top_5 = teams_scores_sorted[:5]
    
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🏆 What's the Side Bewb At?</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #2E7D32 0%, #4CAF50 50%, #8BC34A 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #1B5E20 0%, #2E7D32 100%);
            color: white;
            text-align: center;
            padding: 40px 20px;
        }}
        
        .header h1 {{
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        .header p {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .champion {{
            background: linear-gradient(135deg, #FFD700 0%, #FFA000 100%);
            margin: 20px;
            padding: 30px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(255,215,0,0.3);
            border: 3px solid #FFC107;
        }}
        
        .champion h2 {{
            color: #E65100;
            font-size: 2em;
            margin-bottom: 10px;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
        }}
        
        .champion .team-name {{
            font-size: 1.5em;
            font-weight: bold;
            color: #1B5E20;
            margin-bottom: 5px;
        }}
        
        .champion .points {{
            font-size: 3em;
            font-weight: bold;
            color: #D84315;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}
        
        .champion .week {{
            background: #E65100;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            display: inline-block;
            margin-top: 10px;
            font-weight: bold;
        }}
        
        .top-4 {{
            padding: 20px;
        }}
        
        .score-item {{
            background: #f8f9fa;
            margin: 15px 0;
            padding: 20px;
            border-radius: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .score-item:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 15px rgba(0,0,0,0.15);
        }}
        
        .rank {{
            background: #4CAF50;
            color: white;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 1.2em;
        }}
        
        .team-info {{
            flex-grow: 1;
            margin-left: 20px;
        }}
        
        .team-name {{
            font-weight: bold;
            color: #2E7D32;
            font-size: 1.2em;
        }}
        
        .week {{
            background: #81C784;
            color: white;
            padding: 4px 12px;
            border-radius: 15px;
            font-size: 0.9em;
            display: inline-block;
            margin-top: 5px;
        }}
        
        .points {{
            font-size: 1.5em;
            font-weight: bold;
            color: #1B5E20;
        }}
        
        .footer {{
            background: #E8F5E8;
            text-align: center;
            padding: 20px;
            color: #2E7D32;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏆 Top 5 Scores</h1>
            <p>Current Bewb Holder</p>
        </div>
        
        <div class="champion">
            <h2>🥇 CHAMPION</h2>
            <div class="team-name">{top_5[0][1]}</div>
            <div class="points">{top_5[0][3]:.2f}</div>
            <div class="week">Week {top_5[0][2]}</div>
        </div>
        
        <div class="top-4">
            <h3 style="color: #2E7D32; margin-bottom: 20px; text-align: center;">🏆 Top 4 Runners-Up</h3>
"""
    
    for i, score in enumerate(top_5[1:], 2):
        team_id, team_name, week, points = score
        html += f"""
            <div class="score-item">
                <div class="rank">{i}</div>
                <div class="team-info">
                    <div class="team-name">{team_name}</div>
                    <div class="week">Week {week}</div>
                </div>
                <div class="points">{points:.2f}</div>
            </div>"""
    
    html += """
        </div>
        
        <div class="footer">
            <p>🏈 Generated with Fantasy Football Data</p>
        </div>
    </div>
</body>
</html>"""
    
    with open("index.html", "w") as f:
        f.write(html)
    
    print("HTML report generated: index.html")


# Generate the HTML report
generate_html_report(teams_scores_sorted)