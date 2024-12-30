import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
import os
import re

def clean_filename(title):
    """Sanitizes a title to be a valid filename."""
    return re.sub(r'[\\/*?:"<>|]', "", title)

def get_transcripts_from_playlist(playlist_url, output_dir="transcripts"):
    """
    Downloads transcripts from a YouTube playlist.

    Args:
        playlist_url: The URL of the YouTube playlist.
        output_dir: The directory to save transcripts.
    """

    ydl_opts = {
        'extract_flat': 'in_playlist',
        'skip_download': True,  # We only want metadata
        'quiet': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(playlist_url, download=False)

        if 'entries' not in info_dict:
            print("Error: Could not retrieve playlist information.")
            return

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        for entry in info_dict['entries']:
            if entry is not None:
                video_id = entry.get('id')
                title = entry.get('title', video_id)
                filename = f"{clean_filename(title)}.txt"
                filepath = os.path.join(output_dir, filename)

                if os.path.exists(filepath):
                    print(f"Transcript for '{title}' already exists. Skipping.")
                    continue

                try:
                    transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
                    with open(filepath, 'w', encoding='utf-8') as f:
                        for line in transcript:
                            f.write(line['text'] + ' \n')
                    print(f"Downloaded transcript for '{title}'")

                except NoTranscriptFound:
                    print(f"No English transcript found for '{title}' (ID: {video_id})")
                except TranscriptsDisabled:
                    print(f"Transcripts are disabled for '{title}' (ID: {video_id})")
                except Exception as e:
                    print(f"An error occurred for '{title}' (ID: {video_id}): {e}")

def combine_transcripts(input_dir="transcripts", output_file="combined_transcript.txt", max_size_mb=50, max_words = 500000):
    """
    Combines transcripts into a single file (or multiple files), respecting size and word limits.

    Args:
        input_dir: Directory containing transcript files.
        output_file: Base name for the combined output file(s).
        max_size_mb: Maximum size of each output file in megabytes.
        max_words: Maximum words per file to respect NotebookLM limits
    """

    files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f)) and f.endswith('.txt')]
    files.sort()  # Sort for chronological order

    current_output = ""
    file_counter = 1
    current_size = 0
    current_word_count = 0

    for file in files:
        filepath = os.path.join(input_dir, file)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        content_word_count = len(content.split())
        content_size = len(content.encode('utf-8'))

        if current_size + content_size > max_size_mb * 1024 * 1024 or current_word_count + content_word_count > max_words:
            # Write to current file and start a new one
            write_combined_file(current_output, output_file, file_counter)
            file_counter += 1
            current_output = ""
            current_size = 0
            current_word_count = 0

        current_output += content + "\n\n"
        current_size += content_size
        current_word_count += content_word_count

    # Write any remaining content
    if current_output:
        write_combined_file(current_output, output_file, file_counter)

def write_combined_file(content, output_file, file_counter):
    """Helper function to write the combined transcript to a numbered file."""
    output_filename = f"{output_file.split('.')[0]}_{file_counter}.txt"
    with open(output_filename, 'w', encoding='utf-8') as outfile:
        outfile.write(content)
    print(f"Combined transcript (part {file_counter}) written to {output_filename}")

if __name__ == "__main__":
    playlist_url = "https://www.youtube.com/playlist?list=PLhbKLGXaooYpqzPE_muVV68f1Ctav3LAN"  # Replace with your playlist URL
    get_transcripts_from_playlist(playlist_url)
    combine_transcripts()