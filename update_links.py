import requests
import re

# --- Configuration ---
# A list of URLs to download the new links from. The script will process them in this order.
SOURCE_URLS = [
    "https://solii.saqlainhaider8198.workers.dev/",
    "https://raw.githubusercontent.com/doctor-8trange/zyphora/refs/heads/main/data/sony.m3u"
]
# The name of the M3U8 file in your repository
M3U8_FILE = "final.m3u8"
# The markers to identify the section to be updated
START_MARKER = "##--!!--## START AUTO-UPDATE ##--!!--##"
END_MARKER = "##--!!--## END AUTO-UPDATE ##--!!--##"

def fetch_and_combine_content():
    """Fetches content from all source URLs and combines them intelligently."""
    combined_content_lines = []
    
    for index, url in enumerate(SOURCE_URLS):
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception for bad status codes
            print(f"Successfully fetched content from {url}")
            content = response.text
            lines = content.split('\n')
            
            # For the first file, we keep everything.
            # For subsequent files, we skip the #EXTM3U header to avoid duplicates.
            if index == 0:
                combined_content_lines.extend(lines)
            else:
                for line in lines:
                    if not line.strip().startswith("#EXTM3U"):
                        combined_content_lines.append(line)
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching content from {url}: {e}")
            # Continue to the next URL even if one fails
            continue
            
    return '\n'.join(combined_content_lines)

def clean_links(content):
    """Removes the unwanted user-agent/other parts from the links."""
    lines = content.split('\n')
    cleaned_lines = []
    for line in lines:
        # If a line is a URL and contains a '|', truncate it
        # This generic rule works for both sources
        if line.strip().startswith("https://") and '|' in line:
            cleaned_lines.append(line.split('|')[0])
        else:
            cleaned_lines.append(line)
    print("Cleaned the combined links.")
    return '\n'.join(cleaned_lines)

def update_m3u8_file():
    """Updates the local M3U8 file with the new, combined, and cleaned content."""
    # First, get the combined content from all sources
    new_content = fetch_and_combine_content()
    if not new_content:
        print("Aborting update because no content could be fetched from any source.")
        return

    # Clean the combined content
    cleaned_new_content = clean_links(new_content)

    # Read the existing M3U8 file
    try:
        with open(M3U8_FILE, 'r', encoding='utf-8') as f:
            existing_content = f.read()
    except FileNotFoundError:
        print(f"Error: {M3U8_FILE} not found. Creating a new file.")
        existing_content = f"{START_MARKER}\n{END_MARKER}"

    # Use regex to find the content between the markers
    pattern = re.compile(f"({re.escape(START_MARKER)})(.*?)({re.escape(END_MARKER)})", re.DOTALL)

    # Replace the content between the markers with the new cleaned content
    replacement_string = f"\\1\n{cleaned_new_content.strip()}\n\\3"
    updated_content, num_replacements = pattern.subn(replacement_string, existing_content)

    if num_replacements == 0:
        print(f"Error: Could not find the markers in {M3U8_FILE}.")
        print("Please make sure the start and end markers exist in your file.")
        return

    # Write the updated content back to the file
    with open(M3U8_FILE, 'w', encoding='utf-8') as f:
        f.write(updated_content)

    print(f"Successfully updated {M3U8_FILE} with content from all sources.")

if __name__ == "__main__":
    update_m3u8_file()
