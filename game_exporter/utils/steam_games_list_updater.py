import requests

from .logging_helper import setup_logger


def update_steam_games_list(logger=None):
    """
    Fetches the latest list of Steam games and saves it to a JSON file
    in the same directory as this script.
    """
    if logger is None:
        logger = setup_logger(__name__, "DEBUG")
    try:
        logger.info("Fetching latest Steam games list...")
        latest_steam_games = requests.get(
            "https://api.steampowered.com/ISteamApps/GetAppList/v2/"
        )
        latest_steam_games.raise_for_status()

        return latest_steam_games.json()

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data from Steam API: {e}")
    except IOError as e:
        logger.error(f"Error writing to file: {e}")
