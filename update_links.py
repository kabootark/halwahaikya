import requests
import re

# --- Configuration ---
# List of specific channels you want to keep from the filter source
TARGET_CHANNELS = [
    "Aaj Tak", "Zee News", "India Today", "&Prive HD", "Zee Business",
    "WION", "Zee Bharat", "Big Magic", "Zing", "Zee TV HD", "&TV HD",
    "Zee Café HD", "Zee Anmol Cinema 2", "Zee Anmol", "Zee Cinema HD",
    "&Pictures HD", "Zee Anmol Cinema", "Zee Bollywood", "&flix HD",
    "Zee Classic", "&xplorHD", "Zee Zest HD"
]

# The URL of the source that needs to be filtered
FILTER_URL = "https://raw.githubusercontent.com/alex8875/m3u/refs/heads/main/z5.m3u"

# A list of URLs to download the new links from. The script will process them in this order.
SOURCE_URLS = [
    "https://solii.saqlainhaider8198.workers.dev/",
    "https://raw.githubusercontent.com/doctor-8trange/zyphora/refs/heads/main/data/sony.m3u",
    FILTER_URL
]

# The name of the M3U8 file in your repository
M3U8_FILE = "final.m3u8"
# The markers to identify the section to be updated
START_MARKER = "##--!!--## START AUTO-UPDATE ##--!!--##"
END_MARKER = "##--!!--## END AUTO-UPDATE ##--!!--##"

# UPDATED: This function now keeps the entire block for a matched channel, including all lines.
def filter_specific_channels(content, channels_to_keep):
    """
    Parses M3U content and keeps the entire, unmodified element for each desired channel.
    An element includes the #EXTINF line and all subsequent lines until the next #EXTINF.
    """
    lines = content.split('\n')
    filtered_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if line.startswith("#EXTINF"):
            try:
                channel_name = line.split(',')[-1].strip()
                # Check if this is a channel we want to keep
                if any(target.lower() in channel_name.lower() for target in channels_to_keep):
                    # Match found! Now, copy all lines until the next #EXTINF.
                    block_end_index = len(lines)
                    for j in range(i + 1, len(lines)):
                        if lines[j].strip().startswith("#EXTINF"):
                            block_end_index = j
                            break
                    
                    # Add the entire block to our filtered list
                    channel_block = lines[i:block_end_index]
                    filtered_lines.extend(channel_block)
                    
                    # Jump the main index past this block to avoid re-checking
                    i = block_end_index
                    continue
            except IndexError:
                # Malformed #EXTINF line, skip it
                pass
        
        # Move to the next line if no match was found
        i += 1
            
    # Count how many channels were actually found and kept
    found_count = sum(1 for line in filtered_lines if line.strip().startswith("#EXTINF"))
    print(f"Filter complete. Found and kept {found_count} of the targeted channels.")
    return '\n'.join(filtered_lines)

def fetch_and_combine_content():
    """Fetches content from all source URLs, filters where necessary, and combines them."""
    combined_content_lines = []
    
    for index, url in enumerate(SOURCE_URLS):
        try:
            response = requests.get(url)
            response.raise_for_status()
            print(f"Successfully fetched content from {url}")
            content = response.text
            
            if url == FILTER_URL:
                print(f"Applying channel filter for {url}...")
                content = filter_specific_channels(content, TARGET_CHANNELS)
            
            lines = content.split('\n')
            
            if index == 0:
                combined_content_lines.extend(lines)
            else:
                for line in lines:
                    if not line.strip().startswith("#EXTM3U"):
                        combined_content_lines.append(line)
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching content from {url}: {e}")
            continue
            
    return '\n'.join(combined_content_lines)

def clean_links(content):
    """Removes the unwanted user-agent/other parts from the links."""
    lines = content.split('\n')
    cleaned_lines = []
    for line in lines:
        if line.strip().startswith("https://") and '|' in line:
            cleaned_lines.append(line.split('|')[0])
        else:
            cleaned_lines.append(line)
    print("Cleaned the combined links.")
    return '\n'.join(cleaned_lines)

def update_m3u8_file():
    """Updates the local M3U8 file with the new, combined, and cleaned content."""
    new_content = fetch_and_combine_content()
    if not new_content:
        print("Aborting update because no content could be fetched from any source.")
        return

    cleaned_new_content = clean_links(new_content)

    try:
        with open(M3U8_FILE, 'r', encoding='utf-8') as f:
            existing_content = f.read()
    except FileNotFoundError:
        print(f"Error: {M3U8_FILE} not found. Creating a new file.")
        existing_content = f"{START_MARKER}\n{END_MARKER}"

    pattern = re.compile(f"({re.escape(START_MARKER)})(.*?)({re.escape(END_MARKER)})", re.DOTALL)
    replacement_string = f"\\1\n{cleaned_new_content.strip()}\n\\3"
    updated_content, num_replacements = pattern.subn(replacement_string, existing_content)

    if num_replacements == 0:
        print(f"Error: Could not find the markers in {M3U8_FILE}.")
        print("Please make sure the start and end markers exist in your file.")
        return

    with open(M3U8_FILE, 'w', encoding='utf-8') as f:
        f.write(updated_content)

    print(f"Successfully updated {M3U8_FILE} with content from all sources.")

if __name__ == "__main__":
    update_m3u8_file()
