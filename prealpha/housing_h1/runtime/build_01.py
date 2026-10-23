"""Build the permanent housing v1 runtime/save contract without touching the game."""
import hashlib, importlib.util, json, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
IDS = ['h10', 'northside', 'japantown', 'glen', 'corpo']

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p, value):
    assert not p.exists(), p
    p.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')

def main(name):
    assert name.replace('_', '').isalnum()
    out = HERE / 'build' / name
    out.mkdir(parents=True, exist_ok=False)
    inventory_path = ROOT / 'research/housing_h1/compatibility/schema_inventory_01.json'
    parser_path = ROOT / 'research/housing_h1/compatibility/inventory_01.py'
    spec = importlib.util.spec_from_file_location('inventory', parser_path)
    parser = importlib.util.module_from_spec(spec); spec.loader.exec_module(parser)
    source = HERE / 'HousingState_01.reds'
    text = source.read_text(encoding='utf-8-sig')
    types = {'PTFR.Housing.' + n: {'parent': parent, 'fields': parser.fields(body)}
             for n, parent, body in parser.blocks(text) if parser.fields(body)}
    assert set(types) == {'PTFR.Housing.HousingRecord', 'PTFR.Housing.HousingState'}
    assert types['PTFR.Housing.HousingRecord']['fields'][0] == {'name': 'id', 'type': 'CName'}
    contract = {
        'contract': 'PTFR.Housing/save-v1', 'status': 'BETA_FORWARD_SAVE_CONTRACT_NOT_LIVE_PROOF',
        'schema_version': 1, 'migration_revision': 1, 'serialized_types': types,
        'property_ids_in_permanent_order': IDS, 'retained_home_outside_mutable_scope': 'kerry',
        'purchase_states': {'0': 'unpaid', '1': 'debit_pending', '2': 'paid_native_access_pending', '3': 'paid_access_acknowledged', '4': 'uncertain_no_automatic_retry_or_refund'},
        'origin_values': {'0': 'not_activated', '1': 'timely_native_boundary_observation', '2': 'late_import_or_unobserved_history'},
        'native_history': ['apartment_on', 'dlc6_apart_wat_nid_purchased', 'dlc6_apart_wbr_jpn_purchased', 'dlc6_apart_hey_gle_purchased', 'dlc6_apart_cct_dtn_purchased'],
        'history_semantics': 'Two settled observations are frozen only by a native PONR callback within 2.5 simulation seconds and unchanged values, before teardown. A missed callback or load beyond cutoff records unknown; the H10 service flag is never represented as a standalone ownership certificate. History never grants a purchase prerequisite.',
        'fact_ownership': {
            'runtime': ['PTFRH1_Ready', 'PTFRH1_Revision', 'PTFRH1_Fault'] + [f'PTFRH1_{i}_{s}' for i in IDS for s in ['Entitled', 'LossPermit', 'AccessPermit']],
            'native': [f'PTFRH1_{i}_{s}' for i in IDS for s in ['LossApplied', 'AccessApplied']],
            'purchase_ui': [f'PTFRH1_{i}_PurchaseReady' for i in IDS[1:]],
            'native_request_ui_consumed': [f'PTFRH1_{i}_PurchaseRequest' for i in IDS[1:]],
            'quarantine_exception': 'Runtime may clear PurchaseReady on invalid/unsupported state. Existing entitlement mirrors, receipts, original native facts and acknowledgments are never cleared by quarantine.'},
        'migration_rules': [
            'Install does not edit saves. Fresh all-default state initializes v1 once; partial state is never reset.',
            'Activated and native LossApplied are monotonic. Paid/acknowledged receipts can never re-enter the loss or payment path.',
            'Only explicit Purchase with fresh quote, exact source/proximity, safe player and native prerequisites may debit once.',
            'Only RemoveItem success AND exact synchronous balance delta records paid; uncertain/pending reloads never grant, retry or refund.',
            'Unsupported or malformed schemas preserve bytes/receipts and published access, disable known operation permits and all new purchases.',
            'Stable v1 successors must retain every type, field name/type/order, ID/order, fact meaning and saved native owner identity. Add fields only with inert defaults.',
            'A future migration must be monotonic and once-only; never repeat money, losses, rewards, quest dispatch, or native owner creation.',
            'Old catalogues/fingerprints and snapshot array-index meanings are frozen; additions use independent catalogues/classes.',
            'Forward compatibility is a release obligation verified against this contract; file rollback is not save rollback and downgrade support is not promised.'
        ],
        'source_pins': {source.relative_to(ROOT).as_posix(): sha(source), parser_path.relative_to(ROOT).as_posix(): sha(parser_path), inventory_path.relative_to(ROOT).as_posix(): sha(inventory_path)},
    }
    write(out / 'save_contract.json', contract)
    relative = 'r6/scripts/TowerContinued_Housing_H1/HousingState.reds'
    target = out / 'package' / relative; target.parent.mkdir(parents=True)
    shutil.copy2(source, target)
    pins = {p.relative_to(ROOT).as_posix(): sha(p) for p in [source, Path(__file__), HERE / 'test_01.py', parser_path, inventory_path, out / 'save_contract.json']}
    component = {'status': 'BUILT_H1_RUNTIME_NOT_LIVE', 'files': [{'relative': relative, 'sha256': sha(target)}],
                 'source_pins': pins, 'save_contract': (out / 'save_contract.json').relative_to(ROOT).as_posix(),
                 'save_contract_sha256': sha(out / 'save_contract.json'), 'schema_version': 1, 'migration_revision': 1,
                 'properties': IDS, 'currency_writes': 1, 'automatic_debits': 0, 'game_writes': False}
    write(out / 'component.json', component)
    print(json.dumps({'component': str(out / 'component.json'), 'sha256': sha(out / 'component.json')}))

if __name__ == '__main__': main(sys.argv[1])
