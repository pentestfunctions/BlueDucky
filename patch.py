path = '/home/kali/BlueDucky/BlueDucky.py'
with open(path, 'r') as f:
    text = f.read()

old_line = 'adapter.set_property("name", "Robot POC")'
new_line = 'import os; import time; os.system("sudo hciconfig hci0 up"); time.sleep(2); adapter.set_property("name", "Robot POC")'

if old_line in text:
    text = text.replace(old_line, new_line)
    with open(path, 'w') as f:
        f.write(text)
    print("✅ Script patched successfully!")
else:
    print("⚠️ Line not found or already patched.")
