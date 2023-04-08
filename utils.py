from pathlib import Path

import json
import os
import logging
from papercast.types import MP3

logging.basicConfig(level=logging.INFO)


def _get_mp3_size_length(mp3_path: str):
    statinfo = os.stat(mp3_path)
    size = str(statinfo.st_size)

    audio = MP3(mp3_path)
    length = str(audio.info.length)

    return size, length


def _get_episode_metadata_from_json(json_dir, base_url):

    base = Path(base_url)
    episode_meta = []
    for i, path in enumerate(os.listdir(json_dir)):
        logging.info("Processing {}".format(path))
        doc = json.load(open(Path(json_dir) / path))
        if "mp3_path" in doc:
            mp3_path = doc["mp3_path"]
        else:
            mp3_path = doc["outpath"].replace("pdf", "mp3")
            if not os.path.exists(mp3_path):
                logging.warn(
                    f"skipping {doc['title']}: no mp3_path in DB and mp3 file does not exist."
                )
                continue

        if "vttpath" in doc:
            vttpath = doc["vttpath"]
        else:
            vttpath = mp3_path + ".vtt"
            if not os.path.exists(vttpath):
                vttpath = None

        _, length = _get_mp3_size_length(mp3_path)

        try:
            description = doc["description"]
        except KeyError:
            description = ""
        xml_mp3_path = str(
            str(base) + "/data/mp3s/" + str(Path(mp3_path)).split("/")[-1]
        ).replace(
            "https:/", "https://"
        )  # TODO
        if vttpath:
            xml_vttpath = str(
                str(base) + "/data/vtt/" + str(Path(vttpath)).split("/")[-1]
            ).replace(
                "https:/", "https://"
            )  # TODO
        logging.info(str(xml_mp3_path))
        out_doc = {
            "title": doc["title"],
            "subtitle": "",
            "description": description,
            "mp3path": xml_mp3_path,
            "duration": str(length),
            "season": 1,  # TODO
            "episode": i,  # TODO
        }
        if vttpath:
            out_doc["vttpath"] = xml_vttpath
        episode_meta.append(out_doc)

    return episode_meta
