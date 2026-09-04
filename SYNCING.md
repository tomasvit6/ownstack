# Staying in sync with upstream

ownstack is a **port**, not a fork with hand-edits. Upstream
[pstack](https://github.com/cursor/plugins/tree/main/pstack) is actively
maintained, so this repo has to absorb its changes without drifting.

## Why not just merge?

The port renames `pstack` → `ownstack` and `poteto-mode` → `ownstack-mode`
throughout, remaps Cursor built-ins to Claude Code ones, and swaps the
multi-vendor model panels for Claude tiers. That touches **61 of 123 files**,
usually on the same lines upstream keeps editing. A plain `git merge upstream`
would conflict almost everywhere, every time.

So the port lives in `scripts/port.py` as a set of rules instead. Updating means
re-running the transform, not resolving conflicts.

## Updating

```bash
# 1. get the current upstream
git clone --depth 1 --filter=blob:none --sparse \
  https://github.com/cursor/plugins.git /tmp/pstack-upstream
cd /tmp/pstack-upstream && git sparse-checkout set pstack && cd -

# 2. see what would change
python3 scripts/port.py --upstream /tmp/pstack-upstream/pstack --check

# 3. apply it
python3 scripts/port.py --upstream /tmp/pstack-upstream/pstack

# 4. review, then commit
git diff
```

`--check` prints a summary and writes nothing:

```
would change: 3
  M skills/arena/SKILL.md
  M skills/how/SKILL.md
new upstream files: 1
  A skills/some-new-skill/SKILL.md

hand-written, NOT touched (3) - re-review if upstream moved:
  ! LICENSE
  ! README.md
  ! skills/setup-ownstack/SKILL.md
```

## What the script will not touch

Three files were written from scratch for this port and are never overwritten.
The script lists them on every run so you can check them by hand when upstream
moves:

| File | Why it is hand-written |
| --- | --- |
| `README.md` | Describes the port itself, not pstack |
| `LICENSE` | Carries the dual copyright notice MIT requires |
| `skills/setup-ownstack/SKILL.md` | Rewritten for Claude Code config; upstream writes a Cursor `.mdc` rule |

`skills/make-bot-ui` is dropped on purpose: it depends on Cursor's
`update_state` routines API, which has no Claude Code equivalent.

## After a sync

Two things are worth checking when the diff is non-trivial:

1. **New skills** land untransformed apart from the text rules. If upstream adds
   a skill that uses a Cursor-only capability, the script cannot know that. Read
   any new `SKILL.md` before shipping it.
2. **New frontmatter keys.** Claude Code silently ignores unknown keys, so a new
   Cursor-only key will not error, it will just do nothing. Check the frontmatter
   on anything new.

Then verify the plugin still loads:

```bash
claude plugin marketplace add .
claude plugin install ownstack@ownstack --scope user
claude -p "/ownstack:unslop" --max-turns 1     # should load the skill
claude plugin uninstall ownstack@ownstack
claude plugin marketplace remove ownstack
```

## Adding a new transform rule

When upstream introduces a phrase the port needs to change (a new Cursor
built-in, a new model slug), add it to `SUBS` in `scripts/port.py` rather than
editing the generated file. Editing the file directly means the next sync
silently reverts it.

Rules are applied in order, so put longer and more specific patterns first.
After adding one, `--check` should come back clean against the current tree.
