import time
import nltk
import os
import sys
import wave
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

# UnrealSpeech API key
UNREAL_API_KEY = os.getenv('UNREAL_API_KEY')
UNREAL_VOICE_ID = os.getenv('UNREAL_VOICE_ID', 'Liv')
DEFAULT_BACKEND = os.getenv('TTS_BACKEND', 'kokoro_tts').lower()

class UnrealSpeechPaymentError(RuntimeError):
    pass

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

def _is_payment_required_error(exc):
    status = getattr(getattr(exc, 'response', None), 'status_code', None)
    if status == 402:
        return True
    message = str(exc)
    return '402' in message and 'Payment Required' in message

def _write_wav(path, audio, sample_rate):
    """Write mono WAV from float samples in [-1.0, 1.0]."""
    try:
        import numpy as np  # Optional dependency; Kokoro typically brings it in.
        if hasattr(audio, 'detach'):
            audio = audio.detach().cpu().numpy()
        audio_np = np.asarray(audio, dtype=np.float32)
        if audio_np.size == 0:
            raise ValueError('Empty audio buffer')
        audio_np = np.clip(audio_np, -1.0, 1.0)
        audio_int16 = (audio_np * 32767.0).astype(np.int16)
        with wave.open(str(path), 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_int16.tobytes())
        return
    except Exception:
        pass

    # Fallback path without numpy
    if hasattr(audio, 'detach'):
        audio = audio.detach().cpu().numpy()
    if hasattr(audio, 'tolist'):
        audio = audio.tolist()
    if not audio:
        raise ValueError('Empty audio buffer')
    from array import array
    pcm = array('h')
    for sample in audio:
        if sample > 1.0:
            sample = 1.0
        elif sample < -1.0:
            sample = -1.0
        pcm.append(int(sample * 32767.0))
    with wave.open(str(path), 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm.tobytes())

def process_chunks_unreal(chunks, temp_dir):
    audio_files = []
    if not UNREAL_API_KEY:
        raise RuntimeError('UNREAL_API_KEY is not set')
    speech_api = UnrealSpeechAPI(UNREAL_API_KEY)
    
    for i, chunk in enumerate(chunks):
        try:
            audio_data = speech_api.stream(
                text=chunk,
                voice_id=UNREAL_VOICE_ID,  # or Zoe
                bitrate="192k"
            )
            file_name = temp_dir / f"audio_chunk_{i+1}.mp3"
            save(audio_data, file_name)
            audio_files.append(file_name)
            print(f"Processed and saved chunk {i+1}: {chunk[:30]}...")
        except Exception as e:
            if _is_payment_required_error(e):
                raise UnrealSpeechPaymentError(
                    'UnrealSpeech returned 402 Payment Required. Check plan/quota.'
                ) from e
            print(f"Error processing chunk {i+1}: {str(e)}")
        time.sleep(1)  # Respect rate limit
    return audio_files

def _load_kokoro_backend():
    try:
        from kokoro import KPipeline  # type: ignore
        return 'pipeline', KPipeline
    except Exception:
        pass
    try:
        from kokoro import KModel  # type: ignore
        return 'model', KModel
    except Exception as exc:
        raise ImportError(
            'Kokoro is not installed. Install it before using --backend kokoro.'
        ) from exc

def process_chunks_kokoro(chunks, temp_dir, voice, speed, lang_code):
    backend_type, backend_cls = _load_kokoro_backend()
    audio_files = []

    if backend_type == 'pipeline':
        try:
            pipeline = backend_cls(lang_code=lang_code)
        except TypeError:
            pipeline = backend_cls()
        sample_rate = getattr(pipeline, 'sample_rate', getattr(pipeline, 'sr', 24000))
        for i, chunk in enumerate(chunks, start=1):
            try:
                generator = pipeline(chunk, voice=voice, speed=speed, split_pattern=r'\n+')
            except TypeError:
                try:
                    generator = pipeline(chunk, voice=voice, speed=speed)
                except TypeError:
                    generator = pipeline(chunk)
            for j, (_, _, audio) in enumerate(generator, start=1):
                file_name = temp_dir / f"audio_chunk_{i}_{j}.wav"
                _write_wav(file_name, audio, sample_rate)
                audio_files.append(file_name)
                print(f"Processed and saved chunk {i}.{j}: {chunk[:30]}...")
    else:
        model = backend_cls()
        sample_rate = getattr(model, 'sample_rate', getattr(model, 'sr', 24000))
        for i, chunk in enumerate(chunks, start=1):
            try:
                audio = model.generate(chunk, voice=voice)
            except TypeError:
                audio = model.generate(chunk)
            file_name = temp_dir / f"audio_chunk_{i}.wav"
            _write_wav(file_name, audio, sample_rate)
            audio_files.append(file_name)
            print(f"Processed and saved chunk {i}: {chunk[:30]}...")

    return audio_files

def concatenate_audio_files(audio_files, output_file):
    combined = AudioSegment.empty()
    for file in audio_files:
        sound = AudioSegment.from_file(file)
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
    parser.add_argument(
        '--backend',
        choices=['unreal', 'kokoro', 'kokoro_tts'],
        default=DEFAULT_BACKEND,
        help='TTS backend (default: env TTS_BACKEND or kokoro_tts)'
    )
    parser.add_argument(
        '--kokoro-voice',
        default=os.getenv('KOKORO_VOICE', 'af_kore'),
        help='Kokoro voice id (default: env KOKORO_VOICE or af_kore)'
    )
    parser.add_argument(
        '--kokoro-lang',
        default=os.getenv('KOKORO_LANG', 'a'),
        help='Kokoro language code (default: env KOKORO_LANG or a)'
    )
    parser.add_argument(
        '--kokoro-speed',
        type=float,
        default=float(os.getenv('KOKORO_SPEED', '1.0')),
        help='Kokoro speed (default: env KOKORO_SPEED or 1.0)'
    )
    
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
        
        backend = args.backend.lower()
        if backend == 'unreal':
            audio_files = process_chunks_unreal(chunks, temp_dir)
        elif backend in ('kokoro', 'kokoro_tts'):
            audio_files = process_chunks_kokoro(
                chunks,
                temp_dir,
                voice=args.kokoro_voice,
                speed=args.kokoro_speed,
                lang_code=args.kokoro_lang
            )
        else:
            raise RuntimeError(f"Unsupported TTS backend: {backend}")

        if not audio_files:
            raise RuntimeError('No audio chunks generated; aborting.')
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
            
    except UnrealSpeechPaymentError as e:
        print(f"Error generating podcast: {e}")
        sys.exit(1)
    except ImportError as e:
        print(f"Error generating podcast: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error generating podcast: {e}")
        sys.exit(1)
    finally:
        # Clean up temporary files
        try:
            if temp_dir.exists():
                for file in temp_dir.iterdir():
                    if file.is_file():
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
