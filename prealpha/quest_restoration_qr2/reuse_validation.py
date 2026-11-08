"""Validate exact-input equivalence for reused QR1 results without rebuilding."""
from pathlib import Path
import sys
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
B=read(W/'prealpha/quest_restoration_qr1/baseline.json');G=Path(B['game'])
C=read(W/'prealpha/quest_restoration_qr1/candidate_01/compile_01/result.json')
roots=[G/'r6/scripts',G/'red4ext/plugins/Codeware/Scripts',G/'red4ext/plugins/ArchiveXL/Scripts',G/'red4ext/plugins/TweakXL/Scripts',G/'red4ext/plugins/mod_settings']
current={str(p):sha(p) for r in roots for p in r.rglob('*.reds')}
old={p:h for p,h in C['input_pins'].items() if p.endswith('.reds')}
source_delta=[p for p in set(current)|set(old) if current.get(p)!=old.get(p)]
other_delta=[p for p,h in C['input_pins'].items() if not p.endswith('.reds') and (not Path(p).is_file() or sha(p)!=h)]
package_delta=[]
for r in B['package_files']:
 for where in [Path(B['candidate'])/'package',G]:
  p=where/r['path']
  if not p.is_file() or sha(p)!=r['after']:package_delta.append(str(p))
source=Path(B['candidate'])/'archive_source'
resource_delta=[d for d,h in B['private_resources'].items() if not (source/Path(d.replace('\\','/'))).is_file() or sha(source/Path(d.replace('\\','/')))!=h]
result={'status':'PASS' if not(source_delta or other_delta or package_delta or resource_delta) else 'INPUT_CHANGE_REQUIRES_ADJUDICATION','current_redscript_sources':len(current),'compiled_redscript_sources':C['source_count'],'source_delta':source_delta,'compiler_cache_input_delta':other_delta,'managed_package_or_installed_delta':package_delta,'source_payload_delta':resource_delta,'resource_count':len(B['private_resources']),'managed_paths':len(B['package_files']),'scope':'Exact current source/cache/compiler/package equivalence to QR1. No compiler, packer, installer or game launched. Reuses successful evidence only for unchanged inputs.'}
write(O/'reuse_validation.json',result)
print(result)
assert result['status']=='PASS'
