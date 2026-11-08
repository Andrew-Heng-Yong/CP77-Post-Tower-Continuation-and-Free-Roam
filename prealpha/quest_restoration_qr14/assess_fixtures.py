"""Reconcile existing saved evidence with fresh hashes; never reparse or write saves."""
from pathlib import Path
from collections import Counter
import csv, json
from prepare import H, read, sha, write

def main():
    q12 = H.parent / 'quest_restoration_qr12'
    q13 = H.parent / 'quest_restoration_qr13'
    ip = q12 / 'analysis_final_02/verified_fixture_inventory.json'
    inventory = read(ip)
    catalogue = read(q12 / 'catalogue.json')
    captured = set(catalogue['facts'])
    baseline = read(H / 'baseline.json')
    pins = baseline['save_sha256']
    inputs = [ip, q12 / 'catalogue.json', q12 / 'saved_cache_bindings.json',
        q12 / 'observations/runtime_eligibility_02/result.json', q13 / 'TEST_CARDS.md',
        q13 / 'worker_a/enrollment_contract_01.json', q13 / 'worker_c/ronald_serialized_01/review.json']
    for r in inventory['summary']['parser_inputs']:
        assert sha(r['path']) == r['sha256'], r['path']
    names = ['q302_ronald_messages_enabled', 'q302_ronald_known', 'q302_05_ronald_messages',
             'q302_05_ronald_counter', 'q302_ronald_tree', 'PTFRQR7_RonaldNews_Issued']
    rows = []
    seen_current = set()
    for r in inventory['rows']:
        p = Path(r['source'])
        actual = pins.get(str(p)) if r['kind'] == 'GAME_SAVE' else (sha(p) if p.is_file() else None)
        binding = 'EXACT_BODY' if actual == r['sha256'] else 'CHANGED_OR_MISSING_BODY'
        if r['kind'] == 'GAME_SAVE':
            seen_current.add(str(p))
        evidence = {}
        facts = r.get('saved_parse', {}).get('facts', {})
        for n in names:
            evidence[n] = {'status': 'NOT_CAPTURED_BY_QR12_CATALOGUE' if n not in captured else
                ('PRESENT' if facts.get(n) else 'SERIALIZED_ABSENCE_NOT_RUNTIME_ZERO'), 'rows': facts.get(n, [])}
        status = 'UNKNOWN'
        reason = 'First-offer predicates/contact state and saved child support refresh are not established.'
        if binding != 'EXACT_BODY':
            reason = 'Old saved evidence is stale for this body; no automatic inference or reparse.'
        elif r['kind'] != 'GAME_SAVE':
            reason = 'Offline backup is not an authorized loadable genuine Tower fixture; eligibility/owners remain unknown.'
        elif not any(s.get('scenario') == 'RONALD_prospective_news' and s.get('status') != 'NOT_TESTABLE' for s in r['scenarios']):
            status = 'NOT_TESTABLE'; reason = 'QR12 marks this history unavailable for post-Tower testing; do not replay The Tower to manufacture eligibility.'
        rows.append({'source': str(p), 'kind': r['kind'], 'slot': r['slot_directory'],
            'saved_evidence_sha256': r['sha256'], 'current_sha256': actual, 'binding': binding,
            'lineage': r['lineage'], 'status': status, 'reason': reason, 'fact_evidence': evidence,
            'owner_status': 'OPAQUE_NO_EXECUTING_OWNER_PROOF', 'contact_state': 'OPAQUE_RAW_JOURNAL_RECORD_IS_NOT_ENUM'})
    for p, digest in pins.items():
        if Path(p).name == 'sav.dat' and p not in seen_current:
            rows.append({'source': p, 'kind': 'GAME_SAVE', 'slot': Path(p).parent.name,
                'saved_evidence_sha256': None, 'current_sha256': digest, 'binding': 'NO_REUSED_PARSE',
                'lineage': 'UNKNOWN', 'status': 'UNKNOWN', 'reason': 'New slot since QR12; exact history/contact/owner not decoded.',
                'fact_evidence': {}, 'owner_status': 'UNKNOWN', 'contact_state': 'UNKNOWN'})
    result = {'status': 'NO_READY_NEW_BEHAVIOR_FIXTURE', 'method': 'Reuse QR12 parsed evidence only when body hashes still bind. Fresh QR14 save hash census; no repeated static audit or saved-state parser.',
        'inputs': [{'path': str(p), 'sha256': sha(p)} for p in inputs],
        'scenario': 'QR13_Ronald_first_consent_contact', 'rows': rows,
        'counts': dict(Counter((r['kind'] + ':' + r['status']) for r in rows)),
        'body_bindings': dict(Counter(r['binding'] for r in rows)), 'ready': [],
        'new_first_offer_facts_not_previously_captured': [n for n in names if n not in captured],
        'exact_missing': ['Genuine retained-Tower fixture with naturally unoffered subscription (native1730 uses q302_05_ronald_messages>=1 to skip offer); prior refusal cannot be reset.',
            'Native known/topic branch and q302_05_ronald_counter history, exact Inactive Ronald contact, natural real consent.',
            'Freshly admitted existing B0 child5 support ownership, or independently qualified saved-child graph/prefab transition; fact/journal presence is not proof.'],
        'brendan': {'status': 'NOT_TESTABLE_ON_KNOWN_SELECTED_FIXTURES', 'reason': 'ManualSave23/24 HS1 origins are post_ending_fallback; live Inactive journals/private Issued1 Entered1 do not satisfy strict earned final-Theo certificate/owner conditions.',
            'no_fabrication': True},
        'no_repeat': ['Bullets/Jinguji and both load checks', 'Zane shop', 'Wilson', 'Cynthia', 'D00E', 'user-completed Skippy'],
        'game_launches': 0, 'save_writes': 0, 'live_API_calls': 0,
        'next': 'No immediate gameplay test. Deployment readiness is separate from fixture eligibility. After authorization/installation, only genuine new natural eligibility may qualify a short S02 capture; do not reset history or assume old child acquires new support.'}
    write(H / 'fixture_assessment.json', result)
    with (H / 'fixture_inventory.csv').open('x', newline='', encoding='utf-8') as f:
        fields = ['source','kind','slot','saved_evidence_sha256','current_sha256','binding','lineage','status','reason','owner_status','contact_state']
        w = csv.DictWriter(f, fields, extrasaction='ignore'); w.writeheader(); w.writerows(rows)
    print({'status': result['status'], 'rows': len(rows), 'counts': result['counts'], 'binding': result['body_bindings'], 'not_captured': result['new_first_offer_facts_not_previously_captured']})

if __name__ == '__main__':
    main()
