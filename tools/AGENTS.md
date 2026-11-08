# Tooling scope

Follow root AGENTS.md and the relevant `docs/knowledge/` workflow. Tools include destructive historical builders/installers as well as read-only analyzers. Inspect parameters, imports and top-level side effects before invocation or reuse. File names such as `test_`, `validate_` or `current` do not guarantee read-only or current behavior.

Use fresh outputs and exact input inventories. Never rerun old generators against pinned candidates, overwrite source baselines, install frameworks, change the game cache or execute a deployment as an incidental “test.” Load `build_phase2a.ps1` with `-HelpersOnly` and an explicit tool path for its API. Whole-script imports of B5 and other builders can mutate outputs.

For audit tooling, preserve handle identity, nested graphs, actual entry sockets and provider provenance. Report opaque/unsupported input as unknown. Keep depot collisions separate from generated XL phase-node ID collisions. A new comprehensive parity auditor needs its own scope/fixtures; it was not built during instruction maintenance.
