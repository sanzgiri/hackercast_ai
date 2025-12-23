#!/usr/bin/env python3
"""
Podcast publishing script with AWS S3 hosting.
This version uploads MP3 files to S3 and updates the RSS feed accordingly.
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET
from xml.dom import minidom
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
GITHUB_TOKEN = os.getenv('GITHUB_API_KEY')
GITHUB_REPO = "sanzgiri/hackercast_ai"
BASE_PATH = Path("/Users/sanzgiri/hackercast_ai")
OUTPUT_DIR = BASE_PATH / "output"
RSS_FILENAME = "podcast.xml"

# AWS S3 Configuration
S3_BUCKET = "hackercast-ai-podcast"
S3_REGION = "us-east-1"
S3_BASE_URL = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com"

def upload_mp3_to_s3(mp3_path, s3_key):
    """Upload MP3 file to S3 with proper content-type."""
    print(f"Uploading {mp3_path} to S3...")
    
    try:
        s3_client = boto3.client('s3', region_name=S3_REGION)
        
        with open(mp3_path, 'rb') as file:
            s3_client.put_object(
                Bucket=S3_BUCKET,
                Key=s3_key,
                Body=file,
                ContentType='audio/mpeg',
                CacheControl='public, max-age=31536000'  # Cache for 1 year
            )
        
        mp3_url = f"{S3_BASE_URL}/{s3_key}"
        print(f"✓ Uploaded to: {mp3_url}")
        return mp3_url
        
    except ClientError as e:
        print(f"✗ Error uploading to S3: {e}")
        print(f"\nMake sure you've run: ./setup_s3.sh")
        sys.exit(1)
    except FileNotFoundError:
        print(f"✗ Error: MP3 file not found: {mp3_path}")
        sys.exit(1)

def upload_artwork_to_s3(artwork_path, s3_key="artwork/hackerpulse_cover.jpg"):
    """Upload podcast artwork to S3 with proper content-type."""
    if not Path(artwork_path).exists():
        print(f"⚠️ Artwork not found: {artwork_path}, skipping...")
        return None
    
    print(f"Uploading artwork {artwork_path} to S3...")
    
    try:
        s3_client = boto3.client('s3', region_name=S3_REGION)
        
        # Determine content type from file extension
        content_type = 'image/jpeg' if artwork_path.lower().endswith(('.jpg', '.jpeg')) else 'image/png'
        
        with open(artwork_path, 'rb') as file:
            s3_client.put_object(
                Bucket=S3_BUCKET,
                Key=s3_key,
                Body=file,
                ContentType=content_type,
                CacheControl='public, max-age=31536000'  # Cache for 1 year
            )
        
        artwork_url = f"{S3_BASE_URL}/{s3_key}"
        print(f"✓ Artwork uploaded to: {artwork_url}")
        return artwork_url
        
    except ClientError as e:
        print(f"✗ Error uploading artwork to S3: {e}")
        return None
    except Exception as e:
        print(f"✗ Unexpected error uploading artwork: {e}")
        return None

def update_rss_feed(mp3_url, mp3_size, date_str):
    """Update RSS feed with new episode or create if doesn't exist."""
    rss_path = OUTPUT_DIR / RSS_FILENAME
    
    if not rss_path.exists():
        print(f"✗ Error: RSS feed not found: {rss_path}")
        print("Make sure you've generated episodes first.")
        sys.exit(1)
    
    # Load episode metadata
    td_path = OUTPUT_DIR / f"hn_td_{date_str}.txt"
    if not td_path.exists():
        print(f"✗ Error: Episode metadata not found: {td_path}")
        sys.exit(1)
    
    with open(td_path, 'r') as f:
        lines = f.read().strip().split('\n')
        title = lines[0].replace('Title: ', '') if len(lines) > 0 else f"HackerCast Episode - {date_str}"
        description = lines[1].replace('Description: ', '') if len(lines) > 1 else "Daily tech news from Hacker News"
    
    # Register namespaces to preserve prefixes
    ET.register_namespace('itunes', 'http://www.itunes.com/dtds/podcast-1.0.dtd')
    ET.register_namespace('atom', 'http://www.w3.org/2005/Atom')
    ET.register_namespace('podcast', 'https://podcastindex.org/namespace/1.0')
    
    # Parse existing RSS
    tree = ET.parse(rss_path)
    root = tree.getroot()
    channel = root.find('channel')
    
    if channel is None:
        print("✗ Error: Invalid RSS feed structure")
        sys.exit(1)
    
    # Update lastBuildDate to trigger Apple Podcasts refresh
    from email.utils import formatdate
    build_date = channel.find('lastBuildDate')
    if build_date is None:
        build_date = ET.SubElement(channel, 'lastBuildDate')
    build_date.text = formatdate(timeval=None, localtime=False, usegmt=True)
    print(f"✓ Updated lastBuildDate to trigger podcast refresh")
    
    # Check if episode already exists
    episode_found = False
    guid_text = f"hackercast-{date_str}"
    
    for item in channel.findall('item'):
        guid = item.find('guid')
        if guid is not None and guid.text == guid_text:
            print(f"Updating existing episode for {date_str}...")
            
            # Update enclosure URL and size
            enclosure = item.find('enclosure')
            if enclosure is not None:
                enclosure.set('url', mp3_url)
                enclosure.set('length', str(mp3_size))
            
            # Update link
            link = item.find('link')
            if link is not None:
                link.text = mp3_url
                
            episode_found = True
            print(f"✓ Updated existing episode in RSS feed")
            break
    
    if not episode_found:
        # Create new episode
        print(f"Creating new episode for {date_str}...")
        
        # Create new item element
        item = ET.Element('item')
        
        # Episode details
        ET.SubElement(item, 'title').text = title
        ET.SubElement(item, 'description').text = description
        ET.SubElement(item, 'link').text = mp3_url
        ET.SubElement(item, 'author').text = "sanzgiri@gmail.com (HackerCast AI)"
        
        # iTunes namespace elements
        # Get the namespace from the root element
        ns = {'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd'}
        ET.register_namespace('itunes', 'http://www.itunes.com/dtds/podcast-1.0.dtd')
        
        itunes_author = ET.SubElement(item, '{http://www.itunes.com/dtds/podcast-1.0.dtd}author')
        itunes_author.text = "HackerCast AI"
        
        itunes_summary = ET.SubElement(item, '{http://www.itunes.com/dtds/podcast-1.0.dtd}summary')
        itunes_summary.text = description
        
        itunes_explicit = ET.SubElement(item, '{http://www.itunes.com/dtds/podcast-1.0.dtd}explicit')
        itunes_explicit.text = "false"
        
        # Format date for RSS (RFC 2822 format)
        episode_date = datetime.strptime(date_str, "%m%d%Y")
        rss_date = episode_date.strftime("%a, %d %b %Y %H:%M:%S +0000")
        ET.SubElement(item, 'pubDate').text = rss_date
        
        # GUID (unique identifier)
        guid = ET.SubElement(item, 'guid')
        guid.text = guid_text
        guid.set('isPermaLink', 'false')
        
        # Enclosure for MP3
        enclosure = ET.SubElement(item, 'enclosure')
        enclosure.set('url', mp3_url)
        enclosure.set('type', 'audio/mpeg')
        enclosure.set('length', str(mp3_size))
        
        # Insert at the beginning of items (after channel metadata)
        insert_position = 0
        for i, child in enumerate(channel):
            if child.tag == 'item':
                insert_position = i
                break
        
        if insert_position > 0:
            channel.insert(insert_position, item)
        else:
            # No items yet, append to end
            channel.append(item)
        
        print(f"✓ Created new episode in RSS feed")
    
    # Sort all episodes by date (newest first) to ensure correct order
    from email.utils import parsedate_to_datetime
    
    def get_episode_date(item):
        """Extract datetime from episode's pubDate."""
        pubdate_elem = item.find('pubDate')
        if pubdate_elem is not None:
            return parsedate_to_datetime(pubdate_elem.text)
        return datetime.min.replace(tzinfo=None)
    
    # Get all items and sort
    items = channel.findall('item')
    items_sorted = sorted(items, key=get_episode_date, reverse=True)
    
    # Remove all items from channel
    for item in items:
        channel.remove(item)
    
    # Re-insert in correct order
    insert_position = 0
    for i, child in enumerate(channel):
        if child.tag == 'lastBuildDate':
            insert_position = i + 1
            break
    
    for i, item in enumerate(items_sorted):
        channel.insert(insert_position + i, item)
    
    print(f"✓ Episodes sorted chronologically (newest first)")
    
    # Save updated RSS with proper formatting
    # First convert to string
    xml_str = ET.tostring(root, encoding='utf-8')
    
    # Pretty print with minidom
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent="  ", encoding='utf-8')
    
    # Remove extra blank lines that minidom adds
    lines = pretty_xml.decode('utf-8').split('\n')
    lines = [line for line in lines if line.strip()]
    pretty_xml = '\n'.join(lines) + '\n'
    
    # Write to file
    with open(rss_path, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)
    
    print(f"✓ Saved RSS feed: {rss_path}")
    return rss_path

def upload_rss_to_github(rss_path):
    """Upload RSS feed to GitHub."""
    try:
        from github import Github
        
        if not GITHUB_TOKEN:
            print("✗ Error: GITHUB_API_KEY not found in environment")
            print("Set it in .env file or environment variables")
            sys.exit(1)
        
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)
        
        with open(rss_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
            # Try to update existing file
            contents = repo.get_contents(RSS_FILENAME)
            repo.update_file(
                contents.path,
                f"Update podcast feed - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                content,
                contents.sha
            )
            print(f"✓ Updated RSS feed on GitHub")
        except:
            # Create new file if it doesn't exist
            repo.create_file(
                RSS_FILENAME,
                f"Create podcast feed - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                content
            )
            print(f"✓ Created RSS feed on GitHub")
            
    except ImportError:
        print("✗ Error: PyGithub not installed. Run: pip install PyGithub")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error uploading RSS to GitHub: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Publish podcast episode to S3')
    parser.add_argument('--date', required=True, help='Date in MMDDYYYY format')
    parser.add_argument('--upload-artwork', metavar='PATH', help='Upload artwork to S3 (optional)')
    args = parser.parse_args()
    
    date_str = args.date
    
    # Validate date format
    try:
        datetime.strptime(date_str, '%m%d%Y')
    except ValueError:
        print("✗ Error: Date must be in MMDDYYYY format")
        sys.exit(1)
    
    print("=" * 60)
    print("HackerCast AI - Publishing to AWS S3")
    print("=" * 60)
    print(f"Date: {date_str}")
    print()
    
    # Upload artwork if specified
    if args.upload_artwork:
        print("Uploading podcast artwork...")
        artwork_url = upload_artwork_to_s3(args.upload_artwork)
        if artwork_url:
            print(f"✓ Artwork available at: {artwork_url}")
            print("⚠️ Remember to update RSS feed manually with new artwork URL")
        print()
    
    # Check if MP3 exists
    mp3_filename = f"hn_transcript_{date_str}.mp3"
    mp3_path = OUTPUT_DIR / mp3_filename
    
    if not mp3_path.exists():
        print(f"✗ Error: MP3 file not found: {mp3_path}")
        print("Generate the podcast audio first.")
        sys.exit(1)
    
    # Get MP3 size
    mp3_size = mp3_path.stat().st_size
    print(f"MP3 file: {mp3_filename}")
    print(f"Size: {mp3_size:,} bytes ({mp3_size/1024/1024:.2f} MB)")
    print()
    
    # Upload to S3
    s3_key = f"episodes/{mp3_filename}"
    mp3_url = upload_mp3_to_s3(str(mp3_path), s3_key)
    print()
    
    # Update RSS feed
    rss_path = update_rss_feed(mp3_url, mp3_size, date_str)
    print()
    
    # Upload RSS to GitHub
    upload_rss_to_github(rss_path)
    print()
    
    print("=" * 60)
    print("✓ Publishing Complete!")
    print("=" * 60)
    print(f"Episode URL: {mp3_url}")
    print(f"RSS Feed: https://raw.githubusercontent.com/{GITHUB_REPO}/refs/heads/main/{RSS_FILENAME}")
    print()
    print("Test playback:")
    print(f"  curl -I {mp3_url} | grep content-type")
    print()

if __name__ == "__main__":
    main()
