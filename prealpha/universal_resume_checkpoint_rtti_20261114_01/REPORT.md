# Execution checkpoint registration repair

14 November 2026. The startup log from candidate 02 shows that RED4ext loaded the plugin and then rejected two unresolved native functions. The plugin stopped at a combined type and property check. That log leaves the exact rejected lookup unknown. The installed game is running the verified RD10 rollback. [Startup and rollback evidence](../universal_resume_checkpoint_repair_20261114_01/REPORT.md)

The workspace repair reuses the game’s own strong-handle descriptors from the three system getters on ScriptGameInstance. The native MultiSelectCovers.selectedCovers property supplies the dynamic Uint64 array descriptor for capture and decode. Each descriptor is checked for its ABI shape before it is used to construct either global signature. The registrar reports individual descriptor and property failures. Capture becomes available after both functions read back from the registry and the runtime hooks are ready. [Registration code](RegisterReader.inc) · [Descriptor checks](CheckpointRegistration.hpp)

## Offline verification

- All 148 sources compiled against the restored RD10 registry. Reading the compiled definitions confirmed that the quest, delay and clock parameters reference the same types as the stock getter results. The capture presentation and result and the decoder input reference the exact array type used by the stock property. [Compile and signature readback](compile_02/receipt.json)
- Twenty-three registration fixture checks passed. The fixture hides all four compound type names used by candidate 02 and supplies the stock descriptors. The checks cover both complete signatures and rejection of mismatched, missing and ambiguous descriptors. Six anchors in the pinned game executable tie the stock class, function and property names to native registration sites. [Registration fixture results](checks_02/results.json)
- Forty-one checkpoint fixtures passed with the revised DLL source. The candidate pairs the new DLL with the previously verified history and recovery script bytes. The current 51 RD10 Core files and 26 dependencies verified before and after the workspace checks. [Candidate receipt](candidate_02/receipt.json)

Live startup and capture and reload through a genuine Tower run are pending. The staged DLL is the registration repair. The earlier logging-only probe remains on disk as evidence of the separate diagnostic work.
