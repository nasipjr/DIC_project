with open('templates/base.html', 'rb') as f:
    data = f.read()

# Find the translations block
# It starts around: const translations = {
# Let's find "const translations"
start_idx = data.find(b"const translations")
if start_idx == -1:
    start_idx = data.find(b"translations = {")

if start_idx != -1:
    # Let's find the closing brace of this dictionary. Since it has nested structure or just simple keys:
    # Let's write the block of 4000 bytes from start_idx to a file.
    block = data[start_idx:start_idx+15000]
    with open('scratch/translations_block.txt', 'w', encoding='utf-8') as f_out:
        f_out.write(block.decode('utf-8', errors='replace'))
    print("Wrote translations block to scratch/translations_block.txt")
else:
    print("Could not find translations block")
