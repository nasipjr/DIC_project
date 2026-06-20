import os
import re

exclude_dirs = ['.git', '.gemini', 'venv', 'myenv', '__pycache__', 'scratch', 'unused']
english_texts = set()

# Regex to find potential English words or phrases (sequences of alphabetical chars and spaces, at least one letter)
# Also need to ignore Jinja2 tags: {{...}} and {%...%}
jinja_tag_re = re.compile(r'({%.*?%}|{{.*?}})')

for root, dirs, files in os.walk('templates'):
    # prune excluded dirs
    dirs[:] = [d for d in dirs if d not in exclude_dirs]
    for file in files:
        if file.endswith('.html'):
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Remove style and script blocks
                    content = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', content, flags=re.IGNORECASE)
                    content = re.sub(r'<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>', '', content, flags=re.IGNORECASE)
                    
                    # Find all tag contents and attribute values like placeholder="..." and title="..."
                    # Let's find tags and text outside tags
                    # A simple way to get visible text is to strip HTML tags and extract remaining text
                    # but we also want placeholders and titles.
                    placeholders = re.findall(r'placeholder="([^"]+)"', content)
                    titles = re.findall(r'title="([^"]+)"', content)
                    for p in placeholders + titles:
                        p_clean = jinja_tag_re.sub('', p).strip()
                        if p_clean and any(c.isalpha() for c in p_clean):
                            english_texts.add(p_clean)
                    
                    # Strip tags to find text nodes
                    text_content = re.sub(r'<[^>]+>', '\n', content)
                    for line in text_content.split('\n'):
                        line_clean = jinja_tag_re.sub('', line).strip()
                        # Clean multiple spaces/punctuation
                        line_clean = re.sub(r'\s+', ' ', line_clean)
                        # Remove leading/trailing non-alpha except quotes/brackets if any
                        line_clean = line_clean.strip(' \t\n\r\f\v-:,.*•')
                        if line_clean and any(c.isalpha() for c in line_clean):
                            # Ensure it's not a Jinja statement or variable
                            if not (line_clean.startswith('{%') or line_clean.startswith('{{')):
                                english_texts.add(line_clean)
            except Exception as e:
                print(f"Error reading {path}: {e}")

# Save to a file sorted
with open('scratch/extracted_strings.txt', 'w', encoding='utf-8') as out:
    for text in sorted(english_texts):
        out.write(text + '\n')

print(f"Extracted {len(english_texts)} unique strings to scratch/extracted_strings.txt")
