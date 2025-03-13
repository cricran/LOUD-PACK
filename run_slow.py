import json
import os
import shutil
import subprocess
import time




def convert_hash_to_ogg(hash_value, source_path, destination_path):
    # Recursively search for the corresponding sound file in the source path
    for root, dirs, files in os.walk(source_path):
        for file in files:
            if hash_value in file:
                source_file = os.path.join(root, file)
                # Convert the file to .ogg and copy it to the destination path
                destination_file = os.path.splitext(destination_path)[0] + '.ogg'
                shutil.copy2(source_file, destination_file)
                return

def increase_volume_ogg(file_path, increase_dB):
    # Increase the volume of an .ogg file by adding the specified value in decibels
    output_file_path = os.path.splitext(file_path)[0] + '_temp.ogg'
    # Redirect ffmpeg's standard output to a null file
    with open(os.devnull, 'w') as null_file:
        ffmpeg_command = [
            'ffmpeg',
            '-i', file_path,
            '-af', f'volume={increase_dB}dB',
            output_file_path
        ]
        subprocess.run(ffmpeg_command, stdout=null_file, stderr=subprocess.STDOUT)
    
    # Check if the temporary file has been created
    if os.path.exists(output_file_path):
        # Remove the destination file if it already exists
        if os.path.exists(file_path):
            os.remove(file_path)
        # Rename the temporary file to the destination file
        os.rename(output_file_path, file_path)

def create_sound_folders(sound_path):
    # Create the necessary folders for the sound path
    os.makedirs(os.path.normpath(os.path.dirname(sound_path)), exist_ok=True)

def create_sound_list(src):
    file = open('data.json')
    data = json.load(file)
    dico = {}
    for i in data['objects']:
        if ".ogg" in i:
            dico[i] = [data['objects'][i]["hash"], str(data['objects'][i]["hash"])[:2]]
    return dico

def format_time(seconds):
    # Convert time to hours, minutes, and seconds
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours)} hours {int(minutes)} minutes {int(seconds)} seconds"

def main():
    if os.name == 'posix' :
        home = os.path.expanduser("~")
        mc_src = os.path.join(home, ".var/app/com.mojang.Minecraft/.minecraft/assets")
    else :
        mc_src = os.path.join(os.getenv("APPDATA"), ".minecraft/assets")
    # minecraft indexs folder
    mc_index = os.path.join(mc_src, "indexes")
    #
    mc_objects = os.path.join(mc_src, "objects")
    # list of game file
    json_files = []
    for file in os.listdir(mc_index):
        json_files.append(file)
    # selection of the game version
    print("Chose the version of the game you want :")
    for i, file in enumerate(json_files):
        print(f"\t - {i} : {file}")
    chose = int(input())
    file = os.path.join(mc_index, json_files[chose])
    print(file)
    dico = create_sound_list(file)
    # name the sound pack
    print("Name your loud pack :")
    name = str(input())
    os.mkdir(name)
    dst = os.path.join(name)
    os.chdir(dst)
    os.mkdir("assests")
    dst = os.chdir("assests")
    # create loud pack
    num_lines = len(dico)
    processed_files = 0
    start_time = time.time()
    for skey, sval in dico.items():
        create_sound_folders(skey)
        convert_hash_to_ogg(sval[0], os.path.join(mc_objects, sval[1]), skey)
        increase_volume_ogg(skey, 50)  # Increase volume by 50 decibels
        
        processed_files += 1
        elapsed_time = time.time() - start_time
        if elapsed_time > 0:
            files_per_second = processed_files / elapsed_time
            remaining_files = num_lines - processed_files
            estimated_time_remaining = remaining_files / files_per_second
        
            progress = processed_files / num_lines
            bar_length = 40
            progress_bar = "[" + "=" * int(bar_length * progress) + "-" * (bar_length - int(bar_length * progress)) + "]"
            print(f"Progress: {progress_bar} {processed_files}/{num_lines} files processed | Estimated time remaining: {format_time(estimated_time_remaining)}", end='\r')
    return 1




main()