import os

base_html_path = 'templates/base.html'

with open(base_html_path, 'rb') as f:
    data = f.read()

# Target corrupted byte sequence
target = b',\x84\xd8\xa3\xd8\xad\xd8\xaf",'
replacement = b','

if target in data:
    fixed_data = data.replace(target, replacement)
    try:
        # Verify decode succeeds
        fixed_data.decode('utf-8')
        # Write back to file
        with open(base_html_path, 'wb') as f_out:
            f_out.write(fixed_data)
        print("Success: templates/base.html has been successfully fixed and written!")
    except Exception as e:
        print("Error: Fix applied but decode still failed:", e)
else:
    print("Error: Target corrupted byte sequence not found in templates/base.html")
