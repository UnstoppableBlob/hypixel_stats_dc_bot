import requests
import json
import math # For math.floor

# Import the config file to get the API key
try:
    import config
    # Attempt to load API_KEY from config.py
    # If config.API_KEY is not set or empty, user will be prompted later.
    PRESET_API_KEY = getattr(config, 'API_KEY', '')
except ImportError:
    PRESET_API_KEY = ''
    print("Warning: 'config.py' not found. You will be prompted for your API key.")
except AttributeError:
    PRESET_API_KEY = ''
    print("Warning: 'API_KEY' not found in 'config.py'. You will be prompted for your API key.")


def _get_nested_stat(data, path, default=0):
    """
    Safely retrieves a nested value from a dictionary.

    Args:
        data (dict): The dictionary to search within.
        path (str): A dot-separated string representing the path to the value (e.g., "stats.Bedwars.kills_bedwars").
        default: The value to return if any part of the path is not found.

    Returns:
        The value found at the specified path, or the default value.
    """
    keys = path.split('.')
    current_data = data
    for key in keys:
        if isinstance(current_data, dict) and key in current_data:
            current_data = current_data[key]
        else:
            return default
    return current_data

def get_hypixel_player_data(username, api_key):
    """
    Fetches Hypixel player data using a username and API key.

    Args:
        username (str): The Minecraft username of the player.
        api_key (str): Your Hypixel API key.

    Returns:
        dict: A dictionary containing the player data if successful, otherwise None.
    """
    base_url = "https://api.hypixel.net/"
    headers = {
        "API-Key": api_key
    }

    # Step 1: Get UUID from Username
    print(f"Attempting to fetch UUID for username: {username}...")
    uuid_endpoint = f"{base_url}player?name={requests.utils.quote(username)}"
    try:
        uuid_response = requests.get(uuid_endpoint, headers=headers)
        uuid_response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
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

    # Step 2: Get Player Data using UUID
    print(f"Fetching player data for UUID: {player_uuid}...")
    player_data_endpoint = f"{base_url}player?uuid={player_uuid}"
    try:
        player_data_response = requests.get(player_data_endpoint, headers=headers)
        player_data_response.raise_for_status() # Raise an HTTPError for bad responses
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
    """
    Extracts and calculates important Bedwars statistics from player data.

    Args:
        player_data (dict): The full player data dictionary.

    Returns:
        dict: A dictionary containing only the requested Bedwars stats.
    """
    bedwars_stats = {}

    # Safely get Bedwars specific stats
    bw_data = _get_nested_stat(player_data, "stats.Bedwars", {})
    
    # Define Bedwars modes and their API prefixes
    bedwars_modes = {
        "Overall": "", # For general stats like 'kills_bedwars'
        "Solo": "eight_one_",
        "Doubles": "eight_two_",
        "Trios": "four_three_",
        "Quads": "four_four_",
        "4v4": "four_two_", # Sometimes distinct, sometimes same as Quads
        "Dream Mode": "dream_" # For dream mode specific stats
    }

    # --- General Bedwars Stats ---
    bedwars_stats["Bedwars Level"] = _get_nested_stat(player_data, "achievements.bedwars_level")
    bedwars_stats["Prestige"] = f"Determined by Bedwars Level ({bedwars_stats['Bedwars Level']})"
    bedwars_stats["Tokens"] = _get_nested_stat(player_data, "total_tokens", _get_nested_stat(player_data, "rewards.total_tokens", 0))
    bedwars_stats["Quests Completed"] = _get_nested_stat(player_data, "achievements.bedwars_quests_completed", 0)
    bedwars_stats["Karma"] = _get_nested_stat(player_data, "karma")
    bedwars_stats["Winstreak"] = _get_nested_stat(bw_data, "winstreak")

    # --- Resource Collection (not including dream) ---
    bedwars_stats["Diamonds Collected"] = _get_nested_stat(bw_data, "diamond_resources_collected_bedwars")
    bedwars_stats["Emeralds Collected"] = _get_nested_stat(bw_data, "emerald_resources_collected_bedwars")
    bedwars_stats["Gold Collected"] = _get_nested_stat(bw_data, "gold_resources_collected_bedwars")
    bedwars_stats["Iron Collected"] = _get_nested_stat(bw_data, "iron_resources_collected_bedwars")


    # --- Stats broken down by game mode ---
    for mode_name, prefix in bedwars_modes.items():
        # Kills
        kills = _get_nested_stat(bw_data, f"{prefix}kills_bedwars")
        if kills > 0:
            bedwars_stats[f"Kills ({mode_name})"] = kills

        # Final Kills
        final_kills = _get_nested_stat(bw_data, f"{prefix}final_kills_bedwars")
        if final_kills > 0:
            bedwars_stats[f"Final Kills ({mode_name})"] = final_kills

        # Bed Breaks
        bed_breaks = _get_nested_stat(bw_data, f"{prefix}beds_broken_bedwars")
        if bed_breaks > 0:
            bedwars_stats[f"Bed Breaks ({mode_name})"] = bed_breaks

        # Deaths
        deaths = _get_nested_stat(bw_data, f"{prefix}deaths_bedwars")
        if deaths > 0:
            bedwars_stats[f"Deaths ({mode_name})"] = deaths

        # Final Deaths
        final_deaths = _get_nested_stat(bw_data, f"{prefix}final_deaths_bedwars")
        if final_deaths > 0:
            bedwars_stats[f"Final Deaths ({mode_name})"] = final_deaths

        # Wins
        wins = _get_nested_stat(bw_data, f"{prefix}wins_bedwars")
        if wins > 0:
            bedwars_stats[f"Wins ({mode_name})"] = wins

        # Losses
        losses = _get_nested_stat(bw_data, f"{prefix}losses_bedwars")
        if losses > 0:
            bedwars_stats[f"Losses ({mode_name})"] = losses

        # Calculated Ratios (only if both numerator and denominator exist and are not zero)
        if kills > 0 or deaths > 0:
            bedwars_stats[f"Kill Death Ratio (KDR) ({mode_name})"] = round(kills / max(1, deaths), 2) if deaths > 0 else "N/A"
        
        if final_kills > 0 or final_deaths > 0:
            bedwars_stats[f"Final Kill Death Ratio (FKDR) ({mode_name})"] = round(final_kills / max(1, final_deaths), 2) if final_deaths > 0 else "N/A"
        
        if wins > 0 or losses > 0:
            bedwars_stats[f"Win Loss Ratio (WLR) ({mode_name})"] = round(wins / max(1, losses), 2) if losses > 0 else "N/A"

    return bedwars_stats

def calculate_skywars_level(experience):
    """
    Calculates Skywars level from raw experience points.
    Based on common Hypixel SW XP progression.
    """
    xps = [0, 20, 70, 150, 250, 500, 1000, 2000, 3500, 6000, 10000, 15000]
    
    if experience >= 15000:
        return (experience - 15000) / 10000 + 12
    else:
        for i in range(len(xps)):
            if experience < xps[i]:
                # Linear interpolation for levels below 12
                if i == 0: # Handle case where XP is very low (e.g., 0-19)
                    return experience / xps[0] if xps[0] > 0 else 0
                return i + (experience - xps[i-1]) / (xps[i] - xps[i-1])
    return 0 # Fallback

def get_skywars_prestige_name(level):
    """
    Determines the Skywars prestige name based on the calculated level.
    """
    # Use math.floor to get the integer part of the level for prestige mapping
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
    elif level_int < 60: # Rainbow stars are typically levels 50-59
        return "Rainbow"
    else: # Levels 60+ are usually Mythic or higher
        return "Mythic"


def extract_skywars_important_stats(player_data):
    """
    Extracts and calculates important Skywars statistics from player data
    based on the provided list, broken down by game mode.

    Args:
        player_data (dict): The full player data dictionary.

    Returns:
        dict: A dictionary containing only the requested Skywars stats.
    """
    skywars_stats = {}

    # Safely get Skywars specific stats
    sw_data = _get_nested_stat(player_data, "stats.SkyWars", {})

    # --- General Skywars Stats ---
    sw_experience = _get_nested_stat(sw_data, "skywars_experience")
    skywars_level = calculate_skywars_level(sw_experience)
    skywars_stats["Level"] = round(skywars_level, 2)
    skywars_stats["Prestige"] = get_skywars_prestige_name(skywars_level)
    skywars_stats["Coins"] = _get_nested_stat(sw_data, "coins")
    skywars_stats["Soul Well Uses"] = _get_nested_stat(sw_data, "soul_well_uses")
    skywars_stats["Soul Well Legendaries"] = _get_nested_stat(sw_data, "soul_well_leg")
    skywars_stats["Soul Well Rares"] = _get_nested_stat(sw_data, "soul_well_rares")
    skywars_stats["Paid Souls"] = _get_nested_stat(sw_data, "paid_souls")
    skywars_stats["Souls Gathered"] = _get_nested_stat(sw_data, "souls_gathered")
    skywars_stats["Eggs Thrown"] = _get_nested_stat(sw_data, "egg_thrown")
    skywars_stats["Enderpearls Thrown"] = _get_nested_stat(sw_data, "enderpearls_thrown")

    # Define Skywars modes and their API prefixes (common ones)
    # These prefixes are based on how Hypixel structures its API data for different modes.
    skywars_modes = {
        "Overall": "", # For general stats that apply to all modes combined
        "Solo Normal": "solo_normal_",
        "Solo Insane": "solo_insane_",
        "Team Normal": "team_normal_", # Often refers to doubles or general teams
        "Team Insane": "team_insane_",
        "Mega Normal": "mega_normal_",
        "Mega Insane": "mega_doubles_", # Mega Insane usually refers to Mega Doubles
        "Mini": "mini_", # Common prefix for mini modes
        "Labs": "lab_", # Common prefix for lab modes
    }

    # --- Stats broken down by game mode ---
    for mode_name, prefix in skywars_modes.items():
        # Kills
        kills = _get_nested_stat(sw_data, f"{prefix}kills")
        if kills > 0:
            skywars_stats[f"Kills ({mode_name})"] = kills

        # Assists
        assists = _get_nested_stat(sw_data, f"{prefix}assists")
        if assists > 0:
            skywars_stats[f"Assists ({mode_name})"] = assists

        # Deaths
        deaths = _get_nested_stat(sw_data, f"{prefix}deaths")
        if deaths > 0:
            skywars_stats[f"Deaths ({mode_name})"] = deaths

        # Wins
        wins = _get_nested_stat(sw_data, f"{prefix}wins")
        if wins > 0:
            skywars_stats[f"Wins ({mode_name})"] = wins

        # Losses
        losses = _get_nested_stat(sw_data, f"{prefix}losses")
        if losses > 0:
            skywars_stats[f"Losses ({mode_name})"] = losses

        # Arrows Shot (mode specific)
        arrows_shot = _get_nested_stat(sw_data, f"{prefix}arrows_shot")
        if arrows_shot > 0:
            skywars_stats[f"Arrows Shot ({mode_name})"] = arrows_shot

        # Arrows Hit (mode specific)
        arrows_hit = _get_nested_stat(sw_data, f"{prefix}arrows_hit")
        if arrows_hit > 0:
            skywars_stats[f"Arrows Hit ({mode_name})"] = arrows_hit

        # Calculated Ratios (only if relevant stats exist and are not zero)
        # KDR
        if (kills > 0 or deaths > 0) and (kills != 0 or deaths != 0):
            skywars_stats[f"Kill Death Ratio (KDR) ({mode_name})"] = round(kills / max(1, deaths), 2) if deaths > 0 else "N/A"
        
        # WLR
        if (wins > 0 or losses > 0) and (wins != 0 or losses != 0):
            skywars_stats[f"Win Loss Ratio (WLR) ({mode_name})"] = round(wins / max(1, losses), 2) if losses > 0 else "N/A"

        # Arrow Hit/Shot Ratio
        if (arrows_shot > 0 or arrows_hit > 0) and (arrows_shot != 0 or arrows_hit != 0):
            skywars_stats[f"Arrow Hit/Shot Ratio ({mode_name})"] = round(arrows_hit / max(1, arrows_shot), 2) if arrows_shot > 0 else "N/A"

    return skywars_stats

if __name__ == "__main__":
    # Get input from the user
    minecraft_username = input("Enter your Minecraft username: ").strip()
    
    # Try to get API key from config.py, otherwise prompt the user
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
            
            # Prompt for game mode
            game_mode_input = input("Enter the game mode you want to see data for (e.g., Bedwars, SkyWars, Arcade): ").strip()

            if game_mode_input.lower() == "bedwars":
                important_bedwars_stats = extract_bedwars_important_stats(player_info)
                print("\n--- Important Bedwars Stats ---")
                for stat, value in important_bedwars_stats.items():
                    # Format numbers with commas for readability
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
                # Fallback for other game modes (raw data)
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
