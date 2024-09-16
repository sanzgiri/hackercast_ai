import sys
import requests
from bs4 import BeautifulSoup
import json
import openai
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

# OpenAI API key
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

def fetch_hn_top_stories(num_stories: int, interval: str) -> list[dict]:
    """
    Fetch top stories from Hacker News based on the interval.

    Args:
        num_stories (int): Number of top stories to fetch.
        interval (str): Interval for fetching stories ('daily', 'weekly', 'monthly').

    Returns:
        list[dict]: List of top stories with their details.
    """
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
        story = {'title': story_details['title'], 'url': story_details['url']}
        stories.append(story)

    return stories

def fetch_bb_top_stories(num_stories: int, interval: str) -> list[dict]:
    """
    Fetch top stories from BBC based on the interval.

    Args:
        num_stories (int): Number of top stories to fetch.
        interval (str): Interval for fetching stories ('daily', 'weekly', 'monthly').

    Returns:
        list[dict]: List of top stories with their details.
    """
    if interval == 'daily':
        url = 'https://news.bensbites.com/'
    elif interval == 'weekly':
        url = 'https://news.bensbites.com/'
    elif interval == 'monthly':
        url = 'https://news.bensbites.com/'
    else:
        raise ValueError("Unsupported interval. Use 'daily', 'weekly', or 'monthly'.")
    
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    stories = []

    for item in soup.select('.gs-c-promo-heading__title')[:num_stories]:
        stories.append({'title': item.get_text(), 'url': item.find_parent('a')['href']})

    return stories

def fetch_ph_top_stories(num_stories: int, interval: str) -> list[dict]:
    """
    Fetch top stories from Product Hunt based on the interval.

    Args:
        num_stories (int): Number of top stories to fetch.
        interval (str): Interval for fetching stories ('daily', 'weekly', 'monthly').

    Returns:
        list[dict]: List of top stories with their details.
    """
    if interval == 'daily':
        url = 'https://api.producthunt.com/v1/posts'
    elif interval == 'weekly':
        url = 'https://api.producthunt.com/v1/posts?sort_by=weekly'
    elif interval == 'monthly':
        url = 'https://api.producthunt.com/v1/posts?sort_by=monthly'
    else:
        raise ValueError("Unsupported interval. Use 'daily', 'weekly', or 'monthly'.'")
    
    response = requests.get(url)
    posts = response.json()['posts'][:num_stories]
    stories = [{'title': post['name'], 'url': post['discussion_url']} for post in posts]
    return stories

def fetch_gh_top_stories(num_stories: int, interval: str) -> list[dict]:
    """
    Fetch top stories from GitHub based on the interval.

    Args:
        num_stories (int): Number of top stories to fetch.
        interval (str): Interval for fetching stories ('daily', 'weekly', 'monthly').

    Returns:
        list[dict]: List of top stories with their details.
    """
    if interval == 'daily':
        url = 'https://api.github.com/search/repositories?q=stars:>1&sort=stars'
    elif interval == 'weekly':
        url = 'https://api.github.com/search/repositories?q=stars:>1&sort=stars&order=desc&per_page=7'
    elif interval == 'monthly':
        url = 'https://api.github.com/search/repositories?q=stars:>1&sort=stars&order=desc&per_page=30'
    else:
        raise ValueError("Unsupported interval. Use 'daily', 'weekly', or 'monthly'.'")
    
    response = requests.get(url)
    repos = response.json()['items'][:num_stories]
    stories = [{'title': repo['name'], 'url': repo['html_url']} for repo in repos]
    return stories

def fetch_lb_top_stories(num_stories: int, interval: str) -> list[dict]:
    """
    Fetch top stories from Lobsters based on the interval.

    Args:
        num_stories (int): Number of top stories to fetch.
        interval (str): Interval for fetching stories ('daily', 'weekly', 'monthly').

    Returns:
        list[dict]: List of top stories with their details.
    """
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


def summarize_content(title: str, url: str, content: str) -> str:
    """
    Summarize the given content using an LLM.

    Args:
        content (str): The content to summarize.

    Returns:
        str: The summarized content.
    """

    openai.api_key = OPENAI_API_KEY
    prompt = "Summarize the following content in less than 140 words in a style suitable for a hackernews podcast."
    content = f"Title:{title}\nURL:{url}\nContent:{content}"
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
    summary = {'Title': title, 'URL': url, 'Summary': summary}
    print(summary, estimated_cost)
    return summary, estimated_cost

def extract_summary(title: str, url: str) -> str:
    """
    Extract summary from a given URL.

    Args:
        url (str): The URL to extract the summary from.

    Returns:
        str: The extracted summary.
    """
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    paragraphs = soup.find_all('p')
    content = ' '.join([para.get_text() for para in paragraphs])
    summary, cost = summarize_content(title, url, content)
    return summary, cost

def add_intro_and_conclusion(summaries: list[str]) -> str:
    """
    Add an introduction and conclusion to the list of summaries using an LLM.

    Args:
        summaries (list[str]): List of summaries.

    Returns:
        str: The combined text with introduction and conclusion.
    """
    openai.api_key = OPENAI_API_KEY
    prompt = "Create an introduction and conclusion for the following summaries in a style suitable for a podcast:\n\n"
    # Concatenate the dictionaries into a single string
    content = ""
    for summary in summaries:
        content += f"Title: {summary['Title']}\nURL: {summary['URL']}\nSummary: {summary['Summary']}\n\n"

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",  # Replace with the specific model you want to use
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": content}
        ]
    )
    combined_text = response['choices'][0]['message']['content']
    # Calculate tokens and estimate cost
    tokens_used = response['usage']['total_tokens']
    cost_per_1M_tokens = 0.15
    estimated_cost = (tokens_used / 1000000) * cost_per_1M_tokens
    print(combined_text)

    return combined_text, estimated_cost
    
    
def create_summaries(source: str, interval: str, num_stories: int) -> str:
    """
    Create summaries for a given source and interval.

    Args:
        source (str): The source to fetch stories from ('hn', 'bb', 'ph', 'gh', 'lb').
        interval (str): Interval for fetching stories ('daily', 'weekly', 'monthly').
        num_stories (int): Number of top stories to fetch.

    Returns:
        None
    """
    if source == 'hn':
        stories = fetch_hn_top_stories(num_stories, interval)
    elif source == 'bb':
        stories = fetch_bb_top_stories(num_stories, interval)
    elif source == 'ph':
        stories = fetch_ph_top_stories(num_stories, interval)
    elif source == 'gh':
        stories = fetch_gh_top_stories(num_stories, interval)
    elif source == 'lb':
        stories = fetch_lb_top_stories(num_stories, interval)
    else:
        raise ValueError("Unsupported source. Use 'hn' for Hacker News, 'bb' for BBC, 'ph' for Product Hunt, 'gh' for GitHub, or 'lb' for Lobsters.")

    #print(stories)
    summaries = []
    tot_cost = 0
    for story in stories:
        summary, cost = extract_summary(story['title'], story['url'])
        summaries.append(summary)
        tot_cost += cost

    combined_text, cost = add_intro_and_conclusion(summaries)
    tot_cost += cost

    summary_file = f'{source}_summaries_{datetime.now().strftime("%m%d%Y")}.txt'
    with open(summary_file, 'w') as f:
        f.write(combined_text)

    print(f"Summaries with introduction and conclusion written to {summary_file}")
    with open(summary_file, 'w') as f:
        for summary in summaries:
            f.write(summary + '\n')

    print(f"Summaries written to {summary_file}")        
    print(f"Total estimated cost: ${tot_cost:.2f}")

if __name__ == "__main__":
    """
    Main function to create summaries based on user input.

    Args:
        None

    Returns:
        None
    """
    source = sys.argv[1]
    interval = sys.argv[2]
    num_stories = int(sys.argv[3])
    create_summaries(source, interval, num_stories)
