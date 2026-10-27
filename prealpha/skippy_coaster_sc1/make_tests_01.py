from pathlib import Path
H=Path(__file__).resolve().parent
W=H.parents[1]
src=W/'prealpha/world_workspots_w2/test_deploy_w3_01.py'
out=H/'test_deploy_01.py'
assert not out.exists()
s=src.read_text()
for old,new in {
 'H / "candidate_04"':'H / "candidate_07"',
 'OLD = H / "candidate_02/package"':'OLD = W / "prealpha/world_workspots_w2/candidate_04/package"',
 'SCRIPT = H / "deploy_w3_01.ps1"':'SCRIPT = H / "deploy_01.ps1"',
 'H = Path(__file__).resolve().parent':'H = Path(__file__).resolve().parent\nW = H.parents[1]',
}.items():
 assert s.count(old)==1,(old,s.count(old))
 s=s.replace(old,new)
out.write_text(s)
print(out)
