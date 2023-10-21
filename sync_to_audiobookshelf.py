import os
import json
import textwrap
from collections import defaultdict
from tqdm import tqdm
import shutil
import logging
from pathlib import Path
from bs4 import BeautifulSoup
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
file_handler = logging.FileHandler('sync_to_audiobookshelf.log')
file_handler.setLevel(logging.DEBUG)
logger.addHandler(stream_handler)
logger.addHandler(file_handler)
logger.setLevel(logging.DEBUG)


FEED_XML_PATH = './feed.xml'
MOUNTPOINT = '/Users/gabe/mnt/audiobookshelf/papers'
DATA_DIR = "./data/mp3s/"
PDF_DIR = "./data/pdfs/"
OVERWRITE = False
OVERWRITE_METADATA = False

# Parse the XML file to find the associated mp3 files and metadata
with open(FEED_XML_PATH, 'r') as file:
    soup = BeautifulSoup(file, 'xml')
    logger.debug('Parsing XML file')
    items = list(soup.find_all('item'))

print(f'Found {len(items)} items in the XML file')
print(len(set([item.find('itunes:episode').text.strip() for item in items])))
if not set([item.find('itunes:episode').text.strip() for item in items]) == set([str(i) for i in range(1, len(items) + 1)]):
    print('WARNING: The episode numbers are not sequential')
    episode_map = defaultdict(list)
    for item in items:
        episode_map[item.find('itunes:episode').text.strip()].append(item)
    print(episode_map.keys())
    for episode, items in episode_map.items():
        if len(items) > 1:
            print(f'Episode {episode} has {len(items)} items')
            for item in items:
                print(item.find('title').text)
            print('')

# Directory where sshfs is mounted
def get_item_metadata(item):
    # Extract relevant information
    track_name = item.find('title').text
    track_file = item.find('guid').text  # The actual mp3 file name
    track_file = track_file.replace("https://g-simmons.github.io/g-simmons-papercast/data/mp3s/","").strip()
    title = item.find('title').text.strip()
    # print(title)
    metadata = {
        "title": title,
        "volumeNumber": item.find("itunes:episode").text.strip(),
        "description": item.find('itunes:summary').text if item.find('itunes:summary') else "",
        "track_file": track_file,
        "track_name": track_name,
        "pdf_name": track_name.replace(".mp3", ".pdf"),
    }
    return metadata

def copy_mp3(item_metadata):
    track_name = ''.join(e for e in item_metadata["track_name"] if e.isalnum() or e.isspace())
    pdf_name = track_name.replace(".mp3", ".pdf")
    new_directory_path = Path(MOUNTPOINT + "/" + item_metadata["track_file"][:30] + '/')

    new_directory_path.mkdir(parents=True, exist_ok=True)

    source_file_path = Path(DATA_DIR) / item_metadata["track_file"]

    if not source_file_path.exists():
        return item_metadata

    destination_file_path = new_directory_path / item_metadata["track_file"]
    if not destination_file_path.parent.exists():
        destination_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    existed = False
    if OVERWRITE or not destination_file_path.exists():
        existed = True
        shutil.copy2(source_file_path, destination_file_path)

    if not existed or OVERWRITE_METADATA:
        opf_template = """<?xml version="1.0"?>
        <package version="2.0" xmlns="http://www.idpf.org/2007/opf" unique-identifier="id-{id}">

        <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
            <dc:title>{title}</dc:title>
            <dc:language>en</dc:language>
            <dc:volumeNumber>{volume_number}</dc:volumeNumber>
            <dc:description>{description}</dc:description>
            <dc:series>All Papers</dc:series>
        </metadata>

        </package>"""

        json_template = {
            "tags": [],
            "chapters": [],
            "metadata": {
                "title": item_metadata['title'],
                "subtitle": None,
                "authors": [],
                "narrators": [],
                "series": [
                "All Papers"
                ],
                "genres": [],
                "publishedYear": None,
                "publishedDate": None,
                "publisher": None,
                "description": None,
                "isbn": None,
                "asin": None,
                "language": None,
                "explicit": False,
                "abridged":False 
            }
        }

        with open(new_directory_path / 'metadata.json', 'w') as metafile:
            metafile.write(json.dumps(json_template, indent=4))

        with open(new_directory_path / 'metadata.opf', 'w') as metafile:
            metafile.write(opf_template.format(id=item_metadata["track_file"], title=item_metadata['title'], volume_number=item_metadata['volumeNumber'].strip(), description=item_metadata['description']))
        


    return item_metadata


# import time

# def copy_mp3(x):
#     time.sleep(1.0)  # to visualize the progress
#     return x

if __name__ == '__main__':
    with tqdm(total=len(items)) as pbar:
        with ThreadPoolExecutor(10) as executor:
            futures = {executor.submit(copy_mp3, get_item_metadata(arg)): arg for arg in items}
            results = {}
            for future in concurrent.futures.as_completed(futures):
                arg = futures[future]
                results[arg] = future.result()
                pbar.update(1)
