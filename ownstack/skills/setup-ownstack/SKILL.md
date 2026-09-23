---
name: setup-ownstack
description: Configure which models and effort levels ownstack uses per role. Detects what this session can dispatch and writes an override file the skills read. Use for /setup-ownstack, "configure ownstack models", or changing ownstack's model choices.
---

# Setup ownstack

Write `~/.claude/ownstack-models.md`, a config file that sets ownstack's model and effort per role. Skills read it and fall back to their inline defaults when a line is absent, so this is an override layer, not a requirement. Running ownstack without it works fine.

## Steps

### 1. Detect what you can dispatch

Claude Code subagents take a `model` (`opus`, `sonnet`, `haiku`, `fable`, or `inherit`) and agent definitions take an `effort` (`low`, `medium`, `high`, `xhigh`, `max`). ownstack writes roles as `model:effort`, for example `opus:max`.

Confirm which models this account can actually dispatch before writing them. If you cannot confirm, ask the user which they have. Never write a model you have not confirmed. `inherit` is always valid and means the role runs on the parent session's model.

### 2. Load current state

The default role mapping is the shape in step 5. If `~/.claude/ownstack-models.md` exists, read it and treat its values as current. Otherwise start from the defaults.

### 3. Map and confirm

Show every role with its current value, marking anything unavailable as needing a choice. Ask whether to accept as-is or change specific roles. Prefer AskUserQuestion over free text.

For panel roles (how critics, arena runners, architect runners, interrogate reviewers) the value is a list, and one subagent runs per entry, so the list length sets the panel size. `arena cross-judge pool` is also a list, but Arena picks one entry whose model or effort differs from the parent's when possible.

`swarm workers` is the default for every worker unless a race assigns another value per arm.

### 4. Validate

Every model written must be one this session can dispatch; `inherit` always passes. If a chosen value is unavailable, stop and ask again. A config pointing at a model the user cannot use breaks every delegation that reads it.

### 5. Write the config

Write `~/.claude/ownstack-models.md`. Overwrite the whole file so re-runs stay idempotent. Shape:

```
# ownstack model configuration
# One line per role, as `model:effort`. Delete a line to fall back to the skill default.
# `inherit` as a value: the role runs on the parent session's model.
# Models: opus, sonnet, haiku, fable, inherit. Effort: low, medium, high, xhigh, max.

feature, refactoring: sonnet:high
bug-fix: opus:max
perf-issue: opus:max
hillclimb: opus:max
judgment and prose: opus:max
hardest tasks: opus:max
how explorer: sonnet:high
how explainer: opus:max
how critics: fable:max, opus:max, sonnet:high, haiku:medium
why investigators: sonnet:high
why synthesizer: opus:max
reflect tooling: opus:high
reflect judgment, divergent, synthesizer: opus:max
arena runners: fable:max, opus:max, sonnet:high, haiku:medium
arena cross-judge pool: fable:max, opus:max, sonnet:high, haiku:medium
swarm workers: sonnet:high
architect runners: fable:max, opus:max, sonnet:high, haiku:medium
interrogate reviewers: fable:max, opus:max, sonnet:high, haiku:medium
```

### 6. Offer to load it automatically

Claude Code does not auto-load arbitrary files. For the config to reach every session, one line must reference it from a `CLAUDE.md`. Offer to append this to `~/.claude/CLAUDE.md`:

```
When running ownstack skills, read `~/.claude/ownstack-models.md` for per-role model choices.
```

On yes, append it if that exact line is not already present. On no, tell the user the config still applies whenever they mention it, and move on.

### 7. Confirm

Tell the user what was written and where. Re-running this skill updates it.

### 8. Offer a verification skill (optional)

Check whether the project has a way to drive the real app for proof (a `verify-*` skill, or an existing harness). If not, offer once: "want a project-local verification skill, so agents can drive the app the way a user does and prove changes work? I can generate one with /create-verification-skill." On yes, invoke `/create-verification-skill`. On no, move on without pushing.
