"""Preserve the failed workspace fixture and derive null-safe deployment v2."""
from common import *
changes={
 'deploy_01.ps1':('deploy_02.ps1',{
    '[IO.File]::Replace($stage,$target,$null)':'[IO.File]::Replace($stage,$target,[NullString]::Value)',
    'install_manifest_01.json':'install_manifest_02.json',
    'deployment_tests_01.json':'deployment_tests_02.json',
    "'deploy_fixtures'":"'deploy_fixtures_02'"}),
 'test_deploy_01.py':('test_deploy_02.py',{
    'install_manifest_01.json':'install_manifest_02.json',
    'deployment_tests_01.json':'deployment_tests_02.json',
    'deploy_01.ps1':'deploy_02.ps1',
    "'deploy_fixtures'":"'deploy_fixtures_02'"}),
 'make_install_manifest_01.py':('make_install_manifest_02.py',{
    'install_manifest_01.json':'install_manifest_02.json',
    'deploy_01.ps1':'deploy_02.ps1','test_deploy_01.py':'test_deploy_02.py'})}
for original,(name,replacements) in changes.items():
    text=(HERE/original).read_text(encoding='utf-8')
    for before,after in replacements.items():
        assert before in text,(name,before)
        text=text.replace(before,after)
    dest=HERE/name;assert not dest.exists();dest.write_text(text,encoding='utf-8')
    print(name)
