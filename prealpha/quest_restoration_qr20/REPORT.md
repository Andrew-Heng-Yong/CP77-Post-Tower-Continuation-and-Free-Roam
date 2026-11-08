# Bartmoss thread visibility after the Tower

## Live observation and cause

After installing QR19 the user could not see the Bartmoss conversation. The read-only CET screenshot produced:

```text
Contact=1 Thread=2 Final text=2
Ready=1 Permit=1 Issued=1 Entered=1
Nancy=1 Website unlocked=0
```

The screenshot SHA256 is `7E9EC423DE79C050EA634DCE9A670546B6ADC97015138BF7D537CF9C4B9114E2`. It establishes the loaded journal and receipt values. The reply did not independently identify the exact loaded save body. The older same-playthrough body captured for QR19 has both listeners that are connected downstream of the native final text writer. This supports the earlier delivery history. The new screenshot shows the message and thread are still Active while the contact is Inactive. It does not identify which action made the contact inactive. [QR19 saved evidence](../quest_restoration_qr19/evidence_01.json)

The installed QR19 script-cache decompile shows the phone view calling `MessengerUtils.GetSimpleContactDataArray`. That method first sets `context.stateFilter.active = true` and calls `GetContacts`. Only the contacts in that result proceed to child messages and conversation assembly. Its unread filtering is a second, independent filter. An inactive parent is therefore enough to hide an active thread. The native base and EP1-provided base journal variants both define this contact as `Texter`, with default calling disabled. [Decompile provenance](native_ui_01/manifest.json) and [verified filter excerpt](verification.json)

## Bounded script repair

QR20 adds one call on the existing S29 tick. It requires a real post-Tower, started and active MQ018 owner with the existing Issued/Entered and Nancy receipts. The website step must still be untouched. The original S29 sample checks all existing quest state and the five retained texts. The target must be the exact Inactive Bartmoss parent of native type `Texter`, with calling unavailable. The only new mutation activates that contact with `JournalNotifyOption.DoNotNotify`. Once the contact is Active, the code exits without another write.

The same QR19 owner can continue after this change. The patch reuses the retained texts and original listeners, creates no listener or phone controller, marks no text read, and leaves website activation to the authored quest. No new registration, depot, quest fact or persistent field is introduced. The archive and 50 other package paths match QR19 exactly.

The initial SCC attempt rejected a direct enum inequality. The final method uses enum equality helpers and passed the fresh complete 148-source compile. The script allowlist and five negative mutation controls passed. All 51 staged ZIP paths verified, with the QR19 archive and its 1,577-member readback preserved. All 77 installed dependency/Core files and six protected save files matched. [Compile](compile_02/result.json) and [package manifest](candidate_01/package_manifest.json)

## First test after authorized deployment

Load the same post-Tower save and let free roam settle. Open **Phone → Messages**, select **All Messages** if necessary, and check for Bartmoss. Open the existing conversation and note whether the website objective appears. Record any new notification. If the contact appears but the website still fails to activate, the next read-only check is the final message’s actual visited status and the `mq018_visit_website` fact. Runtime contact activation, visible phone listing and the website transition remain unverified until observed.

```lua
do local j,q=Game.GetJournalManager(),Game.GetQuestsSystem(); local c=j:GetEntryByString("contacts/bartmoss","gameJournalContact"); local m=j:GetEntryByString("contacts/bartmoss/bartmoss_spam/msg07","gameJournalPhoneMessage"); print("Contact="..(IsDefined(c) and tostring(j:GetEntryState(c)) or "missing")); print("Read="..(IsDefined(m) and tostring(j:IsEntryVisited(m)) or "missing").." Website unlocked="..tostring(q:GetFactStr("mq018_visit_website"))) end
```
