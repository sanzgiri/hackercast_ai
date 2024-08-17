import sys
import requests
from bs4 import BeautifulSoup
import json

def get_hn_top_stories(num_stories):
    response = requests.get('https://hacker-news.firebaseio.com/v0/topstories.json')
    top_stories = response.json()[:num_stories]
    stories = []

    for story_id in top_stories:
        story_url = f'https://hacker-news.firebaseio.com/v0/item/{story_id}.json'
        story_details = requests.get(story_url).json()
        stories.append(story_details)

    return stories

def get_bb_top_stories(num_stories):
    response = requests.get('https://www.bbc.com/news')
    soup = BeautifulSoup(response.content, 'html.parser')
    stories = []

    for item in soup.select('.gs-c-promo-heading__title')[:num_stories]:
        stories.append({'title': item.get_text(), 'url': item.find_parent('a')['href']})

    return stories

def get_ph_top_stories(num_stories):
    response = requests.get('https://api.producthunt.com/v1/posts')
    posts = response.json()['posts'][:num_stories]
    stories = [{'title': post['name'], 'url': post['discussion_url']} for post in posts]
    return stories

def get_gh_top_stories(num_stories):
    response = requests.get('https://api.github.com/search/repositories?q=stars:>1&sort=stars')
    repos = response.json()['items'][:num_stories]
    stories = [{'title': repo['name'], 'url': repo['html_url']} for repo in repos]
    return stories

def get_lb_top_stories(num_stories):
    response = requests.get('https://lobste.rs/hottest.json')
    posts = response.json()[:num_stories]
    stories = [{'title': post['title'], 'url': post['url']} for post in posts]
    return stories
def get_summary(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    paragraphs = soup.find_all('p')
    summary = ' '.join([para.get_text() for para in paragraphs[:5]])
    return summary

def generate_summaries(source, num_stories):
    if source == 'hn':
        stories = get_hn_top_stories(num_stories)
    elif source == 'bb':
        stories = get_bb_top_stories(num_stories)
    elif source == 'ph':
        stories = get_ph_top_stories(num_stories)
    elif source == 'gh':
        stories = get_gh_top_stories(num_stories)
    elif source == 'lb':
        stories = get_lb_top_stories(num_stories)
        raise ValueError("Unsupported source. Use 'hn' for Hacker News or 'bb' for BBC.")

    summaries = []
    for story in stories:
        summary = get_summary(story['url'])
        summaries.append(summary)

    with open(f'{source}_summaries_latest.txt', 'w') as f:
        for summary in summaries:
            f.write(summary + '\n')

if __name__ == "__main__":
    source = sys.argv[1]
    num_stories = int(sys.argv[2])
    generate_summaries(source, num_stories)
