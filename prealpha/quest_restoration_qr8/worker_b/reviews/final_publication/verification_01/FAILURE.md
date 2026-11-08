Initial private checker stopped before the full pass because work_queue was
newly included by publication02 and had no corresponding publication01 entry.
Its preserved old snapshot is still hash-verified; only the checkpoint had a
prior-publication pin. The checker was also aligned with actual presentation
stage and newly corrected checkpoint field names before attempt02. No canonical
input changed because of this private checker failure.
