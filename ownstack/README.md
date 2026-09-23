# ownstack

**A Claude Code port of [pstack](https://github.com/cursor/plugins/tree/main/pstack) by [Lauren Tan](https://github.com/poteto).**

pstack is a set of rigorous agent workflows for Cursor: principle skills, adversarial review panels, and verification playbooks built around one idea, that if you want to go fast, you go deep first. The original is excellent and it is MIT licensed. It is also Cursor-native, so it does not run in Claude Code as published.

ownstack is that plugin ported: same skills, same playbooks, same thesis, rewritten against Claude Code's plugin format, agent tool, and model lineup. All credit for the design and the writing goes to the original author. See [Attribution](#attribution) and [What changed in the port](#what-changed-in-the-port).

## Install

```bash
/plugin marketplace add tomasvit6/ownstack
/plugin install ownstack@ownstack
```

## Get started

Two steps:

1. Run `/setup-ownstack`, pick a reasoning budget, and pick which models each role uses. Optional; the defaults work.
2. Run `/ownstack-mode` whenever you are doing something that needs rigor.

```
/ownstack-mode the export writes duplicate rows when a retry lands mid-run.
repro first, then fix and verify.
```

You do not name a playbook or list skills. "repro first" and a checkable outcome are all the routing signal `/ownstack-mode` needs: it matches the Bug fix playbook, copies the steps into a todo list, and calls the other skills as each step fires.

New here? The [guide](./docs/guide/README.md) walks through a first real task, from setup and prompting through verification and overnight runs.

## What it is

The entry point is `/ownstack-mode`. It reads your request, picks a playbook, and runs the other skills as the steps need them. Everything else is situational.

Underneath sit 23 `principle-*` skills, one idea each, that the mode navigates into when a decision calls for it: fix root causes, make illegal states unrepresentable, subtract before you add, prove it works. They are the substance of the plugin, and they are what makes the output different from an agent that just writes code quickly.

### Core

| Skill | Use it when |
| --- | --- |
| `/ownstack-mode` | the entry point. picks a playbook and routes the rest. |
| `/architect` | non-trivial work where jumping to code locks in the wrong shape. |
| `/arena` | run N candidates at one task, pick a base, graft in the best of the losers. |
| `/interrogate` | adversarial multi-reviewer pass over a change. |
| `/swarm` | fan out N parallel workers, drain, return one report. |
| `/how` | how does this work, where should this live, which layer owns it. |
| `/why` | why does it work this way, design rationale, regression history. |
| `/teach` | explain a subsystem or change so a person actually understands it. |
| `/figure-it-out` | large migration or ambitious change with no narrower playbook. |
| `/blast-radius` | what could this break outside the diff. |
| `/tdd` | a failing test first, when the test target is cheap and obvious. |
| `/reflect` | review the transcript, route learnings into concrete skill edits. |
| `/recall` | catch me up, where did I leave off. |

### Prose and code hygiene

| Skill | Use it when |
| --- | --- |
| `/unslop` | cut AI tells from any writing. |
| `/technical-writing` | docs, RFCs, readmes, PR descriptions, commit messages. |
| `/no-comments` | strip narrating comments and workaround sermons. |
| `/bro` | restate the last message in plain language. |
| `/typescript-best-practices` | reading or editing TypeScript. |

### Verification and long runs

| Skill | Use it when |
| --- | --- |
| `/create-verification-skill` | the repo has no scripted way to prove UI/CLI/service behavior. |
| `/maintain-verification-skill` | keep that skill and its feature map honest over time. |
| `/show-me-your-work` | a reviewable decision trail for unattended work. |
| `/automate-me` | capture your own working style into a personal `-mode` skill. |
| `/setup-ownstack` | change which model and effort each role uses. |

### Principles

23 `principle-*` skills the mode navigates into as decisions come up. Read them directly if you want the thesis: `principle-fix-root-causes`, `principle-type-system-discipline`, `principle-prove-it-works`, `principle-subtract-before-you-add`, `principle-guard-the-context-window`, and 19 more in [`skills/`](./skills/).

## Agents

- **`ownstack-agent`** runs the whole style end to end. Spawn it with `subagent_type: "ownstack-agent"`. It reads `ownstack-mode` in full, including the principles index, before doing any work. Substituting `general-purpose` skips that read and drifts.
- **`comment-sicko`** is a read-only comment reviewer. Usually invoke it through `/no-comments` rather than directly.

## What changed in the port

Honest accounting of what is different from upstream pstack.

**Mechanical, no behavior change**

- `.cursor/` paths → `.claude/`; `.cursor-plugin/` → `.claude-plugin/` with Claude Code's manifest schema.
- `/add-plugin` → `/plugin marketplace add` + `/plugin install`.
- `subagent_type: generalPurpose` → `general-purpose`. The camelCase form is not valid in Claude Code.
- Agent frontmatter: `is_background` → `background`, and `Comment Sicko` → `comment-sicko`, since Claude Code requires kebab-case agent names and silently skips files that violate it.
- Cursor built-ins remapped to Claude Code equivalents: `create-skill` → `skill-creator`, `/deslop` → `/simplify`, `control-ui` / `control-cli` → the `claude-in-chrome` and `run` skills. `/loop` exists in both.

**Real differences**

- **Model panels are Claude-only now.** Upstream races Opus, GPT, and Grok against each other and leans on cross-vendor disagreement. Claude Code's Agent tool dispatches Claude models only, so each vendor maps to a Claude family by tier: upstream's top judgment model to `fable`, GPT to `opus`, and the fast Grok code model to `sonnet`. Panels keep one entry per family, since the signal is cross-model agreement. The fan-out-and-cross-judge structure is intact; the diversity is intra-Claude and weaker for it. This is the one place the port loses something real.
- **`environment: "cloud"` and `run_in_background` are not Claude Code Agent parameters.** Cloud-agent fan-out became concurrent in-message subagents, with `isolation: "worktree"` where upstream relied on separate VMs to keep writers off each other.
- **`typescript-best-practices` no longer auto-activates.** Upstream used `paths: ["**/*.ts"]` to load it on TypeScript files. Claude Code has no path-triggered skill activation, so it is manual: `/typescript-best-practices`.
- **`/setup-ownstack` writes a plain config file**, not a Cursor always-applied rule. Claude Code does not auto-load arbitrary files, so the skill offers to add one referencing line to your `~/.claude/CLAUDE.md`.
- **`make-bot-ui` was dropped.** It depended on Cursor's `update_state` routines API, which has no Claude Code equivalent. Shipping it would have shipped a skill that cannot run.
- **`automations/benny`** (Slack issue triage) is ported for paths and naming, but it was built for Cursor's hosted automations. Treat it as a starting point, not a working integration.

**How invocation works here**

45 of the 46 skills keep `disable-model-invocation: true` from upstream. In Claude Code that means their descriptions stay out of the model's context, so they never fire on an unrelated prompt. Both intended paths still work, and both were verified against a real install:

- You type `/ownstack:unslop` (or any skill name) and it loads in full.
- `/ownstack-mode` routes into them by file path, the way upstream designed it, so the playbooks and principle skills load without needing the Skill tool.

The tradeoff is that the model will not reach for these skills on its own. That is the intended behavior for a plugin this opinionated.

## Upgrading

A `~/.claude/ownstack-models.md` written before the three-model panels pins the old defaults: four-entry panels with `haiku`, and a `how critics` line the `how` skill no longer reads. Delete those role lines, or delete the file, then run `/setup-ownstack` again. A rerun keeps any role whose value differs from the default.

## Attribution

ownstack is a derivative work of **pstack**, copyright (c) 2026 **Lauren Tan** ([@poteto](https://github.com/poteto)), used under the MIT License. The original lives at [cursor/plugins](https://github.com/cursor/plugins/tree/main/pstack) and its README invites exactly this: "fork it. improve it. make it yours."

The skills, playbooks, principles, and nearly all of the prose are the original author's work. This repository's contribution is the port: the format conversion, the Claude Code capability mapping, and the honest documentation of what did not survive the move.

If you use Cursor, use [pstack](https://github.com/cursor/plugins/tree/main/pstack) directly. It is the original and it will stay ahead of this fork.

The [`LICENSE`](./LICENSE) file retains the original copyright notice, as the MIT License requires.

## License

MIT. See [`LICENSE`](./LICENSE).
