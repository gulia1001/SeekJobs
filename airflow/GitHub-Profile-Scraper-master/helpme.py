import json
import re
from pathlib import Path


def save_json(filename, json_data):
    path = Path("{}.json".format(filename))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fp:
        json.dump(json_data, fp, indent=True, ensure_ascii=False)


def save_text(filename, text):
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def extract_data(data_needed, data_from_github):
    data = {}
    for key, value in data_from_github.items():
        if key in data_needed:
            data[key] = value
    return data


def group_with_same_key(items, key):
    grouped = []
    for item in items:
        if key in item:
            grouped.append(item[key])
    return grouped


def slugify(value):
    lowered = value.strip().lower()
    return re.sub(r"[^a-z0-9]+", "_", lowered).strip("_")
