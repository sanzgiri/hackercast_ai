import requests
import argparse
import os
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
from bs4 import BeautifulSoup

def get_top_stories(num_stories):
    """
    Fetch top stories from Hacker News using Algolia API
    """
    url = 'https://hn.algolia.com/api/v1/search'
    params = {
        'query': '',
        'tags': 'front_page',
        'numericFilters': 'points>100',
        'hitsPerPage': num_stories
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data['hits']

def extract_urls(stories):
    """
    Extract URLs from the stories
    """
    return [story['url'] for story in stories if 'url' in story]

def scrape_webpage(url):
    """
    Scrape the content of the webpage
    """
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text
        text = soup.get_text()
        
        # Break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
    except Exception as e:
        return f"Error scraping webpage: {str(e)}"

def get_summary(url):
    """
    Get a summary of the article using Anthropic's API
    """
    anthropic = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    
    content = scrape_webpage(url)
    
    prompt = f"{HUMAN_PROMPT} Please provide a brief summary of the following article content:\n\n{content[:4000]}{AI_PROMPT}"
    
    try:
        completion = anthropic.completions.create(
            model="claude-2",
            max_tokens_to_sample=300,
            prompt=prompt
        )
        return completion.completion.strip()
    except Exception as e:
        return f"Error summarizing article: {str(e)}"

def main():
    parser = argparse.ArgumentParser(description="Extract URLs of top N articles from Hacker News")
    parser.add_argument('num_articles', type=int, help="Number of top articles to fetch")
    args = parser.parse_args()

    stories = get_top_stories(args.num_articles)
    urls = extract_urls(stories)

    print(f"Top {args.num_articles} Hacker News articles:")
    for i, url in enumerate(urls, 1):
        summary = get_summary(url)
        print(f"{i}. {url}")
        print(f"   Summary: {summary}\n")

if __name__ == "__main__":
    main()
