with open('templates/base.html', 'rb') as f:
    data = f.read()

# Let's decode the entire file replacing errors with a placeholder
decoded = data.decode('utf-8', errors='replace')

# Write to a clean utf-8 file
with open('scratch/base_utf8.txt', 'w', encoding='utf-8') as f_out:
    f_out.write(decoded)

print("Wrote base.html to scratch/base_utf8.txt with error replacements")
