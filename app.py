import os
import sys
import time
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template
from sqlalchemy.exc import OperationalError
from PlanItemPayload import PlanItemPayload
from pco_service import get_plan_details
from models import db, Plan, PlanSong

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

#Create tables if they don't exist
with app.app_context():
    retries = 5
    while retries > 0:
        try:
            db.create_all()
            print("Successfully connected to the database!", file=sys.stderr)
            break
        except OperationalError:
            retries -= 1
            print(f"Database not ready. Retrying in 5 seconds... ({retries} attempts left)", file=sys.stderr)
            time.sleep(5)
    else:
        print("Could not connect to the database. Exiting.", file=sys.stderr)
        sys.exit(1)

@app.route("/bibcservicesongs", methods=["GET","POST"])
def webhook():
    if request.method == "POST":
        payload = request.json
        
        if not payload:
            return jsonify({"error": "No payload"}), 400
        
        print(f"\n\nReceived webhook: {payload}", file=sys.stderr)
        
        plan_item_payload = PlanItemPayload(payload) 

        if plan_item_payload.check_payload() == False:
            return jsonify({"error": "Bad payload"}), 400

        action = plan_item_payload.get_action()
        is_song = plan_item_payload.check_if_song()
        plan_id = plan_item_payload.get_plan_id()
        
        if not is_song and action == "destroyed":
            #if a plan was deleted
            PlanSong.query.filter_by(plan_id=plan_id).delete()
            Plan.query.filter_by(plan_id=plan_id).delete()
            db.session.commit()
            print(f"\nRemoved Plan {plan_id}\n", file=sys.stderr)
            return jsonify({"status": "success"}), 200

        
        #check if plan is in database, add if not
        plan = Plan.query.filter_by(plan_id=plan_id).first()
        if not plan:
            plan_details = get_plan_details(plan_item_payload.get_plan_url())
            plan = Plan(plan_id=plan_id, plan_name=plan_details["plan_title"], plan_date=plan_details["plan_date"])
            db.session.add(plan)
            db.session.commit()
        
        if is_song and action in ["created", "updated"]:
            song_id = plan_item_payload.get_song_id()
            song_details = plan_item_payload.get_song_details()
            position_in_plan = plan_item_payload.get_position_in_plan()
            
            #check if song is already in plan
            plan_song = PlanSong.query.filter_by(plan_id=plan_id, song_id=song_id).first()
            
            if plan_song:
                #if yes update song details/ position
                plan_song.position = position_in_plan
                plan_song.song_title = song_details.get("song_title")
                plan_song.song_key = song_details.get("song_key")
            else:
                #else create new entry
                new_plan_song = PlanSong(
                    plan_id=plan_id,
                    song_id=song_id,
                    song_title=song_details.get("song_title"),
                    song_key=song_details.get("song_key"),
                    position=position_in_plan
                )
                db.session.add(new_plan_song)
            
            db.session.commit()
            print(f"\nSaved Song {song_details.get('song_title')} at position {position_in_plan}\n", file=sys.stderr)
        
        elif is_song and action == "destroyed":
            # if song was removed from plan delete from database
            song_id = plan_item_payload.get_song_id()
            PlanSong.query.filter_by(plan_id=plan_id, song_id=song_id).delete()
            db.session.commit()
            print(f"\nRemoved Song {song_id} from Plan {plan_id}\n", file=sys.stderr)
                
        return jsonify({"status": "success"}), 200
    
    #GET
    today = datetime.now()
    seven_days_later = today + timedelta(days=7)
    
    upcoming_plans = Plan.query.filter(
        Plan.plan_date >= today,
        Plan.plan_date <= seven_days_later
    ).order_by(Plan.plan_date.asc()).all()
    
    return render_template("index.html", plans=upcoming_plans)
    
if __name__ == "__main__":
    # 0.0.0.0 - accessible inside the docker network
    app.run(host="0.0.0.0", port=5000)
