# ownstack

A Claude Code port of [pstack](https://github.com/cursor/plugins/tree/main/pstack) by [Lauren Tan](https://github.com/poteto), used under the MIT License.

Rigorous agent workflows for Claude Code: 44 skills covering engineering principles, adversarial review panels, and verification playbooks. The thesis is the original author's, that if you want to go fast, you go deep first.

## Install

```bash
/plugin marketplace add tomasvit6/ownstack
/plugin install ownstack@ownstack
```

Then run `/ownstack-mode` on any task that needs rigor.

Full documentation, the skill catalogue, and an honest account of what changed in the port: **[`ownstack/README.md`](./ownstack/README.md)**.

## Staying current

Upstream pstack is actively maintained. This repo keeps up by **re-deriving** the
port rather than merging: every rename and capability remap lives in
`scripts/port.py`, so pulling upstream changes is one command instead of a
conflict in 60+ files. A weekly GitHub Action opens an issue when upstream moves.

See [SYNCING.md](./SYNCING.md).

## Attribution

All credit for the skills, playbooks, and principles goes to [Lauren Tan](https://github.com/poteto). This repository's contribution is the Claude Code port. If you use Cursor, use [pstack](https://github.com/cursor/plugins/tree/main/pstack) directly.

## License

MIT. See [`LICENSE`](./LICENSE).
