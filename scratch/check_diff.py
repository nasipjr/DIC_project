import subprocess
import re

try:
    diff_output = subprocess.check_output(["git", "diff", "templates/settings/settings.html"], text=True)
    for line in diff_output.splitlines():
        if line.startswith('-'):
            print(line)
except Exception as e:
    print("Error:", e)
