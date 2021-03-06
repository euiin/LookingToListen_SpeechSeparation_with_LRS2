'''
    This files samples (n=2) audio files and creates another audio file with mixed audio.
    It stores the mixed audio in data/train/mixed directory.
'''
import os
import re
import math
import glob
import random
import itertools
import subprocess
import pandas as pd
from tqdm import tqdm
from pathlib import Path


AUDIO_MIX_COMMAND_PREFIX = "ffmpeg -y -t 00:00:03 -ac 1 "
AUDIO_DIR = "/home/euiin/SpeechSeparation/data/extr_audio"
MIXED_AUDIO_DIR = "/home/euiin/SpeechSeparation/data/train/mixed"
REL_AUDIO_DIR = "../../data/train/mixed" # not used
VIDEO_DIR = "/home/euiin/SpeechSeparation/data/train"
REL_VIDEO_DIR = "/home/euiin/SpeechSeparation/data/train" # not used
AUDIO_SET_DIR = "./../../data/audio_set/audio" # 여기 머야

STORAGE_LIMIT = 5_000_000_000
REMOVE_RANDOM_CHANCE = 0.9

def sample_audio_set():
    """
        sample random audio files as a noise from audio set dataset
    """
    audio_files = glob.glob(os.path.join(AUDIO_SET_DIR, "*"))
    total_files = len(audio_files)

    total_choices = max(1, int(random.gauss(mu=1, sigma=1)))
    choices = list(range(total_files))
    random.shuffle(choices)
    #import pdb; pdb.set_trace()
    return [audio_files[i] for i in choices[:total_choices]]

def requires_excess_storage_space(n, r):
    # r will be very small anyway
    total = n**r / math.factorial(r)
    #total bytes
    storage_space = total * 90 # approximate storage requirement is (600K for spec and 90K for audio)

    if storage_space > STORAGE_LIMIT:
        return storage_space, True

    return storage_space, False


def nCr(n, r): 
    return (math.factorial(n) / (math.factorial(r) * math.factorial(n - r))) 

def audio_mixer(dataset_size: int, input_audio_size=2, video_ext=".mp4", audio_ext=".wav", file_name="temp.csv", audio_set=False, validation_size=0.3) -> None:
    """
        generate the combination dataframe used in data_loader.py

        Args:
            dataset_size: restrict total possible combinations
            input_audio_size: input size
            video_ext: extension of video
            audio_ext: extension of audio
            file_name: file name of combination dataframe to save
            audio_set: use audio set dataset
    """
    audio_mix_command_suffix = "-filter_complex amix=inputs={}:duration=longest "
    audio_files = glob.glob(os.path.join(AUDIO_DIR, "*"))
    total_audio_files = len(audio_files)
    
    total_val_files = int(total_audio_files * validation_size)
    total_train_files = total_audio_files - total_val_files

    train_files = audio_files[:total_train_files]
    val_files = audio_files[-total_val_files:]
    
    def retrieve_name(f):
        f = os.path.splitext(os.path.basename(f))[0]
        return re.sub(r'_part\d', '', f)
    
    def mix(audio_filtered_files, file_name_df, offset):
        #Generate all combinations and trim total possibilities
        audio_combinations = itertools.combinations(audio_filtered_files, input_audio_size)
        audio_combinations = itertools.islice(audio_combinations, dataset_size)

        storage_space, excess_storage = requires_excess_storage_space(len(audio_filtered_files), input_audio_size)

        if excess_storage:
            storage_space = (1 - REMOVE_RANDOM_CHANCE) * storage_space
            print(f"Removing {REMOVE_RANDOM_CHANCE * 100} percent of combinations")
            print(f"Saving total space: {storage_space - storage_space * REMOVE_RANDOM_CHANCE:,} Kbytes")

        print(f"Occupying space: {storage_space:,} Kbytes")

        #Store list of tuples, consisting of `input_audio_size`
        #Audio and their corresponding video path
        video_inputs = []
        audio_inputs = []
        mixed_audio = []
        noises = []
        
        total_comb_size = nCr(len(audio_filtered_files), input_audio_size)
        
        for indx, audio_comb in tqdm(enumerate(audio_combinations), total=total_comb_size):
            #skip few combinations if required storage is very high
            try:
                if excess_storage and random.random() < REMOVE_RANDOM_CHANCE:
                    continue

                base_names = [os.path.basename(fname)[:11] for fname in audio_comb]
                if len(base_names) != len(set(base_names)):
                    # if audio from the same video, assume same speaker and ignore it.
                    continue
                if audio_set:
                    noise_input = sample_audio_set()
                    noises.append(":".join(noise_input))
                    audio_comb = (*audio_comb, *noise_input)
                
                audio_inputs.append(audio_comb)
                #Convert audio file path to corresponding video path
                video_inputs.append(tuple(os.path.join(VIDEO_DIR, retrieve_name(f) +video_ext)
                                            for f in audio_comb))

                audio_mix_input = ""
                for audio in audio_comb:
                    audio_mix_input += f"-i {audio} "

                
                mixed_audio_name = os.path.join(MIXED_AUDIO_DIR, f"{indx+offset}{audio_ext}")
                audio_command = AUDIO_MIX_COMMAND_PREFIX + audio_mix_input + audio_mix_command_suffix.format(len(audio_comb)) + mixed_audio_name

                process = subprocess.Popen(audio_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)#.communicate()
                mixed_audio.append(mixed_audio_name)
                
                #print(video_inputs, audio_inputs, mixed_audio, noises)
            except KeyboardInterrupt as e:
                print("Caught Interrupt!")
                break
        
        combinations = {}
        for i in range(input_audio_size):
            combinations[f"video_{i+1}"] = []
            combinations[f"audio_{i+1}"] = []
        combinations["mixed_audio"] = []

        min_length = min(min(len(video_inputs), len(audio_inputs)), len(mixed_audio))
        print(f"Total combinations: {min_length}")

        video_inputs = video_inputs[:min_length]
        audio_inputs = audio_inputs[:min_length]
        mixed_audio = mixed_audio[:min_length]

        assert len(video_inputs) == len(audio_inputs) == len(mixed_audio)

        for videos, audios, mixed in zip(video_inputs, audio_inputs, mixed_audio):
            #fix proper path issue
            mixed = re.sub(r'../../', '../', mixed)
            for i in range(input_audio_size):
                v = re.sub(r'../../', '../', videos[i])
                a = re.sub(r'../../', '../', audios[i])
                
                combinations[f"video_{i+1}"].append(v)
                combinations[f"audio_{i+1}"].append(a)
            combinations["mixed_audio"].append(mixed)

        columns = [f"video_{i+1}" for i in range(input_audio_size)] + [f"audio_{i+1}" for i in range(input_audio_size)] + ["mixed_audio"]
        df = pd.DataFrame(combinations).reindex(columns=columns)
        df.to_csv(file_name_df, index=False)
        
        if audio_set:
            pd.Series(noises).to_csv("noise_only.csv", index=False, header=False)
        return  indx # df.shape[0]

    offset = mix(train_files, "../train.csv", 0)
    mix(val_files, "../val.csv", offset)


if __name__ == "__main__":
    audio_mixer(100_000_000, audio_set=False)

