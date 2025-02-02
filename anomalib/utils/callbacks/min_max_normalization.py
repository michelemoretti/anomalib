"""Anomaly Score Normalization Callback that uses min-max normalization."""

# Copyright (C) 2022 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Any, Dict

import pytorch_lightning as pl
from pytorch_lightning import Callback
from pytorch_lightning.utilities.cli import CALLBACK_REGISTRY
from pytorch_lightning.utilities.types import STEP_OUTPUT

from anomalib.models.components import AnomalyModule
from anomalib.post_processing.normalization.min_max import normalize


@CALLBACK_REGISTRY
class MinMaxNormalizationCallback(Callback):
    """Callback that normalizes the image-level and pixel-level anomaly scores using min-max normalization."""

    def on_test_start(self, _trainer: pl.Trainer, pl_module: AnomalyModule) -> None:
        """Called when the test begins."""
        if pl_module.image_metrics is not None:
            pl_module.image_metrics.set_threshold(0.5)
        if pl_module.pixel_metrics is not None:
            pl_module.pixel_metrics.set_threshold(0.5)

    def on_validation_batch_end(
        self,
        _trainer: pl.Trainer,
        pl_module: AnomalyModule,
        outputs: STEP_OUTPUT,
        _batch: Any,
        _batch_idx: int,
        _dataloader_idx: int,
    ) -> None:
        """Called when the validation batch ends, update the min and max observed values."""
        if "anomaly_maps" in outputs.keys():
            pl_module.min_max(outputs["anomaly_maps"])
        else:
            pl_module.min_max(outputs["pred_scores"])

    def on_test_batch_end(
        self,
        _trainer: pl.Trainer,
        pl_module: AnomalyModule,
        outputs: STEP_OUTPUT,
        _batch: Any,
        _batch_idx: int,
        _dataloader_idx: int,
    ) -> None:
        """Called when the test batch ends, normalizes the predicted scores and anomaly maps."""
        self._normalize_batch(outputs, pl_module)

    def on_predict_batch_end(
        self,
        _trainer: pl.Trainer,
        pl_module: AnomalyModule,
        outputs: Dict,
        _batch: Any,
        _batch_idx: int,
        _dataloader_idx: int,
    ) -> None:
        """Called when the predict batch ends, normalizes the predicted scores and anomaly maps."""
        self._normalize_batch(outputs, pl_module)

    @staticmethod
    def _normalize_batch(outputs, pl_module):
        """Normalize a batch of predictions."""
        stats = pl_module.min_max.cpu()
        outputs["pred_scores"] = normalize(
            outputs["pred_scores"], pl_module.image_threshold.value.cpu(), stats.min, stats.max
        )
        if "anomaly_maps" in outputs.keys():
            outputs["anomaly_maps"] = normalize(
                outputs["anomaly_maps"], pl_module.pixel_threshold.value.cpu(), stats.min, stats.max
            )
