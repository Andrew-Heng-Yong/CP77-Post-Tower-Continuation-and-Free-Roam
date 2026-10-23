"""Static scope checks for the one-site redscript A4 startup candidate.

Game redscript compilation and runtime behavior require a closed-game install
and the subsequent disposable-save regression; this is not a compiler.
"""
from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCE = (ROOT / "redscript/PTFR_Afterlife_NativeBootstrap_A4/AfterlifeNativeBootstrapA4.reds").read_text(encoding="utf-8")
WRITES = re.findall(r'quests\.SetFact\(n"([^"]+)"\s*,', SOURCE)
REQUIRED = {
    "PostTowerFreeRoamActive", "PTFRP0_DR13", "q307_active", "q307_done",
    "q307_finished", "q307_2079", "q307_main_game_killed",
    "q305_johnny_scene_active", "mirror_interaction_disabled",
    "q115_point_of_no_return", "PTFRALMA2_Boot",
    "PTFRALMA2_Requested", "PTFRB0ALM_Enabled", "PTFRB0ALM_Near",
    "PTFRB0ALM_Active", "PTFRB0ALM_Interrupted",
    "PTFRALMA2_Interrupted",
}
assert set(WRITES) == {"PTFRB0ALM_Enabled", "PTFRALMA2_Requested"}
assert WRITES == ["PTFRB0ALM_Enabled", "PTFRALMA2_Requested", "PTFRB0ALM_Enabled"]
assert REQUIRED <= set(re.findall(r'quests\.GetFact\(n"([^"]+)"\)', SOURCE))
assert "this.attempts > 300" in SOURCE
assert "GetLocalPlayerMainGameObject" in SOURCE
assert "dx * dx + dy * dy + dz * dz <= 49.0" in SOURCE
assert SOURCE.count("private func OnAttach()") == 1
assert SOURCE.count("private func OnDetach()") == 1
assert SOURCE.count("public func Poll(") == 1
assert SOURCE.count("public func Call()") == 1
assert SOURCE.count("{") == SOURCE.count("}")
assert "GetMod(" not in SOURCE and "CET" not in SOURCE
print("A4 static PASS: Afterlife/Tower guards, two mod-owned fact targets, bounded startup, no CET or vanilla writes.")
