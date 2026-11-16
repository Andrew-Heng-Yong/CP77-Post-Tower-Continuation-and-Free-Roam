"""Create the HS4 two-file transaction from the inspected, pinned HS3 template."""
from pathlib import Path
from build import HERE, BASE, sha, one

def main():
    source=BASE/'deploy.py'
    assert sha(source)=='30FEA27495D546DA8128F815B23B3736EFB4348FC86A0F31A274A4AB7A119926'
    text=source.read_text()
    for old,new in (
        ('explicitly requested HS3 installation','requested global-latest HS4 installation'),
        ('from common import HERE, BASE, MANIFEST as BASELINE,','from build import HERE, BASE, BASELINE,'),
        ("EPOCH = 'HS3_NATIVE_HISTORY_CAPTURE'","EPOCH = 'HS4_GLOBAL_LATEST_HISTORY'"),
        ("BEFORE = 'QP2_QUEST_HISTORY_AUTOLOAD'","BEFORE = 'HS3_NATIVE_HISTORY_CAPTURE'"),
        ("SCHEMA = 'PTFR_HS3_NATIVE_HISTORY_CAPTURE_CORE_V1'","SCHEMA = 'PTFR_HS4_GLOBAL_LATEST_HISTORY_CORE_V1'"),
        ('CHANGES = {RED, LUA, ARCHIVE}','CHANGES = {RED, LUA}'),
    ): text=one(text,old,new)
    text=text.replace('candidate_04','candidate_02').replace('compile_04','compile_02').replace('core_history_capture_hs3_01','core_global_latest_hs4_01').replace('HS3_candidate_','HS4_candidate_')
    text=one(text,"    assert read(HERE / 'deployment_sources_01.json')['status'] == 'PASS_CURRENT_PROVIDERS_AND_REGISTRATIONS'", """    # No archive resource, ArchiveXL registration or generated phase node changes.
    for rel in (ARCHIVE, ARCHIVE+'.xl'):
        assert sha(PACKAGE/rel)==sha(game/rel)
    write(HERE/'unchanged_resources.json', {'status':'PASS_UNCHANGED_ARCHIVE_AND_XL',
        'files':{p:sha(PACKAGE/p) for p in (ARCHIVE,ARCHIVE+'.xl')},
        'baseline_manifest_sha256':sha(BASELINE), 'resource_or_node_additions':0})""")
    start=text.index('    working = []\n')
    end=text.index("    template = BASE / 'deploy_core.ps1'",start)
    text=text[:start]+'    working = []  # The transaction protects every current save by exact hash.\n'+text[end:]
    text=one(text,'9444BC4C10B91AEBB819CF67785198FBA291F4B39B3FD1679607A2608395A630','D84D6A09FACD7BBC7B7BFBFAA7F8FD7278EB4B20F26879804A4A3195485EBBEB')
    text=text.replace("HERE / 'deployment_sources_01.json'", "HERE / 'unchanged_resources.json'")
    text=one(text,'User explicitly requested: install and I will test. Install candidate_02 for the Manual Save 26 prospective HS3 capture test.',
        'Ongoing user-authorized mod installation/test; follow-up instruction: bruh just use global latest. Update the two snapshot scripts to HS4 candidate_02.')
    start=text.index('    for old, new in (\n',text.index('def prepare():'))
    end=text.index('    exclusive_text(INSTALLER, script)',start)
    replacement='''    for old, new in (
        ('# Replace exactly the snapshot REDscript, CET exporter and combined archive.', '# Replace exactly the two snapshot scripts for global-latest loading.'),
        (sha(BASE / 'core_manifest_01.json'), sha(MANIFEST)),
        ('PTFR_HS3_NATIVE_HISTORY_CAPTURE_CORE_V1', SCHEMA),
        ("$manifest.source_epoch -cne 'HS3_NATIVE_HISTORY_CAPTURE'", f"$manifest.source_epoch -cne '{EPOCH}'"),
        ("$manifest.predecessor_epoch -cne 'QP2_QUEST_HISTORY_AUTOLOAD'", f"$manifest.predecessor_epoch -cne '{BEFORE}'"),
        ('recovery/core_history_capture_hs3_01', 'recovery/core_global_latest_hs4_01'),
        ("$wanted=@('archive/pc/mod/zzzz_PTFR_Combined.archive','bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_HistorySnapshotHS1/init.lua','r6/scripts/PTFR_Consolidated/PTFR_HistorySnapshotHS1.reds')",
         '$wanted=@(' + ','.join("'" + p + "'" for p in sorted(CHANGES)) + ')'),
        ('$changes.Count -ne 3', '$changes.Count -ne 2'),
        ('Core51/three-file HS3 capture scope drift', 'Core51/two-file HS4 global-latest scope drift')):
        script = one(script, old, new)
'''
    text=text[:start]+replacement+text[end:]
    text=one(text,"'archive_source': str(HERE / 'archive_02/archive_source')","'archive_source': previous['archive_source']")
    text=one(text,"'unchanged_core_paths': 48","'unchanged_core_paths': 49")
    text=one(text,"'gameplay': 'PENDING_USER_MANUALSAVE_26_TEST'","'gameplay': 'PENDING_USER_GLOBAL_LATEST_LOAD_OBSERVATION'")
    with (HERE/'deploy.py').open('x',encoding='utf-8',newline='\n') as out:out.write(text)
    print('Created fresh HS4 deployment preparation; historical template preserved.')

if __name__=='__main__':main()
