# compresseion tool to minify json files by removing whitespace and newlines. 
# This can be useful for reducing file size when storing or transmitting data, 
# especially if the JSON files are large. The script reads a JSON file,loads it into memory, 
# and then writes it back out in a compact format without any unnecessary spaces or line breaks.

import json

def minify_json(input_file, output_file):
    # 1. Load the data
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except UnicodeDecodeError:
        with open(input_file, 'r', encoding='utf-16') as f:
            data = json.load(f)

    # 2. Save without indentation or extra spaces
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, separators=(',', ':'))

# Run the script
# i should probably make this a command line tool but for now this is fine
minify_json('session.json', 'session_minified.json')
