"""Successor of probe_03: guarantee the standalone system starts on player load."""
from pathlib import Path
import hashlib
import json
import shutil

H = Path(__file__).resolve().parent
W = H.parent.parent
BASE = H / "probe_03"
O = H / "probe_04"
assert not O.exists(), "Preserve prior evidence"
old = json.loads((BASE / "source_manifest.json").read_text(encoding="utf-8"))
assert old["status"] == "ADDITIVE_PROBE_SOURCE_NOT_PACKED_OR_INSTALLED"
resource = BASE / "source/towercontinued/world_workspots_ww1/ce_pac_cvi_116_owner.questphase"
reds = BASE / "package/r6/scripts/PTFR_WW1_Prototype/WW1Probe.reds"
assert hashlib.sha256(reds.read_bytes()).hexdigest().upper() == old["script_sha256"]
source = reds.read_text(encoding="utf-8")
assert "@wrapMethod(PlayerPuppet)" not in source
source += '''
// One local-player hook creates this separate probe's system after load.
// It does not touch NPC AI or change the wrapped game's result.
@wrapMethod(PlayerPuppet)
protected cb func OnGameAttached() -> Bool {
  let result = wrappedMethod();
  let probe = GameInstance.GetScriptableSystemsContainer(this.GetGame()).Get(n"PTFR.WorldWorkspotsWW1.WorldWorkspotsWW1Driver") as WorldWorkspotsWW1Driver;
  return result;
}
'''
assert source.count("@wrapMethod(PlayerPuppet)") == 1
assert "@wrapMethod(NPCPuppet)" not in source
targetResource = O / "source/towercontinued/world_workspots_ww1/ce_pac_cvi_116_owner.questphase"
targetResource.parent.mkdir(parents=True)
shutil.copyfile(resource,targetResource)
targetScript = O / "package/r6/scripts/PTFR_WW1_Prototype/WW1Probe.reds"
targetScript.parent.mkdir(parents=True)
targetScript.write_text(source,encoding="utf-8",newline="\n")
receipt = {"status":"ADDITIVE_PROBE_SOURCE_WITH_PLAYER_STARTUP_NOT_PACKED_OR_INSTALLED",
           "previous":"probe_03 (no guaranteed startup; historical only)",
           "resource_sha256":hashlib.sha256(targetResource.read_bytes()).hexdigest().upper(),
           "script_sha256":hashlib.sha256(targetScript.read_bytes()).hexdigest().upper(),
           "player_hooks":1,"npc_hooks":0,"game_writes":0,"save_writes":0}
(O / "source_manifest.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
print(json.dumps(receipt,indent=2))
