
# import os
# import cv2
# import time
# import argparse
# import subprocess
# import pandas as pd
# from pathlib import Path
# import concurrent.futures

# from tqdm import tqdm

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
AUDIO_SET_DIR = "/home/euiin/SpeechSeparation/data/extr_audio"
audio_files = glob.glob(os.path.join(AUDIO_SET_DIR, "*"))
total_files = len(audio_files)

a=int(random.gauss(mu=1, sigma=1))
total_choices = max(1, a)
print(a,'random gauss')
print(total_choices,'total_choices')
choices = list(range(total_files))
print(choices,'choices')
random.shuffle(choices)

