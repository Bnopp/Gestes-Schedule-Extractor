import requests
from bs4 import BeautifulSoup

# Step 0: Start a session to handle cookies and maintain the session state
session = requests.Session()

# Step 1: Get the login page to extract the CSRF token
login_page = session.get("https://www.gestes.info/gestes/connexion")
soup = BeautifulSoup(login_page.text, "html.parser")

# Extract the CSRF token from the login page
csrf_token = soup.find("input", {"name": "_csrfToken"})["value"]

print(f"CSRF Token: {csrf_token}")
