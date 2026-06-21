with open('templates/base.html', 'rb') as f:
    data = f.read()

text = data.decode('utf-8', errors='replace')
lines = text.splitlines()

# Write lines 750 to 900
with open('scratch/base_lines_750_900.txt', 'w', encoding='utf-8') as f_out:
    for idx in range(745, min(920, len(lines))):
        f_out.write(f"Line {idx+1}: {lines[idx]}\n")

print("Wrote lines 750 to 900 to scratch/base_lines_750_900.txt")
