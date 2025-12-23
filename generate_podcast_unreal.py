import time
import nltk
import os
import sys
from pathlib import Path
from nltk.tokenize import sent_tokenize
from unrealspeech import UnrealSpeechAPI, save
from pydub import AudioSegment
from dotenv import load_dotenv
from datetime import datetime
import shutil


nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)
# Load environment variables from the .env file
load_dotenv()

# OpenAI API key
UNREAL_API_KEY = os.getenv('UNREAL_API_KEY')

# Initialize UnrealSpeechAPI client
speech_api = UnrealSpeechAPI(UNREAL_API_KEY)

def read_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def chunk_text(text, max_chars=950):
    sentences = sent_tokenize(text)
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_chars:
            current_chunk += sentence + " "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + " "
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def process_chunks(chunks, temp_dir):
    audio_files = []
    
    for i, chunk in enumerate(chunks):
        try:
            audio_data = speech_api.stream(
                text=chunk,
                voice_id="Liv",  # or Zoe 
                bitrate="192k"
            )
            file_name = temp_dir / f"audio_chunk_{i+1}.mp3"
            save(audio_data, file_name)
            audio_files.append(file_name)
            print(f"Processed and saved chunk {i+1}: {chunk[:30]}...")
        except Exception as e:
            print(f"Error processing chunk {i+1}: {str(e)}")
        time.sleep(1)  # Respect rate limit
    return audio_files

def concatenate_audio_files(audio_files, output_file):
    combined = AudioSegment.empty()
    for file in audio_files:
        sound = AudioSegment.from_mp3(file)
        combined += sound
    combined.export(output_file, format="mp3")
    print(f"All audio files concatenated into {output_file}")

def copy_file_to_icloud(source_file):
    
    # Define the destination path in iCloud
    destination = '/Users/sanzgiri/Library/Mobile Documents/com~apple~CloudDocs/hackerpulse'
    # Copy the file
    try:
        shutil.copy2(source_file, destination)
        print(f"File copied successfully to {destination}")
    except FileNotFoundError:
        print("Source file or destination directory not found.")
    except PermissionError:
        print("Permission denied. Make sure you have the necessary permissions.")
    except shutil.SameFileError:
        print("Source and destination are the same file.")
    except Exception as e:
        print(f"An error occurred: {e}")

# Main execution
if __name__ == "__main__":
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate podcast from transcript.')
    parser.add_argument('input_file', nargs='?', help='Input transcript file')
    parser.add_argument('--force', action='store_true', help='Force regeneration even if files exist')
    
    args = parser.parse_args()
    
    # Get date string for file naming
    date_str = datetime.now().strftime("%m%d%Y")
    
    if args.input_file:
        input_file = args.input_file
    else:
        input_file = f'output/hn_transcript_{date_str}.txt'

    output_file = input_file.replace('.txt', '.mp3')
    td_file = f'output/hn_td_{date_str}.txt'
    
    # Check if MP3 already exists
    if Path(output_file).exists() and not args.force:
        print(f"✅ MP3 file already exists: {output_file}")
        print(f"📊 Size: {Path(output_file).stat().st_size / 1024:.0f} KB")
        print("🚫 Skipping regeneration to save API tokens")
        print("💡 Delete the MP3 file if you want to regenerate")
        print("💡 Or use --force to overwrite existing files")
        sys.exit(0)
    
    # Check if input file exists
    if not Path(input_file).exists():
        print(f"❌ Input file not found: {input_file}")
        print("💡 Run generate_summaries_hn.py first")
        sys.exit(1)
    
    print(f"🎵 Generating new MP3 from: {input_file}")

    # Create a temporary directory for audio chunks
    temp_dir = Path("temp_audio_chunks")
    temp_dir.mkdir(exist_ok=True)

    try:
        # Read and process the text
        text = read_file(input_file)
        chunks = chunk_text(text)
        print(f"📝 Processing {len(chunks)} text chunks...")
        
        audio_files = process_chunks(chunks, temp_dir)
        print(f"Generated {len(audio_files)} audio files.")

        # Concatenate all audio files
        concatenate_audio_files(audio_files, output_file)
        
        # Verify output file was created
        if Path(output_file).exists():
            size_mb = Path(output_file).stat().st_size / (1024 * 1024)
            print(f"✅ Podcast saved to {output_file}")
            print(f"📊 Final size: {size_mb:.1f} MB")
        else:
            print("❌ Failed to create MP3 file")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error generating podcast: {e}")
        sys.exit(1)
    finally:
        # Clean up temporary files
        try:
            for file in temp_dir.glob("*.mp3"):
                file.unlink()
            temp_dir.rmdir()
            print("🧹 Cleaned up temporary files")
        except Exception as e:
            print(f"⚠️ Warning: Could not clean up temp files: {e}")

    print(f"🎉 Podcast generation completed successfully!")
    # Commented out iCloud sync - can be enabled if needed
    # copy_file_to_icloud(output_file)
    # copy_file_to_icloud(input_file)
    # copy_file_to_icloud(td_file)
