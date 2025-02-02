import pandas as pd
import requests
from bs4 import BeautifulSoup
import plotly.express as px
import streamlit as st

# Function to scrape BartTorvik team efficiency data
def scrape_barttorvik():
    url = "https://barttorvik.com/trank.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
    except requests.RequestException as e:
        st.error(f"Error fetching BartTorvik data: {e}")
        return pd.DataFrame(columns=["Team", "AdjO", "AdjD", "Tempo", "SOS"])
    
    table = soup.find("table")  # Find the first table on the page
    if not table:
        st.error("Error: Could not find BartTorvik data table.")
        return pd.DataFrame(columns=["Team", "AdjO", "AdjD", "Tempo", "SOS"])
    
    rows = table.find_all("tr")[1:]
    data = []
    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 5:
            continue
        try:
            team_name = cols[1].text.strip()
            adj_o = float(cols[4].text.strip())  # Adjusted Offense
            adj_d = float(cols[5].text.strip())  # Adjusted Defense
            tempo = float(cols[7].text.strip())  # Tempo
            sos = float(cols[14].text.strip())   # Strength of Schedule
            data.append([team_name, adj_o, adj_d, tempo, sos])
        except (ValueError, IndexError):
            continue
    
    return pd.DataFrame(data, columns=["Team", "AdjO", "AdjD", "Tempo", "SOS"])

# Function to fetch sportsbook odds from The Odds API
def fetch_sportsbook_odds():
    api_url = "https://api.the-odds-api.com/v4/sports/basketball_ncaab/odds"
    import os
    api_key = "0a6ecad6f9b4a95ad8a3942789c0884e"  # Fetch from environment variable  # Replace with a real API key
    params = {
        "regions": "us",
        "markets": "h2h,spreads,totals",
        "apiKey": api_key
    }
    try:
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        st.error(f"Error fetching sportsbook data: {e}")
        return pd.DataFrame(columns=["Team A", "Team B", "Spread", "Over/Under", "Moneyline A", "Moneyline B"])
    
    odds_data = []
    for game in data:
        try:
            team_a = game["home_team"]
            team_b = game["away_team"]
            spread = game["bookmakers"][0]["markets"][1]["outcomes"][0]["point"]
            over_under = game["bookmakers"][0]["markets"][2]["outcomes"][0]["point"]
            moneyline_a = game["bookmakers"][0]["markets"][0]["outcomes"][0]["price"]
            moneyline_b = game["bookmakers"][0]["markets"][0]["outcomes"][1]["price"]
            odds_data.append([team_a, team_b, spread, over_under, moneyline_a, moneyline_b])
        except (KeyError, IndexError):
            continue
    
    return pd.DataFrame(odds_data, columns=["Team A", "Team B", "Spread", "Over/Under", "Moneyline A", "Moneyline B"])

# Streamlit App
def main():
    st.title("CharlesCovers - College Basketball Analytics")
    
    st.subheader("Team Tempo vs Offensive Efficiency")
    bart_data = scrape_barttorvik()
    sportsbook_data = fetch_sportsbook_odds()
    
    if bart_data.empty:
        st.error("Error fetching BartTorvik data")
    else:
        fig = px.scatter(bart_data, x="Tempo", y="AdjO", title="Team Tempo vs Offensive Efficiency",
                         labels={"Tempo": "Possessions per Game", "AdjO": "Adjusted Offensive Efficiency"})
        st.plotly_chart(fig)
    
    if sportsbook_data.empty:
        st.error("Error fetching sportsbook odds")
    else:
        st.subheader("Sportsbook Odds")
        st.dataframe(sportsbook_data)

if __name__ == "__main__":
    main()
