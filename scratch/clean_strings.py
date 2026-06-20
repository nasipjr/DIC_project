import re

clean_strings = []
jinja_or_junk = re.compile(r'({%|}}|{%|%}|bi-|remaining-|^\d+$|^[\s\W]+$|else|format_price|date\')')

with open('scratch/extracted_strings.txt', 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        if jinja_or_junk.search(line):
            continue
        # Check if it has any alphabetical chars
        if not any(c.isalpha() for c in line):
            continue
        clean_strings.append(line)

with open('scratch/cleaned_ui_strings.txt', 'w', encoding='utf-8') as out:
    for s in clean_strings:
        out.write(s + '\n')

print(f"Cleaned UI strings: {len(clean_strings)}")
