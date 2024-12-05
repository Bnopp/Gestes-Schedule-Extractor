# Gestes-Schedule-Extractor

This project was made to extract schedule/calendar data from the GEST-ES student platform and make it available in an iCal format to allow students to sync their personal calendar with the platform

## How to use
1. Execute `python -m schedule.schedule` to generate the classes and exams `.ics` files under `schedule/data/calendars`

2. Execute `python -m schedule.server` to start the api providing the `iCal` files for synchronization

## Functions
- The server updates the `.ics` files every 15 minutes by executing the schedule extraction.
- To make the api endpoints available for public use, you can use a tool like `ngrok` to map local ports to a public domain ip adress.
