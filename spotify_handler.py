import spotipy
from spotipy.oauth2 import SpotifyOAuth
from datetime import datetime, timedelta
import os
import base64
from requests import exceptions

def set_playlist_cover(sp, playlist_id, image_path="bibc_logo.png"):
    with open(image_path, "rb") as image_file:
        # Convert image to base64 string
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        
    # Upload to Spotify
    try:
        sp.playlist_upload_cover_image(playlist_id, encoded_string)
    except exceptions.ReadTimeout:
        print("Failed to upload cover image")


scope = "playlist-modify-public playlist-modify-private ugc-image-upload playlist-read-private"

def get_spotify_client():
    auth_manager = SpotifyOAuth(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
        scope=scope,
    )

    token_info = auth_manager.refresh_access_token(os.getenv("SPOTIFY_REFRESH_TOKEN"))
    sp = spotipy.Spotify(auth=token_info["access_token"])
    return sp
    
def is_within_next_7_days(plan_date):
    if not plan_date:
        return False
    if isinstance(plan_date, str):
        plan_date = datetime.fromisoformat(plan_date)
    now = datetime.now()
    return now <= plan_date <= now + timedelta(days=7)
    
def search_track(sp, song_title):
    """Search Spotify for a track. Returns spotify track ID or None."""
    results = sp.search(q=song_title, type="track", limit=5)
    tracks = results["tracks"]["items"]
    return tracks[0]["id"] if tracks else None
    

def find_existing_playlist(sp, name):
    """Search the user's playlists for one matching the given name. Returns ID or None."""
    user_id = os.getenv("SPOTIFY_USER_ID")
    offset = 0
    while True:
        response = sp.current_user_playlists(limit=50, offset=offset)
        for playlist in response["items"]:
            if playlist["name"].lower() == name.lower() or playlist["name"].lower() == "bibc "+name.lower():
                return playlist["id"]
        if response["next"]:
            offset += 50
        else:
            break
    return None

def build_playlist_tracks(sp, songs, plan):
    """
    Resolve Spotify track IDs for all songs in the plan.
    Updates song_spotify_id on the model objects (caller commits).
    Returns list of track IDs (skipping unresolved songs).
    """
    from models import db, PlanSong

    track_ids = []
    for song in sorted(songs, key=lambda s: s.position):
        if not song.song_spotify_id:
            existing = PlanSong.query.filter(
                PlanSong.song_title == song.song_title,
                PlanSong.song_spotify_id.isnot(None)
            ).first()
            if existing:
                song.song_spotify_id = existing.song_spotify_id
            else:
                found_id = search_track(sp, song.song_title)
                if found_id:
                    song.song_spotify_id = found_id
        if song.song_spotify_id:
            track_ids.append(f"spotify:track:{song.song_spotify_id}")
    return track_ids
 
def _set_playlist_tracks(sp, playlist_id, track_uris):
    """Replace all tracks in a playlist."""
    if not track_uris:
        sp.playlist_replace_items(playlist_id, [])
        return
    sp.playlist_replace_items(playlist_id, track_uris)

def delete_playlist(playlist_id):
    try:
        sp = get_spotify_client()
    except Exception as e:
        print(f"Spotify auth failed: {e}")
        return
    sp.current_user_unfollow_playlist(playlist_id)
    print(f"removed playlist {playlist_id} from account")

def sync_plan_to_spotify(plan):
    """
    Main entry point. Call this after DB is updated for a plan.
    Creates or updates the Spotify playlist for the given plan.
    Only acts if the plan is within the next 7 days.
    """
    from models import db

    if not is_within_next_7_days(plan.plan_date):
        return

    if not plan.songs:
        return

    try:
        sp = get_spotify_client()
    except Exception as e:
        print(f"Spotify auth failed: {e}")
        return

    user_id = os.getenv("SPOTIFY_USER_ID")
    playlist_name = plan.plan_backup_name or str(plan.strftime('%A, %B %d at %I:%M %p'))
    description = f"Songs for {plan.plan_date.strftime('%A, %B %d at %I:%M %p') if plan.plan_date else ''} {plan.plan_pco_id}"

    #Find or create the playlist
    if not plan.plan_spotify_id:
        existing_id = find_existing_playlist(sp, playlist_name)
        if existing_id:
            plan.plan_spotify_id = existing_id
        else:
            new_playlist = sp._post("me/playlists", payload={
                "name": f"BIBC {playlist_name}",
                "public": True,
                "description": description
            })
            plan.plan_spotify_id = new_playlist["id"]

    # Update playlist name/description in case plan details changed
    sp.playlist_change_details(
        playlist_id=plan.plan_spotify_id,
        name=f"BIBC {playlist_name}",
        description=description,
    )
		
    # Resolve tracks and replace playlist contents
    track_uris = build_playlist_tracks(sp, plan.songs, plan)
    _set_playlist_tracks(sp, plan.plan_spotify_id, track_uris)

    set_playlist_cover(sp, plan.plan_spotify_id)
	
    db.session.commit()
    print(f"Synced '{playlist_name}' to Spotify ({len(track_uris)} tracks)")
