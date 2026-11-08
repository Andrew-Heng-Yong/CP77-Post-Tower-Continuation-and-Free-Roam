# Killing in the Name retained Bartmoss messages

## Finding

The November 4 AutoSave-8 contains `mq018_started=1` and `mq018_active=1`. The original body writes both before entering the messages phase. QR18 requires both to be zero at the S29 script gate and the two private graph checks. No private Issued or Entered record is present in this body. Nancy’s existing private controller also waits for the S29 Permit before claiming its own receipt.

The October 26 AutoSave-16 backup from the same playthrough retains the original MQ018 phase and message-phase slots, plus the original final-message visited and read listeners at `[0,2,82,6,37,7]:67/69`. Their saved event slots are `5416` and `5900`. The newer AutoSave-8 retains both path names but has no original MQ018 slots in either the event registry or phase freezer. This demonstrates a lost wait in the compared save evidence. The two files have different point-of-no-return IDs, so the comparison does not establish uninterrupted ancestry. The current SMS journal states were not decoded from disk. [Saved and source evidence](evidence_01.json)

Every Breath You Take is a separate completed history. The user reported completing it before the ending. The October 26 backup and November 4 body both list `mq028` in finished-quest metadata, and the latter stores `mq028_done=1`. Its entry, main graph, Blue Moon controller and S29 conditions for this quest are preserved.

## QR19 candidate

On a genuine post-Tower save, the new branch accepts a narrow message-stage history with `mq018_started=1` and `mq018_active=1`, intact Active Bartmoss texts `01/02/05/06/07`, the original inactive quest and objective checks, untouched website progress, and an unclaimed S29 owner. It requires the five original campaign milestones and retains the common Tower, player, and support gates. Two stable live samples are required. The runtime decision uses each player’s own facts and journal and has no slot, file or snapshot certificate requirement beyond the mod’s existing common startup readiness.

The new input travels through the existing private entry and phase identities into `mq018_01_msgs:67/69`. It rejoins the original XOR at `71`, then the native website activation and Nancy branch. The new path cannot reach the earlier message senders or the original `mq018_active` increment. There are no new native fact, journal, reward, controller or registration writers. Nancy uses the existing S29 phone initializer and PH1/PH3 support. The five original producer routes, website check, Nancy and relay branches, scene adaptations and cleanup are preserved. An incomplete message chain, active website or later progress defers.

## Verification and next evidence

- Three typed resources serialized and read back. The previous guard rejects the retained-message witness and the successor accepts it. Nineteen negative cases and one missing-listener control passed. All original nested graphs and the fresh-start route were compared. [Typed verification](verification.json)
- The full current 148-source offline compile passed. The staged archive and ZIP passed all 1,577 member hashes and 51 package file checks. The two changed package files are the combined archive and S29 script. The archive changes only the three existing private MQ018 depots. Installed QR18, its diagnostics and six protected original save files matched their pins. [Compile](compile_01/result.json) and [package manifest](candidate_01/package_manifest.json)

The candidate is staged. Current quest and message journal values are still needed to qualify AutoSave-8 as a gameplay fixture. Live delivery of the two rearmed listeners, Nancy’s actual callback, world support and save/reload remain untested. No gameplay, installation or save/fact writes were performed.
