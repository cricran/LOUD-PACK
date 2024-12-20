import json
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

def convert_and_increase_volume(hash_value, source_path, destination_path, increase_dB):
    for root, dirs, files in os.walk(source_path):
        for file in files:
            if hash_value in file:
                source_file = os.path.join(root, file)
                output_file_path = os.path.splitext(destination_path)[0] + '.ogg'
                ffmpeg_command = [
                    'ffmpeg', '-i', source_file,
                    '-af', f'volume={increase_dB}dB',
                    '-y', output_file_path
                ]
                subprocess.run(ffmpeg_command, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
                return destination_path

def create_sound_folders(sound_path, assets_path):
    full_path = os.path.join(assets_path, sound_path)
    os.makedirs(os.path.normpath(os.path.dirname(full_path)), exist_ok=True)
    return full_path

def create_sound_list(src):
    with open(src) as file:
        data = json.load(file)
    return {i: [data['objects'][i]["hash"], str(data['objects'][i]["hash"])[:2]] 
            for i in data['objects'] if ".ogg" in i}

def format_time(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours)} hours {int(minutes)} minutes {int(seconds)} seconds"

def process_file(skey, sval, mc_objects, increase_dB, assets_path):
    destination_path = create_sound_folders(skey, assets_path)
    convert_and_increase_volume(sval[0], os.path.join(mc_objects, sval[1]), destination_path, increase_dB)
    return skey

def main():
    mc_src = os.path.join(os.getenv("APPDATA"), ".minecraft/assets")
    mc_index = os.path.join(mc_src, "indexes")
    mc_objects = os.path.join(mc_src, "objects")

    json_files = [file for file in os.listdir(mc_index) if file.endswith('.json')]
    file_dates = [
        datetime.fromtimestamp(os.path.getctime(os.path.join(mc_index, file))).strftime('%Y-%m-%d %H:%M:%S')
        for file in json_files
    ]

    print("Choose the version of the game you want:")
    for i, (file, date) in enumerate(zip(json_files, file_dates)):
        print(f"\t - {i} : {file} (Created on {date})")

    while True:
        try:
            chose = int(input("Enter the number corresponding to your choice: "))
            if 0 <= chose < len(json_files):
                break
            else:
                print(f"Please enter a number between 0 and {len(json_files) - 1}.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")

    chosen_file = os.path.join(mc_index, json_files[chose])
    dico = create_sound_list(chosen_file)
    
    name = input("Name your loud pack: ")
    pack_path = os.path.join(os.getcwd(), name)
    assets_path = os.path.join(pack_path, "assets")
    os.makedirs(assets_path, exist_ok=True)

    num_lines = len(dico)
    processed_files = 0
    start_time = time.time()
    increase_dB = 50  # Volume increase in dB

    with ThreadPoolExecutor() as executor:
        future_to_file = {
            executor.submit(process_file, skey, sval, mc_objects, increase_dB, assets_path): skey
            for skey, sval in dico.items()
        }
        
        for future in as_completed(future_to_file):
            skey = future_to_file[future]
            processed_files += 1
            elapsed_time = time.time() - start_time
            avg_time_per_file = elapsed_time / processed_files
            estimated_time_remaining = avg_time_per_file * (num_lines - processed_files)
            
            progress = processed_files / num_lines
            bar_length = 40
            filled_length = int(bar_length * progress)
            progress_bar = "[" + "=" * filled_length + "-" * (bar_length - filled_length) + "]"
            
            if processed_files % 5 == 0 or processed_files == num_lines:
                print(f"Progress: {progress_bar} {processed_files}/{num_lines} files processed | Estimated time remaining: {format_time(estimated_time_remaining)}", end='\r')
    
    print("\nProcessing completed.")
    return 1

main()