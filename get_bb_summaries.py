import requests
from bs4 import BeautifulSoup
import openai
from datetime import datetime
from dotenv import load_dotenv
import os
import sys

# Load environment variables from the .env file
load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Function to extract titles and URLs
def get_bbtop_stories(num_stories):

    url = "https://news.bensbites.com/"
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
    
        posts = soup.find_all('h3')  
        bb_titles = []
        bb_urls = []
        
        for post in posts[:num_stories]:
            title = post.get_text(strip=True)
            link = post.find('a')['href']
            bb_titles.append(title)
            bb_urls.append(link)

        return bb_titles, bb_urls
    else:
        return None


def fetch_url_content(url):
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://google.com'
    })
    response = session.get(url)
    if response.status_code == 200:
        return response.text
    else:
        return None

# Function to summarize content using GPT-4 API
def summarize_content(title, content):
    # hackercast key
    openai.api_key = OPENAI_API_KEY
    prompt = "Summarize the following content in less than 140 words in a style suitable for a hackernews podcast"
    content = f"Title:{title}\n\nContent:{content}"
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",  # Replace with the specific model you want to use
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": content}
        ]
    )
    summary = response['choices'][0]['message']['content']
    # Calculate tokens and estimate cost
    tokens_used = response['usage']['total_tokens']
    cost_per_1M_tokens = 0.15
    estimated_cost = (tokens_used / 1000000) * cost_per_1M_tokens
    print(summary, estimated_cost)
    return summary, estimated_cost

# Main function to summarize a URL
def summarize_url(title, url):
    content = fetch_url_content(url)
    if content:
        summary, cost = summarize_content(title, content)
        return summary, cost
    else:
        return "Failed to fetch content from the URL."
    
def get_bb_summaries(num_stories):

    num_stories = int(sys.argv[1])
    tot_cost = 0
    bb_titles, bb_urls = get_bbtop_stories(num_stories)
    print(bb_titles, bb_urls)
    summaries = []

    for i in range(len(bb_urls)):
        url = bb_urls[i]
        title = bb_titles[i]
        summary, cost = summarize_url(title, url)
        summaries.append(summary)
        tot_cost += cost

    summary_file = f'bb_summaries_{datetime.now().strftime("%m%d%Y")}.txt'

    with open(summary_file, 'w') as f:
        for summary in summaries:
            f.write(summary + '\n')

    print(f"Summaries written to {summary_file}")       
    print(f"Total estimated cost: ${tot_cost:.2f}")

    os.system(f"ln -s {summary_file} bb_summaries_latest.txt")

    num_stories = int(num_stories)
    tot_cost = 0
    bb_titles, bb_urls = get_bbtop_stories(num_stories)
    print(bb_titles, bb_urls)
    summaries = []

    for i in range(len(bb_urls)):
        url = bb_urls[i]
        title = bb_titles[i]
        summary, cost = summarize_url(title, url)
        summaries.append(summary)
        tot_cost += cost

    summary_file = f'bb_summaries_{datetime.now().strftime("%m%d%Y")}.txt'

    with open(summary_file, 'w') as f:
        for summary in summaries:
            f.write(summary + '\n')

    print(f"Summaries written to {summary_file}")       
    print(f"Total estimated cost: ${tot_cost:.2f}")

    os.system(f"ln -s {summary_file} bb_summaries_latest.txt")
    return summary_file


