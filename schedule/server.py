from flask import Flask, send_file, jsonify
import logging
import os
import json
from datetime import datetime, timedelta
from threading import Thread
import time
from flask_cors import CORS
from schedule.schedule import (
    Schedule,
    format_data,
    split_events_by_type,
    generate_ics,
    process_schedule,
)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Paths for calendars
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
COURSES_FILE = os.path.join(BASE_DIR, "schedule/data/calendars/courses.ics")
EXAMS_FILE = os.path.join(BASE_DIR, "schedule/data/calendars/exams.ics")
CSV_FILE = os.path.join(BASE_DIR, "schedule/data/csv/schedule.csv")

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Variable to store last sync time
last_sync_time = None


def perform_resync():
    """
    Function to perform resync of calendars.
    """
    global last_sync_time
    try:
        # Initialize Schedule instance
        schedule = Schedule()

        logging.info("Logging in to the schedule system...")
        page = schedule.login()
        if not page:
            logging.error("Failed to log in to the schedule system.")
            return

        logging.info("Fetching schedule data...")
        raw_data = schedule.get_schedule(page)
        if not raw_data:
            logging.error("Failed to fetch schedule data.")
            return

        # Clean and parse data
        logging.info("Cleaning and parsing schedule data...")
        formatted_data = format_data(raw_data)
        events = json.loads(formatted_data)

        # Process and save
        logging.info("Processing schedule and generating files...")
        process_schedule(events, CSV_FILE)
        courses, exams = split_events_by_type(events)

        if courses:
            generate_ics(courses, COURSES_FILE)
        if exams:
            generate_ics(exams, EXAMS_FILE)

        # Update last sync time
        last_sync_time = datetime.now()

        logging.info("Resync completed successfully.")
    except Exception as e:
        logging.error(f"Error during resync: {e}")


def auto_resync():
    """
    Automatically resync files every 15 minutes.
    """
    while True:
        logging.info("Starting automatic resync...")
        perform_resync()
        logging.info("Next resync in 15 minutes...")
        time.sleep(15 * 60)  # Sleep for 15 minutes


@app.route("/calendar/<calendar_type>.ics")
def serve_calendar(calendar_type):
    """
    Serve the requested ICS file (courses or exams).
    :param calendar_type: 'courses' or 'exams'
    """
    try:
        if calendar_type == "courses" and os.path.exists(COURSES_FILE):
            return send_file(
                COURSES_FILE, as_attachment=True, download_name="courses.ics"
            )
        elif calendar_type == "exams" and os.path.exists(EXAMS_FILE):
            return send_file(EXAMS_FILE, as_attachment=True, download_name="exams.ics")
        else:
            return jsonify({"error": "Invalid calendar type or file not found."}), 404
    except Exception as e:
        logging.error(f"Error serving file: {e}")
        return jsonify({"error": "Internal Server Error"}), 500


@app.route("/resync", methods=["POST"])
def resync_calendars():
    """
    Resync calendar files by fetching schedule data and regenerating files.
    """
    try:
        perform_resync()
        return jsonify({"message": "Calendars resynchronized successfully!"}), 200
    except Exception as e:
        jsonify({"error": "Failed to resync calendars.", "details": str(e)}), 500


@app.route("/last-sync", methods=["GET"])
def get_last_sync_time():
    """
    Get the last synchronization time.
    """
    if last_sync_time:
        return jsonify(
            {"last_sync_time": last_sync_time.strftime("%Y-%m-%d %H:%M:%S")}
        ), 200
    else:
        return jsonify({"last_sync_time": "Never"}), 200


if __name__ == "__main__":
    # Start the automatic resync in a separate thread
    resync_thread = Thread(target=auto_resync, daemon=True)
    resync_thread.start()

    # Run the Flask app
    app.run(host="0.0.0.0", port=5000, ssl_context=("cert.pem", "key.pem"))
