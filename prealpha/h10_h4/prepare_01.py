"""Narrow H10 purchase eligibility to real control, dialogue and motion guards."""
from pathlib import Path
import hashlib,json,shutil
H=Path(__file__).resolve().parent;W=H.parent.parent;C=H/'candidate_01';G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
rel='r6/scripts/TowerContinued_Housing_H1/HousingState.reds'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
b=C/'before'/rel;b.parent.mkdir(parents=True,exist_ok=True);assert not b.exists();shutil.copyfile(G/rel,b)
s=b.read_text(encoding='utf-8-sig');a=s.index('  private func SafeActor(player: ref<PlayerPuppet>) -> Bool {');z=s.index('  private func ProfileReady() -> Bool {',a)
safe=s[a:z];assert safe.count('scenes.IsEntityInScene(player.GetEntityID()) ||')==1
purchase=safe.replace('SafeActor(player:', 'PurchaseSafeActor(player:').replace('scenes.IsEntityInScene(player.GetEntityID()) || ', '')
purchase='''  // Post-ending free roam can retain an ambient scene ownership flag even
  // after V has normal control. Only purchase eligibility permits that case.
  // The original migration guard and every other player safeguard remain.
'''+purchase
s=s[:z]+purchase+s[z:]
old='this.Fact("PTFRPA2_Finished") == 1 && this.SafeActor(player) &&';new='this.Fact("PTFRPA2_Finished") == 1 && this.PurchaseSafeActor(player) &&'
assert s.count(old)==1;s=s.replace(old,new)
old='if !this.SafeActor(player) {';new='if !this.PurchaseSafeActor(player) {'
assert s.count(old)==1;s=s.replace(old,new)
out=C/'package'/rel;out.parent.mkdir(parents=True,exist_ok=True);assert not out.exists();out.write_text(s,encoding='utf-8')
assert sha(b)==sha(G/rel)
changes=[{'target':rel,'before':sha(b),'after':sha(out)}]
(C/'changes_01.json').write_text(json.dumps(changes,indent=2)+'\n')
# Use the same reproducible current game stack, but keep H3 proof sources pinned.
script=(W/'prealpha/h10_h3/compile_01.py').read_text(encoding='utf-8-sig')
assert not (H/'compile_01.py').exists();(H/'compile_01.py').write_text(script,encoding='utf-8')
print(json.dumps(changes))
