import os
from pathlib import Path

from dotenv import load_dotenv
import globmatch
import boto3
import logging

load_dotenv()

# Load environment variables
BACKUP_FOLDER = os.getenv("BACKUP_FOLDER", None)
ACCESS_KEY = os.getenv("ACCESS_KEY", None)
SECRET_ACCESS_KEY = os.getenv("SECRET_ACCESS_KEY", None)
BUCKET = os.getenv("FILE_KEY_PREFIX", None)
LOG_LEVEL = os.getenv("LOG_LEVEL", 30)
UPLOAD_ROOT_FOLDER = os.getenv("UPLOAD_ROOT_FOLDER", "")

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

log = logging.getLogger("aws-uploader")
log.setLevel(int(LOG_LEVEL))


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
    ignore_patterns = load_ignore()
    for file_path in BACKUP_FOLDER.glob("*/**/*"):
        if not file_path.is_file():
            continue
        upload_file_key = file_path.relative_to(BACKUP_FOLDER)

        # If we don't have any ignore patterns or our file key doesn't match the patterns upload the file
        if len(ignore_patterns) == 0 or not match(upload_file_key, ignore_patterns):
            log.info(f"Uploading: {upload_file_key}")
            _total_files_uploaded += 1
            client.upload_file(UPLOAD_ROOT_FOLDER + file_path.as_posix(), BUCKET, upload_file_key)
        else:
            log.info(f"Skipped: {upload_file_key}")
    log.info(f"Finished Uploading {_total_files_uploaded} files")


if __name__ == '__main__':
    main()
