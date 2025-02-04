# Submit subjects selection
driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()

# Wait for the courses page to load
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "a")))

# Parse the page with BeautifulSoup
soup = BeautifulSoup(driver.page_source, 'html.parser')

# Extract and print all course links
for a_tag in soup.find_all('a'):
    print(a_tag.text)

# Close the WebDriver
driver.quit()