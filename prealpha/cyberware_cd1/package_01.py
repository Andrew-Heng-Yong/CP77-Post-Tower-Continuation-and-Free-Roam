"""Verify preservation against the compiled alpha and package two diagnostic files."""
from pathlib import Path
import json,re,zipfile
from prepare_01 import ROOT,OUT,ZIP,EQUIP,COVER,sha

def method(text,signature):
    start=text.index(signature);brace=text.index('{',start)
    depth=0;quoted=False;escape=False
    for i in range(brace,len(text)):
        char=text[i]
        if quoted:
            if escape:escape=False
            elif char=='\\':escape=True
            elif char=='"':quoted=False
            continue
        if char=='"':quoted=True
        elif char=='{':depth+=1
        elif char=='}':
            depth-=1
            if depth==0:return text[start:i+1]
    raise AssertionError('Unclosed method')

def main():
    result=json.loads((OUT/'compile_01/result.json').read_text())
    assert result['status']=='PASS_FULL_SCC_NOT_LIVE' and result['sources']==90
    baseline=ROOT/'prealpha/h10_h4/candidate_01/compile_01/compiled.script'
    before=baseline.read_text(encoding='utf-8-sig')
    after=(OUT/'compile_01/compiled.script').read_text(encoding='utf-8-sig')
    original=method(before,'public final func PTFRR1Remove(id: ItemID)')
    current=method(after,'public final func PTFRR1Remove(id: ItemID)')
    stripped=re.sub(r'^.*ModLog\(n"PTFR_CyberwareCD1".*\n','',current,flags=re.M)
    assert re.sub(r'\s+','',original)==re.sub(r'\s+','',stripped),'Compiled removal changed beyond logging'
    methods=['public final func PTFRR1RestrictedEquipped()', 'public final func PTFRR2Healthy()', 'public final func PTFRR2Ready(player: wref<PlayerPuppet>)']
    # The first two symbols have stable signatures in this decompiler output.
    for signature in methods[:2]:assert method(before,signature)==method(after,signature),signature
    diagnostics=method(after,'public static func Item(id: ItemID)') if 'public static func Item(id: ItemID)' in after else None
    assert 'PTFR.RestrictionsR1.CyberwareDiagnosticsCD1' in after
    changes=json.loads((OUT/'changes_01.json').read_text())
    assert sha(ZIP.read_bytes())==changes['base_zip_sha256']
    payload={}
    for row in changes['changes']:
        data=(OUT/'package'/row['path']).read_bytes();assert sha(data)==row['after'];payload[row['path']]=data
    assert set(payload)=={EQUIP,COVER}
    readme='''# PTFR CD1: alpha cyberware diagnostics

For TowerContinuation-v0.1.1-alpha.20261024 only. This is a two-file diagnostic
overlay. It is NOT an inventory repair or a fix for the setup stop. Expect the
same safety stop, now with enough information to investigate it.

1. Close Cyberpunk 2077.
2. Back up these two existing files outside the game's r6/scripts folder:
   - r6/scripts/PTFR_PreAlpha/PTFR_Restrictions_R1/EquipmentHooks.reds
   - r6/scripts/TowerContinued_Loading_LC1/StartupCoverLC1.reds
3. Merge this ZIP's r6 folder into the game folder, replacing only those two files.
4. Load an untouched pre-ending test save, ideally the original save used for
   the failed attempt. Run the ending/setup once. Do not use repeated reloads
   of a partially processed save as a repair.
5. After setup stops, close the game and copy this file before launching again:
   bin/x64/plugins/cyber_engine_tweaks/gamelog.log
6. Send that log to the mod author. Look for [PTFR_CyberwareCD1] BEFORE, AFTER,
   and FAIL rows. These identify the exact failed preservation comparison.

The original inventory checks, native unequip call, retry restrictions, profile
transactions, saved fields and readiness barrier remain unchanged. The overlay
does not clear faults, grant items, force completion or change frameworks.
Running the game still performs the alpha's original setup work; diagnostics
are not a passive inventory preview.

To remove CD1, close the game and restore your two backed-up files. The same
two files can also be extracted from the original alpha ZIP. Do not install
both versions under r6/scripts. File restoration does not undo saved gameplay.

Verified: full 90-source local SCC compilation including EquipmentEx, compiled
removal-body equivalence after excluding diagnostic log statements, original
fault/readiness conditions and saved fields retained. Live behavior on the
tester's computer remains unverified. The exact tester patch/dependency versions
are not yet confirmed.
'''
    payload['PTFR-CD1/READ-ME-FIRST.txt']=readme.encode('utf-8')
    payload['PTFR-CD1/FILES.json']=json.dumps(changes,indent=2).encode('utf-8')
    dest=ROOT/'dist/cyberware-cd1/PTFR-CD1-diagnostics-for-alpha.zip'
    dest.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(dest,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,data in sorted(payload.items()):z.writestr(name,data)
    with zipfile.ZipFile(dest) as z:
        assert z.testzip() is None and set(z.namelist())==set(payload)
        for name,data in payload.items():assert z.read(name)==data,name
    zip_hash=sha(dest.read_bytes())
    dest.with_suffix('.zip.sha256').write_text(zip_hash+'  '+dest.name+'\n')
    report={'status':'PASS_DIAGNOSTIC_PACKAGE_NOT_GAMEPLAY_FIX','zip':str(dest),'sha256':zip_hash,'bytes':dest.stat().st_size,'changed_game_files':2,'compiled_removal_preserved_except_logging':True,'compiled_restricted_item_scan_unchanged':True,'compiled_health_gate_unchanged':True,'source_cover_fault_predicate_and_remaining_barrier_unchanged':True,'saved_schema_unchanged':True,'zip_readback':'PASS','compiled_sha256':result['compiled_sha256'],'original_alpha_zip_unchanged':True,'local_game_installed':False,'public_release_changed':False,'tester_reproduction_pending':True}
    (OUT/'package_result_01.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
