"""
Extremely fast mixing (100+ audio files per second)
generates a lot of empty/corrupted files
"""
import pandas as pd

from pathlib import Path
from argparse import ArgumentParser

def remove_corrupt_audio(audio_dir, df, path, expected_audio_size=96_000):
    files = audio_dir.rglob("*wav")

    corrupt_audio = []

    for f in files:
        size = f.stat().st_size
        if size < expected_audio_size:
            corrupt_audio.append(Path(*f.parts[1:]).as_posix())

    print(f"Found total corrupted files: {len(corrupt_audio)}")

    print(corrupt_audio)
    filtered_df = df[~df["mixed_audio"].isin(corrupt_audio)]

    filtered_df.to_csv(path, index=False)

if __name__ == "__main__":

    parser = ArgumentParser()

    parser.add_argument("--mixed-dir", default=Path("/home/euiin/SpeechSeparation/data/extr_audio"), type=Path)
    parser.add_argument("--train-df", default=Path("../train.csv"), type=Path)
    parser.add_argument("--val-df", default=Path("../val.csv"), type=Path)

    args = parser.parse_args()

    train_df = pd.read_csv(args.train_df)
    val_df = pd.read_csv(args.val_df)

    remove_corrupt_audio(args.mixed_dir, train_df, args.train_df)
    remove_corrupt_audio(args.mixed_dir, val_df, args.val_df)
