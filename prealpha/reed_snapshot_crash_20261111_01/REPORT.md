# Reed rooftop crash repair and main-world Johnny installation

11 November 2026. The crash report at 5:01:10 p.m. Toronto time contains a save identical to Manual Save 26. The engine faulted at `Cyberpunk2077.exe+0x4f0e19`, reading `0x14` through a null first operand during a native array search. The second operand in the dump is `q307_point_of_no_return`. This matches the installed snapshot cutoff's `ArrayFindFirst` call in `TryFreeze`. [Crash evidence](crash_evidence.json)

The replacement checks the fact's name only when the sampled value differs. It uses the same row catalogue and compares the name as a CName. Only the expected q307 cutoff transition from 0 to 1 can differ without invalidating a row. The verified value still comes from the pre-ending sample. The capture timing, persistent fields, export format and native ending assets stay the same. [Source patch](source.patch) · [Offline verification](verification.json)

Both requested updates were installed in one transaction. The snapshot REDscript contains the crash repair. The combined archive contains the seven audited post-Tower Johnny removal routes. The archive has 1,737 members. The other 49 Core files match the previous installation. [Johnny changes](../johnny_main_world_removal_20261111_01/REPORT.md) · [Installed manifest](deployment_01/installed_manifest_01.json)

All 148 registered REDscript sources compiled offline. The fact comparison checks covered all 158 snapshot rows and 4,715 fact fields. Twelve transaction fixture actions passed, including recovery from an interruption between the two replacements. The installed check verified all 51 Core paths, the 26 dependencies, all 316 save files, and rollback copies for both replaced files. [Transaction fixtures](fixture_results.json) · [Rollback readiness](deployment_01/rollback_readiness.json)

The next live check is the Reed call and snapshot export from Manual Save 26. The post-Tower encounter cuts also await gameplay validation.
