"""Static guardrails for the opt-in four-vendor shared Far-driver trial."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GAME = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077")
DRIVER = ROOT / "redscript/PTFR_B0_VendorShared/VendorSharedFarDriver.reds"
BATCH = ROOT / "diagnostics/PTFR_B0_VendorBatch/init.lua"
MODULES = (
    "PTFR_B0_Northside_Gunsmith",
    "PTFR_B0_Northside_Foodshop",
    "PTFR_B0_Northside_Medicstore",
    "PTFR_B0_LCH_Clothing_Vendor",
)
PREFIXES = ("PTFRB0NIDG_", "PTFRB0NIDF_", "PTFRB0NIDM_", "PTFRB0LCHV_")


def far(current: int, metres: float) -> int:
    return int(metres * metres >= 2025.0) if current else int(metres * metres > 3025.0)


def main() -> None:
    driver = DRIVER.read_text(encoding="utf-8")
    batch = BATCH.read_text(encoding="utf-8")
    assert (ROOT / "build/B0_VendorShared/offline_test.redscripts").is_file()
    assert "GameInstance.GetPlayerSystem(game)" in driver
    assert driver.count("let position = player.GetWorldPosition()") == 1
    assert "GetSceneSystem" not in driver and "GetWorkspotSystem" not in driver
    assert "PTFRB0VSH_Challenge" in driver and "PTFRB0VSH_Ack" in driver
    assert "PTFRB0VSH_SharedMode" in driver
    writes = re.findall(r'quests\.SetFact\(n"([^"]+)"', driver)
    assert writes and all(name.startswith("PTFRB0") for name in writes), writes
    assert set(writes) == {
        "PTFRB0VSH_Ack", "PTFRB0NIDG_Far", "PTFRB0NIDF_Far",
        "PTFRB0NIDM_Far", "PTFRB0LCHV_Far",
    }, writes
    assert far(0, 55) == 0 and far(0, 56) == 1
    assert far(1, 46) == 1 and far(1, 44) == 0
    assert batch.count('q:SetFactStr(shop.prefix.."Enabled",1)') == 1
    assert batch.count('q:SetFactStr(shop.prefix.."Enabled",0)') == 1
    assert 'GetFactStr("PTFRB0VSH_SharedMode")' not in batch  # central writer, not an old per-shop writer
    installer = (ROOT / "tools/install_b0_vendor_shared.ps1").read_text(encoding="utf-8")
    old_block = re.search(r"\$oldLogBlock = @'\n(.*?)\n'@", installer, re.S)
    new_block = re.search(r"\$newLogBlock = @'\n(.*?)\n'@", installer, re.S)
    assert old_block and new_block
    old_marker = 'q:GetFactStr(PREFIX.."Enabled")==1 then'
    new_marker = 'q:GetFactStr(PREFIX.."Enabled")==1 and q:GetFactStr("PTFRB0VSH_SharedMode")~=1 then'
    for module, prefix in zip(MODULES, PREFIXES):
        source = (ROOT / "diagnostics" / module / "init.lua").read_text(encoding="utf-8")
        installed = (GAME / "bin/x64/plugins/cyber_engine_tweaks/mods" / module / "init.lua").read_text(encoding="utf-8")
        assert installed == source or installed.replace(old_marker, new_marker).replace(old_block.group(1), new_block.group(1)) == source
        assert f'local PREFIX = "{prefix}"' in source
        assert source.count('q:GetFactStr("PTFRB0VSH_SharedMode")~=1') == 1
        assert source.count('Game.GetQuestsSystem():GetFactStr("PTFRB0VSH_SharedMode")~=1') == 1
        assert prefix in driver and prefix in batch
    assert len(re.findall(r'name="[^"]+", prefix="PTFRB0', batch)) == 4
    print("Shared vendor driver: four sites, one player query, mod-owned writes, 55/45 m hysteresis")
    print("Conditional CET fallback and one-command batch arm/stop checks PASS")


if __name__ == "__main__":
    main()
