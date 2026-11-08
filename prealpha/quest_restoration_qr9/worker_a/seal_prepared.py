"""Seal reviewed prepared tools; no real installer action."""
from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def read(p):return json.loads(p.read_text())
previous=H/'prepared_01.json';p=read(previous)
canonical=H/'deploy_qr9_guarded.ps1';assert sha(canonical)==p['final_source']['sha256']
peer=H.parent/'worker_c/reviews/installer_final_01/review.json';r=read(peer)
assert r['status']=='APPROVE_FROZEN_OFFLINE_INSTALLER_WITH_EXPLICIT_AUTHORIZATION_AND_RUNTIME_LIMITS'and r['source_sha256']==sha(canonical)
assert sha(peer)=='D5A13B8DF11C4E61F8DA800B6211A671E016F52E541F6A541E53ABDFA9D605A1'
promotion=H/'canonical_promotion_01.json';assert read(promotion)['after_sha256']==sha(canonical)
p.update(status='PREPARED_FIXTURE_VERIFIED_INDEPENDENTLY_REVIEWED_NOT_DEPLOYED',predecessor=dict(path=str(previous),sha256=sha(previous)),canonical_promotion=dict(path=str(promotion),sha256=sha(promotion),status='PASS'),independent_installer_review=dict(path=str(peer),sha256=sha(peer),status=r['status'],final_checks=32,prior_independent_scenarios=4,prior_independent_assertions=84),canonical_script=dict(path=str(canonical),sha256=sha(canonical)))
p['documents']=[dict(path=str(H/n),sha256=sha(H/n))for n in ['REPORT.md','DEPLOYMENT.md']]
out=H/'prepared_02.json';assert not out.exists();out.write_text(json.dumps(p,indent=2)+'\n');print(json.dumps(dict(path=str(out),status=p['status'],sha256=sha(out))))
