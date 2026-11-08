"""Explicit private successor to prototype01; no builder rerun/installed writes."""
from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent;W=H.parents[2];A=H/'addon/bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_QR9_Diagnostics'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
if (H/'addon_manifest_02.json').exists():raise RuntimeError('Frozen successor exists')
old=read(H/'snapshots/prototype_01/addon_manifest.json');cfg=read(A/'watch.json');cfg['version']='QR9B02';cfg['declared_build']['source_lua_sha256']=sha(A/'init.lua')
cfg['profiles']['S03']['vehicles']=['Vehicle.v_sportbike1_yaiba_kusanagi_player','Vehicle.v_sportbike1_yaiba_kusanagi_player_02','Vehicle.v_sportbike1_yaiba_kusanagi_player_03','Vehicle.v_sportbike1_yaiba_kusanagi_tyger_player']
cfg['profiles']['S03']['vehicle_semantics']='Native typed vehicle record identities. Getter reports player-unlocked entitlement, not inventory possession or proof of native VehicleAvailable evaluation/full eligibility.'
save(A/'watch.json',cfg)
manifest=dict(old);manifest['version']='QR9B02';manifest['predecessor_snapshot']='snapshots/prototype_01';manifest['files']=[dict(r,sha256=sha(A/Path(r['path']).name),bytes=(A/Path(r['path']).name).stat().st_size)for r in old['files']];manifest['active_dependencies_scope']='Existing CET ASI only. QR8 expected core is metadata, NOT an observed installed state; separate Core Verify receipt required before gameplay.';save(H/'addon_manifest_02.json',manifest)
proof=read(H/'api_proof.json');proof['additional_API_support']={'VehicleSystem.IsVehiclePlayerUnlocked':'Current compiled PTFR_SideJobsS29.reds159/792 and SideJobsS28.reds139 use same read-only getter. Lua Game/TweakDBID exposure remains guarded, not executed. It observes player-unlocked record state, not necessarily every native VehicleAvailable condition or full eligibility.','CET literal availability':'Current ASI export-name presence corroborates interface names only; no full-binary equivalence claim.'};proof['additional_local_sources']=[{'path':str(W/'prealpha/quest_restoration_qr8/candidate_01/package/r6/scripts/PTFR_Consolidated'/n),'sha256':sha(W/'prealpha/quest_restoration_qr8/candidate_01/package/r6/scripts/PTFR_Consolidated'/n)}for n in['PTFR_SideJobsS29.reds','PTFR_SideJobsS28.reds']];save(H/'api_proof_02.json',proof)
print('Private prototype02 frozen:2addon files; native vehicle reads added; cleanup failures aggregated')
