from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time

# Initialize WebDriver
driver = webdriver.Chrome()  # Ensure you have the chromedriver that matches your Chrome version

# Navigate to the website
driver.get("https://banner.aus.edu/axp3b21h/owa/bwckctlg.p_disp_cat_term_date")

# Select the term
select_term = Select(driver.find_element(By.NAME, "cat_term_in"))
select_term.select_by_value("202510")  # Value for Fall 2024

# Submit term selection
driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()

# Wait for the next page to load
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "subj_id")))

# Select all subjects
select_subject = Select(driver.find_element(By.ID, "subj_id"))
for option in select_subject.options:
    select_subject.select_by_visible_text(option.text)


# Submit subjects selection
driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()

# Wait for the courses page to load
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "a")))

# Parse the page with BeautifulSoup
soup = BeautifulSoup(driver.page_source, 'html.parser')

# Extract and print all course links
with open('Courses.txt', "w", encoding="utf-8") as file:
    for a_tag in soup.find_all('a'):
        # Replace newline characters with a space and strip leading/trailing spaces
        course_text = a_tag.text.replace('\n', ' ').strip()
        # Check if the course_text contains more than one word
        if len(course_text.split()) > 1:
            file.write(course_text + '\n')

# Close the WebDriver
driver.quit()