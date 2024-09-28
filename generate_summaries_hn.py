import sys
import requests
from bs4 import BeautifulSoup
import json
from openai import OpenAI
from datetime import datetime
from dotenv import load_dotenv
import os
import re

# Load environment variables from the .env file
load_dotenv()

# OpenAI API key
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GITHUB_API_KEY = os.getenv('GITHUB_API_KEY')


def fetch_hn_top_stories(num_stories: int, interval: str) -> list[dict]:
     
    owner = "headllines"
    if interval == 'daily':
        repo = "hackernews-daily"
    elif interval == 'weekly':
        repo = "hackernews-weekly"
    token = os.getenv('GITHUB_API_KEY')
    url = f"https://api.github.com/repos/{owner}/{repo}/issues?state=all&sort=created&direction=desc&per_page=1"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    response = requests.get(url, headers=headers)
    issue = response.json()
    issue_text = issue[0]["body"]

    pattern = r'(\d+)\.\s+\*\*\[(.+?)\]\((.+?)\)\*\*\n(\d+) points by .+? \| \[(\d+) comments\]\((.+?)\)'
    matches = re.finditer(pattern, issue_text, re.MULTILINE)
    
    issues = []
    for match in matches:
        issue = {
    #        "rank": int(match.group(1)),
            "title": match.group(2),
            "url": match.group(3),
    #        "points": int(match.group(4)),
    #        "number_of_comments": int(match.group(5)),
    #        "comments_link": match.group(6)       
        }
        issues.append(issue)
    
    return issues[:num_stories]


def summarize_content(title: str, url: str, content: str) -> str:
    """
    Summarize the given content using an LLM.

    Args:
        content (str): The content to summarize.

    Returns:
        str: The summarized content.
    """

    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = "Summarize the following content in less than 140 words in a style suitable for a hackernews podcast. Do not start with 'in this episode' or 'in todays episode'."
    content = f"Title:{title}\nURL:{url}\nContent:{content}"
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Replace with the specific model you want to use
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": content}
        ]
    )
    summary = response.choices[0].message.content
    # Calculate tokens and estimate cost
    tokens_used = response.usage.total_tokens
    cost_per_1M_tokens = 0.15
    estimated_cost = (tokens_used / 1000000) * cost_per_1M_tokens
    summary = {'Title': title, 'URL': url, 'Summary': summary}
    #print(summary, estimated_cost)
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


def add_intro_and_conclusion(summaries: list[str], interval: int) -> str:
    """
    Add an introduction and conclusion to the list of summaries using an LLM.

    Args:
        summaries (list[str]): List of summaries.

    Returns:
        str: The combined text with introduction and conclusion.
    """
    client = OpenAI(api_key=OPENAI_API_KEY)
    today = datetime.now().strftime("%B %d, %Y")
    cost_per_1M_tokens = 0.15

    if interval == 'daily':
        prompt = f""" The name of the podcast is Hackerpulse. The content is summaries of today's top stories from HackerNews.
                      Today's date is {today}. The name of the narrator is Data.
                      Generate the following based on the content:
                        1. A very brief introduction for the summaries in a style suitable for a podcast.
                        2. A very brief conclusion for the summaries in a style suitable for a podcast.
                        3. A Title for the HackerPulse podcast episode based on the summaries and the date.
                        4. A Description for the HackerPulse podcast episode based on the summaries and the date.
                      Output should be in a dictionary format with keys 'Introduction', 'Conclusion', 'Title', and 'Description'."""  
    elif interval == 'weekly':
        prompt = f""" The name of the podcast is Hackerpulse. The content is summaries of the past week's top stories from HackerNews.
                      Today is the week of {today}. The name of the narrator is Data.
                      Generate the following based on the content:
                        1. A very brief introduction for the summaries in a style suitable for a podcast.
                        2. A very brief conclusion for the summaries in a style suitable for a podcast.
                        3. A Title for the HackerPulse podcast episode based on the summaries and the date.
                        4. A Description for the HackerPulse podcast episode based on the summaries and the date.
                      Output should be in a dictionary format with keys 'Introduction', 'Conclusion', 'Title', and 'Description'."""
    

    # Concatenate the dictionaries into a single string
    content = ""
    for summary in summaries:
        content += f"{summary['Summary']}\n\n"

    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Replace with the specific model you want to use
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": content},
            {"role": "user", "content": "Please format your entire response as a JSON object with keys 'Introduction, 'Conclusion', 'Title' and 'Description'."}
        ]
    )

    # Calculate tokens and estimate cost
    tokens_used = response.usage.total_tokens
    estimated_cost = (tokens_used / 1000000) * cost_per_1M_tokens
    ictd_text = response.choices[0].message.content

    try:
        parsed_response = json.loads(ictd_text)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        #print(f"Response content: {ictd_text}")
        return None, None, None, 0  # or handle this error as appropriate
    
    intro_text = parsed_response.get('Introduction', '')
    conclu_text = parsed_response.get('Conclusion', '')
    title = parsed_response.get('Title', '')
    description = parsed_response.get('Description', '')
    combined_text = f"{intro_text}\n\n{content}\n\n{conclu_text}"

    #print(combined_text, title, description, estimated_cost)
    return combined_text, title, description, estimated_cost

    
def create_summaries(interval: str, num_stories: int) -> str:
    """
    Create summaries for a given source and interval.

    Args:
        interval (str): Interval for fetching stories ('daily', 'weekly', 'monthly').
        num_stories (int): Number of top stories to fetch.

    Returns:
        None
    """

    stories = fetch_hn_top_stories(num_stories, interval)
    summaries = []
    tot_cost = 0
    for story in stories:
        summary, cost = extract_summary(story['title'], story['url'])
        summaries.append(summary)
        tot_cost += cost

    combined_text, title, description, cost = add_intro_and_conclusion(summaries, interval)
    tot_cost += cost

    transcript_file = f'output/hn_transcript_{datetime.now().strftime("%m%d%Y")}.txt'
    with open(transcript_file, 'w') as f:
        f.write(combined_text)
       
    summary_file = f'output/hn_jsonl_{datetime.now().strftime("%m%d%Y")}.txt'
    with open(summary_file, 'w') as f:
        for summary in summaries:
            json_line = json.dumps(summary) + '\n'
            f.write(json_line)
        f.write(f"\n\nTitle: {title}\nDescription: {description}")
        print(f"\n\nTitle: {title}\nDescription: {description}")

    print(f"JSON summaries written to {summary_file}")        
    print(f"Total estimated cost: ${tot_cost:.4f}")


if __name__ == "__main__":
    """
    Main function to create summaries based on user input.

    Args:
        None

    Returns:
        None
    """

    interval = sys.argv[1]
    num_stories = int(sys.argv[2])
    create_summaries(interval, num_stories)
