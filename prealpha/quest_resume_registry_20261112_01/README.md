# Mid-progress restoration registry

Start with the [current bounded report](report_02/REPORT.md) and [checkpoint](checkpoint.json). The source inventory and stage contexts are built; semantic stage, ownership, support and receipt review remains in progress. This is step 1 of the resume plan, not a deployed resume feature.

The selected roster has 160 jobs and 1,719 authored phase/objective references. Fifteen separately scoped records and 43 additional installed scanner/cyberpsycho activities are accounted separately. Excluded jobs and prerequisite-only references are retained without expanding admission.

## Read-only lookup

From the repository root:

```powershell
& 'C:\Users\Ayong\.local\bin\python3.14.exe' -X utf8 -B prealpha/quest_resume_registry_20261112_01/lookup.py 'Machine Gun' --stage 01_deliver_skippy
& 'C:\Users\Ayong\.local\bin\python3.14.exe' -X utf8 -B prealpha/quest_resume_registry_20261112_01/lookup.py 'The Gig' --stage 02_reward
```

These commands open the checkpoint-selected SQLite files with `mode=ro`. They print source records and make no game, save or workspace writes. Add `--full` for complete stage-site contexts. Required local evidence is ignored game-derived data; a clean checkout alone cannot supply it. The original `query.py` remains pinned historical tooling; use `lookup.py` for the current checkpoint.

## Evidence locations

| Location | Contents |
| --- | --- |
| `registry_02/registry.sqlite3` | Every captured provider, exact parameters, graph edges, journal references, effects, registrations and selection records |
| `routes_02/routes.sqlite3` | Caller-input structural MAY traversal; boundaries retained |
| `contexts_01/contexts.sqlite3` | Stage/site packets and recursive source owner/support scopes for 175 selected/separate records |
| `activities_01/registry.json` | The 26 scanner and 17 cyberpsycho activity roots, with 167 phase/objective references |
| `report_02/interface_review.json` | Follow-up classification of twelve unresolved input-interface cases |
| `contexts_01/verification.json` | Thirteen source readback checks, including actual Machine Gun and The Gig nodes |
| `evidence_05/journal_decode.json` | Bounded base-journal decoder failures; no accepted lossy export |

The context fields describe source connectivity. They do not assert required live actors, earned prerequisites, paid rewards, simultaneous objectives or safe resume entrances. The source registry preserves full typed parameters for that review. Keep exact provider/graph/node identities when adding reviewed contracts.

Preparation/capture/analysis scripts are recorded engineering tools, not rerunnable setup instructions. They create named fresh output directories and refuse existing evidence. `finish_pass.py` also advances the analysis checkpoint. No script here installs the mod, launches the game or edits a save. Preserve failed predecessors and use explicit successor output directories for new investigations.
