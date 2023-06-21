import os
import subprocess
from collections import deque
from datetime import date, datetime

from mkdocs.plugins import BasePlugin


def iterate_file_history(file_path: str):
    command = ["git", "log", "--date=short", "--pretty=%ad", file_path]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    while True:
        line = process.stdout.readline()
        if not line:
            break
        yield datetime.strptime(line.decode("utf-8").strip(), "%Y-%m-%d").date()


def update_metadata_with_file_dates(file_path: str, metadata: dict):
    history_iterator = iterate_file_history(file_path)

    try:
        metadata["creation_date"] = next(history_iterator)
    except StopIteration:
        metadata["creation_date"] = datetime.utcnow().date()

    try:
        metadata["revision_date"] = deque(history_iterator, maxlen=1).pop()
        if metadata["revision_date"] == metadata["creation_date"]:
            metadata["revision_date"] = None
    except IndexError:
        metadata["revision_date"] = None

    return metadata


class MkdocsGitDatesPlugin(BasePlugin):
    def on_page_markdown(self, markdown, page, config, files):
        src_file_path = os.path.join(config.docs_dir, page.file.src_uri)
        update_metadata_with_file_dates(src_file_path, page.meta)
        return markdown
