# Final post Tower gig and side job whitelist

21 October 2026

The final broader selection contains **80 gigs and 78 side jobs**. This closes
the title-selection pass: 30 additions and one removal from R5. Full recursive
prerequisite coverage was not established by that pass. Implementation and
playtesting remain separate; editing this list does not activate quests in the
installed mod.

The [complete named catalogue](whitelist_final_r6_catalogue.md) lists every
decision; its membership is unchanged. The current [R6.1 JSON](../research/gig_restoration/lore_whitelists_v6_1_dependencies.json)
also records native journal IDs, prerequisites, reasons and source identities.
[The current-selection pointer](../research/gig_restoration/lore_whitelist_current.json)
identifies R6.1 without rewriting R6 or older inputs used by installed packages.

## Prerequisite completion rule

If a required prerequisite is excluded from restoration, the selected follow-up
may be eligible **only if that prerequisite was genuinely completed before the
Tower ending**, with the required outcome. If it was unfinished, never started,
or its pre-ending completion is unknown, the follow-up stays blocked. Do not
restore the excluded prerequisite, force completion or backdate history to unlock
the child. Completion observed only after Tower does not establish when it happened.

This applies to required excluded ancestors in the actual dependency chain,
preserving native AND/OR conditions. Shared resources alone are not dependencies.
An approved prerequisite can still be played after Tower under its own rules and
unlock its successor normally. The child must itself pass all selection and
native eligibility checks; parent completion is necessary, not sufficient.

For example, Raymond Chandler Evening and Small Man, Big Mouth require the
appropriate pre-ending Heroes completion; later Brendan jobs require the earned
earlier Brendan history. Neither family authorizes replaying the excluded job.
No existing owner or completed reward is cancelled by this policy-only revision.

The earlier 1,903 checks did not verify a complete recursive dependency graph.
That coverage and runtime enforcement remain to be implemented and verified.

## Final scope

Of the 227 reviewed records, 158 are included, 51 are excluded, and 18 belong
to separate activity, world-service or earned-reward tracks. None is left with
an undecided selection status. The other 188 roots in the 415-root native
catalogue are other categories, including main quests and vehicle records;
they are not new side-job admissions.

The existing conservative time-aware alternate is retained with **34 gigs and
29 side jobs**. No new additions were made to that alternate. The broader
list is the implementation target; it permits retiming undated commissions,
not reversing established deaths, endings or fixed historical events.

## Added gigs

- Psychofan
- Going Up or Down?
- Bring Me the Head of Gustavo Orta
- Sr. Ladrillo's Private Collection
- Race to the Top
- Scrolls before Swine
- Family Heirloom
- Greed Never Pays

Psychofan's Kerry memorabilia is not Kerry participation. Family Heirloom's
previously unresolved Dan scene was found in the official archives. Neither
finding permits a Kerry story or a new version of the native gig logic.

## Added side jobs

| Job or family | Required boundary |
| --- | --- |
| I'm in Love with My Car; The Highwayman; Ezekiel Saw the Wheel; Space Oddity | Preserve original discovery, incident, vehicle and reward ownership. |
| Raymond Chandler Evening | Earned Heroes prerequisite only; coordinate Pepe/Cynthia services and phone ownership. Hide Johnny's independent cigarette/lighter props as well as his body. |
| Every Breath You Take | Earned earlier band history only; do not replay Kerry quests to unlock Blue Moon's job. |
| These Boots Are Made for Walkin' | Original Nomad eligibility and earned prerequisites; preserve Lana choices and car entitlement. |
| Small Man, Big Mouth | Original Streetkid eligibility and genuinely completed Heroes history; no funeral replay. |
| KOLD MIRAGE | Preserve the physical power-cut alternative and Nix service. Reward acquisition does not authorize cyberdeck use. |
| Sinnerman; There Is A Light That Never Goes Out; They Won't Go When I Go | Treat the three journals as one native family. Preserve opt-outs, deaths, recording choices and payouts; no resurrection of a resolved outcome. |
| This Corrosion | Earned component and recipe only. The native completion check accepts inventory ownership; it does not require equipping Canto. |
| Venus in Furs | Meredith must have survived the original outcome; restore only the unresolved invitation/encounter, never The Pickup. |
| Freedom | Broader retiming of vehicle recovery; retain earned race/main-story prerequisites. Archived Yorinobu ownership is not a live Yorinobu scene or authority to reverse Tower politics. |
| Sweet Dreams | Native inventory escrow and recovery must be safe and exactly once. No repeated confiscation, default inventory replacement or new implant. |
| Don't Lose Your Mind | Only an unresolved original-Delamain sequel after earned Epistrophy completion. Never undo an already completed reset, merge, destruction or reward. |
| One Way or Another | Earned Nele outcome from Roads to Redemption and original world-story activation; no blanket world-story restart. The earlier Prototype in the Scraper attribution was incorrect. |
| Corpo of the Month | Earned Alan/Milko outcome and unclaimed reward; no Treating Symptoms replay. |
| Where Eagles Dare; Killing In The Name | Native wired Personal Link paths, not remote quickhacks. No added cyberdeck, forced minigame success or attribute increase. |
| Nitro (Youth Energy) | Uses the existing Basic Kiroshi Optics exception, not a new cyberware allowance. Verify robot control and safe return to V under the installed profile. |

Freedom's car-owner records support this retiming interpretation, not a claim
that its original chronology is unchanged. The public walkthrough also
describes the vehicle as Yorinobu's property rather than a meeting with him.
[Freedom walkthrough](https://vulkk.com/2025/07/19/how-to-get-the-rayfield-caliburn-mordred-in-cyberpunk-2077/)

For Don't Lose Your Mind, the shipped Tower cab scene has branches for the
different `sq025_delamain_fate` values, including the original identity.
The sequel also has alternatives to its high-Intelligence merge outcome.
[Sequel walkthrough](https://cyberpunk.fandom.com/wiki/Don't_Lose_Your_Mind)

## Removed or left excluded

**I Can See Clearly Now** is removed from both variants. The stock dumpster
template uses an EASY Athletics check mapped to Strength plus skillcheck
bonus; the inspected curve has values 4, 4 and 10, above Body 3. Its quest
waits for the physical demolition interaction. This is a conservative
profile decision, not a captured live threshold: the placed override and
effective bonus remain unmeasured. No strength increase, Gorilla Arms or fact
bypass is authorized.

**Spray Paint and Coin Operated Boy remain selected only when the earlier
Brendan prerequisite was genuinely completed.** They do not authorize
restoring the excluded dumpster job or fabricating that completion.

**Money for Nothing remains excluded from this release selection.** The stash
is behind a movable dumpster, but a Body-3-compatible native route was not
established. A guide describes the obstacle without settling its required
attribute value, so no specific threshold or proven impossibility is claimed.
[Stash location and obstacle](https://upcomer.com/cyberpunk-2077-where-to-find-katyas-stash/)
The commonly repeated `wst_ep1_08` attribution is not safe dispatch authority:
the inspected shipped controller belongs to a merchant/body event.

**Water Runs Dry and Dirty Second Hands are excluded.** Their earlier
Myers/Reed operation is not an independent post-ending commission. A new
story adaptation is outside stock restoration.

Heroes, Misty/Tarot jobs, live Panam/Judy/Kerry stories, Johnny-central or
takeover stories, cyberdeck-use tutorials, contradictory ending epilogues,
the fixed old election premises and unproven placeholder records stay out.
River is not globally banned; his excluded jobs have individual
post-Tower premise conflicts. Historical names, archived material and reused
animation names are not treated as actual character participation.

## Profile and home rules

Personal Link and **stock Basic Kiroshi Optics** were already approved in the
[equipment policy](../research/restriction_profiles/whitelist.json). Nitro's
shipped optics requirement is therefore not sufficient reason to exclude it.
This corrects the provisional optics objection; it does not approve another
implant, combat quickhack or operating system.

Johnny's voice stays, using the already approved invisible internal actor.
His visible body and independent scene props must remain hidden. No Johnny
engram revival, takeover or undoing of Tower is allowed.

**Kerry's house is the sole retained-home/access exception.** Preserve
existing access without removal or repurchase; do not create Kerry quests,
romance history or an actor. H10 costs 25,000 to repurchase. Other previously
owned apartments also require repurchase, at their normal prices.

Completed jobs stay completed. The target side-job policy restarts unfinished
jobs once and starts never-started jobs natively. General unfinished-job
restart is still unimplemented. Gig freshness and development assumptions
remain separate; this audit creates no pre-ending history certificate.

## Remaining implementation work

These are engineering and acceptance tasks, not another undecided whitelist:

1. Migrate selection into successor packages safely. Deny new Heroes admission
   and the removed fresh Brendan route; preserve already-issued owners,
   completed rewards, Claire and shared support. **Do not remove all of S27.**
2. Implement the selected new families with original graphs, earned
   prerequisites, native contact/service setup and exactly-once rewards.
   Add safe retirement/reset handling before restarting unfinished jobs.
3. Resolve Cuckoo's Nest's named scene dependency and the complete native
   owners of the EP1 follow-ups. Keep the existing Claire embedded-helper
   evidence; its external-name gap is not a reason to discard the repair.
4. Address reachable Viktor service lines about Misty/Relic separately from
   Paid in Full's bounded debt branch. Do not reopen Misty's shop or run
   unrelated Tarot donor logic.
5. Test new job entry, choices, calls, inventory and rewards under the actual
   nerf profile, Johnny presentation, death/reload and cold reload. Test
   Nitro's return-to-V cleanup and Sweet Dreams' inventory recovery explicitly.

The installed mod, game saves, facts and recovery chain were not changed by
this audit. The current source selection is not a claim that all 158 jobs
are installed or work in every save.

## Verification basis

The selection reconciles the 129-row R5 recheck and 98 omitted records,
including the prior 943-resource retained-job screen and the scoped candidate
reviews. This pass adds native Personal Link, minigame, optics-localization
and Tower Delamain evidence. Exa supplied 20 result sources across four
search workstreams, with three fetched excerpts; native files remain primary
for mechanics.

[Assessment](../research/whitelist_final_r6/assessment_01.json) and
[verification results](../research/whitelist_final_r6/verification_01.json)
record membership, source identity and targeted native assertions. These
checks do not replace gameplay tests or certify every dynamic branch.
