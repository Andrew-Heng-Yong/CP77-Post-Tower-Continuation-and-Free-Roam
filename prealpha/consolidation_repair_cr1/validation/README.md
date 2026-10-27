# CR1 independent semantic regression checks

These checks use the pre-existing S25, SR1, JD1 and S30 repair contracts and
freshly decode the candidate's serialized resources. They do not import the CR1
builder, invoke historical mutating tests, call game APIs, or write game/save
files. `checks_contract_01.json` pins 70 independent source files.

`test_semantics_01.py` checks 30 groups:

- The complete 1172-resource inventory, all 30 selected corrective payloads,
  1142 unchanged resources, the same 51 install paths, and 50 unchanged
  non-archive install files.
- Yoko's four component choices; Viktor's two native debt options and bounded
  owner guards; Wilson's gun-order dispatch and release/reacquire acknowledgement;
  Fred's native boxing introduction; Bullets' service rearm loop; Dennis' entry
  acknowledgement; shared cleanup and its 17 character branches, NCPD branch and
  inline courier cleanup; and the S25 Delamain controller receipt.
- The original 33 corrective native conditions in 17 resources, including
  adversarial journal states and sibling-receipt values. Runtime history and
  admission safeguards remain byte-identical to S30.
- Retained SR1 MQ058 completion-port and Delamain message/controller repairs,
  the S30 three-job wrappers and native/scene/workspot resources, the English
  48-scene lipmap, and Dennis' initializer ownership restrictions.

The expected regression mode runs the same checks on S30 candidate 02. It must
detect all nine explicitly named repair groups while retaining the three SR1,
S30 and runtime preservation groups. The completed negative control is
`s30_negative_01.json`: 439 assertions evaluated, 27 groups failed as expected,
and all three retained groups passed. Assertions stop within a failing group;
this negative count is not a count of independent gameplay defects.

CR1 candidate 01 passed all 30 groups and 2057 assertions in
`candidate_positive_01.json`, using 38 fresh serialized-resource decodes in
`cr1_positive_readback_01`. The full inventory and unchanged-file checks also
passed. Its status is
`PASS_INDEPENDENT_SEMANTIC_REPAIR_AND_PRESERVATION_NOT_LIVE`.

To validate a successor, first run `decode_checks_01.ps1` with its candidate
root and a fresh output directory name. Then run `test_semantics_01.py` with
that directory's `inventory.json` and a fresh report filename. Add
`--expect-regression` only for the S30 negative control. Existing decode/report
outputs are not overwritten. The candidate root must contain `archive_source`
and `package`; the combined archive is verified separately by the parent build.

This is offline source and serialized-resource validation. It does not establish
engine execution, migration of already serialized quest owners, phone completion,
reward behavior, or save/reload behavior. The complete resource preservation
check covers the all-81 selection without claiming an engine test of all 81 jobs.
The unresolved 11-marker difference is outside this validation's scope.
