# Post Tower Cyberware Treatment Sheet

11 November 2026. Design for stock Cyberpunk 2077 2.5 and Phantom Liberty cyberware and physical recovery after genuine Tower completion. The installed profile is documented in [profiles/README.md](../profiles/README.md).

Reed identifies the Personal Link and simple coprocessors as tolerable. V says even simple muscle boosters are out, and Viktor finds that V’s cortex no longer responds to implant signals. Limited Function therefore retains a specific civilian, cosmetic, or structural function. [Reed’s diagnosis](../research/q307_extracted/json/ep1/quest/main_quests/q307/scenes/q307_03_hospital.scene.json#L23639) · [V’s holocall](../research/q307_extracted/json/ep1/quest/main_quests/q307/scenes/q307_03a_friends_holocall.scene.json#L44736) · [Viktor’s examination](../research/q307_extracted/json/ep1/quest/main_quests/q307/scenes/q307_06_viktor.scene.json#L32876)

## Cyberware by treatment level

Quality and Iconic variants follow their named model’s treatment. [Stock catalogue](https://cyberpunk.fandom.com/wiki/Cyberpunk_2077_Cyberware)

### Level 1 — Remove after the ending

Unequip all combat Arms and all Hands cyberware into owned inventory once at the post-Tower handoff. Block refitting, with the Level 3 tattoo exception below.

- **Gorilla Arms** — all variants.
- **Mantis Blades** — all variants, including MaxTac Mantis Blades.
- **Monowire** — all variants.
- **Projectile Launch System** — all variants.
- **Hands** — all, including the hand tattoos at the initial handoff.

Cosmetic styles follow their parent implant. The vanilla hospital and ending outfits hide arm cyberware. Physical unequip is the proposed free-roam treatment. [Arms catalogue](https://gamestegy.com/cyberpunk-2077/wiki/arms-cyberware) · [CDPR’s arm style notes](https://www.cyberpunk.net/en/news/52120/check-out-whats-coming-to-night-city-in-the-edgerunners-2-update-for-cyberpunk-2077)

### Level 2 — Permanently disable

Keep equipped hardware installed with its effects disabled after the ending. Block upgrades, part changes and refitting. V can choose to remove it at a ripperdoc.

- **Frontal Cortex, Operating System, Nervous System, Circulatory System and Legs** — all.
- **Face** — all except Basic Kiroshi Optics.
- **Skeleton** — all except Titanium Bones.
- **Integumentary System** — all except Chitin, Subdermal Armor and Carapace.

Additional Skeleton and Integumentary exceptions remain open. Use Level 2 for the other models until an explicit Limited Function rule is added.

#### Skeleton and Integumentary review

The review covers all 13 stock Skeleton models and all 15 stock Integumentary models. An armor exception requires item text or construction evidence for a protective layer that could plausibly work independently of the implant’s other effects. A flat Armor stat shows how the game models protection. Evidence about the material supports the lore inference. [Skeleton catalogue](https://gamestegy.com/cyberpunk-2077/wiki/skeleton-cyberware) · [Integumentary catalogue](https://gamestegy.com/cyberpunk-2077/wiki/integumentary-system-cyberware)

**Skeleton.** Para Bellum has separate flat Armor and a whole-Armor multiplier. Rara Avis relies on a whole-Armor multiplier and adds Body-attuned Health. Their shared flavor line leaves the construction unspecified. Bionic Joints are described as mechatronic support, and Epimorphic Skeleton’s description gives a general enhancement to resistance and performance. Those models stay at Level 2. Dense Marrow’s melee boost also falls under V’s restriction on muscle boosters. [Para Bellum item text](../research/misty_viktor_world/bradbury_localization/json/base/localization/en-us/onscreens/onscreens.json.json#L385876) · [Bionic Joints item text](../research/misty_viktor_world/bradbury_localization/json/base/localization/en-us/onscreens/onscreens.json.json#L196379) · [Dense Marrow item text](../research/misty_viktor_world/bradbury_localization/json/base/localization/en-us/onscreens/onscreens.json.json#L196400)

**Integumentary.** Nano-plating has separable flat Armor and a projectile interception effect. The name suggests plating, but the item description leaves the layer’s unpowered protection unresolved. Cellular Adapter’s stock armor comes with Tech-linked explosion resistance, weapon damage and recharge bonuses. RangeGuard, ProxiShield, Peripheral Inverse, Countershell and Cogito Lattice supply protection that depends on enemy distance, damage taken or available RAM. Those models stay at Level 2. [Nano-plating](https://cyberpunk.fandom.com/wiki/Nano-plating) · [Cellular Adapter](https://cyberpunk.fandom.com/wiki/Cellular_Adapter) · [Integumentary catalogue](https://gamestegy.com/cyberpunk-2077/wiki/integumentary-system-cyberware)

### Level 3 — Limited function

Keep the listed Skeleton and Integumentary implants installed after the ending and retain only their listed effects.

**Johnny’s Special, Together Forever and Tyger Claws Dermal Imprint** come out with the other Hands items at the initial handoff. V can refit the owned tattoos afterward for visible ink only. Smart targeting and any other implant effects stay disabled. The one-time removal must recognize a completed handoff so reloading does not unequip a refitted tattoo.

| Implant | Retained function | Basis and limits |
| --- | --- | --- |
| **Titanium Bones** | Carry-capacity contribution only | The item text describes metal-infused bones that bear heavy loads. The stock record also grants Armor and Body-attuned Health. The treatment retains load support and suppresses the other bonuses. [Item text](../research/misty_viktor_world/bradbury_localization/json/base/localization/en-us/onscreens/onscreens.json.json#L196337) |
| **Chitin** | Reduced flat Armor | The genetically modified shell supplies the physical rationale. The stock record has separate in-combat and out-of-combat health regeneration modifiers. Both stay off. [Item description and effects](https://cyberpunk.fandom.com/wiki/Chitin) |
| **Subdermal Armor** | Reduced flat Armor | The game’s scanner describes a physical armor layer reinforced by reactive nano-transmitters. Level 3 represents the layer alone, with stock attunement and secondary bonuses suppressed. [Scanner text](../research/misty_viktor_world/bradbury_localization/json/base/localization/en-us/onscreens/onscreens.json.json#L262354) |
| **Carapace** | Reduced flat Armor | The stock plating record supplies flat Armor separately from its side and rear hit effect. Residual physical protection is an inference from the plating. The directional effect and Tech attunement stay off. [Item effects](https://cyberpunk.fandom.com/wiki/Carapace) |

#### Limited-function effect handling

Use the existing stock items and preserve their identity and parts. After the Tower handoff, suppress the limited item’s stock equipment packages, attached-part effects and separately applied equipment stats. Apply only the approved effect for that item. Track each Armor or carry-capacity modifier by item instance and reconcile it on equip, unequip and reload so it applies once. The game supplies no separate value for unpowered material protection, so Armor and carry-capacity amounts remain open design choices. In-game verification must establish that only the retained contribution survives. [Native equipment effects](../research/redscript_2_5/framework_probe_01/current_minimal.script#L90825) · [Separate item stats](../research/redscript_2_5/framework_probe_01/current_minimal.script#L89131) · [Existing modifier ownership](../redscript/PTFR_Restrictions_R3/ProfilePhysical.reds#L38)

### Level 4 — Keep functional

**Personal Link and Basic Kiroshi Optics** stay installed and retain their normal functions after the ending.

## Physical recovery

Day 0 starts when V regains control after genuine Tower completion and cleanup. Maximum Health and Stamina increase over the recovery period.

| Milestone | Maximum HP | Maximum stamina |
| --- | ---: | ---: |
| Day 0 | 25 | 25 |
| End of recovery, provisionally day 30 in game | 125 | 75 |

Thirty in-game days is the proposed default. Keep the duration, the four stat targets and the progression curve independently adjustable. The recovery clock governs vitals. Implant treatment is determined by its level.

## Settings and save continuity

Keep the treatment assigned to each stock model, its allowed equipment operations and any retained effects and amounts adjustable alongside the recovery settings. Keep the proposed defaults in the profile definition and preserve save-local recovery progress and completed handoff actions across reloads. A later revision needs an explicit transition for saves using an earlier definition. The existing no-vitals path must remain available.
