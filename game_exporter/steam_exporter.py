import os
import time

import requests
from prometheus_client import Gauge, start_http_server

from game_exporter.utils.logging_helper import setup_logger
from game_exporter.utils.steam_games_list_updater import update_steam_games_list


# --- Environment Variables ---
LOG_LEVEL = os.getenv("STEAM_EXPORTER_LOG_LEVEL", "INFO").upper()
API_KEY = os.environ.get("STEAM_EXPORTER_API_KEY")
STEAM_ID = os.environ.get("STEAM_EXPORTER_STEAM_ID")
PORT = int(os.environ.get("STEAM_EXPORTER_PORT", "9099"))
INTERVAL = int(os.environ.get("STEAM_EXPORTER_INTERVAL", "60"))
GAMES_JSON_PATH = os.environ.get(
    "STEAM_EXPORTER_GAMES_JSON_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "steam_games.json"),
)
INCLUDE_FRIENDS = str(os.environ.get("STEAM_EXPORTER_INCLUDE_FRIENDS", "true").lower())

logger = setup_logger(__name__, LOG_LEVEL)

logger.debug(f"Log level set to: '{LOG_LEVEL}'")
logger.debug(f"Using API_KEY: '{API_KEY}'")
logger.debug(f"Using STEAM_ID: '{STEAM_ID}'")
logger.debug(f"Exporter will run on port: '{PORT}'")
logger.debug(f"Update interval set to: '{INTERVAL} seconds'")
logger.debug(f"Using GAMES_JSON_PATH: '{GAMES_JSON_PATH}'")
logger.debug(
    f"Include friends set to: '{INCLUDE_FRIENDS}' and {'will' if INCLUDE_FRIENDS == 'true' else 'will not'} include friends"
)

if not API_KEY or not STEAM_ID:
    logger.error(
        "STEAM_EXPORTER_API_KEY and STEAM_EXPORTER_STEAM_ID must be set as environment variables."
    )
    exit(1)

# --- Prometheus Metrics ---
PERSONA_STATE = Gauge(
    "steam_exporter_online_status",
    "The user's current status. 0 - Offline, 1 - Online, 2 - Busy, 3 - Away, 4 - Snooze, 5 - looking to trade, 6 - looking to play.",
    ["username", "game_name", "account_id", "game_id"],
)
LAST_LOGOFF = Gauge(
    "steam_exporter_last_online",
    "The last time the user was online, in unix time.",
    ["username", "account_id"],
)

# Global cache for the games list
STEAM_GAMES_CACHE = {}


def load_steam_games_once():
    """
    Loads the steam games list from JSON into a global cache.
    If the file doesn't exist, it attempts to create it once.
    """
    global STEAM_GAMES_CACHE
    data = update_steam_games_list(logger)
    STEAM_GAMES_CACHE = {
        int(app["appid"]): app["name"] for app in data["applist"]["apps"]
    }
    logger.info(
        f"Successfully loaded {len(STEAM_GAMES_CACHE)} games into cache after creation."
    )


def get_account_ids(api_key, steam_id):
    """Fetch the list of friend Steam IDs."""
    if INCLUDE_FRIENDS != "true":
        return [steam_id]  # Only include our own ID

    params = {"key": api_key, "steamid": steam_id, "relationship": "friend"}
    try:
        response = requests.get(
            "https://api.steampowered.com/ISteamUser/GetFriendList/v0001/",
            params=params,
        )
        response.raise_for_status()
        friends_json = response.json()
        account_ids = [
            friend["steamid"]
            for friend in friends_json.get("friendslist", {}).get("friends", [])
        ]
        account_ids.append(steam_id)  # Add our own ID
        return account_ids
    except requests.exceptions.RequestException as e:
        logger.error(f"Could not fetch friend list: {e}")
        return [steam_id]  # Fallback to just our own ID


def get_player_summaries(api_key, steam_ids):
    """Fetch player summaries for a list of Steam IDs."""
    # Steam API allows up to 100 steam ids per request
    if not steam_ids:
        return []
    params = {"key": api_key, "steamids": ",".join(steam_ids)}
    try:
        response = requests.get(
            "http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/",
            params=params,
        )
        response.raise_for_status()
        return response.json().get("response", {}).get("players", [])
    except requests.exceptions.RequestException as e:
        logger.error(f"Could not fetch player summaries: {e}")
        return []


def update_metrics():
    """Fetch data from Steam and update Prometheus metrics."""
    account_ids = get_account_ids(API_KEY, STEAM_ID)
    players = get_player_summaries(API_KEY, account_ids)

    for player in players:
        steam_id = player.get("steamid", "N/A")
        persona_name = player.get("personaname", "N/A")

        game_id_val = player.get("gameid", 0)
        game_name = "N/A"
        if game_id_val and STEAM_GAMES_CACHE:
            if int(game_id_val) in STEAM_GAMES_CACHE:
                game_name = player.get(
                    "gameextrainfo", STEAM_GAMES_CACHE[int(game_id_val)]
                )
            else:
                game_name = "Unknown Game"
                logger.warning(
                    f"Game ID {game_id_val} not found in cache. Try updating the games list json."
                )

        personastate_labels = {
            "username": persona_name,
            "game_name": game_name,
            "account_id": steam_id,
            "game_id": game_id_val,
        }

        last_logoff_labels = {
            "username": persona_name,
            "account_id": steam_id,
        }

        # Set the gauge values with the corresponding labels
        PERSONA_STATE.labels(**personastate_labels).set(player.get("personastate", 0))
        LAST_LOGOFF.labels(**last_logoff_labels).set(player.get("lastlogoff", 0))

        if steam_id == STEAM_ID:
            logger.debug(
                f"Updated metrics for {persona_name} ({steam_id}) (your account)"
            )
        else:
            logger.debug(f"Updated metrics for {persona_name} ({steam_id})")


def main():
    """Main function to run the exporter."""
    # Load the steam games list into memory once at startup. ~ 30MB
    load_steam_games_once()

    start_http_server(PORT)
    logger.info("Steam exporter started...")

    while True:
        update_metrics()
        logger.debug(f"Metrics updated. Sleeping for {INTERVAL} seconds.")
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
