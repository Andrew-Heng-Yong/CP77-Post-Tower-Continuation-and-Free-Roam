# Restriction profile scope

Follow root AGENTS.md, `README.md` in this directory and `docs/knowledge/invariants.md`. `active.json` selects the actual installed-design profile; the proposed three-way product selector is not implemented merely by being described in old prose.

Profile/catalogue edits are runtime behavior changes, not documentation maintenance. Preserve module containment, schema, reviewed perk dependencies, item-versus-functional permission distinction and conservative save migration. Unknown catalogues stop a migration before mutation; unknown cyberware must not cause owned-item destruction. Changing a selector/module requires generation, validation, current-input compilation and separately authorized deployment. Do not rewrite Tower/Relic story state or silently change no-vitals behavior.
