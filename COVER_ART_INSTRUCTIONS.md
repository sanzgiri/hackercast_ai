# Cover Art Setup for HackerCast AI

## ✅ Cover Art Configured!

Your podcast is now configured to use `hackerpulse_img.jpg` as cover art.

### Current Setup:
- **File:** `hackerpulse_img.jpg` (in your project directory)
- **GitHub URL:** `https://raw.githubusercontent.com/sanzgiri/podcast-feed/main/hackerpulse_img.jpg`
- **Auto-upload:** The script will automatically upload this image to GitHub if it doesn't exist

### What Happens When You Run `publish_podcast.py`:

1. ✅ **Checks for cover art** in your GitHub repo
2. ✅ **Auto-uploads** `hackerpulse_img.jpg` if not found
3. ✅ **Uses the image** in RSS feed for all podcast platforms

### Cover Art Requirements Met:
- **Size:** Should be 1400x1400 pixels minimum (3000x3000 recommended)
- **Format:** JPEG (✅ your file is JPG)
- **File size:** Should be under 500KB
- **Location:** ✅ Automatically managed in GitHub

### No Manual Steps Required!
The publish script now handles everything automatically:
- Uploads cover art to GitHub if needed
- References it correctly in the RSS feed
- Makes it available to all podcast directories

Your podcast feed will now display the cover art in:
- Apple Podcasts
- Spotify
- Google Podcasts
- All other podcast platforms

Just run `python publish_podcast.py` and everything will be set up automatically! 🎨