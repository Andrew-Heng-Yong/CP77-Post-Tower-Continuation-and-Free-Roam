# Beta release and save continuity

The release target set on 23 October 2026 is a complete initial post-Tower
transition and world state, with some selected quests still unavailable and
known bugs documented. A beta save must remain a supported input to the stable
release. This is a release requirement, not a claim that an unbuilt stable
version has already passed an upgrade test.

Housing H1 is installed as build `prealpha/housing_h1/build/h1_02`. Its permanent
v1 format and existing saved identities passed source and compiled checks;
installation left saved games unchanged. It does not publish a beta or declare
all initial-state work complete. Actual transition and save-upgrade fixtures
are still required below.

## Persistent format

Preserve shipped REDscript module/class names and every saved field's name and
type. Preserve existing catalogue fingerprints, array indexing and admission
certificates. Future quest additions belong in a new compatible catalogue or
an explicitly tested migration; replacing a catalogue under an old saved array
is not an upgrade strategy.

Preserve shipped native quest resource paths, injected boot IDs and saved node
identities. Keep old owners available while saves can contain them. Existing
Issued/Started/Completed facts remain meaningful across updates. New owners
must not duplicate an old owner, replay a reward or restart an unfinished job.

Housing adds a permanent `PTFR.Housing.HousingState` system. Its versioned
record stores observed ownership provenance, one-time loss and repurchase
receipts. Loading a save cannot reconstruct a missing receipt from the current
cash balance, erase an uncertain transaction or charge again automatically.
Unknown pre-Tower history is not relabeled as observed history.

One-time arrival, profile refunds, quest rewards and housing loss are separate
transactions. An update must preserve their acknowledgements and completed
stages rather than restarting the initial transition. The working H10 arrival
and camera are retained.

## Required upgrade evidence before a public beta

- Record the exact shipped persistence schema, catalogue mappings, fact
  namespaces, native owner paths and node identities in the release manifest.
- Verify an actual beta save can load with the successor build, both before and
  after a housing purchase, while a restored quest is in progress.
- Check a second load, death/checkpoint recovery and interrupted purchase. Cash,
  ownership, inventory, rewards and quest stage must not be replayed or lost.
- Preserve completed jobs; resume supported unfinished jobs; defer unsupported
  continuation while retaining its progress.
- Test a genuine pre-Tower capture through the ending and initial arrival.
  Development fixture assumptions must not be a public admission path.
- State the supported game/framework versions and any required update order.

Static schema checks and workspace compilation support these checks; they do
not prove the game's save serializer or native owner reload behavior. The
stable release must run the same compatibility checks against retained beta
fixtures before distribution. A future game update may need a separate
compatibility fix; no save-format promise can substitute for that test.

File rollback restores mod files only. It does not reverse actions already
saved in the game. Beta-to-stable support does not imply that an older pre-alpha
or an uninstalled mod can safely interpret a newer save.
