# Known limitations
- **No guaranteed savings.** Effects depend on the workload and on how consistently the workflow is followed.
  Nothing here increases subscription limits. No benchmark results are claimed.
- **Token counts ≠ subscription usage.** The mapping from tokens to Claude plan limits is not published; use `/usage`.
- **Transcript format is internal** to Claude Code and may change. The report fails loudly (exit 3) rather than
  guessing; please open an issue with your Claude Code version.
- **Context resets are manual.** The model cannot clear its own context; the skill only recommends it.
- **Checkpoints are lossy:** they keep what was recorded.
- **Skill triggering is model-judged:** ask for the skill explicitly when it matters.
- **Platforms:** Linux tested locally; macOS via CI on GitHub Actions; Windows instructions provided but untested
  (Git Bash/WSL needed for the shell scripts).
- **Not an orchestrator:** no background processes, no automatic session management, no model switching.
