# This repository is governed by SEMANTICS.md.
# Code that violates semantics is considered a bug, not an implementation choice.

agentic-flows defines the minimal contracts and entrypoints for describing, resolving, and tracing agentic flows across the Bijux core stack.

It does not execute flows, schedule work, run agents, or perform retrieval; it only defines the schema and stubs those systems depend on.

It relates to the five Bijux cores by providing shared contracts used by bijux-agent (agents), bijux-rag (retrieval), bijux-rar (reasoning artifacts), bijux-vex (verification), and bijux-cli (interface).

An agentic flow is a structured, multi-step plan of agent and retrieval actions with explicit verification gates.
