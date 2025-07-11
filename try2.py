import requests
import config

def get_data(player: str):
    url = f"https://api.hypixel.net/player?name={player}"
    headers = {
        "API-Key": config.API_KEY
    }
    response = requests.get(url, headers=headers)
    return response.json()

