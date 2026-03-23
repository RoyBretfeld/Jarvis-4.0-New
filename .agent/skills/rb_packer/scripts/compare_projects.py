import os
import zipfile
import tempfile
import shutil
import hashlib
from pathlib import Path

def get_file_hash(filepath):
    """Calculate MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        return None

def compare_directories(dir1, dir2):
    """Compare two directories recursively."""
    dc = filecmp.dircmp(dir1, dir2)
    # This is standard library filecmp, but might be too simple. Let's do a custom walk.
    pass

def scan_directory(directory):
    """Scan directory and return dict of relative_path -> (size, hash)."""
    file_map = {}
    directory = Path(directory)
    for root, _, files in os.walk(directory):
        for file in files:
            full_path = Path(root) / file
            rel_path = full_path.relative_to(directory).as_posix()
            
            # Skip .git and irrelevant files
            if ".git" in rel_path.split("/"):
                continue
                
            try:
                stat = full_path.stat()
                file_hash = get_file_hash(full_path)
                file_map[rel_path] = {
                    "size": stat.st_size,
                    "hash": file_hash,
                    "mtime": stat.st_mtime
                }
            except Exception as e:
                print(f"Error scanning {rel_path}: {e}")
    return file_map

def main():
    zip_path = r"E:\_____1111____Projekte-Programmierung\Antigravity\____1____Webseiten\Marek Szostak\_coachmarek-17-02-26.zip"
    target_dir = r"E:\_____1111____Projekte-Programmierung\Antigravity\____1____Webseiten\Marek Szostak\_coachmarek.de"
    
    print(f"Comparing:")
    print(f"  Local: {target_dir}")
    print(f"  Zip:   {zip_path}")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Extracting zip to {temp_dir}...")
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
        except Exception as e:
            print(f"Failed to extract zip: {e}")
            return

        # Handle case where zip contains a single top-level folder
        extracted_items = os.listdir(temp_dir)
        if len(extracted_items) == 1 and os.path.isdir(os.path.join(temp_dir, extracted_items[0])):
            compare_root = os.path.join(temp_dir, extracted_items[0])
            print(f"  (Detected nested folder in zip: {extracted_items[0]})")
        else:
            compare_root = temp_dir

        print("Scanning local directory...")
        local_files = scan_directory(target_dir)
        
        print(f"Scanning zip contents...")
        zip_files = scan_directory(compare_root)
        
        # Compare
        all_files = set(local_files.keys()) | set(zip_files.keys())
        
        added = []
        removed = []
        modified = []
        
        for f in all_files:
            in_local = f in local_files
            in_zip = f in zip_files
            
            if in_local and not in_zip:
                # Present in local, missing in zip -> Added locally (or removed in zip timeframe)
                # Goal: "was ist anders" -> interpret differences.
                # Usually user wants to know what changed in the ZIP relative to local, or vice versa.
                # "mit zip vergleichen" -> implies Local is reference, Zip is "other".
                # But usually "what is different in the zip compared to now".
                # I will report both.
                added.append(f) # In local only
            elif in_zip and not in_local:
                removed.append(f) # In zip only (so missing locally)
            else:
                # Both exist, check content
                if local_files[f]["hash"] != zip_files[f]["hash"]:
                    modified.append(f)
        
        print("\n--- COMPARISON REPORT ---")
        print(f"Total files in Local: {len(local_files)}")
        print(f"Total files in Zip:   {len(zip_files)}")
        
        if modified:
            print("\n[MODIFIED FILES] (Content changed):")
            for f in sorted(modified):
                print(f"  * {f}")
                
        if added:
            print("\n[LOCAL ONLY] (Present in local folder, missing in zip):")
            for f in sorted(added):
                print(f"  + {f}")
                
        if removed:
            print("\n[ZIP ONLY] (Present in zip, missing in local folder):")
            for f in sorted(removed):
                print(f"  - {f}")
                
        if not modified and not added and not removed:
            print("\nIdentical content!")

if __name__ == "__main__":
    main()
