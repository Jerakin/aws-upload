import os
from pathlib import Path
import hashlib
import json

from dotenv import load_dotenv
import globmatch
import boto3
import logging

load_dotenv()

# Load environment variables
BACKUP_FOLDER = os.getenv("BACKUP_FOLDER", None)
ACCESS_KEY = os.getenv("ACCESS_KEY", None)
SECRET_ACCESS_KEY = os.getenv("SECRET_ACCESS_KEY", None)
BUCKET = os.getenv("BUCKET", None)
LOG_LEVEL = os.getenv("LOG_LEVEL", 30)
UPLOAD_ROOT_FOLDER = os.getenv("UPLOAD_ROOT_FOLDER", "")
USE_CACHE = os.getenv("USE_CACHE", False).lower() in ('true', '1')
BUF_SIZE = 65536


# Ensure proper environment
if not ACCESS_KEY or not SECRET_ACCESS_KEY:
    raise ValueError("Specify credentials")

if not BACKUP_FOLDER:
    raise ValueError("Specify folder to backup")
else:
    BACKUP_FOLDER = Path(BACKUP_FOLDER)

if not BUCKET:
    raise ValueError("Specify bucket name")

if UPLOAD_ROOT_FOLDER:
    if not UPLOAD_ROOT_FOLDER.endswith("/"):
        UPLOAD_ROOT_FOLDER += "/"

# Set up logging
log = logging.getLogger("aws-uploader")
log.setLevel(int(LOG_LEVEL))
logging.basicConfig(format='%(message)s')

log.info(f"Using cache: {USE_CACHE}")

# Set up the cache
# the cache is a simple json file with the key of
# the file name and the sha1 of the entire file as
# the value.
if USE_CACHE:
    index_file = Path().home() / ".awsuploadindex"
    index_data = {}

    if not index_file.exists():
        index_file.touch()
    else:
        with index_file.open() as f:
            index_data = json.load(f)


def get_sha1(path):
    sha1 = hashlib.sha1()

    with path.open('rb') as fp:
        while True:
            data = fp.read(BUF_SIZE)
            if not data:
                break
            sha1.update(data)
    return sha1.hexdigest()


def load_ignore():
    ignore_file = (Path(__file__).parent / ".ignore")
    patterns = []
    if not ignore_file.exists():
        return patterns

    with (Path(__file__).parent / ".ignore").open() as fp:
        for x in fp.readlines():
            if x.startswith("#"):
                continue
            patterns.append(x.strip())
    return patterns


def match(key, ignore_patterns):
    for pattern in ignore_patterns:
        if globmatch.glob_match(key, [pattern]):
            return True
    return False


def main():
    log.info("Starting Uploader")
    client = boto3.client('s3', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_ACCESS_KEY)

    _total_files_uploaded = 0
    _total_files_skipped = 0
    ignore_patterns = load_ignore()
    for file_path in BACKUP_FOLDER.glob("*/**/*"):
        if not file_path.is_file():
            continue
        upload_file_key = file_path.relative_to(BACKUP_FOLDER)

        # If we don't have any ignore patterns or our file key doesn't match the patterns upload the file
        if len(ignore_patterns) == 0 or not match(upload_file_key, ignore_patterns):
            if USE_CACHE:
                cache_key = upload_file_key.as_posix()
                file_sha1 = get_sha1(file_path)
                if cache_key in index_data:
                    if index_data[cache_key] == file_sha1:
                        log.debug(f"  Not changed: {upload_file_key}")
                        _total_files_skipped += 1
                        continue
                index_data[cache_key] = file_sha1

            log.debug(f"  Uploading: {upload_file_key}")
            _total_files_uploaded += 1
            client.upload_file(UPLOAD_ROOT_FOLDER + file_path.as_posix(), BUCKET, upload_file_key.as_posix())
        else:
            log.debug(f"  Skipped: {upload_file_key}")

    if USE_CACHE:
        with index_file.open("w") as fp:
            json.dump(index_data, fp, indent='  ')

    log.info(f"Finished Uploading")
    log.info(f"  Uploaded {_total_files_uploaded} files")
    log.info(f"  Skipped {_total_files_skipped} files")


if __name__ == '__main__':
    main()
