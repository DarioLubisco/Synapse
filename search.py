import sys

word = sys.argv[1]
file_path = sys.argv[2]

with open(file_path, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if word in line.lower():
            print(f"{i+1}: {line.strip()}")
