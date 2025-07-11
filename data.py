with open("dataformat.jsonc") as f:
    file = f.read()

for line in file.splitlines():
    if "//" in line:
        print(line.split("//")[1].strip())