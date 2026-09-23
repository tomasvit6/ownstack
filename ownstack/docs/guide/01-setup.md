# Set up ownstack

In this page you install the plugin, pick which models ownstack uses, and run your first task. Setup is one command plus a short conversation.

## Install the plugin

In Claude Code, run:

```text
/plugin marketplace add tomasvit6/ownstack
/plugin install ownstack@ownstack
```

Claude Code confirms the plugin is installed.

## Pick your models

Run:

```text
/setup-ownstack
```

[`/setup-ownstack`](../../skills/setup-ownstack/SKILL.md) detects the models you have access to, asks for a reasoning budget, shows you each role (code delegates, judgment, the review panels), and asks what you want. Answer the questions. It writes `~/.claude/ownstack-models.md`, a small config file the ownstack skills read.

You only override what you care about. A role with no line in the rule keeps the skill's default. To restore a default, delete that role's line. A rerun of `/setup-ownstack` keeps any role whose model differs from the default. A rule written before 0.15.3 pins the old default models, so delete those role lines, or delete the file, then run `/setup-ownstack` again.

You might be wondering what happens if you use Auto. Set a role to `inherit` and ownstack omits the subagent `model` field, so the subagent runs on your parent session's model. For a panel role the value is a list, and one subagent runs per entry, so the list length sets the panel size. Setup also configures `swarm workers`, the default model for every `/swarm` worker unless a race names a model for each arm.

## Accept the verification offer, or don't

At the end of setup, `/setup-ownstack` looks for a way to prove app behavior in your project, either a `verify-*` skill or an existing harness. If it finds neither, it offers once to generate one with [`/create-verification-skill`](../../skills/create-verification-skill/SKILL.md).

Say yes and it writes `.claude/skills/verify-<app>/`, a project-local skill that teaches agents to drive your app the way a user does. It proves the skill works once before handing it over. Say no and setup moves on. You can run `/create-verification-skill` yourself any time. [Verify and ship](./06-verify-and-ship.md#create-a-project-verification-skill) covers when it earns its place.

After setup, start a new session so the config is in context.

## Run your first task

Pick something real but small, and describe it the way you'd describe it to a colleague:

```text
/ownstack-mode add a --json flag to this command. text output stays byte-identical. verify both.
```

Watch the todo list. Its first items are the matched playbook's steps copied in, the Feature playbook for this prompt. If `/ownstack-mode` skips a step, the step stays in the list with `skip: <reason>`, so you can see what it chose not to do.

From here you can type normal follow-ups. `/ownstack-mode` is sticky. It stays on for the conversation until you opt out by saying so.

Next: [Route work through `/ownstack-mode`](./02-ownstack-mode.md).
