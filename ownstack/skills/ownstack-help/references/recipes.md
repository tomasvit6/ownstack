# Prompts worth copying

Swap in the real paths, skills, and done checks. Informal wording works.

## Understand

- `/ownstack-mode read <thread>. restate the underlying issue in your own words, in plain english.`
- `/in-your-own-words <long or messy ask>`
- `/sharpen <your task>`
- `/ownstack-mode investigate why <symptom>. give me what we know, what data you used, and your best hypotheses. don't change any code yet.`
- `use /how to understand <subsystem>. then use /why to find out why it broke recently.`
- `/recall my work on <topic> from last week, then read <issue>.`
- `/teach me why you implemented it this way and not <other way>. what did you trade off?`
- `/ownstack-mode take over this branch. read the decision log, find what's done, and continue. don't redo finished work.`

## Build

- Bug: `/ownstack-mode <symptom>. repro first, then fix and verify.`
- Bug in an app: `/ownstack-mode repro this with /verify-<app>. if it repros on main, fix it and show me a video as proof.`
- Bug with a cheap test: `/ownstack-mode repro <bug> first. if there's a cheap test path, /tdd it. then fix and rerun.`
- Feature: `/ownstack-mode add <behavior>. <current output> stays byte-identical. verify both.`
- Refactor: `/ownstack-mode move <code> into one module, zero behavior change. record the current output first and prove it's unchanged after.`
- Perf: `/ownstack-mode <operation> takes <time> on <fixture>. trace it, fix the measured cause, show me before and after.`

## Design and plan

- `/ownstack-mode prototype a few options for <feature>. take screenshots or videos for me to compare.`
- `/ownstack-mode we need <feature>. /architect it first, and answer open questions with prototypes. let me review before proceeding.`
- `/ownstack-mode write a tutorial for how i would use <new package> first. then /teach me why it beats the current one.`
- `ask /arena for a second opinion on this thread and our approach.`
- `/ownstack-mode turn this design into a plan. small verifiable PRs, each with its own verification steps.`
- `/ownstack-mode plan the migration of <library> to <target>. small verifiable PRs. the result must match the original exactly, bugs included.`

## Review and ship

- `/interrogate the whole branch, but skeptically. don't change anything yet. no nitpicks unless it's a real bug or regression.` Read the dismissals too.
- `/swarm check every package under <dir> against its check script. one worker per package. one report.`
- `/ownstack-mode open the pr. small ordered commits, evidence in the description.`
- `/ownstack-mode babysit this pr. get it green.` For status only: `/ownstack-mode check on pr <number>. anything outstanding?`
- `/ownstack-mode land the stack.`

## Away and back

- `/ownstack-mode im going to bed. <goal> in a fresh worktree off <base>. done means <checks>. keep a decision log. don't ask me before committing. /loop until done. if you're truly stuck after a few hours, stop and write up why.`
- `/show-me-your-work catch me up on what you did last night.` Read its Attention section first.
- `/ownstack-mode full autopilot on this queue. each item is independent.`
- `/ownstack-mode autopilot these changes but stack them, don't ship. i'll land the stack.`
- `/reflect capture what we learned so the next run doesn't repeat it.` Approve only edits that change a future decision.
- `/bro` restates the last reply in plain words.
