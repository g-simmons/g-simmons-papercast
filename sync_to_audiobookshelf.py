import os
from tqdm import tqdm
import shutil
import logging
from pathlib import Path
from bs4 import BeautifulSoup

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

# Parse the XML file to find the associated mp3 files and metadata
with open(FEED_XML_PATH, 'r') as file:
    soup = BeautifulSoup(file, 'lxml')
    logger.debug('Parsing XML file')
    items = soup.find_all('item')

# Directory where sshfs is mounted

for item in tqdm(items):
    # Extract relevant information
    track_name = item.find('title').text
    track_file = item.find('guid').text  # The actual mp3 file name
    track_file = track_file.replace("https://g-simmons.github.io/g-simmons-papercast/data/mp3s/","").strip()
    metadata = {
        "title": item.find('title').text,
        "volumeNumber": item.find("itunes:episode").text,
    }

    # Define path based on metadata
    track_name = ''.join(e for e in track_name if e.isalnum() or e.isspace())
    pdf_name = track_name.replace(".mp3", ".pdf")
    new_directory_path = Path(MOUNTPOINT + "/" + track_file[:30] + '/')

    # Create the directory (if it doesn't exist)
    logger.debug(f'Creating directory {new_directory_path}')
    # new_directory_path.mkdir(parents=True, exist_ok=True)

    # # Define the paths for copying
    source_file_path = Path(DATA_DIR) / track_file

    if not source_file_path.exists():
        print(source_file_path)
        logger.warning(f'File {source_file_path} does not exist')
        continue


    destination_file_path = new_directory_path / track_file
    if not destination_file_path.parent.exists():
        logger.debug(f'Creating directory {destination_file_path.parent}')
        destination_file_path.parent.mkdir(parents=True, exist_ok=True)
    logger.debug(f'Copying {str(source_file_path)} to {str(destination_file_path)}')

    # # Copy mp3
    shutil.copy2(source_file_path, destination_file_path)

    # # Write the metadata
    # with open(new_directory_path / 'metadata.opf', 'w') as metafile:
    #     metafile.write(metadata)



