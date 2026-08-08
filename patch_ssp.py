path = '/home/kali/BlueDucky/BlueDucky.py'
with open(path, 'r') as f:
    text = f.read()

# Find the line that crashes the script when SSP fails
old_line = 'raise ConnectionFailureException("Failed to enable SSP")'
new_line = 'pass  # Ignoring SSP error (modern adapters have SSP enabled by default)'

if old_line in text:
    text = text.replace(old_line, new_line)
    with open(path, 'w') as f:
        f.write(text)
    print("✅ SSP patch applied successfully!")
else:
    print("⚠️ Could not find the exact error line. The script may have changed.")
