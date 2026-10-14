#!/usr/bin/env python3
"""
Re-derive ownstack from upstream pstack.

ownstack is a port, not a fork with hand-edits. Everything that turns pstack
into ownstack lives here as a rule, so pulling upstream changes means re-running
this script instead of resolving conflicts in 60+ rebranded files.

Usage:
    python3 scripts/port.py --upstream <path-to-cursor/plugins/pstack>
    python3 scripts/port.py --upstream <path> --check   # diff only, no writes

Files listed in HAND_WRITTEN are never overwritten; the script reports when
upstream changes them so you can review by hand.
"""

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Appended to the guide index so the ported docs carry their attribution.
GUIDE_FOOTER = (
    "\n---\n\n*This guide, including its illustrations, is from "
    "[pstack](https://github.com/cursor/plugins/tree/main/pstack) by "
    "[Lauren Tan](https://github.com/poteto), used under the MIT License "
    "and adapted for Claude Code.*\n"
)

# Files this port rewrote from scratch. The script refuses to clobber them and
# instead tells you when upstream has moved, so you can re-review deliberately.
HAND_WRITTEN = {
    "README.md",
    "LICENSE",                      # dual copyright notice; never auto-generate
    "skills/setup-ownstack/SKILL.md",
    "skills/ownstack-help/SKILL.md",  # upstream's is about Cursor Custom Modes
}

# Files dropped from the port entirely, with the reason.
DROPPED = {
    "skills/make-bot-ui": "depends on Cursor's update_state routines API; no Claude Code equivalent",
}

# Directory / file renames applied to paths.
PATH_RENAMES = [
    ("skills/poteto-mode", "skills/ownstack-mode"),
    ("skills/setup-pstack", "skills/setup-ownstack"),
    ("skills/poteto-help", "skills/ownstack-help"),
    ("agents/poteto-agent.md", "agents/ownstack-agent.md"),
    ("docs/guide/02-poteto-mode.md", "docs/guide/02-ownstack-mode.md"),
]

EFFORTS = ["max", "xhigh", "high", "medium", "low"]

# Per-profile, so `CLAUDE_CONFIG_DIR=~/.claude_work claude` and a second
# profile each keep their own model choices.
CONFIG = "${CLAUDE_CONFIG_DIR:-~/.claude}/ownstack-models.md"

# Ordered text substitutions. Order matters: longer/more specific first.
SUBS = [
    # --- config paths ---
    (r"~/\.cursor/rules/pstack-models\.mdc", CONFIG),
    (r"\.cursor/rules/pstack-models\.mdc", CONFIG),
    (r"~/\.cursor/", "~/.claude/"),
    (r"\.cursor/skills/", ".claude/skills/"),
    (r"\.cursor/automations/", ".claude/automations/"),
    (r"\.cursor/plugins/", ".claude/plugins/"),
    (r"\.cursor/projects/", ".claude/projects/"),
    (r"\.cursor/worktrees/", ".claude/worktrees/"),
    (r"\.cursor/settings", ".claude/settings"),
    (r"\.cursor/benny/", ".claude/benny/"),
    (r"\.cursor-plugin", ".claude-plugin"),
    (r"\.cursor\b", ".claude"),

    # --- branding ---
    (r"\bpstack\b", "ownstack"),
    (r"\bPstack\b", "Ownstack"),
    (r"\bPSTACK\b", "OWNSTACK"),
    (r"/poteto-mode", "/ownstack-mode"),
    (r"\bpoteto-mode\b", "ownstack-mode"),
    (r"\bpoteto-agent\b", "ownstack-agent"),
    (r"\bPoteto Mode\b", "Ownstack Mode"),
    (r"\bpoteto's\b", "ownstack's"),
    (r"\bPoteto\b", "Ownstack"),
    (r"\bpoteto\b", "ownstack"),

    # --- bundled tooling package name ---
    (r"@cursor-skill/", "@ownstack-skill/"),

    # --- install commands ---
    (r"/add-plugin ownstack", "/plugin install ownstack@ownstack"),

    # --- Claude Code agent API ---
    (r"\bgeneralPurpose\b", "general-purpose"),
    (r"\bis_background: true\b", "background: true"),
    (r'`subagent_type: "Comment Sicko"`', '`subagent_type: "comment-sicko"`'),
    (r"\bTask subagent\b", "Agent subagent"),
    (r"\ba `Task` subagent\b", "an Agent subagent"),

    # --- Cursor built-ins -> Claude Code equivalents ---
    (r"Cursor's built-in `create-skill` skill \(Cursor's built-in for authoring SKILL\.md files\)",
     "the `skill-creator` skill"),
    (r"the \*\*create-skill\*\* skill \(Cursor's built-in for authoring SKILL\.md files\)",
     "the `skill-creator` skill"),
    (r"Cursor's built-in `create-skill` skill", "the `skill-creator` skill"),
    (r"Cursor's built-in `create-skill`", "the `skill-creator` skill"),
    (r"routes through Cursor's built-in `create-skill`", "routes through the `skill-creator` skill"),
    (r"through Cursor's built-in `create-skill` flow", "through the `skill-creator` flow"),

    (r"Cursor's `/loop` command \(a built-in, not a ownstack skill\)",
     "the `/loop` skill (a Claude Code built-in, not an ownstack skill)"),
    (r"`/loop` is Cursor's built-in wake mechanism, not a ownstack skill",
     "`/loop` is a Claude Code built-in wake mechanism, not an ownstack skill"),
    (r"Cursor's `/loop` command", "the `/loop` skill"),
    (r"cursor's `/loop` command", "the `/loop` skill"),

    (r", and not Cursor's built-in babysit skill, whose description matches the same words\.", "."),
    (r", not Cursor's built-in babysit skill, whose description matches the same words\.", "."),
    (r" This playbook replaces Cursor's built-in babysit skill for these requests, so do not route there even though its description matches the same words\.", ""),

    # --- cursor-team-kit -> Claude Code skills ---
    (r"a slop-strip \(the `deslop` skill from the `cursor-team-kit` plugin \(`/deslop`\)\)", "a slop-strip (`/simplify`)"),
    (r"the `deslop` skill from the `cursor-team-kit` plugin \(`/deslop`\)", "the `/simplify` skill"),
    (r"Run `/deslop` from `cursor-team-kit` over the diff before commit", "Run `/simplify` over the diff before commit"),
    (r"runs `/deslop` on the diff before each commit", "runs `/simplify` on the diff before each commit"),
    (r"`/deslop` ships in the `cursor-team-kit` plugin, not in ownstack\. If you don't have it, ask",
     "`/simplify` is a Claude Code built-in. If it is unavailable, ask"),
    (r"`/deslop`", "`/simplify`"),

    (r"`control-ui` or `control-cli` from `cursor-team-kit` as the change demands",
     "the `claude-in-chrome` skill for web UIs or the `run` skill for CLIs, as the change demands"),
    (r"`control-cli` or `control-ui` from `cursor-team-kit` as the change demands",
     "the `run` skill for CLIs or the `claude-in-chrome` skill for web UIs, as the change demands"),
    (r"Browser, Electron, and web UIs use `control-ui` from `cursor-team-kit`\. CLIs and TUIs use `control-cli` from `cursor-team-kit`\.",
     "Browser and web UIs use the `claude-in-chrome` skill. CLIs and TUIs use the `run` skill."),
    (r"with the matching control skill, such as `control-cli` or `control-ui` from `cursor-team-kit`, or a named driver where none exists",
     "with the matching skill, such as `run` for CLIs or `claude-in-chrome` for web UIs, or a named driver where none exists"),
    (r"each a Cursor cloud agent, each exercising the real surface with the matching control skill \(such as `control-ui` or `control-cli` from `cursor-team-kit`\)",
     'each in its own worktree (`isolation: "worktree"`), each exercising the real surface with the matching skill (such as `claude-in-chrome` for web UIs or `run` for CLIs)'),
    (r"Drive through `control-ui` or `control-cli` from `cursor-team-kit`\.",
     "Drive through the `claude-in-chrome` skill or the `run` skill."),
    (r"`control-ui` or `control-cli` runtime verification \(from `cursor-team-kit`\)",
     "browser or CLI runtime verification (`claude-in-chrome`, `run`)"),
    (r"the matching control skill \(such as `control-ui` or `control-cli` from `cursor-team-kit`\)",
     "the matching skill (such as `claude-in-chrome` for web UIs or `run` for CLIs)"),
    (r"its control skill \(such as `control-ui` or `control-cli` from `cursor-team-kit`\)",
     "its matching skill (such as `claude-in-chrome` for web UIs or `run` for CLIs)"),
    (r"Name the real path, such as `control-cli`, `control-ui`, or the targeted tests\.",
     "Name the real path, such as the `run` skill, the `claude-in-chrome` skill, or the targeted tests."),
    (r"`cursor-team-kit` publishes `control-cli` \(CLIs and TUIs\) and `control-ui` \(browser / Electron / web UIs\)\.",
     "Use the `run` skill for CLIs and TUIs, and the `claude-in-chrome` skill for browser and web UIs."),

    # --- cloud agents -> local subagents ---
    (r"Each owner is a Cursor cloud agent that", 'Each owner is a background subagent in its own worktree (`isolation: "worktree"`) that'),
    (r"each a Cursor cloud agent", "each a background subagent"),
    (r"One Cursor cloud agent per PR", "One background subagent per PR"),
    (r"Each live lane runs on its own cloud VM at the PR head",
     "Each live lane runs in its own git worktree at the PR head"),
    (r"the cloud agent's status in the Cursor dashboard", "the background task status via `/tasks`"),
    (r"After a Cursor restart: local agents are dead, cloud work is not\.",
     "After a session restart: in-process subagents are dead, pushed branches and open PRs are not."),
    (r"a Cursor restart", "a session restart"),
    (r'"restart Cursor"', '"restart Claude Code"'),

    (r'Always `environment: "cloud"` unless the task needs this machine',
     'Always `isolation: "worktree"` for writers unless the task needs shared local state'),
    (r"Cloud agents cannot read the local store, so their briefs inline what they need or point at repo paths\.",
     "Worktree agents see an isolated checkout, so their briefs inline what they need or point at repo paths."),
    (r'Spawn all N workers in one message with `subagent_type: general-purpose`, `environment: "cloud"`, `run_in_background: true`, and the step 4 model, left unset for `auto` or `inherit-parent`\. Use `environment: "local"` only when the worker needs access to something on the user\'s computer\.',
     'Spawn all N workers in one message (independent Agent calls in a single response run concurrently) with `subagent_type: general-purpose` and the step 4 model, left unset for `inherit`. Give a writer `isolation: "worktree"` so parallel workers do not fight over the same checkout; leave it off when the worker needs the live working tree.'),
    (r"\*\*Defaults for every `Task` call\.\*\* `run_in_background: true`, agent mode \(readonly strips MCP\), file",
     "**Defaults for every Agent call.** Launch independent agents in one message so they run concurrently, file"),
    (r"Spawn all N subagents in one message with `run_in_background: true`, each with the task",
     "Spawn all N subagents in one message so they run concurrently, each with the task"),
    (r"a role line of `inherit-parent` or `auto` runs that role on the parent chat model \(omit Task `model`\)",
     "a role line of `inherit` runs that role on the parent session model (omit the Agent `model` field)"),

    # --- MCP discovery ---
    (r"list the available MCPs from the Cursor environment\. Use the available-tools map when present\. Otherwise inspect the `mcps/` directory Cursor exposes for enabled MCP servers\.",
     "list the available MCP servers from the session tool list. Use the available-tools map when present. Otherwise check `.mcp.json` and the configured MCP servers for this project."),

    # --- benny / Slack ---
    (r"Prefer configured Cursor Slack actions", "Prefer configured Slack MCP actions"),
    (r"Never build or open a Cursor protocol deep link\. ", ""),
    (r"the user's Cursor model picker or supported model list", "the models available to this session"),
    (r"two live Cursor automations", "two live scheduled agents"),
    (r"two cursor automations", "two scheduled agents"),
    (r"The human enters setup by pointing Cursor at", "The human enters setup by pointing Claude Code at"),
    (r"the human enters setup by pointing cursor at this file",
     "the human enters setup by pointing Claude Code at this file"),
    (r"i want two cursor automations that work together in one slack issue channel",
     "i want two scheduled agents that work together in one slack issue channel"),
    (r"point cursor at", "point Claude Code at"),

    # --- Cursor-only local paths ---
    (r"`~/Library/Application Support/Cursor` \(`state\.vscdb\.backup`, and `snapshots/roots/<root>` where a `<root>` named for a folder you opened as a workspace balloons\)[;,] ", ""),
    (r"If Cursor also exposes a models API or CLI that lists the user's entitled models, prefer it for completeness\. ", ""),

    # --- names that must be kebab-case in Claude Code ---
    # An agent whose `name` is not kebab-case is silently skipped at load time.
    (r"^name: Comment Sicko$", "name: comment-sicko"),
    (r"^(description: A deranged comment-hater that savors deletion and condemns workaround code\.)$",
     "description: A deranged comment-hater that savors deletion and condemns workaround code.\ncolor: red"),
    (r"^name: Ownstack Mode$", "name: ownstack-mode"),

    # --- install / setup docs ---
    (r"In a Cursor chat, run:", "In Claude Code, run:"),
    (r"Cursor confirms the plugin is installed\.", "Claude Code confirms the plugin is installed."),
    (r"^/plugin install ownstack@ownstack$",
     "/plugin marketplace add tomasvit6/ownstack\n/plugin install ownstack@ownstack"),
    (r"It writes `~/\.claude/ownstack-models\.md`, a small rule every ownstack skill reads\.",
     f"It writes `{CONFIG}`, a small config file the ownstack skills read. Each Claude Code profile (`CLAUDE_CONFIG_DIR`) keeps its own."),
    (r"Set a role to `inherit-parent` or `auto` and ownstack omits the subagent `model` field, so the subagent inherits your parent chat model\. Both values mean the same thing, and neither is a model slug\.",
     "Set a role to `inherit` and ownstack omits the subagent `model` field, so the subagent runs on your parent session's model."),
    (r"After setup, start a new chat\. The model rule applies to new sessions\.",
     "After setup, start a new session so the config is in context."),

    # --- models: cross-vendor -> Claude families, by tier ---
    # Upstream's Claude model keeps its family and effort. Its fast code model
    # maps to sonnet one effort step lower, as the cheap tier.
    (r"Families go by prefix: `claude-\*`, and `grok-\*` with `cursor-grok-\*` and `composer-\*`\.",
     "Families go by model name: `fable`, `opus`, `sonnet`, `haiku`."),
    (r" A refused `composer-\*` entry runs on `grok-4\.7-xhigh-fast`\.", ""),
    (r" A refused `composer-\*` entry runs on Reviewer B's default\.", ""),
    *[(rf"`claude-opus-5-5-{e}`", f"`opus` at `{e}` effort") for e in EFFORTS],
    *[(rf"\bclaude-opus-5-5-{e}\b", f"opus:{e}") for e in EFFORTS],
    (r"`grok-4\.7-xhigh-fast`", "`sonnet` at `high` effort"),
    (r"`grok-4\.7-medium-fast`", "`sonnet` at `medium` effort"),
    (r"\bgrok-4\.7-xhigh-fast\b", "sonnet:high"),
    (r"\bgrok-4\.7-medium-fast\b", "sonnet:medium"),

    # --- transcripts: Cursor's agent-transcripts/ -> Claude Code's project dir ---
    # Claude Code keeps a session at ~/.claude/projects/<slug>/<session-id>.jsonl
    # and its subagents at <session-id>/subagents/*.jsonl. The system prompt does
    # not name the directory, so the rules spell out the slug.
    (r"Transcripts live at `~/\.claude/projects/<slug>/agent-transcripts/<uuid>/<uuid>\.jsonl`, where `<slug>` is the workspace path with the leading slash dropped and each \"/\" turned into \"-\" \(so `/Users/you/proj` becomes `Users-you-proj`\)\. Every line is one chat message\.",
     "Transcripts live at `~/.claude/projects/<slug>/<session-id>.jsonl`, where `<slug>` is the workspace path with every non-alphanumeric character turned into \"-\" (so `/Users/you/proj` becomes `-Users-you-proj`). Subagent chats sit under `<session-id>/subagents/`. Every line is one event, and chat messages are the `\"type\":\"user\"` and `\"type\":\"assistant\"` lines."),
    (r"The parent finds its own transcript file before fanning out\. The system prompt names the active workspace's `agent-transcripts/` directory\. Use that path\.",
     "The parent finds its own transcript file before fanning out. It is `~/.claude/projects/<slug>/$CLAUDE_CODE_SESSION_ID.jsonl`, where `<slug>` is the directory the session started in with every non-alphanumeric character turned into `-`. Use that directory."),
    (r"ls -t <agent-transcripts>/\*\.jsonl <agent-transcripts>/\*/\*\.jsonl <agent-transcripts>/\*/subagents/\*\.jsonl 2>/dev/null \| head -10",
     "ls -t ~/.claude/projects/<slug>/$CLAUDE_CODE_SESSION_ID.jsonl ~/.claude/projects/<slug>/*.jsonl 2>/dev/null | head -10"),
    (r"Three transcript layouts: legacy flat \(`<id>\.jsonl`\), current nested \(`<id>/<id>\.jsonl`\), and subagent \(`<parent>/subagents/<child>\.jsonl`\)\.",
     "Two transcript layouts: session (`<id>.jsonl`) and subagent (`<id>/subagents/<child>.jsonl`)."),
    (r"For each candidate, read the first JSONL line and check that `message\.content\[0\]\.text` contains the conversation's opening user prompt\. Take the matching path\.",
     "Take `$CLAUDE_CODE_SESSION_ID.jsonl` when that variable is set. Otherwise, for each candidate, find the first `\"type\":\"user\"` line and check that its `message.content` holds the conversation's opening user prompt. Take the matching path."),
    (r"The system prompt names the workspace's `agent-transcripts/` directory\. Use only that path\.",
     "They live in `~/.claude/projects/<slug>/`, where `<slug>` is the directory the session started in with every non-alphanumeric character turned into `-`. Use only that directory."),
    (r"Read this run's transcript under the active workspace's `agent-transcripts/` directory \(the system prompt names the path\)\.",
     "Read this run's transcript, `~/.claude/projects/<slug>/$CLAUDE_CODE_SESSION_ID.jsonl` (`<slug>` is the directory the session started in with every non-alphanumeric character turned into `-`)."),
    (r"under the active workspace's `agent-transcripts/` directory \(the system prompt names this path\)",
     "in this project's transcript directory, `~/.claude/projects/<slug>/` (`<slug>` is the directory the session started in with every non-alphanumeric character turned into `-`)"),
    (r"under the active workspace's `agent-transcripts/` directory \(the system prompt names the path\. ",
     "in this project's transcript directory, `~/.claude/projects/<slug>/` (`<slug>` is the directory the session started in with every non-alphanumeric character turned into `-`. "),
    (r"find this conversation's transcript in the `agent-transcripts/` directory the system prompt names\.",
     "find this conversation's transcript, `~/.claude/projects/<slug>/$CLAUDE_CODE_SESSION_ID.jsonl` (`<slug>` is the directory the session started in with every non-alphanumeric character turned into `-`)."),
    (r"Reading local transcripts under `agent-transcripts/`\.", "Reading local transcripts under `~/.claude/projects/`."),

    # worktree-audit.sh: Claude Code names a project dir after the whole path,
    # and a worktree session gets its own dir (<repo-slug>--claude-worktrees-*),
    # so search the repo's dir and every dir that extends it.
    (r"# Transcripts dir: ~/\.claude/projects/<slugified-repo-path>/agent-transcripts\.",
     "# Transcript dirs: ~/.claude/projects/<slug>*, the repo's own and its worktrees'."),
    (r"slug=\$\(printf '%s' \"\$main_wt\" \| sed 's#\^/##; s#/#-#g'\)",
     "slug=$(printf '%s' \"$main_wt\" | sed 's#[^A-Za-z0-9]#-#g')"),
    (r"transcripts=\"\$HOME/\.claude/projects/\$slug/agent-transcripts\"",
     "transcripts=(\"$HOME/.claude/projects/$slug\"*)"),
    (r"if \[ -d \"\$transcripts\" \]; then", "if [ -d \"${transcripts[0]}\" ]; then"),
    # ripgrep is not guaranteed on PATH (Claude Code bundles its own, visible
    # only inside its shell), so search with grep, which matches the same
    # fixed strings.
    (r"rg -l -e \"\$\{wt\}/\" -e \"\$\{wt\}\\\"\" \"\$transcripts\" 2>/dev/null",
     "grep -rlF --include='*.jsonl' -e \"${wt}/\" -e \"${wt}\\\"\" \"${transcripts[@]}\" 2>/dev/null"),

    # --- whole paragraphs about Cursor-only features ---
    # Matched exactly, so an upstream edit to one stops matching and the leak
    # guard flags the paragraph for a fresh port.
    (re.escape("To keep `/ownstack-mode` on for the whole chat, pick it from the `/` menu with Option+Enter (Mac) or Alt+Enter (Windows) instead of Enter. That makes it a [Custom Mode](https://cursor.com/docs/skills), which stays in context on every turn until you exit it. Custom Modes are available in the Agents Window and the CLI. Plain Enter attaches the skill to one message, and it fades as the chat moves on."),
     "`/ownstack-mode` attaches the skill to the message you send it with, and it fades as the chat moves on, so start each new task with `/ownstack-mode`."),
    (re.escape("The cleanest isolation is a [cloud subagent](https://cursor.com/docs/subagents#cloud-subagents). Each one gets its own VM and branch, so it can install dependencies, run your app, and record video of the result without touching your machine. Type `/in-cloud` before the task, or ask the parent chat to hand work to cloud subagents."),
     'The cleanest isolation is a worktree subagent. Spawned with `isolation: "worktree"`, each one gets its own checkout and branch, so its edits and build output stay out of your working tree. Ports and other machine-wide state are still shared, so give each agent its own port. Ask the parent chat to hand work to worktree subagents.'),
    (r"or that you're about to go offline or restart Cursor\.", "or that you're about to go offline or restart Claude Code."),
    (re.escape("A [Cursor Project](https://cursor.com/blog/projects) gives one coordinator agent a persistent thread. The coordinator doesn't write code. It directs subagents, which run in the cloud by default, so the work continues when your laptop is closed."),
     "A long-running Claude Code session can be the coordinator. The coordinator doesn't write code. It directs subagents, which run on this machine, so keep the machine awake, or run the coordinator as a cloud session on claude.ai/code so the work continues when your laptop is closed."),
    (re.escape("**Match the model to the job.** Before each spawn, start from the role's line or default and pick the reasoning level and speed the job needs. The `/setup-ownstack` budget sets each role's starting level, xhigh by default. Raise it one step, up to max, for the hardest or subtlest work. Lower it one step for judgment and two or more steps for routine work. Use fast mode only when the job is urgent, meaning CI or trunk is red or a person is blocked on the result right now. Otherwise use standard speed, the same slug without `-fast`. Verification is the exception and stays on the `swarm workers` model and speed (`sonnet` at `high` effort by default). Change only the effort level and whether the slug is fast, and keep the family the role names, so a diverse panel stays diverse. If the family has no slug at that level and speed, use its nearest slug. A role on `auto` or `inherit-parent` stays on the parent model. If the Task tool rejects the adjusted slug, do not try another adjusted slug. Use the role's line or default and say so."),
     "**Match the model to the job.** Before each spawn, start from the role's line or default and pick the effort the job needs. The `/setup-ownstack` budget sets each role's starting effort. Raise it one step, up to `max`, for the hardest or subtlest work. Lower it one step for judgment and two or more steps for routine work. Verification is the exception and stays on the `swarm workers` value (`sonnet` at `high` effort by default). Change only the effort, and keep the model the role names, so a diverse panel stays diverse. A role on `inherit` stays on the parent model. If the Agent tool rejects the adjusted value, do not try another. Use the role's line or default and say so."),

    # --- Cursor speed tiers: Claude Code subagents have no per-call fast mode ---
    (r"reasoning level and fast or standard speed", "effort"),

    # --- model config wording ---
    (r"in the `ownstack-models\.mdc` rule", f"in `{CONFIG}`"),
    (r"in the `/setup-ownstack` rule", "in the `/setup-ownstack` config"),
    (r"If the rule or that line is missing", "If the file or that line is missing"),
    (r"if the rule or the line is missing", "if the file or the line is missing"),
    (re.escape('- **Treating `auto` as a model slug.** `auto` and `inherit-parent` mean "omit the model field so the subagent inherits the parent chat model."'),
     '- **Treating `inherit` as a model slug.** `inherit` means "omit the model field so the subagent runs on the parent session model."'),
    (r"an `auto` or `inherit-parent` entry", "an `inherit` entry"),
    (r"`auto` or `inherit-parent`", "`inherit`"),
    (r"`inherit-parent` or `auto`", "`inherit`"),
    (r"the parent chat model", "the parent session model"),
]

# Frontmatter keys Claude Code does not support (silently ignored, but removed
# so the files stay honest about what actually applies).
DROP_FRONTMATTER_KEYS = ["mode", "icon", "color", "reminder", "paths"]

# Code files that get the text rules too. Kept narrow: SUBS is written for prose.
SCRIPT_SUFFIXES = {".mjs", ".sh"}

# Anything matching these AFTER transformation means the ruleset missed something.
# The script refuses to write when it sees one, so an unrecognised upstream
# phrase fails loudly instead of landing in the repo off-brand or unportable.
LEAK_PATTERNS = [
    (r"(?i)\bpoteto\b", "upstream branding"),
    (r"(?i)\bpstack\b", "upstream branding"),
    (r"(?i)cursor-team-kit", "Cursor-only plugin"),
    (r"(?i)\bcursor\b", "Cursor reference"),
    (r"\.cursor\b", "Cursor path"),
    (r"\bgeneralPurpose\b", "invalid subagent_type (must be kebab-case)"),
    (r"\bis_background\b", "invalid agent key (use `background`)"),
    (r'environment:\s*"(cloud|local)"', "not a Claude Code Agent parameter"),
    (r"\brun_in_background\b", "not a Claude Code Agent parameter"),
    (r"\bgrok-[\d.]+-\w", "non-Claude model slug"),
    (r"\bgpt-[\d.]+-\w*(sol|max|mini|nano)", "non-Claude model slug"),
    (r"\bclaude-(fable|opus|sonnet|haiku)-[\d-]+-(max|xhigh|high|medium|low|thinking)", "raw upstream model slug"),
    (r"agent-transcripts", "Cursor transcript layout"),
    (r"`-fast`|standard speed|\bfast mode\b", "Cursor speed tier"),
    (r"`inherit-parent`|`auto` entry", "Cursor model alias (use `inherit`)"),
    (r"/add-plugin", "Cursor install command"),
    (r"/deslop", "Cursor-only skill"),
    (r"\bcontrol-(ui|cli)\b", "Cursor-only skill"),
]

# Substrings that legitimately contain a leak pattern and are not leaks.
LEAK_ALLOW = [
    "upstack",          # stacked-PR jargon, unrelated to pstack
    "cursor location",  # the text cursor, not the editor
    "precursor",
    # our own attribution lines name the upstream project on purpose
    "used under the mit license",
    "github.com/cursor/plugins",
]


def find_leaks(text: str, rel: str):
    """Report upstream-specific text that survived the transform."""
    hits = []
    for line_no, line in enumerate(text.split("\n"), 1):
        low = line.lower()
        if any(a in low for a in LEAK_ALLOW):
            # strip the allowed words, then re-test the remainder
            probe = low
            for a in LEAK_ALLOW:
                probe = probe.replace(a, "")
        else:
            probe = line
        for pat, why in LEAK_PATTERNS:
            if re.search(pat, probe):
                hits.append((line_no, why, line.strip()[:100]))
                break
    return hits


def transform_text(text: str) -> str:
    for pattern, repl in SUBS:
        text = re.sub(pattern, repl.replace("\\", "\\\\"), text, flags=re.M)
    return text


def strip_unsupported_frontmatter(text: str, rel: str) -> str:
    """Remove Cursor-only frontmatter keys from the leading --- block."""
    if not text.startswith("---"):
        return text
    end = text.find("\n---", 3)
    if end == -1:
        return text
    head, body = text[3:end], text[end:]
    kept = []
    for line in head.split("\n"):
        key = line.split(":", 1)[0].strip()
        # comment-sicko keeps a color; it is a valid Claude Code agent key
        if key in DROP_FRONTMATTER_KEYS and not rel.startswith("agents/"):
            continue
        kept.append(line)
    return "---" + "\n".join(kept) + body


def map_path(rel: str) -> str:
    for src, dst in PATH_RENAMES:
        if rel == src or rel.startswith(src + "/"):
            return dst + rel[len(src):]
    return rel


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--upstream", required=True,
                    help="path to a checkout of cursor/plugins, or its pstack/ dir")
    ap.add_argument("--check", action="store_true",
                    help="report what would change without writing")
    args = ap.parse_args()

    up = Path(args.upstream).resolve()
    if (up / "pstack").is_dir():
        up = up / "pstack"
    if not (up / "skills").is_dir():
        print(f"error: {up} does not look like pstack (no skills/)", file=sys.stderr)
        return 2

    root = Path(__file__).resolve().parent.parent
    dest_root = root / "ownstack"

    changed, added, hand, dropped, leaks = [], [], [], [], []

    for src in sorted(up.rglob("*")):
        if not src.is_file():
            continue
        rel = str(src.relative_to(up))
        if rel.startswith(".git/") or "/.git/" in rel:
            continue
        if any(rel.startswith(d) for d in DROPPED):
            dropped.append(rel)
            continue
        # the upstream manifest is replaced by our own
        if rel.startswith(".cursor-plugin/") or rel == "plugin.json":
            continue
        if rel in {".gitignore"} or rel.startswith("assets/"):
            continue

        out_rel = map_path(rel)
        dest = dest_root / out_rel

        if out_rel in HAND_WRITTEN:
            if dest.exists():
                hand.append(out_rel)
            continue

        audited = False
        if src.suffix.lower() in SCRIPT_SUFFIXES:
            # scripts quote playbook text verbatim (check-plan.mjs asserts the
            # "Ten lanes on <model>" line), so they need the same model rules.
            # `cursor` is a normal identifier in code, so skip that one check.
            text = transform_text(src.read_text(encoding="utf-8"))
            for line_no, why, snippet in find_leaks(text, out_rel):
                if why != "Cursor reference":
                    leaks.append(f"{out_rel}:{line_no}  [{why}]  {snippet}")
            new = text.encode("utf-8")
        elif src.suffix.lower() in {".md", ".json", ".yaml", ".yml", ".mdc", ".txt"}:
            text = src.read_text(encoding="utf-8")
            text = transform_text(text)
            if src.name == "SKILL.md" or rel.startswith("agents/"):
                text = strip_unsupported_frontmatter(text, out_rel)
            if out_rel == "docs/guide/README.md":
                # audit before appending our own attribution footer, which
                # names the upstream project deliberately
                for line_no, why, snippet in find_leaks(text, out_rel):
                    leaks.append(f"{out_rel}:{line_no}  [{why}]  {snippet}")
                text = text.rstrip("\n") + "\n" + GUIDE_FOOTER
                audited = True
            if not audited:
                for line_no, why, snippet in find_leaks(text, out_rel):
                    leaks.append(f"{out_rel}:{line_no}  [{why}]  {snippet}")
            new = text.encode("utf-8")
        else:
            new = src.read_bytes()

        if dest.exists():
            if dest.read_bytes() != new:
                changed.append(out_rel)
                if not args.check:
                    dest.write_bytes(new)
        else:
            added.append(out_rel)
            if not args.check:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(new)

    if leaks:
        print("UNPORTED UPSTREAM TEXT - the ruleset does not cover these:\n")
        for l in leaks:
            print(f"  {l}")
        print(f"\n{len(leaks)} leak(s). Add rules to SUBS in scripts/port.py,")
        print("or add the file to HAND_WRITTEN / DROPPED if it cannot be ported.")
        if not args.check:
            print("\nRefusing to write. Nothing changed.", file=sys.stderr)
            return 1
        print()

    verb = "would change" if args.check else "changed"
    print(f"{verb}: {len(changed)}")
    for f in changed:
        print(f"  M {f}")
    if added:
        print(f"new upstream files: {len(added)}")
        for f in added:
            print(f"  A {f}")
    if hand:
        print(f"\nhand-written, NOT touched ({len(hand)}) - re-review if upstream moved:")
        for f in hand:
            print(f"  ! {f}")
    if dropped:
        print(f"\ndropped on purpose ({len(dropped)} files):")
        for d, why in DROPPED.items():
            print(f"  - {d}: {why}")

    if not changed and not added:
        print("up to date with upstream.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
