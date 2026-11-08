"""Prepare one-file El Capitan diagnostic profile successor; never installs."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;P=H.parent;W=P.parents[1]
REL='bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_QR9_Diagnostics/watch.json'
FACT='phonecall_player_with_muamar_el_capitan_reyes'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,j):assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(j,indent=2)+'\n',encoding='utf-8')
def main():
    old=read(P/'diagnostics_manifest_01.json');game=Path(old['game_root'])
    target=game/REL;assert sha(target)=='A1AAB30B9F896CD24687D82CC2160D773C04B7193BDDCA71CC933A4C93997AAA'
    cfg=read(target);original=json.loads(json.dumps(cfg))
    assert 'D00E'not in cfg['profiles']
    cfg['profiles']['D00E']={'facts':[FACT],'journals':[],
        'description':'Human-confirmed callable El Capitan. Native contacts/muamar_el_capitan_reyes, outgoing PhoneSystem fact. Getter differences only, not native callbacks. No quest acceptance or state manipulation.'}
    write(H/'package'/REL,cfg)
    src=W/'research/fixer_offices_fo1/parents/json/base/open_world/fixers/el_capitan/phases/el_capitan.questphase.json'
    raw=read(src);nodes=raw['Data']['RootChunk']['graph']['Data']['nodes']
    native=nodes[20]['Data']['phaseGraph']['Data']['nodes'][3]['Data']
    predicate=native['condition']['Data']['conditions'][1]['Data']['type']['Data']
    assert predicate['addressee']['Data']['realPath']=='contacts/muamar_el_capitan_reyes'
    assert predicate['caller']['Data']['realPath']=='contacts/player'
    write(H/'evidence.json',{'user_report':'el capital is callable and has interactions line in call','interpretation':'El Capitan user-confirmed Call availability; actual loaded slot not independently confirmed.',
        'native_source':str(src),'native_source_sha256':sha(src),'parent_node_id':nodes[20]['Data']['id'],'condition_node_id':native['id'],'predicate':predicate,
        'phone_fact':FACT,'naming_source':str(W/'research/finalboards_dismissal/decompiled/cyberpunk/systems/phoneSystem.script'),
        'naming_source_sha256':sha(W/'research/finalboards_dismissal/decompiled/cyberpunk/systems/phoneSystem.script'),
        'derivation':'GetPhoneCallFactName(player,muamar_el_capitan_reyes): phonecall_ + lowercase caller + _with_ + lowercase addressee. Native phone UI uses ContactData.contactId.',
        'scope':'Adds profiles/D00E only. Lua/Core/other profiles unchanged. No native callback or current engine-write proof.'})
    m=json.loads(json.dumps(old));lua=next(r for r in old['files']if r['path'].endswith('init.lua'))
    assert sha(game/lua['path'])==lua['after']
    m['files']=[{'path':REL,'before':sha(target),'before_bytes':target.stat().st_size,
        'after':sha(H/'package'/REL),'after_bytes':(H/'package'/REL).stat().st_size}]
    m['package_root']=str(H/'package');m['required_files'].append({'path':lua['path'],'sha256':lua['after'],'bytes':lua['after_bytes'],'active_only':False})
    m['proofs'].extend({'path':str(p),'sha256':sha(p)}for p in[P/'deployment_01/completion.json',H/'evidence.json'])
    m['scope']='Exactly one existing diagnostic watch.json replacement. init.lua is a protected dependency; preserve all profiles, Core, saves and logs.'
    write(H/'diagnostics_manifest_01.json',m)
    script=(P/'deploy_diagnostics.ps1').read_text()
    assert sha(P/'deploy_diagnostics.ps1')=='400438835F72415A78D6604EC9551034A2967BEB42206132FC94714E8496806E'
    script=script.replace("$PinnedDiagnosticsManifestSHA='8B42EAC8C161256534DB26F859A62447E8A9921104929B10ADFF83020C1B2DD0'",f"$PinnedDiagnosticsManifestSHA='{sha(H/'diagnostics_manifest_01.json')}'")
    script=script.replace("Join-Path (Split-Path $worker -Parent) 'quest_restoration_qr9/worker_a'","Join-Path (Split-Path (Split-Path $worker -Parent) -Parent) 'quest_restoration_qr9/worker_a'")
    script=script.replace('recovery/diagnostics_qr10d01_01','recovery/diagnostics_d00e_01')
    before="$wanted=@('bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_QR9_Diagnostics/init.lua','bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_QR9_Diagnostics/watch.json')"
    assert script.count(before)==1
    script=script.replace(before,"$wanted=@('"+REL+"')")
    script=script.replace('$manifest.files.Count -ne 2 -or $changes.Count -ne 2','$manifest.files.Count -ne 1 -or $changes.Count -ne 1').replace('Two-existing-diagnostic-leaf scope drift','One-existing-watch-config scope drift')
    dest=H/'deploy_profile.ps1';assert not dest.exists();dest.write_text(script,encoding='utf-8',newline='\n')
    collector=(P/'collect_d00.py').read_text()
    collector=collector.replace("FACT='phonecall_player_with_regina_jones'",f"FACT='{FACT}'")
    collector=collector.replace("'D00'","'D00E'").replace('D00 capture','D00E capture').replace('Regina','El Capitan')
    collector=collector.replace('8B42EAC8C161256534DB26F859A62447E8A9921104929B10ADFF83020C1B2DD0',sha(H/'diagnostics_manifest_01.json'))
    collector=collector.replace('recovery/diagnostics_qr10d01_01','recovery/diagnostics_d00e_01')
    (H/'collect_d00e.py').write_text(collector,encoding='utf-8',newline='\n')
    # Semantic diff: all existing fields/profiles must remain identical.
    verify=json.loads(json.dumps(cfg));verify['profiles'].pop('D00E');assert verify==original
    print({'status':'PREPARED_NOT_INSTALLED','changed_files':1,'profile':'D00E','fact':FACT,'manifest_sha256':sha(H/'diagnostics_manifest_01.json')})
if __name__=='__main__':main()
