"""Project the checked Rite stage into matching script and graph admission inputs."""
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
BATCH = HERE.parent / 'resume_dispatcher_rd5_gigs_20261113_01'
sys.path.insert(0, str(BATCH))
from capture import read, sha, write


def main():
    assessment = BATCH / 'evidence_01/batch_assessment.json'
    stage = next(s for s in read(assessment)['stages'] if s['id'] == 'sts_wat_nid_05')
    fixture = stage['fixture_guard']
    quest = 'contacts/regina_jones/sts_wat_nid_05/'
    route = read(BATCH / 'evidence_02/rite_route.json')
    original = route['existing_entry_condition']
    tag = 'PTFRU9_' + stage['id'] + '_'
    native = {k: v for k, v in original.items() if k not in (tag+'Request', tag+'Permit')}
    native.update(fixture['facts'])
    native.update({tag+'ResumeRequested': 1, tag+'ResumePermit': 1,
                   tag+'Request': 0, tag+'Started': 0, tag+'MainFinished': 0,
                   tag+'OwnerFinished': 0, tag+'CreditEntered': 0, tag+'CreditDone': 0,
                   'sts_wat_kab_nid_05_combat': 0})
    phone = {quest+'brief': 2, quest+'debrief': 1, quest+'sts_wat_nid_05_debrief': 1}
    guard = {'id': stage['id'], 'tag': tag, 'stage': 'get_to_clinic',
             'journals': fixture['journals'], 'history_facts': fixture['facts'],
             'live_phone': phone, 'native_facts': native,
             'item': 'Keycards.nid_05_keycard',
             'assessment_sha256': sha(assessment)}
    write(HERE / 'evidence_01/admission.json', guard)


if __name__ == '__main__':
    main()
