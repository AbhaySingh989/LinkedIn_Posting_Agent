import os
import sys
import subprocess
from zipfile import ZipFile

version = sys.argv[1]
package_name = "crawl4ai"

# Download the wheel file
result = subprocess.run([sys.executable, "-m", "pip", "download", f"{package_name}=={version}", "--no-deps", "-d", "."], capture_output=True, text=True)
if result.returncode != 0:
    print(f"Error downloading {package_name}=={version}:")
    print(result.stderr)
    sys.exit(1)

# Get the name of the downloaded wheel file
try:
    wheel_file_name = [f for f in os.listdir('.') if f.startswith(package_name) and f.endswith('.whl')][0]
except IndexError:
    print(f"Could not find downloaded wheel file for {package_name}=={version}")
    sys.exit(1)

# Open the wheel file and print the METADATA file
try:
    with ZipFile(wheel_file_name, 'r') as zip_ref:
        metadata = zip_ref.read(f"{package_name}-{version}.dist-info/METADATA")
        print(metadata.decode('utf-8'))
except FileNotFoundError:
    print(f"Could not find METADATA file in {wheel_file_name}")
    sys.exit(1)
finally:
    # Remove the downloaded wheel file
    os.remove(wheel_file_name)
