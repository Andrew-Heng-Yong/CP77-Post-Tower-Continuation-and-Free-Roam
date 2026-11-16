# Manual Save 26 CET probe

On 14 November 2026 at 22:34:48 Toronto time, the v0.1.4 native reader logged `PTFR checkpoint probe ready` following the user's report that the MS26 CET command returned `true`. The same log records successful registration at 22:32:15. The installed DLL and history script matched the v0.1.4 manifest. ManualSave-26's `sav.dat` matched the pinned fixture SHA-256 `6BEFAEE9EA1FA77A515C5A1EC9C867EA5B5DACB166D637D24B1423260E9C2AA4`. [Native log](checkpoint.log) · [Installed manifest](../deployment_01/installed_manifest_01.json)

| Native observation | Count |
| --- | ---: |
| Quest phases | 4,061 |
| Live handlers | 10,003 |
| Handler registration slots reported | 10,104 |
| Logical AND state rows | 2,348 |
| Node instance records | 28 |
| Wait handlers observed | 21 |
| Pending notifications | 0 |
| Pending resource requests | 0 |

**Result.** The manual probe passed for this session and completed the transient read of the loaded execution graph. The test covers the reported counts. The user chose to skip the Reed playtest. The live cutoff commit and the dependent post-Tower reload check are deferred. Timer durations and checkpoint persistence remain unverified.
