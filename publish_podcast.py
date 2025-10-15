#!/usr/bin/env python3
"""
Podcast Publisher for HackerCast AI
Automates the process of:
1. Uploading daily podcast MP3 to Google Drive
2. Making it publicly shareable
3. Updating RSS feed with new episode
4. Publishing updated RSS feed to GitHub repository
"""

import os
import sys
import json
import base64
from datetime import datetime
from pathlib import Path
import shutil
import requests
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Load environment variables
load_dotenv()

# Google Drive API scopes
SCOPES = ['https://www.googleapis.com/auth/drive']

class PodcastPublisher:
    def __init__(self):
        self.service = None
        self.drive_folder_id = None
        self.base_path = Path("/Users/sanzgiri/hackercast_ai")
        self.gdrive_path = Path("/Users/sanzgiri/Google Drive/My Drive/hackercast_ai")
        self.github_token = os.getenv('GITHUB_API_KEY')
        self.github_repo = "sanzgiri/podcast-feed"
        self.rss_github_url = f"https://raw.githubusercontent.com/{self.github_repo}/main/rss"
        
    def authenticate_google_drive(self):
        """Authenticate with Google Drive API"""
        creds = None
        token_path = self.base_path / "token.json"
        credentials_path = self.base_path / "credentials.json"
        
        # Load existing token
        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not credentials_path.exists():
                    print("❌ credentials.json not found. Please download from Google Cloud Console.")
                    print("Visit: https://console.cloud.google.com/apis/credentials")
                    return False
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(credentials_path), SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('drive', 'v3', credentials=creds)
        return True
    
    def find_or_create_folder(self, folder_name="hackercast_ai"):
        """Find or create the podcast folder in Google Drive"""
        try:
            # Search for existing folder
            results = self.service.files().list(
                q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'",
                spaces='drive'
            ).execute()
            
            folders = results.get('files', [])
            if folders:
                self.drive_folder_id = folders[0]['id']
                print(f"✅ Found existing folder: {folder_name}")
                return True
            
            # Create new folder
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = self.service.files().create(body=folder_metadata).execute()
            self.drive_folder_id = folder.get('id')
            print(f"✅ Created new folder: {folder_name}")
            return True
            
        except Exception as e:
            print(f"❌ Error with Google Drive folder: {e}")
            return False
    
    def download_rss_from_github(self):
        """Download the current RSS file from GitHub repository"""
        try:
            # First, try to get the current RSS file from GitHub
            api_url = f"https://api.github.com/repos/{self.github_repo}/contents/rss"
            headers = {
                "Authorization": f"Bearer {self.github_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28"
            }
            
            response = requests.get(api_url, headers=headers)
            
            if response.status_code == 200:
                # File exists, download it
                file_data = response.json()
                content = base64.b64decode(file_data['content']).decode('utf-8')
                
                local_rss = self.base_path / "output" / "podcast.xml"
                local_rss.parent.mkdir(parents=True, exist_ok=True)
                
                with open(local_rss, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print("✅ Downloaded current RSS file from GitHub")
                return file_data['sha']  # Return SHA for updating
                
            elif response.status_code == 404:
                print("ℹ️ No existing RSS file found in GitHub repo (will create new one)")
                return None
            else:
                print(f"⚠️ Error accessing GitHub repo: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"⚠️ Could not download RSS from GitHub: {e}")
            print("ℹ️ Will use local RSS file if available")
            return None
    
    def upload_cover_art_to_github(self):
        """Upload cover art to GitHub repository if it doesn't exist"""
        try:
            cover_art_path = self.base_path / "hackerpulse_img.jpg"
            
            if not cover_art_path.exists():
                print("⚠️ hackerpulse_img.jpg not found in project directory")
                return False
            
            # Check if cover art already exists in GitHub
            api_url = f"https://api.github.com/repos/{self.github_repo}/contents/hackerpulse_img.jpg"
            headers = {
                "Authorization": f"Bearer {self.github_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28"
            }
            
            response = requests.get(api_url, headers=headers)
            
            if response.status_code == 200:
                print("✅ Cover art already exists in GitHub repo")
                return True
            elif response.status_code == 404:
                # Upload cover art
                with open(cover_art_path, 'rb') as f:
                    content = f.read()
                
                encoded_content = base64.b64encode(content).decode('utf-8')
                
                data = {
                    "message": "Add podcast cover art",
                    "content": encoded_content
                }
                
                upload_response = requests.put(api_url, headers=headers, json=data)
                
                if upload_response.status_code in [200, 201]:
                    print("✅ Cover art uploaded to GitHub successfully")
                    return True
                else:
                    print(f"❌ Error uploading cover art: {upload_response.status_code}")
                    return False
            else:
                print(f"⚠️ Error checking cover art: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error handling cover art: {e}")
            return False
    
    def upload_mp3_to_github(self, mp3_file_path, date_str):
        """Upload MP3 file to GitHub for podcast-compatible URLs"""
        try:
            from github import Github
            import base64
            
            # Check file size to warn about GitHub limits
            file_size_mb = mp3_file_path.stat().st_size / (1024 * 1024)
            print(f"📊 MP3 file size: {file_size_mb:.1f} MB")
            
            if file_size_mb > 25:
                print("⚠️  Large file detected! Consider using GitHub LFS or alternative hosting.")
                print("   GitHub standard files should be < 25MB for best performance")
            
            if not hasattr(self, 'github'):
                if not self.github_token:
                    print("❌ GitHub token not found")
                    return None
                # Use newer auth method to avoid deprecation warning
                from github import Auth
                auth = Auth.Token(self.github_token)
                self.github = Github(auth=auth)
            
            # Read MP3 file
            with open(mp3_file_path, 'rb') as f:
                mp3_content = f.read()
            
            # Encode for GitHub API
            encoded_content = base64.b64encode(mp3_content).decode('utf-8')
            
            # Create filename with .mp3 extension
            mp3_filename = f"episodes/hn_transcript_{date_str}.mp3"
            
            # Get repository
            repo = self.github.get_repo(self.github_repo)
            
            try:
                # Check if file already exists
                existing_file = repo.get_contents(mp3_filename)
                # Update existing file
                repo.update_file(
                    path=mp3_filename,
                    message=f"Update podcast episode - {date_str}",
                    content=encoded_content,
                    sha=existing_file.sha
                )
                print(f"✅ Updated MP3 file on GitHub: {mp3_filename}")
            except:
                # Create new file
                repo.create_file(
                    path=mp3_filename,
                    message=f"Add podcast episode - {date_str}",
                    content=encoded_content
                )
                print(f"✅ Created MP3 file on GitHub: {mp3_filename}")
            
            # Return the direct URL with .mp3 extension
            github_mp3_url = f"https://raw.githubusercontent.com/{self.github_repo}/main/{mp3_filename}"
            print(f"🎵 MP3 URL: {github_mp3_url}")
            
            return github_mp3_url
            
        except Exception as e:
            print(f"❌ Error uploading MP3 to GitHub: {e}")
            if "too large" in str(e).lower():
                print("💡 Suggestion: Use GitHub LFS, AWS S3, or dedicated podcast hosting")
            import traceback
            traceback.print_exc()
            return None
    
    def upload_rss_to_github(self, file_sha=None):
        """Upload RSS file to GitHub repository"""
        try:
            rss_file = self.base_path / "output" / "rss"  # Changed from podcast.xml to rss
            
            if not rss_file.exists():
                print("❌ RSS file not found")
                return False
            
            # Read RSS content
            with open(rss_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Encode content for GitHub API
            encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
            
            # Prepare API request
            api_url = f"https://api.github.com/repos/{self.github_repo}/contents/rss"  # Changed from podcast.xml to rss
            headers = {
                "Authorization": f"Bearer {self.github_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28"
            }
            
            data = {
                "message": f"Update podcast RSS feed - {datetime.now().strftime('%Y-%m-%d')}",
                "content": encoded_content
            }
            
            # Add SHA if updating existing file
            if file_sha:
                data["sha"] = file_sha
                print("🔄 Updating existing RSS file in GitHub")
            else:
                print("📤 Creating new RSS file in GitHub")
            
            response = requests.put(api_url, headers=headers, json=data)
            
            if response.status_code in [200, 201]:
                print("✅ RSS feed uploaded to GitHub successfully")
                print(f"🔗 RSS Feed URL: {self.rss_github_url}")
                return True
            else:
                print(f"❌ Error uploading to GitHub: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error uploading RSS to GitHub: {e}")
            return False
    
    def upload_or_update_file(self, file_path, file_name=None):
        """Upload new file to Google Drive with .mp3 extension in filename"""
        try:
            if not file_name:
                file_name = Path(file_path).name
                # Ensure .mp3 extension is explicit for podcast compatibility
                if file_path.suffix.lower() == '.mp3' and not file_name.endswith('.mp3'):
                    file_name = file_name + '.mp3'
            
            file_metadata = {
                'name': file_name,
                'parents': [self.drive_folder_id]
            }
            
            media = MediaFileUpload(file_path, resumable=True)
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            file_id = file.get('id')
            
            # Make file publicly shareable
            permission = {
                'type': 'anyone',
                'role': 'reader'
            }
            self.service.permissions().create(
                fileId=file_id,
                body=permission
            ).execute()
            
            # Get shareable link - create podcast-friendly URL
            public_url = f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"
            
            # For MP3 files, create a URL that includes .mp3 in the path for podcast compatibility
            if file_path.suffix.lower() == '.mp3':
                # Use a format that puts the filename directly in the URL path
                # This helps podcast platforms recognize it as an MP3
                base_name = Path(file_path).stem
                direct_link = f"https://drive.google.com/uc?export=download&id={file_id}&filename={base_name}.mp3"
                
                # Alternative approach: Create a GitHub-hosted redirect URL
                # This would be more reliable for podcast platforms
                github_redirect_url = f"https://raw.githubusercontent.com/sanzgiri/podcast-feed/main/redirects/{base_name}.mp3"
                
                # For now, use the Google Drive link but note we need a better solution
                print(f"⚠️  Note: For better podcast platform compatibility, consider hosting MP3 files elsewhere")
                print(f"📝 Suggested alternative: {github_redirect_url}")
            else:
                direct_link = f"https://drive.google.com/uc?export=download&id={file_id}"
            
            print(f"✅ Uploaded {file_name}")
            print(f"🔗 Public link: {public_url}")
            
            return {
                'file_id': file_id,
                'public_url': public_url,
                'direct_link': direct_link
            }
            
        except Exception as e:
            print(f"❌ Error uploading {file_path}: {e}")
            return None
    
    def get_episode_info(self, date_str):
        """Extract episode information from the text file"""
        info_file = self.base_path / "output" / f"hn_td_{date_str}.txt"
        
        if not info_file.exists():
            print(f"❌ Episode info file not found: {info_file}")
            return None
        
        try:
            with open(info_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            # Initialize default values
            episode_data = {
                'title': f"HackerCast Daily - {date_str}",
                'description': "Daily Hacker News summary",
                'introduction': "",
                'conclusion': ""
            }
            
            # Try to parse as JSON first
            try:
                json_data = json.loads(content)
                episode_data.update(json_data)
                return episode_data
            except json.JSONDecodeError:
                pass
            
            # Parse as plain text format
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('Title:'):
                    episode_data['title'] = line.replace('Title:', '').strip()
                elif line.startswith('Description:'):
                    episode_data['description'] = line.replace('Description:', '').strip()
                elif line.startswith('Introduction:'):
                    episode_data['introduction'] = line.replace('Introduction:', '').strip()
                elif line.startswith('Conclusion:'):
                    episode_data['conclusion'] = line.replace('Conclusion:', '').strip()
            
            return episode_data
            
        except Exception as e:
            print(f"❌ Error reading episode info: {e}")
            return {
                'title': f"HackerCast Daily - {date_str}",
                'description': "Daily Hacker News summary",
                'introduction': "",
                'conclusion': ""
            }
    
    def update_rss_feed(self, episode_info, mp3_url, date_str):
        """Update the RSS feed with new episode, removing any existing entry for the same date"""
        rss_file = self.base_path / "output" / "rss"  # Changed from podcast.xml to rss
        
        try:
            # Parse existing RSS or create new one
            if rss_file.exists():
                tree = ET.parse(rss_file)
                root = tree.getroot()
                channel = root.find('channel')
            else:
                # Create new RSS feed with proper namespaces (set attributes only)
                root = ET.Element('rss')
                root.set('version', '2.0')
                root.set('xmlns:itunes', 'http://www.itunes.com/dtds/podcast-1.0.dtd')
                root.set('xmlns:podcast', 'https://podcastindex.org/namespace/1.0')
                root.set('xmlns:atom', 'http://www.w3.org/2005/Atom')
                channel = ET.SubElement(root, 'channel')
                
                # Add required channel elements
                ET.SubElement(channel, 'title').text = "HackerCast AI - Daily Tech News"
                ET.SubElement(channel, 'description').text = "AI-generated daily summaries of top Hacker News stories, covering the latest in technology, startups, and innovation."
                ET.SubElement(channel, 'link').text = "https://github.com/sanzgiri/podcast-feed"
                ET.SubElement(channel, 'language').text = "en-us"
                
                # iTunes required elements (using prefix syntax)
                itunes_author = ET.SubElement(channel, 'itunes:author')
                itunes_author.text = "HackerCast AI"
                
                itunes_summary = ET.SubElement(channel, 'itunes:summary')
                itunes_summary.text = "Stay updated with the latest tech news through AI-generated summaries of trending Hacker News stories."
                
                itunes_owner = ET.SubElement(channel, 'itunes:owner')
                itunes_name = ET.SubElement(itunes_owner, 'itunes:name')
                itunes_name.text = "HackerCast AI"
                itunes_email = ET.SubElement(itunes_owner, 'itunes:email')
                itunes_email.text = "sanzgiri@gmail.com"
                
                # iTunes categories (required)
                itunes_category = ET.SubElement(channel, 'itunes:category')
                itunes_category.set('text', 'Technology')
                itunes_subcategory = ET.SubElement(itunes_category, 'itunes:category')
                itunes_subcategory.set('text', 'News')
                
                # iTunes explicit rating (required)
                itunes_explicit = ET.SubElement(channel, 'itunes:explicit')
                itunes_explicit.text = "false"
                
                # iTunes image (cover art) - using hackerpulse_img.jpg
                itunes_image = ET.SubElement(channel, 'itunes:image')
                itunes_image.set('href', 'https://raw.githubusercontent.com/sanzgiri/podcast-feed/main/hackerpulse_img.jpg')
                
                # Standard RSS image
                image = ET.SubElement(channel, 'image')
                ET.SubElement(image, 'url').text = "https://raw.githubusercontent.com/sanzgiri/podcast-feed/main/hackerpulse_img.jpg"
                ET.SubElement(image, 'title').text = "HackerCast AI"
                ET.SubElement(image, 'link').text = "https://github.com/sanzgiri/podcast-feed"
                
                # Atom self link (required) - updated to use rss filename
                atom_link = ET.SubElement(channel, 'atom:link')
                atom_link.set('href', self.rss_github_url)
                atom_link.set('rel', 'self')
                atom_link.set('type', 'application/rss+xml')
                
                # Podcast namespace elements (required for PSP-1 compliance)
                podcast_guid = ET.SubElement(channel, 'podcast:guid')
                podcast_guid.text = "hackercast-ai-daily-tech-news"
                
                podcast_medium = ET.SubElement(channel, 'podcast:medium')
                podcast_medium.text = "podcast"
                
                # Additional podcast metadata
                ET.SubElement(channel, 'copyright').text = f"© {datetime.now().year} HackerCast AI"
                ET.SubElement(channel, 'managingEditor').text = "sanzgiri@gmail.com (HackerCast AI)"
                ET.SubElement(channel, 'webMaster').text = "sanzgiri@gmail.com (HackerCast AI)"
                ET.SubElement(channel, 'lastBuildDate').text = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
                
                tree = ET.ElementTree(root)
            
            # Update lastBuildDate
            last_build = channel.find('lastBuildDate')
            if last_build is not None:
                last_build.text = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
            
            # Remove any existing episode for this date
            guid_to_remove = f"hackercast-{date_str}"
            items_to_remove = []
            
            for item in channel.findall('item'):
                guid_elem = item.find('guid')
                if guid_elem is not None and guid_elem.text == guid_to_remove:
                    items_to_remove.append(item)
            
            for item in items_to_remove:
                channel.remove(item)
                print(f"🔄 Removed existing episode for {date_str}")
            
            # Create new episode item
            item = ET.Element('item')
            
            # Episode details (all required)
            ET.SubElement(item, 'title').text = episode_info['title']
            ET.SubElement(item, 'description').text = episode_info['description']
            ET.SubElement(item, 'link').text = mp3_url
            ET.SubElement(item, 'author').text = "sanzgiri@gmail.com (HackerCast AI)"
            
            # iTunes episode elements (using prefix syntax)
            itunes_ep_author = ET.SubElement(item, 'itunes:author')
            itunes_ep_author.text = "HackerCast AI"
            
            itunes_ep_summary = ET.SubElement(item, 'itunes:summary')
            itunes_ep_summary.text = episode_info['description']
            
            itunes_ep_explicit = ET.SubElement(item, 'itunes:explicit')
            itunes_ep_explicit.text = "false"
            
            # Format date for RSS (RFC 2822 format)
            episode_date = datetime.strptime(date_str, "%m%d%Y")
            rss_date = episode_date.strftime("%a, %d %b %Y %H:%M:%S +0000")
            ET.SubElement(item, 'pubDate').text = rss_date
            
            # GUID (unique identifier)
            guid = ET.SubElement(item, 'guid')
            guid.text = guid_to_remove
            guid.set('isPermaLink', 'false')
            
            # Enclosure for MP3 (must be audio/mpeg for proper support)
            enclosure = ET.SubElement(item, 'enclosure')
            enclosure.set('url', mp3_url)
            enclosure.set('type', 'audio/mpeg')
            
            # Try to get actual file size
            try:
                mp3_file_path = self.base_path / "output" / f"hn_transcript_{date_str}.mp3"
                if mp3_file_path.exists():
                    file_size = mp3_file_path.stat().st_size
                    enclosure.set('length', str(file_size))
                else:
                    enclosure.set('length', '5000000')  # Default ~5MB
            except:
                enclosure.set('length', '5000000')  # Default ~5MB
            
            # Add to channel (insert at appropriate position)
            # Find position to insert (after channel metadata, before other items)
            insert_position = 0
            for i, child in enumerate(channel):
                if child.tag == 'item':
                    insert_position = i
                    break
            else:
                insert_position = len(channel)
            
            channel.insert(insert_position, item)
            
            # Write updated RSS with proper XML formatting
            # Register namespaces properly for output
            ET.register_namespace('', '')  # Default namespace
            ET.register_namespace('itunes', 'http://www.itunes.com/dtds/podcast-1.0.dtd')
            ET.register_namespace('podcast', 'https://podcastindex.org/namespace/1.0')
            ET.register_namespace('atom', 'http://www.w3.org/2005/Atom')
            
            # Add proper indentation for readability
            self._indent_xml(root)
            
            # Create properly formatted XML string
            xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
            rough_string = ET.tostring(root, encoding='unicode', xml_declaration=False)
            
            # Write the file
            with open(rss_file, 'w', encoding='utf-8') as f:
                f.write(xml_declaration + rough_string)
            
            print(f"✅ Updated RSS feed: {rss_file}")
            print("✅ Added all required iTunes/podcast elements")
            return True
            
        except Exception as e:
            print(f"❌ Error updating RSS feed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _indent_xml(self, elem, level=0):
        """Add proper indentation to XML elements for readability"""
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for child in elem:
                self._indent_xml(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i
    
    def publish_daily_episode(self, date_str=None):
        """Main function to publish daily episode"""
        if not date_str:
            date_str = datetime.now().strftime("%m%d%Y")
        
        print(f"🎙️ Publishing HackerCast episode for {date_str}")
        
        # Authenticate with Google Drive
        if not self.authenticate_google_drive():
            return False
        
        # Find or create folder
        if not self.find_or_create_folder():
            return False
        
        # Download current RSS file from GitHub to sync
        print("📡 Syncing RSS file from GitHub...")
        file_sha = self.download_rss_from_github()
        
        # Upload cover art if needed
        print("🎨 Checking/uploading cover art...")
        self.upload_cover_art_to_github()
        
        # Check if MP3 exists
        mp3_file = self.base_path / "output" / f"hn_transcript_{date_str}.mp3"
        if not mp3_file.exists():
            print(f"❌ MP3 file not found: {mp3_file}")
            return False
        
        # Copy MP3 to Google Drive folder locally first
        local_gdrive_mp3 = self.gdrive_path / f"hn_transcript_{date_str}.mp3"
        try:
            self.gdrive_path.mkdir(parents=True, exist_ok=True)
            shutil.copy2(mp3_file, local_gdrive_mp3)
            print(f"✅ Copied MP3 to local Google Drive folder")
        except Exception as e:
            print(f"⚠️ Could not copy to local Google Drive: {e}")
        
        # Upload MP3 - smart routing based on file size
        mp3_file_size_mb = mp3_file.stat().st_size / (1024 * 1024)
        print(f"📊 MP3 file size: {mp3_file_size_mb:.1f} MB")
        
        if mp3_file_size_mb < 25:  # GitHub can handle files < 25MB well
            print("🎵 Uploading MP3 to GitHub for podcast compatibility...")
            github_mp3_url = self.upload_mp3_to_github(mp3_file, date_str)
            if github_mp3_url:
                podcast_mp3_url = github_mp3_url
            else:
                print("🔄 GitHub upload failed, falling back to Google Drive...")
                mp3_result = self.upload_or_update_file(mp3_file)
                if mp3_result:
                    podcast_mp3_url = mp3_result['direct_link']
                    print("⚠️  Using Google Drive URL - may not be optimal for podcast platforms")
                else:
                    return False
        else:
            print("📁 Large file detected - using Google Drive hosting...")
            print("💡 Consider AWS S3 or dedicated podcast hosting for better performance")
            mp3_result = self.upload_or_update_file(mp3_file)
            if mp3_result:
                podcast_mp3_url = mp3_result['direct_link']
                print("⚠️  Using Google Drive URL - may not be optimal for podcast platforms")
            else:
                return False
        
        # Get episode information
        episode_info = self.get_episode_info(date_str)
        
        # Update RSS feed (this removes any existing entry for the same date)
        if not self.update_rss_feed(episode_info, podcast_mp3_url, date_str):
            return False
        
        # Copy RSS to Google Drive folder locally
        rss_file = self.base_path / "output" / "rss"  # Updated filename
        local_gdrive_rss = self.gdrive_path / "rss"  # Updated filename
        try:
            shutil.copy2(rss_file, local_gdrive_rss)
            print(f"✅ Copied RSS to local Google Drive folder")
        except Exception as e:
            print(f"⚠️ Could not copy RSS to local Google Drive: {e}")
        
        # Upload updated RSS feed to GitHub
        if not self.upload_rss_to_github(file_sha):
            return False
        
        # Output summary
        print(f"\n🎉 Episode published successfully!")
        print(f"📱 Episode: {episode_info['title']}")
        print(f"🎵 MP3 URL: {podcast_mp3_url}")
        print(f"📡 RSS Feed: {self.rss_github_url}")
        print(f"\n✅ RSS feed hosted on GitHub with proper .mp3 URLs!")
        print(f"🍎 Apple Podcasts compatible: {podcast_mp3_url.endswith('.mp3')}")
        print(f"🎯 Use this RSS URL for Spotify/Apple Podcasts: {self.rss_github_url}")
        
        # Storage analysis
        file_size_mb = mp3_file.stat().st_size / (1024 * 1024)
        annual_gb = file_size_mb * 365 / 1024
        print(f"\n💾 Storage Analysis:")
        print(f"   Episode size: {file_size_mb:.1f} MB")
        print(f"   Annual usage (daily): {annual_gb:.1f} GB")
        
        if annual_gb > 1:
            print(f"⚠️  Consider dedicated hosting:")
            print(f"   • AWS S3: ~${annual_gb * 0.023 * 12:.2f}/year")
            print(f"   • Cloudflare R2: ~${annual_gb * 0.015 * 12:.2f}/year") 
            print(f"   • GitHub LFS: $60/year (50GB)")
        else:
            print(f"✅ GitHub free tier sufficient for {1/annual_gb:.1f} years")
        
        return True

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Publish HackerCast AI podcast episode')
    parser.add_argument('--date', type=str, help='Date string in MMDDYYYY format (default: today)')
    parser.add_argument('date_positional', nargs='?', help='Date string as positional argument')
    
    args = parser.parse_args()
    
    # Handle both --date flag and positional argument for backward compatibility
    if args.date:
        date_str = args.date
    elif args.date_positional:
        date_str = args.date_positional  
    else:
        date_str = datetime.now().strftime("%m%d%Y")
        print(f"📅 Using today's date: {date_str}")
    
    print(f"🎙️ Publishing podcast for date: {date_str}")
    
    publisher = PodcastPublisher()
    success = publisher.publish_daily_episode(date_str)
    
    if success:
        print("\n✅ Podcast publishing completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Podcast publishing failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()