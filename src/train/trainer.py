from typing import Union

import torch

import collections
from pathlib import Path
#src.train-> train
from train import ParamConfig
from train import SNRCallback

from catalyst.dl import utils, core
from catalyst.dl.runner import SupervisedRunner
from catalyst.dl.callbacks import EarlyStoppingCallback
from catalyst.dl.callbacks.scheduler import SchedulerCallback


def train(model: torch.nn.Module, dataset: torch.utils.data.Dataset,
          optimizer: torch.optim.Optimizer, criterion: torch.nn.Module,
          config: ParamConfig, val_dataset: torch.utils.data.Dataset=None,
          logdir: str="./logdir", resume: Union[str, None]="logdir/checkpoints/best_full.pth") -> None:
    """
        train the model with specified paremeters
        Args:
            model: neural network model
            dataset: training dataset
            optimizer: optimizer
            criterion: loss function
            val_dataset: validation dataset
            logdir: logdir location to save checkpoints
            resume: path where the partially trained model is stored
    """

    loaders = collections.OrderedDict()
    import pdb; pdb.set_trace()
    train_loader = utils.get_loader(dataset, open_fn=lambda x: {"input_audio": x[-1], "input_video": x[1], "targets": x[0]},
                                    batch_size=config.batch_size, num_workers=config.workers, shuffle=True)
    val_loader = utils.get_loader(val_dataset, open_fn=lambda x: {"input_audio": x[-1], "input_video": x[1], "targets": x[0]},
                                    batch_size=config.batch_size, num_workers=config.workers, shuffle=True)
    loaders = {"train": train_loader, "valid": val_loader}

    scheduler = torch.optim.lr_scheduler.CyclicLR(optimizer, base_lr=config.learning_rate,
                                                  max_lr=config.learning_rate * 10, step_size_up=4*len(train_loader),
                                                  mode="triangular", cycle_momentum=False)
    import pdb; pdb.set_trace()    
    runner = SupervisedRunner(input_key=["input_audio", "input_video"])
    runner.train(model=model, criterion=criterion,
                 optimizer=optimizer, scheduler=scheduler,
                 loaders=loaders, logdir=logdir, verbose=True,
                 num_epochs=config.epochs, resume=resume,
                 callbacks=collections.OrderedDict({"snr_callback": SNRCallback(),
                                                    "sched_callback": SchedulerCallback(mode="batch")})
                 )
