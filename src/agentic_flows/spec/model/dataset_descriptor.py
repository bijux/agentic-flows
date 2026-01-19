# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from dataclasses import dataclass

from agentic_flows.spec.ontology.ids import DatasetID


@dataclass(frozen=True)
class DatasetDescriptor:
    spec_version: str
    dataset_id: DatasetID
    dataset_version: str
    dataset_hash: str


__all__ = ["DatasetDescriptor"]
