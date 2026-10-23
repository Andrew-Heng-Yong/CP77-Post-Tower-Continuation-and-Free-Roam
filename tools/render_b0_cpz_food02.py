"""Render single-site runtime from the proven native-entry vendor template."""
from plan_b0_ordinary_vendor_batch import ROOT,read
from plan_b0_cpz_food02 import DEST
s=read(DEST/'cohort.json')['sites'][0];p=s['prefix'];pos=s['position']
guards={k:v for k,v in read(DEST/'validation/build_manifest.json')['common_guards'].items() if k!='PTFRB0CPZF2_Mode'}
t=ROOT/'redscript/PTFR_B0_VendorVariants/VendorVariantDriver.reds.in'
body=t.read_text().replace('PTFR.B0VendorVariants','PTFR.B0CPZFood02').replace('VendorVariant','CPZFood02').replace('PTFRB0VV_','PTFRB0CPZF2_')
body=body.replace('if this.ReadFact(q, n"PTFRB0CPZF2_Suspended") != 0 { return; }','if this.ReadFact(q, n"PTFRB0CPZF2_Suspended") != 0 || this.ReadFact(q, n"PTFRBASE_Suspended") != 0 { return; }')
args=', '.join(f'n"{p}{suffix}"' for suffix in ('Enabled','Ready','Excluded','Near','Far'))
auto=f'this.AutoSite(q, {args}, n"{s["gate"]}", COMMIT)'
body=body.replace('@@AUTO_CHECKS@@','    pending = '+auto.replace('COMMIT','false')+' || pending;')
body=body.replace('@@AUTO_COMMITS@@','''    let mounting = GameInstance.GetMountingFacility(game).GetMountingInfoSingleWithObjects(player);
    if EntityID.IsDefined(mounting.parentId) { return; }
    let board = player.GetPlayerStateMachineBlackboard();
    if !IsDefined(board) { return; }
    let high = board.GetInt(GetAllBlackboardDefs().PlayerStateMachine.HighLevel);
    let tier = board.GetInt(GetAllBlackboardDefs().PlayerStateMachine.SceneTier);
    if (high != 1 && high != 2) || (tier != 1 && tier != 2) { return; }
    if GameInstance.GetQuestsContentSystem(game).IsTokensActivationBlocked() { return; }
    let locks: array<gameSaveLock>;
    if GameInstance.IsSavingLocked(game,locks) { return; }
    '''+auto.replace('COMMIT','true')+';')
body=body.replace('@@GUARD_READS@@','\n'.join(f'    this.factReads += 1;\n    if q.GetFact(n"{f}") != {v} {{ eligible = false; }}' for f,v in guards.items()))
body=body.replace('@@SITE_CALLS@@',f'    this.UpdateSite(q, position, n"{p}Enabled", n"{p}Near", n"{p}Far", n"{s["gate"]}", {pos["x"]:.9f}, {pos["y"]:.9f}, {pos["z"]:.9f}, 2025.0, 2500.0);')
out=ROOT/'redscript/PTFR_B0_CPZFood02/CPZFood02Driver.reds';out.parent.mkdir(exist_ok=True);out.write_text(body)
facts=list(guards)+[s['gate'],'cct_cpz_food_02_met','PTFRB0CPZF2_Mode','PTFRB0CPZF2_Suspended']
facts += [p+n for n in ('Ready','Enabled','Excluded','Near','Far','Entries','Exits','SpawnActionOut','ActorDistanceGate','ExitWatchArmed','DespawnActionOut')]
lua=ROOT/'diagnostics/PTFR_B0_CPZFood02/init.lua.in'
lua.with_suffix('').write_text(lua.read_text().replace('@@FACTS@@',','.join('"'+f+'"' for f in facts)))
print('Rendered single-site automatic driver and read-only logger')
