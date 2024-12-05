import re
import json
import requests
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
from ics import Calendar, Event


class Schedule:
    def __init__(self):
        self.session = requests.Session()  # Persistent session for cookies
        self.base_url = "https://www.gestes.info/gestes"
        self.login_url = f"{self.base_url}/connexion"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "Referer": f"{self.base_url}/connexion",
        }
        self.username = "your_username"  # Replace with your username
        self.password = "your_password"  # Replace with your password

    def get_csrf_token(self):
        """
        Fetch the login page to extract the CSRF token.
        """
        response = self.session.get(self.login_url, headers=self.headers)
        soup = BeautifulSoup(response.text, "html.parser")
        csrf_token = soup.find("input", {"name": "_csrfToken"})["value"]
        print(f"CSRF Token: {csrf_token}")  # Debugging
        return csrf_token

    def login(self):
        """
        Log in to the system using the extracted CSRF token.
        """
        csrf_token = self.get_csrf_token()
        payload = {
            "_method": "POST",
            "_csrfToken": csrf_token,
            "username": "pl03jlu",
            "password": "maRley88-MANO",
            "mobile": "0",
        }
        response = self.session.post(self.login_url, headers=self.headers, data=payload)

        # Check if the username appears in the response HTML
        if response.status_code == 200 and "pl03jlu" in response.text:
            print("Login successful! Username found in the page.")
            return response.text
        elif response.status_code == 200:
            print("Login failed: Username not found in the page.")
            with open("login_failed.html", "w") as file:
                file.write(response.text)
        else:
            print(f"Login failed! Status code: {response.status_code}")
            print(response.text)  # Debugging
    
    def get_schedule(self, response_text: str):
        """
        Extract event data from the FullCalendar JavaScript configuration.
        """
        soup = BeautifulSoup(response_text, "html.parser")
        script_tags = soup.find_all("script")

        # Find the script containing the FullCalendar initialization
        for script in script_tags:
            if "FullCalendar.Calendar" in script.text:
                calendar_script = script.text
                break
        else:
            print("No FullCalendar script found.")
            return None

        # Extract the events array using regex
        events_pattern = re.search(r"events: (\[.*?\]),", calendar_script, re.DOTALL)
        if events_pattern:
            events_json = events_pattern.group(1)  # Extract JSON string
            print("Events extracted successfully!")
            return events_json
        else:
            print("No events found in the script.")
            return None

def format_data(data):
    data = re.sub(r",\s*\]$", "]", data, flags=re.MULTILINE)

    # Step 2: Fix 'end :' to 'end:'
    data = data.replace("end :", "end:")
    data = data.replace("end :", "end:")  # In case there are multiple occurrences

    # Step 3: Remove spaces after colons in time strings
    data = re.sub(r"T(\d+):\s*(\d+):\s*(\d+)", r"T\1:\2:\3", data)

    # Step 4: Quote property names
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

    # Step 5: Replace single quotes with double quotes
    data = data.replace("'", '"')

    # Step 6: Remove any line breaks inside strings and unindent multi-line strings
    def clean_multiline_strings(match):
        content = match.group(1)
        # Remove line breaks and extra spaces
        content = re.sub(r"\s+", " ", content)
        return f'"{content.strip()}"'

    data = re.sub(r'"(.*?)"', clean_multiline_strings, data, flags=re.DOTALL)

    return data

def process_schedule(events):
    """
    Process the schedule JSON data and save it to a CSV.
    :param events: List of event dictionaries from the JSON data.
    """
    # Extract relevant fields from each event
    schedule_data = []
    for event in events:
        schedule_data.append(
            {
                "ID": event.get("id"),
                "Title": event.get("title"),
                "Start": event.get("start"),
                "End": event.get("end"),
                "Commentaire": event.get("extendedProps", {}).get("commentaire", ""),
                "BackgroundColor": event.get("backgroundColor", ""),
            }
        )

    # Convert to a Pandas DataFrame
    df = pd.DataFrame(schedule_data)

    # Save to CSV
    df.to_csv("schedule/data/csv/schedule.csv", index=False)
    print("Schedule saved to 'schedule.csv'!")
    return df

def filter_schedule_by_date(events, date_str):
    """
    Filter the schedule for a specific date.
    :param events: List of event dictionaries from the JSON data.
    :param date_str: The target date in 'YYYY-MM-DD' format.
    :return: List of events for the specified date.
    """

    # Parse the target date
    target_date = datetime.strptime(date_str, "%Y-%m-%d").date()

    # Define possible date formats
    date_formats = ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"]

    # Filter events
    filtered_events = []
    for event in events:
        for fmt in date_formats:
            try:
                event_date = datetime.strptime(event["start"], fmt).date()
                if event_date == target_date:
                    filtered_events.append(event)
                break
            except ValueError:
                continue  # Try the next format

    return filtered_events

def generate_ics(events, filename):
    """
    Generate an ICS file from the given events.
    :param events: List of event dictionaries from the JSON data.
    :param filename: Name of the output ICS file.
    """
    cal = Calendar()

    for event in events:
        e = Event()
        e.name = event["title"]
        e.begin = event["start"]
        e.end = event["end"]
        e.description = event.get("extendedProps", {}).get("commentaire", "")
        e.location = "Unknown"  # Replace with real data if available
        cal.events.add(e)

    # Save the calendar to a file
    with open(filename, "w", encoding="utf-8") as f:
        f.writelines(cal)
    print(f"ICS file generated: {filename}")

def split_events_by_type(events):
    """
    Split events into courses and exams based on the background color.
    :param events: List of event dictionaries from the JSON data.
    :return: Two lists: courses and exams.
    """
    courses = []
    exams = []

    for event in events:
        if event["backgroundColor"] == "rgb(255, 0 ,0)":
            exams.append(event)
        else:
            courses.append(event)

    return courses, exams

if __name__ == "__main__":
    schedule = Schedule()
    page: str = schedule.login()
    data:str = schedule.get_schedule(page)
    data = format_data(data)

    # Step 7: Parse the JSON data
    try:
        data_json = json.loads(data)
        # Step 8: Pretty-print the JSON data with proper encoding
        #print(json.dumps(data_json, indent=4, ensure_ascii=False))
        with open("events_pretty.json", "w", encoding="utf-8") as file:
            json.dump(data_json, file, indent=4, ensure_ascii=False)
    except json.JSONDecodeError as e:
        print("JSON decode error:", e)
    
    if data_json:
        df = process_schedule(data_json)  # Process and save the schedule
        #print(df.head()) #print the first 5 rows of the DataFrame

        # Split events into courses and exams
        courses, exams = split_events_by_type(data_json)

        # Generate separate ICS files
        if courses:
            generate_ics(courses, filename="schedule/data/calendars/courses.ics")
        if exams:
            generate_ics(exams, filename="schedule/data/calendars/exams.ics")
    
    # if data_json:
    #     # Filter for November 29, 2024
    #     filtered_events = filter_schedule_by_date(data_json, "2024-11-29")
    #     print("Events on 29 November 2024:")
    #     for event in filtered_events:
    #         print(
    #             f"Title: {event['title']}, Start: {event['start']}, End: {event['end']}, Color: {event.get('backgroundColor', 'N/A')}"
    #         )
