#Pytorch model
#Speech-Separation/src/loader/download.py
#Editing Video file -> 3sec

import os
import time
import tqdm
import argparse
import subprocess
import pandas as pd
from pathlib import Path
import concurrent.futures


def crop(path, start, end, downloaded_name):
    command = ("ffmpeg -y -i {}.mp4 -ss {} -t {} -c:v libx264 -crf 18 -preset veryfast -pix_fmt yuv420p "
               "-c:a aac -b:a 128k -strict experimental -r 25 {}")

    start_minute, start_second = int(start // 60), int(start % 60)
    end_minute, end_second = int(end // 60) - start_minute, int(end % 60) - start_second

    new_filepath = downloaded_name + "_final.mp4"

    if os.path.exists(new_filepath) and os.path.isfile(new_filepath):
        return

    command = command.format(downloaded_name, f"{start_minute}:{start_second}", f"{end_minute}:{end_second}", new_filepath)
    os.system(command)
    #subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()

    print("crop done")

    command2 = "mv "+new_filepath+" /home/euiin/SpeechSeparation/data/pre_video"
    #remove_orig_file = f"rm -f {downloaded_name}.mp4"
    os.system(command2)
    #subprocess.Popen(remove_orig_file, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()

def save_video(zargs):
    path, start, end= zargs
    
    downloaded_name = path.as_posix()
    print("downloaded name")
    print(downloaded_name)
    
    crop(path, start, end, downloaded_name)

def main(args):
    links = list()
    lts = dict()
    start_times = list()
    end_times = list()
    for root, dirs, files in os.walk("/home/euiin/SpeechSeparation/data/some_lrs2"):
        for file in files:
            if file.endswith(".mp4"):
                links.append(os.path.join(root, file[:-4]))
                start_times.append(0)
                end_times.append(3)
                

    #pos_x = df.iloc[:, 3][args.start:args.end]
    #pos_y = df.iloc[:, 4][args.start:args.end]

    paths = [Path(os.path.join(args.vid_dir, f)) for f in links]

    link_path = zip(paths, start_times, end_times) #position information delete
    with concurrent.futures.ThreadPoolExecutor(args.jobs) as executor:
        results = list(tqdm.tqdm(executor.map(save_video, link_path), total=len(links)))

if __name__ == "__main__":
    parse = argparse.ArgumentParser(description="Download parameters")
    parse.add_argument("--jobs", type=int, default=1)
    parse.add_argument("--path", type=str, default="../../data/audio_visual/avspeech_train.csv")
    parse.add_argument("--vid-dir", type=str, default="../../data/train/")
    parse.add_argument("--start", type=int, default=0)
    parse.add_argument("--end", type=int, default=10_000)
    args = parse.parse_args()
    main(args)

