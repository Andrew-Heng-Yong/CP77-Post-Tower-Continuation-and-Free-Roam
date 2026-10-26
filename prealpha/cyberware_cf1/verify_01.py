"""Verify compiled preservation and bind the diagnosed native deletion path."""
from pathlib import Path
import hashlib,json,re
H=Path(__file__).resolve().parent;W=H.parent.parent;C=H/'candidate_01'
B=W/'prealpha/h10_h6/candidate_01/compile_04/compiled.script'
A=C/'compile_01/compiled.script'
before=B.read_text(encoding='utf-8-sig');after=A.read_text(encoding='utf-8-sig')
checks=[]
def check(name,condition):
 if not condition:raise AssertionError(name)
 checks.append(name)
def normalize(s):return re.sub(r'\b(wrapper|proxy)\$\d+',r'\1$GENERATED',s)
def classes(s):
 result={}
 for m in re.finditer(r'(?m)^(?:(?:public|abstract|native|importonly|final) )*class ([\w.$]+)[^{\n]*\{',s):
  end=s.index('\n}',m.end())+2;result[m.group(1)]=s[m.start():end]
 return result
def method(s,name):
 m=re.search(r'(?m)^  [^\n]*\bfunc '+re.escape(name)+r'\(',s);assert m,name
 end=re.search(r'(?m)^  }',s[m.end():]);assert end,name
 return s[m.start():m.end()+end.end()]
bc=classes(before);ac=classes(after)
check('compiled class identities unchanged',bc.keys()==ac.keys())
for name in bc:
 if name not in ('EquipmentSystemPlayerData','PowerUpCyberwareEffector'):
  check('unchanged compiled class '+name,normalize(bc[name])==normalize(ac[name]))
for name in ('PTFRR1Remove','PTFRR1RestrictedEquipped','PTFRR1OriginalPurchaseRequirements','RemoveSlotGLPs','RemoveEquipGLPs','UnequipCyberwareParts'):
 check('unchanged equipment method '+name,normalize(method(bc['EquipmentSystemPlayerData'],name))==normalize(method(ac['EquipmentSystemPlayerData'],name)))
for name in ('Initialize','ActionOn','PowerUpCyberwareInSlot'):
 check('unchanged native effector '+name,normalize(method(bc['PowerUpCyberwareEffector'],name))==normalize(method(ac['PowerUpCyberwareEffector'],name)))
for name in bc:
 check('unchanged persistent fields '+name,re.findall(r'(?m)^  .*persistent.*;$',bc[name])==re.findall(r'(?m)^  .*persistent.*;$',ac[name]))
eff=ac['PowerUpCyberwareEffector'];proxy=re.search(r'protected func (proxy\$\d+)\(',eff).group(1)
original=method(bc['PowerUpCyberwareEffector'],'Uninitialize').replace('func Uninitialize(', 'func ORIGINAL(')
delegated=method(eff,proxy).replace('func '+proxy+'(', 'func ORIGINAL(')
check('original effector deletion body retained as fallback',original==delegated)
source=(H/'CyberwarePreservationCF1.reds').read_text()
check('addition does not write inventory or saved fields',not re.search(r'\b(GiveItem|RemoveItem|AddPart|RemovePart|SetFact|persistent|addField)\b',source))
helper=method(ac['EquipmentSystemPlayerData'],'PTFRCF1PreservesExactItem')
for term in ('ItemID.IsValid(id)','ItemID.IsValid(this.ptfrr1PreserveParts)','id == this.ptfrr1PreserveParts','CyberwarePolicy.Denied(this.m_owner, id)'):
 check('compiled exact preservation gate '+term,term in helper)
check('scope has bounded skeleton slot and same owner data','this.m_playerData == EquipmentSystem.GetData(this.m_owner)' in eff and 'gamedataEquipmentArea.MusculoskeletalSystemCW' in eff and 'this.m_targetEquipSlotIndex >= 0' in eff and 'this.m_targetEquipSlotIndex < this.m_playerData.GetNumberOfSlots' in eff)
records=json.loads((W/'diagnostics/alpha_cyberware_20261025_01/local_repro_02/cleanup_records_02.json').read_text(encoding='utf-8-sig'))['records'];byid={x['id']:x for x in records}
for slot,record in enumerate((197133779525,195406304255,193532880752)):
 packages=byid[record]['fields']['OnInsertion'];effectors=[byid[e]['fields'] for p in packages for e in byid[p]['fields'].get('effectors',[])]
 check('stock skeleton slot bound to destructive native effector '+str(slot),any(e.get('effectorClassName')=='PowerUpCyberwareEffector' and e['targetEquipArea']=='MusculoskeletalSystemCW' and e['targetEquipSlotIndex']==str(slot) for e in effectors))
check('native removal clears slot after removing slot packages',before.index('this.RemoveSlotGLPs(',before.index('private final func UnequipItem(equipAreaIndex:')) < before.index('this.RemoveEquipGLPs(currentItem)',before.index('private final func UnequipItem(equipAreaIndex:')))
result={'status':'PASS_COMPILED_AND_SOURCE_CHECKS_NOT_LIVE','checks':checks,'count':len(checks),'unchanged_classes_except_two':len(bc)-2,'baseline_compiled_source_sha256':hashlib.sha256(B.read_bytes()).hexdigest().upper(),'candidate_compiled_source_sha256':hashlib.sha256(A.read_bytes()).hexdigest().upper(),'limitations':['No live effector call trace yet. CD1 readback and CF1 suppression log must pass on retry.','Failure in tester log predates CD1; local CD1 reproduction proves loss of exact advanced item, not total loss of every underlying base item.']}
p=C/'verification_01.json';assert not p.exists();p.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='checks'}))
