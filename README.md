# PCO Song Archive & Spotify Sync

A self-hosted Flask app that listens to [Planning Center Online (PCO)](https://www.planningcenter.com/) webhooks and automatically syncs upcoming service song lists to Spotify playlists. It also serves a simple web page showing songs for services in the next 7 days.

## How It Works

1. PCO sends a webhook to this app whenever a plan item (song) is created, updated, or deleted.
2. The app parses the payload, updates a MySQL database with the current song list for that plan, and then syncs the plan to Spotify.
3. For each plan within the next 7 days, the app finds or creates a Spotify playlist, searches for each song, and replaces the playlist's tracks to match the current plan order.
4. A web page at the app's root URL displays upcoming services and embeds the Spotify playlist if one exists.

A Cloudflare Tunnel is included in the Docker Compose setup to expose the app publicly without opening firewall ports — this is required for PCO webhooks to reach the app.

## Stack

| Layer | Technology |
|---|---|
| App | Python / Flask |
| Database | MySQL 8 |
| Spotify | [Spotipy](https://spotipy.readthedocs.io/) |
| Tunnel | Cloudflare Tunnel (`cloudflared`) |
| Container | Docker / Docker Compose |

## Project Structure

```
.
├── app.py                 # Flask app and webhook route
├── models.py              # SQLAlchemy models (Plan, PlanSong)
├── PlanItemPayload.py     # Parses incoming PCO webhook payloads
├── pco_service.py         # Fetches plan details from the PCO API
├── spotify_handler.py     # Creates/updates Spotify playlists
├── templates/
│   └── index.html         # Web UI for upcoming services
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## Prerequisites

- Docker & Docker Compose
- A [Planning Center](https://www.planningcenter.com/) account with API access
- A [Spotify Developer](https://developer.spotify.com/) app
- A [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/) token (or another way to expose the app publicly)

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/your-username/pco-song-archive-and-spotify-sync.git
cd pco-song-archive-and-spotify-sync
```

### 2. Get a Spotify refresh token

The app uses a long-lived refresh token to authenticate with Spotify without needing a browser-based login on every restart. To get one, run Spotipy's auth flow locally once:

```python
from spotipy.oauth2 import SpotifyOAuth

auth = SpotifyOAuth(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
    redirect_uri="YOUR_REDIRECT_URI",
    scope="playlist-modify-public playlist-modify-private ugc-image-upload playlist-read-private"
)
token = auth.get_access_token(as_dict=True)
print(token["refresh_token"])
```

### 3. Create a `.env` file

```env
# MySQL
MYSQL_ROOT_PASSWORD=your_root_password
MYSQL_DATABASE=your_database_name
MYSQL_USER=your_db_user
MYSQL_PASSWORD=your_db_password
DATABASE_URL=mysql+pymysql://your_db_user:your_db_password@db/your_database_name

# Planning Center
PCO_APP_ID=your_pco_app_id
PCO_SECRET=your_pco_secret

# Spotify
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=your_spotify_redirect_uri
SPOTIFY_USER_ID=your_spotify_user_id
SPOTIFY_REFRESH_TOKEN=your_spotify_refresh_token

# Cloudflare
CLOUDFLARE_TUNNEL_TOKEN=your_cloudflare_tunnel_token
```

### 4. Add a playlist cover image (optional)

Place a `bibc_logo.png` in the project root to use as the Spotify playlist cover. If the file is missing, the cover upload step will fail — you can remove the `set_playlist_cover` call in `spotify_handler.py` if you don't need this.

### 5. Start the app

```bash
docker compose up -d
```

The app will wait for MySQL to be healthy before starting, and will create the required tables on first run.

### 6. Configure the PCO webhook

In Planning Center, go to **Integrations → Webhooks** and add a new webhook pointing to your public URL:

```
https://your-tunnel-domain.com/bibcservicesongs
```

Subscribe to the `plan_item` events (created, updated, destroyed) and the `plan.destroyed` event.

## Web UI

Visiting the app's root URL (`/bibcservicesongs`) in a browser shows upcoming services for the next 7 days. If a Spotify playlist has been created for a plan, it is embedded directly on the page. Otherwise, the song list and keys are displayed as plain text.

## Notes

- Plans are only synced to Spotify if their date falls **within the next 7 days**.
- Spotify sync runs in a background thread so it doesn't delay the webhook response.
- The app handles duplicate webhook deliveries gracefully — songs and plans are upserted, not duplicated.
- Playlist names are prefixed with `BIBC ` (e.g. `BIBC Contemporary Service`). The app will find an existing playlist by name before creating a new one.
