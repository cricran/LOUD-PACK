import json
import os
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def convert_hash_to_ogg(hash_value, source_path, destination_path):
    for root, dirs, files in os.walk(source_path):
        for file in files:
            if hash_value in file:
                source_file = os.path.join(root, file)
                destination_file = os.path.splitext(destination_path)[0] + '.ogg'
                shutil.copy2(source_file, destination_file)
                return

def increase_volume_ogg(file_path, increase_dB):
    output_file_path = os.path.splitext(file_path)[0] + '_temp.ogg'
    with open(os.devnull, 'w') as null_file:
        ffmpeg_command = [
            'ffmpeg',
            '-i', file_path,
            '-af', f'volume={increase_dB}dB',
            output_file_path
        ]
        subprocess.run(ffmpeg_command, stdout=null_file, stderr=subprocess.STDOUT)
    
    if os.path.exists(output_file_path):
        if os.path.exists(file_path):
            os.remove(file_path)
        os.rename(output_file_path, file_path)

def create_sound_folders(sound_path):
    os.makedirs(os.path.normpath(os.path.dirname(sound_path)), exist_ok=True)

def create_sound_list(src):
    with open('data.json') as file:
        data = json.load(file)
    return {i: [data['objects'][i]["hash"], str(data['objects'][i]["hash"])[:2]] 
            for i in data['objects'] if ".ogg" in i}

def format_time(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours)} hours {int(minutes)} minutes {int(seconds)} seconds"

def process_file(skey, sval, mc_objects):
    create_sound_folders(skey)
    convert_hash_to_ogg(sval[0], os.path.join(mc_objects, sval[1]), skey)
    increase_volume_ogg(skey, 50)
    return skey

def main():
    mc_src = os.path.join(os.getenv("APPDATA"), ".minecraft/assets")
    mc_index = os.path.join(mc_src, "indexes")
    mc_objects = os.path.join(mc_src, "objects")

    json_files = [file for file in os.listdir(mc_index)]
    print("Choose the version of the game you want:")
    for i, file in enumerate(json_files):
        print(f"\t - {i} : {file}")
    chose = int(input())
    file = os.path.join(mc_index, json_files[chose])
    dico = create_sound_list(file)
    
    print("Name your loud pack:")
    name = str(input())
    os.mkdir(name)
    os.chdir(name)
    os.mkdir("assets")
    os.chdir("assets")

    num_lines = len(dico)
    processed_files = 0
    start_time = time.time()

    with ThreadPoolExecutor() as executor:
        future_to_file = {
            executor.submit(process_file, skey, sval, mc_objects): skey
            for skey, sval in dico.items()
        }
        
        for future in as_completed(future_to_file):
            skey = future_to_file[future]
            processed_files += 1
            elapsed_time = time.time() - start_time
            files_per_second = processed_files / elapsed_time if elapsed_time > 0 else 0
            remaining_files = num_lines - processed_files
            estimated_time_remaining = remaining_files / files_per_second if files_per_second > 0 else 0
            
            progress = processed_files / num_lines
            bar_length = 40
            progress_bar = "[" + "=" * int(bar_length * progress) + "-" * (bar_length - int(bar_length * progress)) + "]"
            print(f"Progress: {progress_bar} {processed_files}/{num_lines} files processed | Estimated time remaining: {format_time(estimated_time_remaining)}", end='\r')
    
    print("\nProcessing completed.")
    return 1

main()
