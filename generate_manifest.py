import os
import json
import glob
import logging

logging.basicConfig(format='[%(asctime)s %(levelname)s] %(message)s',
                    datefmt='%m/%d/%Y %H:%M:%S', level=logging.INFO)

SOURCES = ['github-trending', 'github-stars', 'hacker-news', 'huggingface']


def generate_manifest(json_dir='./json', output_path='data/manifest.json'):
    manifest = {}

    for source in SOURCES:
        source_dir = os.path.join(json_dir, source)
        if not os.path.exists(source_dir):
            manifest[source] = []
            continue

        json_files = glob.glob(os.path.join(source_dir, '*.json'))
        dates = sorted([os.path.splitext(os.path.basename(f))[0]
                       for f in json_files], reverse=True)
        manifest[source] = dates
        logging.info(f"Found {len(dates)} dates for {source}")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    logging.info(f"Generated {output_path}")


if __name__ == "__main__":
    generate_manifest()
