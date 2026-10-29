from pathlib import Path
H=Path(__file__).resolve().parent
for name in ['package_01.ps1','deploy_01.ps1']:
    p=H/name;s=p.read_text(encoding='utf-8-sig')
    old=r'default\\quest_[a-f0-9]{16}'
    new=r'default\\(ep1\\)?quest_[a-f0-9]{16}'
    assert old in s;s=s.replace(old,new)
    if name=='package_01.ps1':
        old=r"$expected='base\worlds\03_night_city\_compiled\default\quest_'+$hash.ToString('x16')+'.streamingsector'"
        new=r"""$parent=[IO.Path]::GetDirectoryName([string]$binding.depot)
  if($parent -cnotin @('base\worlds\03_night_city\_compiled\default','base\worlds\03_night_city\_compiled\default\ep1')){throw 'Private sector namespace changed'}
  $expected=$parent+'\quest_'+$hash.ToString('x16')+'.streamingsector'"""
    else:
        old=r"$expected='base\worlds\03_night_city\_compiled\default\quest_'+([uint64]::Parse([string]$binding.node_ref_hash)).ToString('x16')+'.streamingsector'"
        new=r"""$parent=[IO.Path]::GetDirectoryName([string]$binding.depot)
 if($parent -cnotin @('base\worlds\03_night_city\_compiled\default','base\worlds\03_night_city\_compiled\default\ep1')){throw 'Private sector namespace changed'}
 $expected=$parent+'\quest_'+([uint64]::Parse([string]$binding.node_ref_hash)).ToString('x16')+'.streamingsector'"""
    assert old in s;s=s.replace(old,new);p.write_text(s,encoding='utf-8',newline='\n')
p=H/'package_01.py';s=p.read_text(encoding='utf-8-sig')
old="assert normalize(binding['depot'])=='base\\\\worlds\\\\03_night_city\\\\_compiled\\\\default\\\\quest_'+format(int(binding['node_ref_hash']),'016x')+'.streamingsector'"
new=r"""parent=normalize(binding['depot']).rsplit('\\',1)[0]
    assert parent in (r'base\worlds\03_night_city\_compiled\default',r'base\worlds\03_night_city\_compiled\default\ep1')
    assert normalize(binding['depot'])==parent+'\\quest_'+format(int(binding['node_ref_hash']),'016x')+'.streamingsector'"""
assert old in s;s=s.replace(old,new)
s=s.replace("proofs.append(H/'dependencyqueries_01.json')","proofs.extend([H/'dependencyqueries_01.json',H/'extend_ep1_packaging_01.py'])")
p.write_text(s,encoding='utf-8',newline='\n')
