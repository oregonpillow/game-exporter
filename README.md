# Game Exporter

This project provides two simple Prometheus metric exporters for tracking the online and in-game status of your friends on Steam and PlayStation.

- The **Steam exporter** uses the official Steam Web API.
- The **PlayStation exporter** uses the reverse-engineered PlayStation Network API via the `PSNAWP` Python package.

The exporters provide similar metrics, with some differences due to the terminology and data available from each platform.

## Features

- Exports Prometheus metrics for Steam and PlayStation friend activity.
- Tracks online status, last online time, and current game.
- Configurable via environment variables.
- Includes a utility to keep the Steam games list updated.

## Metric Comparison

### Metric Equivalents

This table shows the direct equivalents between the metrics provided by the PlayStation and Steam exporters.

| PlayStation Metric                   | Steam Equivalent               | Description                                                                                                                                                                                                                                               |
| :----------------------------------- | :----------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `playstation_exporter_online_status` | `steam_exporter_online_status` | Tracks the user's online status. While the PlayStation metric is a simple (0 - Offline, 1 - Online), the Steam metric provides more detailed states (0 - Offline, 1 - Online, 2 - Busy, 3 - Away, 4 - Snooze, 5 - looking to trade, 6 - looking to play). |
| `playstation_exporter_last_online`   | `steam_exporter_last_online`   | Tracks the last time a user was online, represented as a Unix timestamp.                                                                                                                                                                                  |

### Label Comparison

This table breaks down the labels available for the metrics from each exporter.

| Label        | PlayStation | Steam | Description                                                                                                                                                                          |
| :----------- | :---------- | :---- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `username`   | ✅          | ✅    | The user's display name (Online ID on PlayStation, Persona Name on Steam).                                                                                                           |
| `account_id` | ✅          | ✅    | The unique identifier for the user's account on the respective platform.                                                                                                             |
| `game_name`  | ✅          | ✅    | The name of the game the user is currently playing. This will be "N/A" if the user is not in a game. _Only provided for the online_status metrics._                                  |
| `game_id`    | ✅          | ✅    | The unique identifier for the game on the respective platform (`npTitleId` on PlayStation, `appid` on Steam). "N/A" if not in a game. _Only provided for the online_status metrics._ |

## Setup and Usage

### Prerequisites

For Steam exporter:

- Steam account id
- Steam API Key - [Steam API instructions](https://steamcommunity.com/dev)

For Playstation exporter:

- A PlayStation NPSSO code - [psnawp instructions](https://github.com/isFakeAccount/psnawp?tab=readme-ov-file#getting-started)

### Installation

1.  Clone the repository:

    ```bash
    git clone https://github.com/oregonpillow/game-exporter.git
    cd game-exporter
    ```

2.  Install the dependencies using `uv`:
    ```bash
    uv pip sync
    ```

### Running the Exporters

#### Steam Exporter

1.  Set the required environment variables:

    ```bash
    export STEAM_EXPORTER_API_KEY="YOUR_API_KEY"
    export STEAM_EXPORTER_STEAM_ID="YOUR_STEAM_ID"
    ```

2.  Run the exporter:
    ```bash
    uv run python -m game_exporter.steam_exporter
    ```
    Metrics will be available at `http://localhost:9099`.

#### PlayStation Exporter

1.  Set the required environment variable:

    ```bash
    export PLAYSTATION_EXPORTER_NPSSO_CODE="YOUR_NPSSO_CODE"
    ```

2.  Run the exporter:
    ```bash
    uv run python -m game_exporter.playstation_exporter
    ```
    Metrics will be available at `http://localhost:9098`.

### Running the Exporters

#### Steam Exporter

1.  Set the required environment variables:

    ```bash
    export STEAM_EXPORTER_API_KEY="YOUR_API_KEY"
    export STEAM_EXPORTER_STEAM_ID="YOUR_STEAM_ID"
    ```

2.  Run the exporter:
    ```bash
    python steam_exporter.py
    ```
    Metrics will be available at `http://localhost:9099`.

#### PlayStation Exporter

1.  Set the required environment variable:

    ```bash
    export PLAYSTATION_EXPORTER_NPSSO_CODE="YOUR_NPSSO_CODE"
    ```

2.  Run the exporter:
    ```bash
    python playstation_exporter.py
    ```
    Metrics will be available at `http://localhost:9098`.

### Docker

You can also run the exporters using Docker. Dockerfiles are provided for each exporter.

#### Building the Images

**Steam Exporter:**

```bash
docker build -f Dockerfile.steam -t steam-exporter .
```

**PlayStation Exporter:**

```bash
docker build -f Dockerfile.playstation -t playstation-exporter .
```

You can also specify the user and group ID at build time:

```bash
docker build --build-arg UID=$(id -u) --build-arg GID=$(id -g) -f Dockerfile.steam -t steam-exporter .
```

#### Running the Containers

**Steam Exporter:**

```bash
docker run -d --name steam-exporter \
  -e STEAM_EXPORTER_API_KEY="YOUR_API_KEY" \
  -e STEAM_EXPORTER_STEAM_ID="YOUR_STEAM_ID" \
  -p 9099:9099 \
  steam-exporter
```

**PlayStation Exporter:**

```bash
docker run -d --name playstation-exporter \
  -e PLAYSTATION_EXPORTER_NPSSO_CODE="YOUR_NPSSO_CODE" \
  -p 9098:9098 \
  playstation-exporter
```

#### Running with Docker Compose

A `docker-compose.yml` file is also provided for convenience. Before running, you must edit the `docker-compose.yml` file and replace the placeholder values for the following environment variables with your actual credentials:

- `STEAM_EXPORTER_API_KEY`
- `STEAM_EXPORTER_STEAM_ID`
- `PLAYSTATION_EXPORTER_NPSSO_CODE`

After editing the file, you can run both exporters with:

```bash
docker-compose up -d
```

### Environment Variables

You can configure the exporters using the following environment variables:

**Steam Exporter:**

| Variable                         | Default | Description                                                                                |
| :------------------------------- | :------ | :----------------------------------------------------------------------------------------- |
| `STEAM_EXPORTER_LOG_LEVEL`       | `INFO`  | Log level for the exporter.                                                                |
| `STEAM_EXPORTER_API_KEY`         | (None)  | **Required.** Your Steam API key.                                                          |
| `STEAM_EXPORTER_STEAM_ID`        | (None)  | **Required.** Your 64-bit Steam ID.                                                        |
| `STEAM_EXPORTER_PORT`            | `9099`  | Port for the metrics endpoint.                                                             |
| `STEAM_EXPORTER_INTERVAL`        | `60`    | Update interval in seconds.                                                                |
| `STEAM_EXPORTER_INCLUDE_FRIENDS` | `true`  | Whether to include friends or not. Set to 'false' to gather metrics for your account only. |

**PlayStation Exporter:**

| Variable                               | Default | Description                                                                                |
| :------------------------------------- | :------ | :----------------------------------------------------------------------------------------- |
| `PLAYSTATION_EXPORTER_LOG_LEVEL`       | `INFO`  | Log level for the exporter.                                                                |
| `PLAYSTATION_EXPORTER_NPSSO_CODE`      | (None)  | **Required.** Your PSN NPSSO code.                                                         |
| `PLAYSTATION_EXPORTER_PORT`            | `9098`  | Port for the metrics endpoint.                                                             |
| `PLAYSTATION_EXPORTER_INTERVAL`        | `120`   | Update interval in seconds.                                                                |
| `PLAYSTATION_EXPORTER_INCLUDE_FRIENDS` | `true`  | Whether to include friends or not. Set to 'false' to gather metrics for your account only. |

## 🪝 Pre-commit Hooks

This project uses a `pre-commit` to manage pre-commit hooks. To set it up:

- `uv tool install pre-commit --with pre-commit-uv`
- `uvx pre-commit install`

Now everytime you make a commit, the configured hooks will run automatically. To force a run of all hooks on all files, use: `uvx pre-commit run -a`

## Building Docker images

```
docker-compose build --no-cache steam-exporter && docker-compose build --no-cache playstation-exporter && docker push oregonpillow/game-exporter:steam-exporter && docker push oregonpillow/game-exporter:playstation-exporter
```
