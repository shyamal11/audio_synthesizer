import requests
from bs4 import BeautifulSoup
from datetime import datetime

# Function to scrape The Verge's tech articles
def scrape_verge():
    url = 'https://www.theverge.com/tech'
    response = requests.get(url)

    if response.status_code != 200:
        print(f"Failed to retrieve data from {url}")
        return []

    # Parse the HTML content
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all articles
    articles = []
    for item in soup.find_all('a', {'class': 'group hover:text-white'}):  # Update selector as needed
        title = item.get('aria-label')
        link = item['href']
        
        # Check if the link is relative and make it absolute
        if not link.startswith('http'):
            link = 'https://www.theverge.com' + link  # Prepend base URL if relative

        # Get publication date by scraping the article page
        article_response = requests.get(link)
        if article_response.status_code == 200:
            article_soup = BeautifulSoup(article_response.text, 'html.parser')
            # Adjust the selector for the publication date as needed
            date_tag = article_soup.find('time')  # Example selector for date; adjust as necessary
            if date_tag:
                published_date = date_tag['datetime']  # This may need adjustment based on the HTML structure
                # Check if the published date is today
                if published_date.startswith(datetime.now().strftime('%Y-%m-%d')):
                    articles.append({'title': title, 'url': link, 'published_date': published_date})

    return articles

# Scrape the articles and print them
news_articles = scrape_verge()
for article in news_articles:
    print(f"Title: {article['title']}")
    print(f"URL: {article['url']}")
    print(f"Published Date: {article['published_date']}")
    print()  # For better readability
