"""Capture one newly discovered string-encoded target, not the old bulk census."""
from pathlib import Path
import sys
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import write
p=O/'shared/tdb_vehicle_target_02/targets.json';assert not p.exists()
write(p,{'targets':['Vehicle.v_sport1_quadra_sport_r7_netrunner'],'provenance':'G18 actual native q304_car_retrieval node291 enables exact vehicle alias in a string property. Existing1200 record capture lacks ID182117316177. This is a read-only supplemental lookup, no gameplay change.'})
s=(O/'read_stock_records.ps1').read_text(encoding='utf-8-sig').replace("'shared/tdb_targets_01/targets.json'","'shared/tdb_vehicle_target_02/targets.json'")
target=O/'read_vehicle_record_02.ps1';assert not target.exists();target.write_text(s,encoding='utf-8')
print({'new_targets':1,'original_capture_preserved':True})
