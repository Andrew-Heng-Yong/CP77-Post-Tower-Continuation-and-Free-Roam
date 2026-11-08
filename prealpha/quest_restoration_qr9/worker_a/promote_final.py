"""Promote only the prepared workspace tool alias; this is not game deployment."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
source=H/'deploy_qr9_guarded_final.ps1';target=H/'deploy_qr9_guarded.ps1';old=H/'evidence/deploy_guarded_C8EE.ps1'
before='C8EE599B3898E4A7C28B5E4FA51D1B768D7EA53C24B7913AC0213B1D9F64DD7A';after='CE020172988081100199A35C9FAA9131444DB4DED52893480F2BA746EFFDA39E'
assert sha(source)==after and sha(target)==before and sha(old)==before
out=H/'canonical_promotion_01.json';assert not out.exists()
target.write_bytes(source.read_bytes());assert sha(target)==after and target.read_bytes()==source.read_bytes()
result=dict(status='PASS_WORKSPACE_TOOL_CANONICAL_ALIAS_PROMOTED',source=str(source),canonical=str(target),before_sha256=before,after_sha256=after,bytes=target.stat().st_size,preserved_predecessor=str(old),game_files_changed=0,save_files_changed=0,installer_invocations=0)
out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(status=result['status'],canonical_sha256=sha(target),receipt_sha256=sha(out))))
