#Pytorch model
#Speech-Separation/src/loader/extract_audio.py
#Extract Audio file from preprocess video

import os
import cv2
import time
import argparse
import subprocess
import pandas as pd
from pathlib import Path
import concurrent.futures

from tqdm import tqdm


def extract(path):
    name = path.stem

    dir_name = path.parents[0]
    audio_dir = args.aud_dir
    audio_path = os.path.join(audio_dir, name)
    video = cv2.VideoCapture(path.as_posix())
    length_orig_video = video.get(cv2.CAP_PROP_FRAME_COUNT)
    #already pre-processed at 25 fps for 3 or more seconds
    #since lrs' all video already are 3 or less sec, we do not have to run 'for' loop
    #if we treat another data type, please make video into 3 secs. Here is no code for video which are more than 3 secs

    #t = int(length_orig_video) // 25
    t=0
    command = (f"ffmpeg -y -i {path.as_posix()} -f {args.audio_extension} -ab 64000 "
                f"-vn -ar {args.sampling_rate} -ac {args.audio_channel} - | sox -t "
                f"{args.audio_extension} - -r 16000 -c 1 -b 8 "
                f"{audio_path}_part.{args.audio_extension} trim {t} 00:{args.duration:02d}")
    os.system(command)
    #subprocess.Popen(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).communicate()
    print("extract done")
    

def main(args):
    file_names = [Path(os.path.join(args.vid_dir, i)) for i in os.listdir(args.vid_dir) if i.endswith("_final.mp4")]
    with concurrent.futures.ThreadPoolExecutor(args.jobs) as executor:
        results = list(tqdm(executor.map(extract, file_names), total=len(file_names)))
    
    

if __name__ == "__main__":
    parse = argparse.ArgumentParser(description="Extract parameters")
    parse.add_argument("--jobs", type=int, default=2)
    parse.add_argument("--aud-dir", type=str, default= "/home/euiin/SpeechSeparation/data/extr_audio")
    parse.add_argument("--vid_dir", type=str, default= "/home/euiin/SpeechSeparation/data/pre_video")
    parse.add_argument("--sampling_rate", type=int, default=16_000)
    parse.add_argument("--audio_channel", type=int, default=2)
    parse.add_argument("--audio_extension", type=str, default="wav")
    parse.add_argument("--duration", type=int, default=3)
    args = parse.parse_args()
    main(args)
