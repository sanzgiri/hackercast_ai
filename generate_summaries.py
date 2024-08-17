import sys
import requests
from bs4 import BeautifulSoup
import json

def fetch_hn_top_stories(num_stories, interval):
    if interval == 'daily':
        url = 'https://hacker-news.firebaseio.com/v0/topstories.json'
    elif interval == 'weekly':
        url = 'https://hacker-news.firebaseio.com/v0/beststories.json'
    elif interval == 'monthly':
        url = 'https://hacker-news.firebaseio.com/v0/askstories.json'
    else:
        raise ValueError("Unsupported interval. Use 'daily', 'weekly', or 'monthly'.")
    
    response = requests.get(url)
    top_stories = response.json()[:num_stories]
    stories = []

    for story_id in top_stories:
        story_url = f'https://hacker-news.firebaseio.com/v0/item/{story_id}.json'
        story_details = requests.get(story_url).json()
        stories.append(story_details)

    return stories

def fetch_bb_top_stories(num_stories, interval):
    if interval == 'daily':
        url = 'https://www.bbc.com/news'
    elif interval == 'weekly':
        url = 'https://www.bbc.com/news/world'
    elif interval == 'monthly':
        url = 'https://www.bbc.com/news/business'
    else:
        raise ValueError("Unsupported interval. Use 'daily', 'weekly', or 'monthly'.")
    
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    stories = []

    for item in soup.select('.gs-c-promo-heading__title')[:num_stories]:
        stories.append({'title': item.get_text(), 'url': item.find_parent('a')['href']})

    return stories

def fetch_ph_top_stories(num_stories, interval):
    if interval == 'daily':
        url = 'https://api.producthunt.com/v1/posts'
    elif interval == 'weekly':
        url = 'https://api.producthunt.com/v1/posts?sort_by=weekly'
    elif interval == 'monthly':
        url = 'https://api.producthunt.com/v1/posts?sort_by=monthly'
    else:
        raise ValueError("Unsupported interval. Use 'daily', 'weekly', or 'monthly'.')
    
    response = requests.get(url)
    posts = response.json()['posts'][:num_stories]
    stories = [{'title': post['name'], 'url': post['discussion_url']} for post in posts]
    return stories

def fetch_gh_top_stories(num_stories, interval):
    if interval == 'daily':
        url = 'https://api.github.com/search/repositories?q=stars:>1&sort=stars'
    elif interval == 'weekly':
        url = 'https://api.github.com/search/repositories?q=stars:>1&sort=stars&order=desc&per_page=7'
    elif interval == 'monthly':
        url = 'https://api.github.com/search/repositories?q=stars:>1&sort=stars&order=desc&per_page=30'
    else:
        raise ValueError("Unsupported interval. Use 'daily', 'weekly', or 'monthly'.')
    
    response = requests.get(url)
    repos = response.json()['items'][:num_stories]
    stories = [{'title': repo['name'], 'url': repo['html_url']} for repo in repos]
    return stories

def fetch_lb_top_stories(num_stories, interval):
    if interval == 'daily':
        url = 'https://lobste.rs/hottest.json'
    elif interval == 'weekly':
        url = 'https://lobste.rs/recent.json'
    elif interval == 'monthly':
        url = 'https://lobste.rs/archived.json'
    else:
        raise ValueError("Unsupported interval. Use 'daily', 'weekly', or 'monthly'.")
    
    response = requests.get(url)
    posts = response.json()[:num_stories]
    stories = [{'title': post['title'], 'url': post['url']} for post in posts]
    return stories
def extract_summary(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    paragraphs = soup.find_all('p')
    summary = ' '.join([para.get_text() for para in paragraphs[:5]])
    return summary

def generate_summaries(source, num_stories):
    if source == 'hn':
        stories = get_hn_top_stories(num_stories, interval)
    elif source == 'bb':
        stories = get_bb_top_stories(num_stories, interval)
    elif source == 'ph':
        stories = get_ph_top_stories(num_stories, interval)
    elif source == 'gh':
        stories = get_gh_top_stories(num_stories, interval)
    elif source == 'lb':
        stories = get_lb_top_stories(num_stories, interval)
    else:
        raise ValueError("Unsupported source. Use 'hn' for Hacker News, 'bb' for BBC, 'ph' for Product Hunt, 'gh' for GitHub, or 'lb' for Lobsters.")

    summaries = []
    for story in stories:
        summary = extract_summary(story['url'])
        summaries.append(summary)

    with open(f'{source}_summaries_latest.txt', 'w') as f:
        for summary in summaries:
            f.write(summary + '\n')

if __name__ == "__main__":
    source = sys.argv[1]
    interval = sys.argv[2]
    num_stories = int(sys.argv[3])
    create_summaries(source, interval, num_stories)
