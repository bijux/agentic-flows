# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations


class FlowID(str):
    pass


class AgentID(str):
    pass


class ToolID(str):
    pass


class ActionID(str):
    pass


class ArtifactID(str):
    pass


class EvidenceID(str):
    pass


class StepID(str):
    pass


class ClaimID(str):
    pass


class BundleID(str):
    pass


class RuleID(str):
    pass


class RequestID(str):
    pass


class ContractID(str):
    pass


class GateID(str):
    pass


class ResolverID(str):
    pass


class VersionID(str):
    pass


class DatasetID(str):
    pass


class TenantID(str):
    pass


class InputsFingerprint(str):
    pass


class ContentHash(str):
    pass


class EnvironmentFingerprint(str):
    pass


class PlanHash(str):
    pass


class PolicyFingerprint(str):
    pass


__all__ = [
    "FlowID",
    "AgentID",
    "ToolID",
    "ActionID",
    "ArtifactID",
    "EvidenceID",
    "StepID",
    "ClaimID",
    "BundleID",
    "RuleID",
    "RequestID",
    "ContractID",
    "GateID",
    "ResolverID",
    "VersionID",
    "DatasetID",
    "TenantID",
    "InputsFingerprint",
    "ContentHash",
    "EnvironmentFingerprint",
    "PlanHash",
    "PolicyFingerprint",
]
