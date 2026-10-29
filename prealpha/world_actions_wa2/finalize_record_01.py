"""Record only verified installed results in the project documentation."""
from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent;W=H.parents[1];C=H/'candidate_01'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest().upper()
installed=read(C/'installed_assessment_01.json')
assert installed['status']=='PASS_WA2_INSTALLED_FILES_AND_SAVE_PRESERVATION'
assert installed['installed_paths']==51 and installed['changed_paths']==3 and installed['archive_members']==1212
assert installed['fixture_actions']==23
semantic=read(C/'semantic_assessment_01.json')
assert str(semantic['status']).startswith('PASS') and len(semantic['resources'])==26
environment=read(H/'environment_review/overall_assessment_01.json')
assert environment['status']=='PASS_ALL_25_NEW_ACTION_ENVIRONMENTS_AND_NATIVE_ACTORS_STATIC_ONLY'
assert environment['checks_passed']==459
for pin in environment['pins']: assert digest(Path(pin['path']))==pin['sha256'],pin['path']
result={'status':'PASS_WA2_INSTALLED_STATIC_AND_DEPLOYMENT_VERIFICATION',
        'actions':25,'new_shooting_groups':[172,173,246,250,289],'new_vehicle_ambient_groups':20,
        'new_support_groups':[250],'preserved_BA1_group':179,'support_groups_total':238,
        'archive_members':1212,'previous_members_unchanged':1186,'installed_paths':51,'changed_paths':3,
        'source_compile_count':64,'fixture_actions':23,'interrupted_rollback_cases':6,
        'save_files_unchanged':installed['save_files_unchanged'],
        'new_cohort_live_status':'UNVERIFIED; user confirms only preceding BA1 prototype',
        'scope_limits':'Stateful encounter/scene operations remain untouched. Source rows130/306 have no current world binding.',
        'zip_sha256':installed['zip']['sha256'],'manifest_sha256':installed['manifest_sha256'],
        'environment_checks':459,
        'proofs':[{'path':str(p),'sha256':digest(p)} for p in [C/'installed_assessment_01.json',C/'semantic_assessment_01.json',C/'cohort_proof_01.json',C/'deployment_tests_01.json',H/'coverage_review/assessment_02.json',H/'environment_review/overall_assessment_01.json']],
        'game_launched':False,'save_writes':0,'native_fact_writes':0,'git_pushed':False,'public_release':False}
out=C/'assessment_01.json';assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n')
def replace(path,old,new):
    text=path.read_text(encoding='utf-8-sig');assert old in text,path
    path.write_text(text.replace(old,new,1),encoding='utf-8',newline='\n')
doc=W/'docs/world_actions_wa2_20261028.md'
replace(doc,'''The current implementation is staged for independent semantic checks, a fresh
64-source compilation, complete archive readback, resource-collision checks and
interrupted-install/rollback fixtures. Installation status will be recorded
after those checks complete. The successor keeps the same 51 installed paths.''',
f'''**Installed on 28 October 2026.** The full 51-path successor replaces only the
combined archive, XL registration and existing Baseline script. All 1,186 prior
archive members are byte-identical; 26 new resources bring the total to 1,212.
All old W3 and BA1 owner resources and receipts are preserved.

Independent verification passed 310 action/support checks and 459 environment,
registry and target checks. Fresh 64-source compilation, every archive member readback,
68-mod-archive collision checks, 23 deployment fixture actions including six
interrupted rollbacks, and actual Validate/Install/Verify/ValidateRollback pass.
All {installed['save_files_unchanged']} save files and names are unchanged.

The full unreleased ZIP SHA-256 is `{installed['zip']['sha256']}`.
The manifest SHA-256 is `{installed['manifest_sha256']}`.
Final evidence: `candidate_01/assessment_01.json`.

With the game and launcher closed, roll back WA2 first using
`prealpha/world_actions_wa2/deploy_01.ps1 -Action ValidateRollback`, then
`-Action Rollback`. Recovery is `recovery/world_actions_wa2_01`. This restores
the prior BA1 files; file rollback cannot undo state already saved by the game.''')
replace(doc,'''The last two bindings are reviewed separately before promotion.''',
'''The last two bindings passed a fresh registry review: only their community
references change, preserving native entry names and counts, including group
319's seven-actor requirement.''')
readme=W/'README.md'
replace(readme,'''The current local [BA1 successor](docs/bottle_actions_ba1_20261028.md) restores
the missing native shooting controller for the matched Coastview bottle-shooting
community. Its 51-file install, resource preservation and rollback are verified;
live shooting, speech and save/reload remain pending.''',
'''The current local [WA2 successor](docs/world_actions_wa2_20261028.md) extends the
user-confirmed [BA1 prototype](docs/bottle_actions_ba1_20261028.md) to five more
shooting groups and twenty native vehicle-ambience groups. It also adds one
exact native support owner omitted by the earlier mapping. The same 51-path
package, full compilation, archive preservation, installation and rollback are
verified; saves are unchanged. Broader gameplay remains unverified, and
stateful encounter/scene actions remain outside this repair.''')
change=W/'CHANGELOG.md'
entry='''- Restored omitted native action controllers for five additional shooting groups and twenty vehicle-ambience groups, preserving the working BA1 prototype. Added one exact native support owner and corrected three proven community/security reference problems. Vehicle events run once per community-ready lifetime; shooting loops retain native combat behavior and safety suspension. The 51-path WA2 successor preserves all 1,186 prior archive resources and adds 26, with fresh 64-source compilation, independent graph checks, full readback, 23 deployment fixture actions and installed rollback verification. Saves are unchanged; expanded gameplay remains unverified. Stateful encounter/scene operations and two unbound shooting definitions remain excluded. See [WA2](docs/world_actions_wa2_20261028.md).
'''
replace(change,'### Restored content and repairs\n\n','### Restored content and repairs\n\n'+entry)
replace(change,'Live shooting, speech and save/reload remain unverified. See [BA1]',
        'The user subsequently confirmed the matched prototype works; speech and save/reload were not separately itemized. See [BA1]')
replace(W/'docs/full_consolidation_v1.md',
        '**Current successor:** [BA1](bottle_actions_ba1_20261028.md) was installed on 28 October.',
        '**Current successor:** [WA2](world_actions_wa2_20261028.md) was installed on 28 October.')
replace(W/'docs/full_consolidation_v1.md',"Use BA1's rollback first.","Use WA2's rollback first.")
agents=W/'AGENTS.md';text=agents.read_text(encoding='utf-8-sig')
notice=f'''Latest 2026-10-28 WA2 BROAD ACTION SUCCESSOR INSTALLED; EXPANSION LIVE PENDING:
User confirms BA1 prototype works and requests all affected NPCs. Audited237W3
owners+240otherCErefs and168externalphases. WA2 adds5shooting controllers
(172173246250289),20nativevehicle radio/light/door controllers and250support.
ExistingBA1group179+all237W3resources/receipts unchanged. Newsupport total238.
Vehicleevents onceperReady lifetime, nativeNotReadyonlyrearm; no globalsafety
bounce replay. Shooting preserves full safetycut+nativecombat loops. Explicit
246foursecurityref rebind,256twoReady/NotReadyrefs,319Spawnedref; exact registry
names/counts preserved.2503line Baseline mapappend,64sourcefreshSCC PASS.
Independent295actionchecks+supportcrosscheck PASS; all1212archivemembers read,
1186oldbyteunchanged,68modarchive newresource0collisions. Full51paths replaces
archive+XL+Baseline only.23fixtureactions incl6interruptedrollbacks PASS.
Actual gameclosed Validate/Install/Verify/ValidateRollback PASS;
{installed['save_files_unchanged']}savefiles/names unchanged. Userliveproof onlyBA1; WA2expandedruntimeunverified.
Source130/306 no currentcommunity/supportbinding; statefulmount/storysecurity/
attitude/scene/fullencounteroperations withheld with exactdispositions, NOT
allNPCgameplayclaim. Do not request moreingametests. No launch/save/nativefact
edit/Gitpush/release. Final candidate_01/assessment_01.json under
prealpha/world_actions_wa2. ZIP SHA {installed['zip']['sha256']}.
Rollback WA2 FIRST gameclosed via prealpha/world_actions_wa2/deploy_01.ps1
-Action ValidateRollback then Rollback; recovery/world_actions_wa2_01.
Fileundo NOT saveundo. docs/world_actions_wa2_20261028.md.

'''
assert text.startswith('# AGENTS.md')
head,rest=text.split('\n\n',1);agents.write_text(head+'\n\n'+notice+rest,encoding='utf-8',newline='\n')
print(json.dumps({'status':result['status'],'assessment_sha256':digest(out),'save_files_unchanged':installed['save_files_unchanged']}))
