"""
LitUNet: PyTorch Lightning wrapper for MONAI UNet segmentation model.

This module contains the LitUNet class that wraps a MONAI UNet for cell segmentation tasks.
It provides training, validation, and inference functionality using PyTorch Lightning.
"""

import os
from glob import glob

import lightning as L
import matplotlib.pyplot as plt
import monai.transforms as t
import torch
from lightning.pytorch.callbacks import LearningRateMonitor, ModelCheckpoint
from lightning.pytorch.loggers import TensorBoardLogger
from matplotlib import pyplot as plt
from monai.data import CacheDataset, DataLoader, Dataset, decollate_batch
from monai.losses import DiceCELoss, DiceFocalLoss, HausdorffDTLoss, TverskyLoss
from monai.metrics import DiceMetric, HausdorffDistanceMetric
from monai.networks.nets import UNet
from monai.visualize import plot_2d_or_3d_image
from monai.visualize.utils import blend_images
from torch import nn
from torch.optim import Adam
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torch.utils.tensorboard import SummaryWriter


class LitUNet(L.LightningModule):
    def __init__(
        self,
        n_classes,
        num_input_channel,
        dropout=0.5,
        check_val=10,
        max_epochs=50,
        optim_lr=0.001,
        optim_betas=(0.9, 0.999),
        optim_eps=1e-08,
        optim_weight_decay=0,
        optim_amsgrad=True,
    ):
        super().__init__()
        self.save_hyperparameters()

        self.model = UNet(
            spatial_dims=2,
            in_channels=num_input_channel,
            out_channels=n_classes,
            channels=(64, 128, 256, 512),
            strides=(2, 2, 2),
            dropout=dropout,
            num_res_units=2,
        )

        self.loss = HausdorffDTLoss(to_onehot_y=True, softmax=True)
        self.dice_metric = HausdorffDistanceMetric(
            include_background=False, reduction="mean", get_not_nans=False
        )

        self.post_pred = t.Compose(
            [t.EnsureType(), t.AsDiscrete(argmax=True, to_onehot=n_classes)]
        )
        self.post_label = t.AsDiscrete(to_onehot=n_classes)

        self.train_step_outputs = []
        self.val_step_outputs = []
        self.train_losses = []
        self.val_losses = []
        self.metric_values = []
        self.best_val_dice = 100000
        self.best_val_epoch = 0

    def forward(self, inputs):
        return self.model(inputs)

    def training_step(self, batch, batch_idx):
        images, labels = batch["image"], batch["label"]
        outputs = self.model(images)
        loss = self.loss(outputs, labels)
        pred = {"train_loss": loss, "train_number": len(labels)}
        self.train_step_outputs.append(pred)
        return {"loss": loss}

    def on_train_epoch_end(self):
        outputs = self.train_step_outputs
        train_loss, num_items = 0, 0
        for output in outputs:
            train_loss += output["train_loss"].sum().item()
            num_items += output["train_number"]

        mean_train_loss = torch.tensor(train_loss / num_items)
        self.log("train_loss", mean_train_loss)
        self.train_losses.append(mean_train_loss.item())
        self.train_step_outputs.clear()  # free memory

    def validation_step(self, batch, batch_idx):
        images, labels = batch["image"], batch["label"]
        outputs = self.model(images)
        loss = self.loss(outputs, labels)
        outputs = [self.post_pred(i) for i in decollate_batch(outputs)]
        labels = [self.post_label(i) for i in decollate_batch(labels)]

        self.dice_metric(y_pred=outputs, y=labels)

        pred = {"val_loss": loss, "val_number": len(outputs)}  # Save all losses
        self.val_step_outputs.append(pred)

        if batch_idx == 25:
            # blend_images(images[0], labels[0])
            plot_2d_or_3d_image(
                images * 255,
                self.current_epoch + 1,
                self.logger.experiment,
                tag="image",
            )
            plot_2d_or_3d_image(
                labels, self.current_epoch + 1, self.logger.experiment, tag="label"
            )
            plot_2d_or_3d_image(
                outputs, self.current_epoch + 1, self.logger.experiment, tag="output"
            )
        return {"val_loss": loss, "val_number": len(outputs)}

    def on_validation_epoch_end(self):
        outputs = self.val_step_outputs
        val_loss, num_items = 0, 0

        for output in outputs:
            val_loss += output["val_loss"].sum().item()
            num_items += output["val_number"]
        mean_val_loss = torch.tensor(val_loss / num_items)
        self.val_losses.append(mean_val_loss.item())

        mean_val_dice = self.dice_metric.aggregate().item()

        self.dice_metric.reset()
        self.val_step_outputs.clear()  # free memory

        if mean_val_dice < self.best_val_dice:
            self.best_val_dice = mean_val_dice
            self.best_val_epoch = self.current_epoch

        print(
            f"current epoch: {self.current_epoch} "
            f"current mean dice: {mean_val_dice:.4f}"
            f"\nbest mean dice: {self.best_val_dice:.4f} "
            f"at epoch: {self.best_val_epoch}"
        )

        self.metric_values.append(mean_val_dice)
        self.log("val_dice", mean_val_dice)
        self.log("val_loss", mean_val_loss)
        self.val_step_outputs.clear()  # free memory

        tensorboard_logs = {"val_dice": mean_val_dice, "val_loss": mean_val_loss}
        return {"log": tensorboard_logs}

    def configure_optimizers(self):

        self.optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=self.hparams.optim_lr,
            betas=self.hparams.optim_betas,
            eps=self.hparams.optim_eps,
            weight_decay=self.hparams.optim_weight_decay,
            amsgrad=self.hparams.optim_amsgrad,
        )
        return {
            "optimizer": self.optimizer,
            "lr_scheduler": {
                "scheduler": ReduceLROnPlateau(self.optimizer, factor=0.1, patience=5),
                "frequency": self.hparams.check_val,
                "monitor": "val_loss",
                "interval": "epoch",
            },
        }

    def plot_losses(self):
        plt.figure(figsize=(10, 5))
        plt.plot(
            [i for i in range(len(self.train_losses))],
            self.train_losses,
            label="Train Loss",
        )
        plt.plot(
            [i * self.hparams.check_val for i in range(len(self.val_losses))],
            self.val_losses,
            label="Validation Loss",
        )
        plt.xlabel("Iterations")
        plt.ylabel("Loss")
        plt.title("Training and Validation Losses")
        plt.legend()
        plt.show()
