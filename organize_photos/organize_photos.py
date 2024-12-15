import os
import sys
import shutil
import hashlib
from datetime import datetime
from pathlib import Path
from PIL import Image

def get_exif_date(file_path):
    """Extract the best date from EXIF metadata using Pillow."""
    try:
        img = Image.open(file_path)
        exif_data = img._getexif()
        if not exif_data:
            return None

        # Common EXIF date tag IDs
        date_tags = [36867, 36868, 306]  # DateTimeOriginal, DateTimeDigitized, DateTime

        for tag_id in date_tags:
            date_str = exif_data.get(tag_id)
            if date_str:
                return date_str
    except Exception as e:
        print(f"Error reading EXIF data from {file_path}: {e}")
    return None

def format_date(date_str):
    """Format date string into the desired format."""
    try:
        date = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
        return {
            "year": date.strftime("%Y"),
            "month": date.strftime("%m"),
            "formatted_date": date.strftime("%Y%m%d%H%M.%S"),
            "timestamp": date.strftime("%Y%m%d_%H%M%S")
        }
    except ValueError:
        return None

def generate_unique_filename(base_name, ext, dest_dir, source_file):
    """Generate a unique filename to avoid collisions."""
    counter = 1
    unique_name = f"{base_name}.{ext}"
    dest_path = dest_dir / unique_name

    while dest_path.exists():
        # Compare checksums
        if dest_path.is_file() and files_are_identical(dest_path, source_file):
            print(f"Duplicate file detected (identical): {source_file} -> {dest_path}. Skipping.")
            return None

        unique_name = f"{base_name}_{counter}.{ext}"
        dest_path = dest_dir / unique_name
        counter += 1

    return dest_path

def files_are_identical(file1, file2):
    """Compare file checksums to determine if they are identical."""
    return get_checksum(file1) == get_checksum(file2)

def get_checksum(file_path, chunk_size=8192):
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def process_file(file_path, dest_dir):
    """Process a single file: copy to destination with organized structure."""
    exif_date = get_exif_date(file_path)
    if not exif_date:
        print(f"No valid date found for: {file_path}")
        return

    date_info = format_date(exif_date)
    if not date_info:
        print(f"Invalid date format for: {file_path}")
        return

    # Organize destination directory structure
    year = date_info["year"]
    month = date_info["month"]
    timestamp = date_info["timestamp"]
    formatted_date = date_info["formatted_date"]

    dest_subdir = dest_dir / year / f"{year}-{month}"
    dest_subdir.mkdir(parents=True, exist_ok=True)

    # Update file creation and modification times
    os.utime(file_path, (datetime.now().timestamp(), datetime.strptime(formatted_date, "%Y%m%d%H%M.%S").timestamp()))

    # Generate a unique filename
    ext = file_path.suffix.lower().lstrip('.')
    base_name = timestamp
    dest_file = generate_unique_filename(base_name, ext, dest_subdir, file_path)
    if dest_file is None:
        return

    # Copy the file and remove the original if successful
    shutil.copy2(file_path, dest_file)
    print(f"Copied successfully: {file_path} -> {dest_file}")
    os.remove(file_path)
    print(f"Removed source file: {file_path}")

def traverse_directory(source_dir, dest_dir):
    """Traverse the source directory and process files."""
    print(f"Traversing directory: {source_dir}")
    for root, _, files in os.walk(source_dir):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                process_file(Path(root) / file, dest_dir)

def main():
    if len(sys.argv) < 3:
        print("Usage: python organize_photos.py <source_directory> <destination_directory>")
        sys.exit(1)

    source_dir = Path(sys.argv[1])
    dest_dir = Path(sys.argv[2])

    if not source_dir.is_dir():
        print(f"Invalid source directory: {source_dir}")
        sys.exit(1)

    print(f"Source Directory: {source_dir}")
    print(f"Destination Directory: {dest_dir}")
    confirm = input("Do you want to proceed? (Y/y to confirm): ").strip().lower()
    if confirm != 'y':
        print("Operation canceled.")
        sys.exit(0)

    traverse_directory(source_dir, dest_dir)

if __name__ == "__main__":
    main()

