# The purpose of this file is to get the list of voices from the elevenlabs API
# and print the voice name and voice id

import requests
import json

from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')

url = "https://api.elevenlabs.io/v1/voices"
headers = {
"Accept": "application/json",
"xi-api-key": ELEVENLABS_API_KEY,
"Content-Type": "application/json"
}
response = requests.get(url, headers=headers)
data = response.json()

for voice in data['voices']:
    print(f"{voice['name']}; {voice['voice_id']}")


# Sarah; EXAVITQu4vr4xnSDxMaL
# Laura; FGY2WhTYpPnrIDTdsKH5
# Charlie; IKne3meq5aSn9XLyUdCD
# George; JBFqnCBsd6RMkjVDRZzb
# Callum; N2lVS1w4EtoT3dr4eOWO
# Liam; TX3LPaxmHKxFdv7VOQHJ
# Charlotte; XB0fDUnXU5powFXDhCwa
# Alice; Xb7hH8MSUJpSbSDYk0k2
# Matilda; XrExE9yKIg1WjnnlVkGX
# Will; bIHbv24MWmeRgasZH58o
# Jessica; cgSgspJ2msm6clMCkdW9
# Eric; cjVigY5qzO86Huf0OWal
# Chris; iP95p4xoKVk53GoZ742B
# Brian; nPczCjzI2devNBz1zQrb
# Daniel; onwK4e9ZLuTAKqWW03F9
# Lily; pFZP5JQG7iQjIQuC4Bku
# Bill; pqHfZKP75CvOlQylNhV4 
