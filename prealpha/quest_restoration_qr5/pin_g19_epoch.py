"""Pin investigation which includes the changed Spy/Steven carrier."""
from pathlib import Path
import sys
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
p=read(O/'progress.json');g=p['groups']['G19'];assert g['status']=='CLAIMED'and g['epoch']==0
g.update(epoch=5,source_epoch_manifest=str(O/'source_epoch_05.json'),source_epoch_sha256=sha(O/'source_epoch_05.json'),scope_note='Current candidate02 includes reviewed Steven future actor helper inside Spy entry carrier; compare original Spy bodies against pinned native and independently assert exact approved delta. Other recipe resources unchanged.')
write(O/'progress.json',p);print({'G19_epoch':'QR5:05','source':'candidate_02'})
