import os
import pytz
import logging

from dotenv import load_dotenv
from datetime import datetime, timedelta
from sqlalchemy.exc import OperationalError

from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS, cross_origin

from instagram import post_story, delete_story_by_id, instagram_post_for_status

# General Configuration
tz = pytz.timezone('Europe/Berlin')
logging.basicConfig(level=logging.DEBUG)
load_dotenv()

# App
app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///state.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configure CORS
allowed_websites = os.getenv("ALLOWED_WEBSITES")
if allowed_websites == "*":
    origins = "*"
elif isinstance(allowed_websites, str):
    origins = [site.strip() for site in allowed_websites.split(",") if site.strip()]
else:
    origins = ""
CORS(app, origins=origins)

db = SQLAlchemy(app)

# State db model definition
class State(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(10), nullable=False, default="default")
    instagram_media_id = db.Column(db.String(50), nullable=True, default="")
    last_update = db.Column(db.DateTime, default=datetime.now(tz), onupdate=datetime.now(tz))

    # Return the state object if present. None otherwise
    @classmethod
    def get_state(cls):
        state = State.query.order_by(State.id.desc()).first()
        if not state:
            # If no state is found, update the status
            cls.update_status(new_status="default")
            state = cls.query.order_by(State.id.desc()).first()  # Get the updated state
        return state

    # Update the current status in db
    @classmethod
    def update_status(cls, new_status, instagram_media_id=None):
        current_state = cls.query.first()

        if current_state:
            current_state.status = new_status
            current_state.instagram_media_id = instagram_media_id
            current_state.last_update = datetime.now(tz)
        else:
            current_state = cls(status=new_status, instagram_media_id=instagram_media_id)
            db.session.add(current_state)
        db.session.commit()
    
    @classmethod
    def has_recent_media_id(cls, timedelta_hours=24):
        """Checks if there is an instagram_media_id and last_update is within the last 24 hours."""
        twenty_four_hours_ago = datetime.now(tz) - timedelta(hours=timedelta_hours)
        
        # Query to check if there's a valid instagram_media_id and if last_update is within the last 24 hours
        state = cls.query.filter(
            cls.instagram_media_id != None,
            cls.last_update >= twenty_four_hours_ago
        ).first()
        
        # Return True if a valid media ID exists and it's within the last 24 hours, otherwise False
        return state is not None

# Create DB tables
with app.app_context():
    try:
        db.create_all()
    except OperationalError as e:
        if 'table state already exists' in str(e):
            pass  # Table already exists, nothing to do
        else:
            raise  # Re-raise other OperationalErrors

# Routes
@app.route('/', methods=['GET'])
@cross_origin()
def get_status():
    current_state = State.get_state()
    return jsonify({"status": current_state.status, "last_update": current_state.last_update}), 200

@app.route("/update_status", methods=['GET'])
def update_status():
    """
    Handles GET requests to check or update the status.
    Requires a valid API key and an 'status' parameter to update.
    """

    # Check API Key
    api_key = request.args.get("api_key")
    if not api_key or api_key != os.getenv("API_KEY"):
        app.logger.debug(f"[Error] Wrong API-Key: '{api_key}' by: {request.remote_addr}")
        return jsonify({"result": "fail", "description": "API-KEY error"}), 401

    new_status = request.args.get("status", "")
    if new_status not in ["default", "canceled", "german", "english", "chat", "now"]:
        app.logger.debug(f"[Error] Wrong status: '{new_status}' by: {request.remote_addr}")
        return jsonify({"result": "fail", "description": "status error"}), 400

    # Check if request tires to set the same state again (e.g. reload of page or double button press)
    # In case also a story should be posted, we accept the request if the last story is older then 6h
    # Otherwise we will return success like a "cached" response 
    current_state = State.get_state()
    if current_state.status == new_status:
        if request.args.get("story"):
            if State.has_recent_media_id(timedelta_hours=6):
                return jsonify({"result": "success"}), 200
        else: return jsonify({"result": "success"}), 200

    # Check if there are story to delete
    if new_status == "default" and State.has_recent_media_id():
        delete_story_by_id(current_state.instagram_media_id)

    # Post an Instagram story
    media_id = None
    story = request.args.get("story", "")
    if story == "true" and instagram_post_for_status(new_status):
        # Delete previous status story
        if State.has_recent_media_id():
            delete_story_by_id(current_state.instagram_media_id)
        # Upload a new story.
        media_id = post_story(os.path.join("assets", f"{new_status}.png"))
        if media_id is None:
            # Update the status in the DB
            State.update_status(new_status=new_status, instagram_media_id=media_id)
            app.logger.info(f"[INFO] Status updated to: '{new_status}' by: {request.remote_addr}")
            return jsonify({"result": "fail", "description": "Failed to upload a story. However, the status was updated successfully."}), 400

    # Update the status in the DB
    State.update_status(new_status=new_status, instagram_media_id=media_id)
    app.logger.info(f"[INFO] Status updated to: '{new_status}' by: {request.remote_addr}")
    return jsonify({"result": "success"}), 200

@app.route("/update_status_graphical", methods=['GET'])
def update_status_graphical():
    """
    Renders a graphical status page where the user will be shown a 'processing' message.
    """
    return render_template("processing.html")

if __name__ == '__main__':
    app.run(host=os.getenv("HOST", "0.0.0.0"), port=int(os.getenv("PORT", 5000)))
