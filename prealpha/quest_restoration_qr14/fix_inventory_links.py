"""Preserve engine02; ignore non-source file links without traversing them."""
import shutil
from prepare import H, read, sha, write

def main():
    matrix = read(H / 'run_02_results.json')
    assert matrix['status'] == 'PASS_DEPLOYMENT_FIXTURES'
    script = H / 'deploy_core.ps1'
    assert sha(script) == matrix['installer_sha256']
    old = H / 'engine_02'; assert not old.exists(); old.mkdir()
    for name in ['deploy_core.ps1', 'test_deployment.py']:
        shutil.copyfile(H / name, old / name)
    s = script.read_text(encoding='utf-8')
    a = "   if($entry.kind -eq 'REPARSE_NOT_FOLLOWED'){throw ('Linked compiler inventory entry refused: '+$entry.path)}"
    b = """   if($entry.kind -eq 'REPARSE_NOT_FOLLOWED'){
    if(($entry.attributes -band [long][IO.FileAttributes]::Directory) -or [IO.Path]::GetExtension($entry.path) -ieq '.reds'){throw ('Linked compiler source/directory refused: '+$entry.path)}
    continue # Non-source file link (e.g. framework log): record, never follow.
   }"""
    assert s.count(a) == 1
    script.write_text(s.replace(a,b), encoding='utf-8')
    write(H / 'engine_02_to_03.json', {'before_sha256': sha(old / 'deploy_core.ps1'), 'after_sha256': sha(script),
        'matrix': {'path': str(H / 'run_02_results.json'), 'sha256': sha(H / 'run_02_results.json')},
        'change': 'Only CheckCompileInventory: ignore non-.reds file links without following. Continue refusing .reds links and directory links. Existing installed framework log symlinks are not compiler inputs.',
        'transaction_protocol_changed': False, 'final_guard_and_actual_payload_controls': 'Independent final-source review required; do not describe run02 as executing engine03.'})
    print({'status': 'ENGINE03_NOT_INSTALLED', 'sha256': sha(script)})

if __name__ == '__main__':
    main()
