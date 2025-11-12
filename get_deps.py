import os
import sys
from zipfile import ZipFile

# Download the wheel file
os.system(f"{sys.executable} -m pip download asyncpraw==7.8.1 --no-deps -d .")

# Get the name of the downloaded wheel file
wheel_file_name = [f for f in os.listdir('.') if f.startswith('asyncpraw') and f.endswith('.whl')][0]

# Open the wheel file and print the METADATA file
with ZipFile(wheel_file_name, 'r') as zip_ref:
    metadata = zip_ref.read("asyncpraw-7.8.1.dist-info/METADATA")
    print(metadata.decode('utf-8'))

# Remove the downloaded wheel file
os.remove(wheel_file_name)
