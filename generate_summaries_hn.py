import sys
import requests
from bs4 import BeautifulSoup
import json
from openai import OpenAI
from datetime import datetime
from dotenv import load_dotenv
import os
import re
import time
from pathlib import Path
from openai import RateLimitError

# Load environment variables from the .env file
load_dotenv()

# OpenAI API key
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GITHUB_API_KEY = os.getenv('GITHUB_API_KEY')

def check_existing_files(date_str):
    """Check if files already exist to avoid regenerating content"""
    base_path = Path("output")
    files_to_check = [
        base_path / f"hn_jsonl_{date_str}.txt",
        base_path / f"hn_transcript_{date_str}.txt", 
        base_path / f"hn_td_{date_str}.txt"
    ]
    
    existing_files = [f for f in files_to_check if f.exists()]
    
    if existing_files:
        print(f"✅ Found existing files from {date_str}:")
        for f in existing_files:
            print(f"   - {f.name} ({f.stat().st_size} bytes)")
        return True
    return False


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
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        response.encoding = response.apparent_encoding  # Fix encoding issues
        issue = response.json()
        issue_text = issue[0]["body"]
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching GitHub data: {e}")
        return []
    except (KeyError, IndexError) as e:
        print(f"❌ Error parsing GitHub response: {e}")
        return []

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

    prompt = """You are creating an engaging podcast segment about a HackerNews story for a tech-savvy audience.

Write a natural, conversational summary that:
- Opens with what the story is about and why it matters
- Highlights what's interesting, unique, or noteworthy
- Keeps a conversational tone without being overly casual or forced
- Makes technical topics accessible while respecting listener intelligence
- Length: roughly 150-200 words

Guidelines:
- Write as if explaining the story to an interested colleague
- Be genuine - don't force enthusiasm or insert artificial interjections
- Focus on substance over style
- Avoid podcast clichés ("In this episode", "Today we're talking about")

IMPORTANT - Only skip inaccessible content:
- If the content is an error page, access denied, paywall, or lacks actual article content, return ONLY: "SKIP_THIS_STORY"
- Do NOT skip based on subjective quality - summarize all accessible stories"""
    content = f"Title:{title}\nURL:{url}\nContent:{content}"
    
    # Retry logic for rate limiting
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Replace with the specific model you want to use
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": content}
                ]
            )
            break
        except RateLimitError as e:
            if attempt == max_retries - 1:
                print(f"❌ OpenAI API quota exceeded after {max_retries} attempts")
                print("Please check your OpenAI account billing and usage at: https://platform.openai.com/usage")
                raise e
            else:
                wait_time = (attempt + 1) * 10  # Wait 10, 20, 30 seconds
                print(f"⏳ Rate limit hit, waiting {wait_time} seconds... (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
    
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
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes
        response.encoding = response.apparent_encoding  # Fix encoding issues
        soup = BeautifulSoup(response.text, 'html.parser')  # Use .text instead of .content
        paragraphs = soup.find_all('p')
        content = ' '.join([para.get_text() for para in paragraphs])
        
        # Clean up any problematic characters
        content = content.encode('utf-8', errors='replace').decode('utf-8')
        
        summary, cost = summarize_content(title, url, content)
        return summary, cost
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching content from {url}: {e}")
        # Return a basic summary if we can't fetch content
        basic_summary = {'Title': title, 'URL': url, 'Summary': f"Unable to fetch content for: {title}"}
        return basic_summary, 0.0
    except Exception as e:
        print(f"❌ Error processing content from {url}: {e}")
        basic_summary = {'Title': title, 'URL': url, 'Summary': f"Error processing content for: {title}"}
        return basic_summary, 0.0


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
        prompt = f"""You are Data, host of HackerPulse - a tech podcast covering top HackerNews stories.
Today's date is {today}.

Note: You are receiving summaries of accessible stories from today's top HackerNews articles. Some stories may have been skipped due to paywalls or access issues.

Based on the story summaries provided, generate:

1. **Introduction**: A clear, engaging opening (2-3 sentences). Set up what listeners will hear without over-selling it.

2. **Conclusion**: A natural closing (2-3 sentences) that wraps up the episode. You can reflect on themes or simply sign off.

3. **Title**: A specific, informative title highlighting the most notable story or theme. Avoid generic formats like "HackerNews Daily - [Date]".

4. **Description**: A clear 2-3 sentence description of what's covered and why it's worth listening to.

Tone: Informative and engaging, but authentic. Avoid performative enthusiasm or corporate podcast language.

Output as JSON with keys: 'Introduction', 'Conclusion', 'Title', 'Description'"""  
    elif interval == 'weekly':
        prompt = f"""You are Data, host of HackerPulse - a tech podcast covering top HackerNews stories.
This is the week of {today}.

Note: You are receiving summaries of accessible stories from this week's top HackerNews articles. Some stories may have been skipped due to paywalls or access issues.

Based on the story summaries provided, generate:

1. **Introduction**: A clear, engaging opening (2-3 sentences). Set up what listeners will hear without over-selling it.

2. **Conclusion**: A natural closing (2-3 sentences) that wraps up the episode. You can reflect on the week's themes or simply sign off.

3. **Title**: A specific, informative title highlighting the most notable story or theme from the week. Avoid generic formats like "HackerNews Weekly - [Date]".

4. **Description**: A clear 2-3 sentence description of what's covered and why it's worth listening to.

Tone: Informative and engaging, but authentic. Avoid performative enthusiasm or corporate podcast language.

Output as JSON with keys: 'Introduction', 'Conclusion', 'Title', 'Description'"""
    

    # Concatenate the dictionaries into a single string
    content = ""
    for summary in summaries:
        content += f"{summary['Summary']}\n\n"

    # Retry logic for rate limiting
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Replace with the specific model you want to use
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": content},
                    {"role": "user", "content": "Please format your entire response as a JSON object with keys 'Introduction, 'Conclusion', 'Title' and 'Description'."}
                ]
            )
            break
        except RateLimitError as e:
            if attempt == max_retries - 1:
                print(f"❌ OpenAI API quota exceeded after {max_retries} attempts")
                print("Please check your OpenAI account billing and usage at: https://platform.openai.com/usage")
                raise e
            else:
                wait_time = (attempt + 1) * 10  # Wait 10, 20, 30 seconds
                print(f"⏳ Rate limit hit, waiting {wait_time} seconds... (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)

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
    skipped_count = 0
    
    for story in stories:
        summary, cost = extract_summary(story['title'], story['url'])
        tot_cost += cost
        
        # Skip stories that are inaccessible or not engaging
        if summary['Summary'] == "SKIP_THIS_STORY":
            skipped_count += 1
            print(f"⏭️  Skipped: {story['title']}")
            continue
        
        # Skip stories with "Unable to fetch content" in the summary
        if "Unable to fetch content" in summary['Summary']:
            skipped_count += 1
            print(f"⏭️  Skipped (unable to fetch): {story['title']}")
            continue
            
        summaries.append(summary)

    print(f"\n📊 Processed {len(summaries)} stories, skipped {skipped_count} stories")
    
    # Only proceed if we have at least one valid summary
    if not summaries:
        print("❌ No valid stories to process. All stories were skipped.")
        return
    
    combined_text, title, description, cost = add_intro_and_conclusion(summaries, interval)
    tot_cost += cost

    transcript_file = f'output/hn_transcript_{datetime.now().strftime("%m%d%Y")}.txt'
    with open(transcript_file, 'w') as f:
        f.write(combined_text)
       
    summary_file = f'output/hn_jsonl_{datetime.now().strftime("%m%d%Y")}.txt'
    td_file = f'output/hn_td_{datetime.now().strftime("%m%d%Y")}.txt'
    with open(summary_file, 'w') as f:
        for summary in summaries:
            json_line = json.dumps(summary) + '\n'
            f.write(json_line)

    with open(td_file, 'w') as f:
        f.write(f"\n\nTitle: {title}\nDescription: {description}")
        print(f"\n\nTitle: {title}\nDescription: {description}")

    print(f"JSON summaries written to {summary_file}")       
    print(f"Transcript written to {transcript_file}")
    print(f"Title and Description written to {td_file}") 
    print(f"Total estimated cost: ${tot_cost:.4f}")


if __name__ == "__main__":
    """
    Main function to create summaries based on user input.
    Includes file existence check to avoid regenerating content.
    """
    
    if len(sys.argv) < 3:
        print("Usage: python generate_summaries_hn.py <interval> <num_stories>")
        print("Example: python generate_summaries_hn.py daily 10")
        sys.exit(1)
    
    interval = sys.argv[1]
    num_stories = int(sys.argv[2])
    
    # Check if files already exist for today
    date_str = datetime.now().strftime("%m%d%Y")
    
    if check_existing_files(date_str):
        print(f"📚 Summary files already exist for {date_str}")
        print("🚫 Skipping regeneration to save API tokens")
        print("💡 Delete files in output/ folder if you want to regenerate")
        sys.exit(0)
    
    print(f"📝 Generating new summaries for {date_str}...")
    create_summaries(interval, num_stories)
