import os
import time
from datetime import datetime

from prometheus_client import Gauge, start_http_server
from psnawp_api import PSNAWP
from game_exporter.utils.logging_helper import setup_logger


# --- Environment Variables ---
LOG_LEVEL = os.getenv("PLAYSTATION_EXPORTER_LOG_LEVEL", "INFO").upper()
NPSSO_CODE = os.environ.get("PLAYSTATION_EXPORTER_NPSSO_CODE")
PORT = int(os.environ.get("PLAYSTATION_EXPORTER_PORT", 9098))
UPDATE_INTERVAL = int(os.environ.get("PLAYSTATION_EXPORTER_INTERVAL", 120))
INCLUDE_FRIENDS = str(
    os.environ.get("PLAYSTATION_EXPORTER_INCLUDE_FRIENDS", "true").lower()
)

logger = setup_logger(__name__, LOG_LEVEL)

logger.debug(f"Log level set to: '{LOG_LEVEL}'")
logger.debug(f"Using NPSSO_CODE: '{NPSSO_CODE}'")
logger.debug(f"Exporter will run on port: '{PORT}'")
logger.debug(f"Update interval set to: '{UPDATE_INTERVAL} seconds'")
logger.debug(
    f"Include friends set to: '{INCLUDE_FRIENDS}' and {'will' if INCLUDE_FRIENDS == 'true' else 'will not'} include friends"
)

if not NPSSO_CODE:
    logger.error("'PLAYSTATION_EXPORTER_NPSSO_CODE' environment variable must be set.")
    exit(1)

# --- Prometheus Metrics ---
ONLINE_STATUS = Gauge(
    "playstation_exporter_online_status",
    "The online status of the user (1 for online, 0 for offline)",
    ["username", "game_name", "account_id", "game_id"],
)
LAST_ONLINE = Gauge(
    "playstation_exporter_last_online",
    "The last time the user was online in Unix timestamp format",
    ["username", "account_id"],
)


def update_metrics(psnawp_client):
    """Fetch data from the PlayStation Network and update Prometheus metrics."""
    logger.debug("Fetching friend data from PSN...")
    try:
        my_profile = psnawp_client.me()
        my_username = my_profile.online_id
        my_account_id = my_profile.account_id

        all_account_ids = {my_account_id: my_username}
        if INCLUDE_FRIENDS == "true":
            friends_list = my_profile.friends_list()
            for friend in friends_list:
                all_account_ids[friend.account_id] = friend.online_id

        presences = my_profile.get_presences(list(all_account_ids.keys()))
        online_users_from_api = {
            p["accountId"] for p in presences.get("basicPresences", [])
        }

        # Set all users to offline first
        for account_id, username in all_account_ids.items():
            if account_id not in online_users_from_api:
                # This user is offline. Set a generic "offline" metric for them.
                ONLINE_STATUS.labels(
                    username=username,
                    game_name="Offline",
                    account_id=account_id,
                    game_id="N/A",
                ).set(0)

        for presence in presences.get("basicPresences", []):
            account_id = presence.get("accountId")
            username = all_account_ids.get(account_id)
            if not username:
                continue  # Should not happen, but good practice

            online_status_str = presence.get("primaryPlatformInfo", {}).get(
                "onlineStatus"
            )
            online_status = 1 if online_status_str == "online" else 0

            last_online_str = presence.get("primaryPlatformInfo", {}).get(
                "lastOnlineDate"
            )
            if last_online_str:
                if last_online_str.endswith("Z"):
                    last_online_str = last_online_str[:-1] + "+00:00"
                last_online = int(datetime.fromisoformat(last_online_str).timestamp())
            else:
                last_online = 0

            game_title_info_list = presence.get("gameTitleInfoList", [])
            game_name = (
                game_title_info_list[0].get("titleName", "Not Playing")
                if game_title_info_list
                else "Not Playing"
            )

            game_id = (
                game_title_info_list[0].get("npTitleId", "N/A")
                if game_title_info_list
                else "N/A"
            )

            # Remove any old metrics for this user to prevent stale game data
            ONLINE_STATUS.remove(username, "Offline", account_id, "N/A")
            ONLINE_STATUS.remove(username, "Not Playing", account_id, "N/A")

            online_status_labels = {
                "username": username,
                "game_name": game_name,
                "account_id": account_id,
                "game_id": game_id,
            }

            last_online_labels = {
                "username": username,
                "account_id": account_id,
            }

            ONLINE_STATUS.labels(**online_status_labels).set(online_status)
            LAST_ONLINE.labels(**last_online_labels).set(last_online)

            if username == my_username:
                logger.debug(
                    f"Updated metrics for {username} ({account_id}) (your account)"
                )
            else:
                logger.debug(f"Updated metrics for {username} ({account_id})")

    except Exception as e:
        logger.error(f"Could not update metrics: {e}")


def main():
    logger.info("Initializing PSN API client...")
    psnawp = PSNAWP(NPSSO_CODE)

    start_http_server(PORT)
    logger.info(f"Playstation exporter started on port {PORT}")

    while True:
        update_metrics(psnawp)
        logger.debug(f"Metrics updated. Sleeping for {UPDATE_INTERVAL} seconds.")
        time.sleep(UPDATE_INTERVAL)


if __name__ == "__main__":
    main()
