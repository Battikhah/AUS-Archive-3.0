import requests
from bs4 import BeautifulSoup

# Base URL of the website
base_url = "https://www.aus.edu/college/sba/faculty?page="

# Number of pages to scrape
num_pages = 7  # Change this to the actual number of pages

with open('Names/names SBA.txt', "w", encoding="utf-8") as file:
    # Loop over each page
    for page_num in range(num_pages):
        # Construct the URL for the current page
        url = base_url + str(page_num)

        # Send a GET request to the website
        response = requests.get(url)

        # Parse the HTML content of the page with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all the names on the page (assuming they are in 'p' tags with a class 'name')
        names = soup.find_all('h4')

        # Print all the names
        for name in names:
            file.write(name.text.strip() + '\n')
