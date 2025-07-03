import requests
import json
import math 


try:
    import config
    PRESET_API_KEY = getattr(config, 'API_KEY', '')
except ImportError:
    PRESET_API_KEY = ''
    print("Warning: 'config.py' not found. You will be prompted for your API key.")
except AttributeError:
    PRESET_API_KEY = ''
    print("Warning: 'API_KEY' not found in 'config.py'. You will be prompted for your API key.")


def _get_nested_stat(data, path, default=0):
    keys = path.split('.')
    current_data = data
    for key in keys:
        if isinstance(current_data, dict) and key in current_data:
            current_data = current_data[key]
        else:
            return default
    return current_data

def get_hypixel_player_data(username, api_key):
    base_url = "https://api.hypixel.net/"
    headers = {
        "API-Key": api_key
    }

    print(f"Attempting to fetch UUID for username: {username}...")
    uuid_endpoint = f"{base_url}player?name={requests.utils.quote(username)}"
    try:
        uuid_response = requests.get(uuid_endpoint, headers=headers)
        uuid_response.raise_for_status() 
        uuid_data = uuid_response.json()

        if not uuid_response.ok or not uuid_data.get("success"):
            error_cause = uuid_data.get("cause", "Unknown error")
            print(f"Error fetching UUID: {error_cause}")
            return None

        player_uuid = uuid_data.get("player", {}).get("uuid")
        if not player_uuid:
            print(f"Player UUID not found for username '{username}'. Check if the username is correct or if the player exists.")
            return None
        
        print(f"UUID found: {player_uuid}")

    except requests.exceptions.RequestException as e:
        print(f"Network or API request error during UUID fetch: {e}")
        return None
    except json.JSONDecodeError:
        print("Error: Could not decode JSON response for UUID fetch.")
        return None

    print(f"Fetching player data for UUID: {player_uuid}...")
    player_data_endpoint = f"{base_url}player?uuid={player_uuid}"
    try:
        player_data_response = requests.get(player_data_endpoint, headers=headers)
        player_data_response.raise_for_status()
        player_data = player_data_response.json()

        if not player_data_response.ok or not player_data.get("success"):
            error_cause = player_data.get("cause", "Unknown error")
            print(f"Error fetching player data: {error_cause}")
            return None

        return player_data.get("player")

    except requests.exceptions.RequestException as e:
        print(f"Network or API request error during player data fetch: {e}")
        return None
    except json.JSONDecodeError:
        print("Error: Could not decode JSON response for player data fetch.")
        return None

def extract_bedwars_important_stats(player_data):
    bedwars_stats = {}


    bw_data = _get_nested_stat(player_data, "stats.Bedwars", {})
    

    kills = _get_nested_stat(bw_data, "kills_bedwars")
    bedwars_stats["Kills (All Modes)"] = kills


    final_kills = _get_nested_stat(bw_data, "final_kills_bedwars")
    bedwars_stats["Final Kills (All Modes)"] = final_kills


    bed_breaks = _get_nested_stat(bw_data, "beds_broken_bedwars")
    bedwars_stats["Bed Breaks (All Modes)"] = bed_breaks

    tokens = _get_nested_stat(player_data, "total_tokens", _get_nested_stat(player_data, "rewards.total_tokens", 0))
    bedwars_stats["Tokens"] = tokens

    bedwars_level = _get_nested_stat(player_data, "achievements.bedwars_level")
    bedwars_stats["Bedwars Level"] = bedwars_level
    bedwars_stats["Prestige"] = f"Determined by Bedwars Level ({bedwars_level})" 


    quests_completed = _get_nested_stat(player_data, "achievements.bedwars_quests_completed", 0)
    
    bedwars_stats["Quests Completed"] = quests_completed


    karma = _get_nested_stat(player_data, "karma")
    bedwars_stats["Karma"] = karma

    winstreak = _get_nested_stat(bw_data, "winstreak")
    bedwars_stats["Winstreak"] = winstreak

    bedwars_stats["Diamonds Collected"] = _get_nested_stat(bw_data, "diamond_resources_collected_bedwars")
    bedwars_stats["Emeralds Collected"] = _get_nested_stat(bw_data, "emerald_resources_collected_bedwars")
    bedwars_stats["Gold Collected"] = _get_nested_stat(bw_data, "gold_resources_collected_bedwars")
    bedwars_stats["Iron Collected"] = _get_nested_stat(bw_data, "iron_resources_collected_bedwars")

    deaths = _get_nested_stat(bw_data, "deaths_bedwars")
    bedwars_stats["Deaths (All Modes)"] = deaths

    final_deaths = _get_nested_stat(bw_data, "final_deaths_bedwars")
    bedwars_stats["Final Deaths (All Modes)"] = final_deaths

    wins = _get_nested_stat(bw_data, "wins_bedwars")
    bedwars_stats["Wins (All Modes)"] = wins

    losses = _get_nested_stat(bw_data, "losses_bedwars")
    bedwars_stats["Losses (All Modes)"] = losses

    bedwars_stats["Kill Death Ratio (KDR)"] = round(kills / max(1, deaths), 2) if deaths > 0 else "N/A"
    bedwars_stats["Final Kill Death Ratio (FKDR)"] = round(final_kills / max(1, final_deaths), 2) if final_deaths > 0 else "N/A"
    bedwars_stats["Win Loss Ratio (WLR)"] = round(wins / max(1, losses), 2) if losses > 0 else "N/A"

    return bedwars_stats

def calculate_skywars_level(experience):
    xps = [0, 20, 70, 150, 250, 500, 1000, 2000, 3500, 6000, 10000, 15000]
    
    if experience >= 15000:
        return (experience - 15000) / 10000 + 12
    else:
        for i in range(len(xps)):
            if experience < xps[i]:
                if i == 0: 
                    return experience / xps[0] if xps[0] > 0 else 0
                return i + (experience - xps[i-1]) / (xps[i] - xps[i-1])
    return 0 

def get_skywars_prestige_name(level):
    level_int = math.floor(level)

    if level_int < 5:
        return "Stone"
    elif level_int < 10:
        return "Iron"
    elif level_int < 15:
        return "Gold"
    elif level_int < 20:
        return "Diamond"
    elif level_int < 25:
        return "Emerald"
    elif level_int < 30:
        return "Sapphire"
    elif level_int < 35:
        return "Ruby"
    elif level_int < 40:
        return "Crystal"
    elif level_int < 45:
        return "Opal"
    elif level_int < 50:
        return "Amethyst"
    elif level_int < 60: 
        return "Rainbow"
    else: 
        return "Mythic"


def extract_skywars_important_stats(player_data):
    skywars_stats = {}


    sw_data = _get_nested_stat(player_data, "stats.SkyWars", {})


    sw_experience = _get_nested_stat(sw_data, "skywars_experience")
    skywars_level = calculate_skywars_level(sw_experience)
    skywars_stats["Level"] = round(skywars_level, 2)
    skywars_stats["Prestige"] = get_skywars_prestige_name(skywars_level)


    skywars_stats["Coins"] = _get_nested_stat(sw_data, "coins")


    kills = _get_nested_stat(sw_data, "kills")
    skywars_stats["Kills (All Modes)"] = kills


    assists = _get_nested_stat(sw_data, "assists")
    skywars_stats["Assists (All Modes)"] = assists

    deaths = _get_nested_stat(sw_data, "deaths")
    skywars_stats["Deaths (All Modes)"] = deaths

    skywars_stats["Kill Death Ratio (KDR)"] = round(kills / max(1, deaths), 2) if deaths > 0 else "N/A"

    wins = _get_nested_stat(sw_data, "wins")
    skywars_stats["Wins (All Modes)"] = wins

    losses = _get_nested_stat(sw_data, "losses")
    skywars_stats["Losses (All Modes)"] = losses

    skywars_stats["Win Loss Ratio (WLR)"] = round(wins / max(1, losses), 2) if losses > 0 else "N/A"

    skywars_stats["Soul Well Uses"] = _get_nested_stat(sw_data, "soul_well_uses")

    skywars_stats["Soul Well Legendaries"] = _get_nested_stat(sw_data, "soul_well_leg")

    skywars_stats["Soul Well Rares"] = _get_nested_stat(sw_data, "soul_well_rares")

    skywars_stats["Paid Souls"] = _get_nested_stat(sw_data, "paid_souls")

    skywars_stats["Souls Gathered"] = _get_nested_stat(sw_data, "souls_gathered")

    skywars_stats["Eggs Thrown"] = _get_nested_stat(sw_data, "egg_thrown")

    skywars_stats["Enderpearls Thrown"] = _get_nested_stat(sw_data, "enderpearls_thrown")

    arrows_shot = _get_nested_stat(sw_data, "arrows_shot")
    skywars_stats["Arrows Shot"] = arrows_shot

    arrows_hit = _get_nested_stat(sw_data, "arrows_hit")
    skywars_stats["Arrows Hit"] = arrows_hit

    skywars_stats["Arrow Hit/Shot Ratio"] = round(arrows_hit / max(1, arrows_shot), 2) if arrows_shot > 0 else "N/A"

    return skywars_stats

if __name__ == "__main__":
    minecraft_username = input("Enter your Minecraft username: ").strip()
    
    if PRESET_API_KEY:
        hypixel_api_key = PRESET_API_KEY
        print("Using API key from config.py")
    else:
        hypixel_api_key = input("Enter your Hypixel API key: ").strip()


    if not minecraft_username or not hypixel_api_key:
        print("Error: Both username and API key are required.")
    else:
        player_info = get_hypixel_player_data(minecraft_username, hypixel_api_key)

        if player_info:
            print("\nPlayer data received successfully!")
            
            game_mode_input = input("Enter the game mode you want to see data for (e.g., Bedwars, SkyWars, Arcade): ").strip()

            if game_mode_input.lower() == "bedwars":
                important_bedwars_stats = extract_bedwars_important_stats(player_info)
                print("\n--- Important Bedwars Stats ---")
                for stat, value in important_bedwars_stats.items():

                    if isinstance(value, (int, float)) and not isinstance(value, bool):
                        print(f"{stat}: {value:,.2f}" if isinstance(value, float) else f"{stat}: {value:,}")
                    elif isinstance(value, dict):
                        print(f"{stat}:")
                        for item, count in value.items():
                            print(f"  - {item}: {count:,}")
                    else:
                        print(f"{stat}: {value}")
                print("-----------------------------")
            elif game_mode_input.lower() == "skywars":
                important_skywars_stats = extract_skywars_important_stats(player_info)
                print("\n--- Important Skywars Stats ---")
                for stat, value in important_skywars_stats.items():
                    if isinstance(value, (int, float)) and not isinstance(value, bool):
                        print(f"{stat}: {value:,.2f}" if isinstance(value, float) else f"{stat}: {value:,}")
                    elif isinstance(value, dict):
                        print(f"{stat}:")
                        for item, count in value.items():
                            print(f"  - {item}: {count:,}")
                    else:
                        print(f"{stat}: {value}")
                print("-----------------------------")
            elif game_mode_input:

                print(f"\nCurrently, detailed important stats are only configured for 'Bedwars' and 'Skywars'.")
                game_mode_data = _get_nested_stat(player_info, f"stats.{game_mode_input.capitalize()}", None)
                if game_mode_data:
                    print(f"\n--- Raw Data for Game Mode: {game_mode_input} ---")
                    print(json.dumps(game_mode_data, indent=2))
                    print("---------------------------------------")
                else:
                    print(f"\nNo data found for game mode: '{game_mode_input}'. Please check the spelling or if the player has played this mode.")
            else:
                print("\nNo game mode entered. Displaying full player data (if available).")
                print(json.dumps(player_info, indent=2))
        else:
            print("\nFailed to retrieve player data.")
