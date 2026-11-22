---
name: token-efficient-workflow
description: Deprecated alias of the claude-lean skill, kept for compatibility with Claude Lean v0.1.0 and v0.1.1. Use only when the user explicitly invokes token-efficient-workflow; then load and follow the claude-lean skill.
---

# token-efficient-workflow → claude-lean (deprecated alias)

This name is kept only for backward compatibility. Load the `claude-lean` skill (Skill tool, or `/claude-lean`) and
follow it exactly; it contains the complete workflow. If `claude-lean` is not installed, tell the user to re-run
Claude Lean's `scripts/install.sh`. Like `claude-lean`, never change the user's model, effort or thinking settings.
