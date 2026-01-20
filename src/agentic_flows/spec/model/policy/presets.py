# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Module definitions for spec/model/policy/presets.py."""

from __future__ import annotations

from agentic_flows.spec.model.policy.non_determinism_policy import NonDeterminismPolicy
from agentic_flows.spec.ontology import EntropyMagnitude
from agentic_flows.spec.ontology.public import EntropySource, NonDeterminismIntentSource


def policy_presets() -> dict[str, NonDeterminismPolicy]:
    """Return non-determinism policy presets for common workflows."""
    return {
        "strict_deterministic": NonDeterminismPolicy(
            spec_version="v1",
            policy_id="strict_deterministic",
            allowed_sources=(),
            allowed_intent_sources=(),
            min_entropy_magnitude=EntropyMagnitude.LOW,
            max_entropy_magnitude=EntropyMagnitude.LOW,
            allowed_variance_class=EntropyMagnitude.LOW,
            require_justification=True,
        ),
        "bounded_llm": NonDeterminismPolicy(
            spec_version="v1",
            policy_id="bounded_llm",
            allowed_sources=(EntropySource.SEEDED_RNG,),
            allowed_intent_sources=(NonDeterminismIntentSource.LLM,),
            min_entropy_magnitude=EntropyMagnitude.LOW,
            max_entropy_magnitude=EntropyMagnitude.MEDIUM,
            allowed_variance_class=EntropyMagnitude.MEDIUM,
            require_justification=True,
        ),
        "human_in_the_loop": NonDeterminismPolicy(
            spec_version="v1",
            policy_id="human_in_the_loop",
            allowed_sources=(EntropySource.HUMAN_INPUT, EntropySource.EXTERNAL_ORACLE),
            allowed_intent_sources=(
                NonDeterminismIntentSource.HUMAN,
                NonDeterminismIntentSource.EXTERNAL,
            ),
            min_entropy_magnitude=EntropyMagnitude.LOW,
            max_entropy_magnitude=EntropyMagnitude.HIGH,
            allowed_variance_class=EntropyMagnitude.HIGH,
            require_justification=True,
        ),
        "exploratory_research": NonDeterminismPolicy(
            spec_version="v1",
            policy_id="exploratory_research",
            allowed_sources=(
                EntropySource.SEEDED_RNG,
                EntropySource.DATA,
                EntropySource.HUMAN_INPUT,
                EntropySource.EXTERNAL_ORACLE,
            ),
            allowed_intent_sources=(
                NonDeterminismIntentSource.LLM,
                NonDeterminismIntentSource.RETRIEVAL,
                NonDeterminismIntentSource.HUMAN,
                NonDeterminismIntentSource.EXTERNAL,
            ),
            min_entropy_magnitude=EntropyMagnitude.LOW,
            max_entropy_magnitude=EntropyMagnitude.HIGH,
            allowed_variance_class=EntropyMagnitude.HIGH,
            require_justification=False,
        ),
    }


def get_policy_preset(name: str) -> NonDeterminismPolicy:
    """Lookup a named policy preset."""
    presets = policy_presets()
    if name not in presets:
        raise KeyError(f"Unknown policy preset: {name}")
    return presets[name]


__all__ = ["get_policy_preset", "policy_presets"]
