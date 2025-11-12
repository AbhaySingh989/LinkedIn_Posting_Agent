import os
import sys
from zipfile import ZipFile

version = sys.argv[1]

# Download the wheel file
os.system(f"{sys.executable} -m pip download crawl4ai=={version} --no-deps -d .")

# Get the name of the downloaded wheel file
wheel_file_name = [f for f in os.listdir('.') if f.startswith('crawl4ai') and f.endswith('.whl')][0]

# Open the wheel file and print the METADATA file
with ZipFile(wheel_file_name, 'r') as zip_ref:
    metadata = zip_ref.read(f"crawl4ai-{version}.dist-info/METADATA")
    print(metadata.decode('utf-8'))

# Remove the downloaded wheel file
os.remove(wheel_file_name)
