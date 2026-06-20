import os
import re

arabic_regex = re.compile(r'[\u0600-\u06FF]')

exclude_dirs = ['.git', '.gemini', 'venv', 'myenv', '__pycache__', 'scratch']

for root, dirs, files in os.walk('.'):
    # prune excluded dirs
    dirs[:] = [d for d in dirs if d not in exclude_dirs]
    for file in files:
        if file.endswith(('.html', '.py', '.js', '.css')):
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    for line_no, line in enumerate(f, 1):
                        if arabic_regex.search(line):
                            print(f"{path}:{line_no}: {line.strip()}")
            except Exception as e:
                pass
