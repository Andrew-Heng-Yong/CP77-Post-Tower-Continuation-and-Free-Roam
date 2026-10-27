# Rejected Raymond admission experiment

`candidate_01` is **not deployable**. It widens `mq040_active` from 0 to 0..1 in the private S29 entry and runtime. The source audit in `prealpha/consolidation_repair_cr1/raymond/assessment_01.md` shows that `mq040_active=1` alone cannot certify retirement of the original MQ040 owner. Starting the private owner could duplicate an active native quest. The candidate also started from S30 and would discard 30 repaired archive resources installed by CR1. `validate_01.py` correctly fails on the installed archive baseline.

The guard changes compiled in an isolated 64-source SCC and the modified CR2W entry read back, but these checks establish syntax and serialization only. **Do not install or distribute this candidate.** The live game remains on CR1.

Current user evidence: Raymond journal inactive, `mq040_active=1`, `mq040_done=0`, `mq040_pepe_intro=0`, `mq040_gangers_scene_done=0`, `elcoyote_barman_default_on=0`, `PTFRB0STPEPE_OwnerActive=0`, `q307_main_game_killed=1`. The quest-system save parser reads the pre-ending and post-ending saves, but the exported `customArray` contains persistent path records; their presence does not prove active execution.

A successor needs an exact, read-only liveness signal for the original MQ040 phase or an acknowledged single-owner retirement seam. It must start from CR1's 51-file package and preserve all 30 CR1 resource repairs.
