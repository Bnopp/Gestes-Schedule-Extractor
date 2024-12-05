import os
import re
import json
import logging
import requests
import pandas as pd
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from ics import Calendar, Event

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class Schedule:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://www.gestes.info/gestes"
        self.login_url = f"{self.base_url}/connexion"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "Referer": self.login_url,
        }
        self.username = "pl03jlu"  # Replace with your username
        self.password = "maRley88-MANO"  # Replace with your password

    def get_csrf_token(self):
        try:
            response = self.session.get(self.login_url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            csrf_token = soup.find("input", {"name": "_csrfToken"})["value"]
            logging.info("CSRF Token fetched successfully.")
            return csrf_token
        except Exception as e:
            logging.error(f"Error fetching CSRF token: {e}")
            raise

    def login(self):
        try:
            csrf_token = self.get_csrf_token()
            payload = {
                "_method": "POST",
                "_csrfToken": csrf_token,
                "username": self.username,
                "password": self.password,
                "mobile": "0",
            }
            response = self.session.post(
                self.login_url, headers=self.headers, data=payload
            )
            if response.status_code == 200 and self.username in response.text:
                logging.info("Login successful.")
                return response.text
            else:
                logging.error("Login failed. Check credentials or network.")
                with open("login_failed.html", "w", encoding="utf-8") as file:
                    file.write(response.text)
                raise Exception("Login failed.")
        except Exception as e:
            logging.error(f"Error during login: {e}")
            raise

    def get_schedule(self, response_text):
        try:
            soup = BeautifulSoup(response_text, "html.parser")
            script_tags = soup.find_all("script")
            for script in script_tags:
                if "FullCalendar.Calendar" in script.text:
                    calendar_script = script.text
                    break
            else:
                logging.warning("No FullCalendar script found.")
                return None

            events_pattern = re.search(
                r"events: (\[.*?\]),", calendar_script, re.DOTALL
            )
            if events_pattern:
                logging.info("Schedule data extracted successfully.")
                return events_pattern.group(1)
            else:
                logging.warning("No events found in the script.")
                return None
        except Exception as e:
            logging.error(f"Error fetching schedule: {e}")
            raise


def format_data(data):
    try:
        data = re.sub(r",\s*\]$", "]", data, flags=re.MULTILINE)
        data = data.replace("end :", "end:")
        data = re.sub(r"T(\d+):\s*(\d+):\s*(\d+)", r"T\1:\2:\3", data)
        property_names = [
            "id",
            "start",
            "end",
            "title",
            "className",
            "backgroundColor",
            "extendedProps",
            "commentaire",
        ]
        pattern = r"(\b(?:" + "|".join(property_names) + r")\b)\s*:"
        data = re.sub(pattern, r'"\1":', data)
        data = data.replace("'", '"')

        def clean_multiline_strings(match):
            content = match.group(1)
            content = re.sub(r"\s+", " ", content)
            return f'"{content.strip()}"'

        data = re.sub(r'"(.*?)"', clean_multiline_strings, data, flags=re.DOTALL)
        logging.info("Data formatted successfully.")
        return data
    except Exception as e:
        logging.error(f"Error formatting data: {e}")
        raise


def split_events_by_type(events):
    courses = []
    exams = []

    for event in events:
        if event["backgroundColor"] == "rgb(255, 0 ,0)":
            exams.append(event)
        else:
            courses.append(event)

    logging.info(f"Split events into {len(courses)} courses and {len(exams)} exams.")
    return courses, exams


def generate_ics(events, filename):
    try:
        cal = Calendar()
        for event in events:
            e = Event()
            e.name = event["title"]
            e.description = event.get("extendedProps", {}).get("commentaire", "")

            # Parse the start and end times
            start_dt = datetime.fromisoformat(event["start"])
            end_dt = datetime.fromisoformat(event["end"])

            # Subtract one hour
            start_dt -= timedelta(hours=1)
            end_dt -= timedelta(hours=1)

            e.begin = start_dt
            e.end = end_dt

            cal.events.add(e)
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            f.writelines(cal)
        logging.info(f"ICS file generated: {filename}")
    except Exception as e:
        logging.error(f"Error generating ICS file: {e}")
        raise


def process_schedule(events, output_path):
    schedule_data = [
        {
            "ID": event.get("id"),
            "Title": event.get("title"),
            "Start": event.get("start"),
            "End": event.get("end"),
            "Commentaire": event.get("extendedProps", {}).get("commentaire", ""),
            "BackgroundColor": event.get("backgroundColor", ""),
        }
        for event in events
    ]
    df = pd.DataFrame(schedule_data)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logging.info(f"Schedule saved to {output_path}.")
    return df


if __name__ == "__main__":
    try:
        schedule = Schedule()
        page = schedule.login()
        raw_data = schedule.get_schedule(page)
        formatted_data = format_data(raw_data)
        events = json.loads(formatted_data)

        # Process and save
        process_schedule(events, "schedule/data/csv/schedule.csv")
        courses, exams = split_events_by_type(events)
        generate_ics(courses, "schedule/data/calendars/courses.ics")
        generate_ics(exams, "schedule/data/calendars/exams.ics")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
