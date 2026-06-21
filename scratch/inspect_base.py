with open('templates/base.html', 'rb') as f:
    data = f.read()

idx = data.find(b"waiting sessions")
if idx != -1:
    context = data[idx-1500:idx+1500].decode('utf-8', errors='replace')
    with open('scratch/base_context.txt', 'w', encoding='utf-8') as f_out:
        f_out.write(context)
    print("Successfully wrote context to scratch/base_context.txt")
else:
    print("Could not find waiting sessions")
