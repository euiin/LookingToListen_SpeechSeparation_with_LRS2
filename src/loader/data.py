import os
import cv2
import librosa
import numpy as np
from pathlib import Path

from typing import Callable, Tuple, List

class Signal:
    '''
        This class holds the video frames and the audio signal.
    '''

    def __init__(self, video_path: str, audio_path: str, audio_ext=".mp3", sr=16_000):
        self.video_path = video_path
        self.audio_path = audio_path
        self._load(sr=sr)
        self._convert_video()

    def _load(self, sr: int):
        self.audio, sr = librosa.load(self.audio_path, sr=sr)
        self.video = cv2.VideoCapture(self.video_path)

    def augment_audio(self, augmenter, *args, **kwargs):
        '''
            Change the audio via the augmenter method.
        '''
        self.audio = augmenter(self.audio, *args, **kwargs)

    def augment_video(self, augmenter: Callable, *args, **kwargs):
        '''
            Change the video via the augmenter method.
        '''
        self.video = augmenter(self.video, *args, **kwargs)

    def _convert_video(self):
        frame_count = int(self.video.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_width = int(self.video.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(self.video.get(cv2.CAP_PROP_FRAME_HEIGHT))

        self.buffer_video = np.empty((frame_count, frame_height, frame_width, 3), np.dtype('uint8'))

        frame = 0
        ret = True

        while (frame < frame_count  and ret):
            ret, self.buffer_video[frame] = self.video.read()
            frame += 1
        self.video.release()
    
    def get_video(self):
        return self.buffer_video

    def get_audio(self):
        return self.audio

    @staticmethod
    def load_audio(audio_path: str, sr=16_000):
        if not os.path.exists(audio_path) or not os.path.isfile(audio_path):
            raise ValueError(f"Path: {audio_path} does not exist")
        return librosa.load(audio_path, sr=sr)[0]


class Augment:
    '''
        Format: function_name(main_signal, *args, **kwargs) -> main_signal:
    '''
    
    @staticmethod
    def overlay(sig1: np.ndarray, sig2: np.ndarray, start: int, end: int, sr=16_000, w1=0.5, w2=0.5):
        '''
            Overlay sig2 on sig1 at [start, end]
        '''
        #Normalise seconds to frames
        start *= sr
        end *= sr

        len1 = len(sig1)
        len2 = len(sig2)

        #Take the weighted sum of the signal
        sig1[start: start + end] = (w1 * sig1[start: start + end] + w2 * sig2).astype(sig1.dtype)
        return sig1

    @staticmethod
    def combine(main_signal, *signals, weights=None):
        '''
            Combine different signals according to their weight.
            Signal length should be the same.
        '''
        signals = [main_signal, *signals]

        total_signals = len(signals)
        
        if weights is None:
            weights = np.ones((total_signals, 1), dtype=np.float32) / total_signals

        combined_signal = np.zeros((signals[0].shape[0], 1), dtype=np.float32)
        weight = 0
        
        #Running Weighted Average Mean
        for i, w in enumerate(weights):
            combined_signal += signals[i] * w
            weight += w
        
        return combined_signal

    @staticmethod
    def align(main_signal: np.ndarray, all_signals: np.ndarray, all_alignments: List[Tuple[int, int]] , sr=16_000):
        '''
            Align signals of different length (smaller) to main_signal.
            Alignments are tuples containing start and end points wrt main_signal.
        '''

        length = len(main_signal)
        assert len(all_signals) == len(all_alignments), "All signals should have alignments"

        for i, (signal, alignment) in enumerate(zip(all_signals, all_alignments)):
            start, end = alignment
            start, end = start * sr, end * sr
            
            prefix = np.zeros((start, 1))
            suffix = np.zeros((length - end, 1))

            signal = np.concatenate((prefix, signal, suffix), axis=0)

            all_signals[i] = signal
        return main_signal
            

if __name__ == "__main__":
    signal = Signal("../../data/train/AvWWVOgaMlk_cropped.mp4", "../../data/train/audio/AvWWVOgaMlk_cropped.mp3")