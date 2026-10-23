import argparse, hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'prealpha/housing_h1/purchase'
def read(path): return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest().upper()
def q(s): return json.dumps(s, ensure_ascii=False)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--build',required=True); ap.add_argument('--locations'); args=ap.parse_args()
    target=BASE/'build'/args.build
    if target.exists(): raise SystemExit('immutable output already exists')
    catalogue=ROOT/'research/housing_h1/native/catalog_01.json'
    data=read(catalogue); properties=data['properties']
    locations=read(ROOT/args.locations) if args.locations else {'purchase':[]}
    locations={p['id']:p for p in locations['purchase']}
    paths=[]; offsets=[]; matches=[]
    for p in properties:
        pid=p['id']
        for kind,device in p['devices'].items():
            if kind in ('door','stash','wardrobe'):
                matches.append(f'    if Equals(kind, {q(kind)}) && HousingDevices.Matches(source, {q(device["path"])}) {{ return {q(pid)}; }}')
        if pid=='h10':
            paths.append(f'    if Equals(id, "h10") {{ return {q(p["devices"]["door"]["path"])}; }}')
        elif pid in locations:
            loc=locations[pid]
            paths.append(f'    if Equals(id, {q(pid)}) {{ return {q(loc["purchase_path"])}; }}')
            xyz=', '.join(str(float(loc['local_position'][k])) for k in ['X','Y','Z'])
            offsets.append(f'    if Equals(id, {q(pid)}) {{ return new Vector4({xyz}, 1.0); }}')
    purchase=BASE/'HousingPurchase.template_04.reds'; devices=BASE/'HousingDevices.template_04.reds'
    relationship=ROOT/'research/housing_h1/native/relationship_scope_01.json'
    relationship_data=read(relationship)
    relationship_devices=[d for d in relationship_data['devices'] if d['kind'] in ('stash','wardrobe')]
    assert len(relationship_devices)==5 and {d['id'] for d in relationship_devices}=={'judy','river','panam'}
    relationship_matches=[f'    if Equals(kind, {q(d["kind"])}) && HousingDevices.Matches(source, {q(d["path"])}) {{ return true; }}' for d in relationship_devices]
    package=target/'package/r6/scripts/TowerContinued_Housing_H1'; package.mkdir(parents=True)
    web=BASE/'HousingWebsite.template_01.reds'
    web_facts=[]
    for suffix in ['wat_nid','wbr_jpn','hey_gle','cct_dtn']:
        for ending in ['purchase_setup','purchase_possibility','purchase','purchased']:
            web_facts.append(f'    if Equals(fact, n"dlc6_apart_{suffix}_{ending}") {{ return true; }}')
    web_text=web.read_text(encoding='utf-8').replace('@@WEBSITE_FACTS@@','\n'.join(web_facts))
    (package/'HousingPurchase.reds').write_text(purchase.read_text(encoding='utf-8').replace('@@LOCATION_PATHS@@','\n'.join(paths)).replace('@@LOCATION_OFFSETS@@','\n'.join(offsets))+web_text,encoding='utf-8')
    (package/'HousingDevices.reds').write_text(devices.read_text(encoding='utf-8').replace('@@DEVICE_MATCHES@@','\n'.join(matches)).replace('@@RELATIONSHIP_DEVICE_MATCHES@@','\n'.join(relationship_matches)),encoding='utf-8')
    pins={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in [Path(__file__),catalogue,purchase,devices,web,relationship]}
    pins.update(relationship_data['source_pins'])
    if args.locations:pins[args.locations]=sha(ROOT/args.locations)
    for p,h in data.get('source_pins',{}).items(): pins[p]=h
    evidence=ROOT/'research/housing_h1/purchase/evidence_01.json'
    if evidence.exists():
        pins[str(evidence.relative_to(ROOT)).replace('\\','/')]=sha(evidence)
        pins.update(read(evidence)['source_pins'])
    web_evidence=ROOT/'research/housing_h1/purchase/web_audit_01.json'
    assert web_evidence.exists()
    pins[str(web_evidence.relative_to(ROOT)).replace('\\','/')]=sha(web_evidence)
    pins.update(read(web_evidence)['source_pins'])
    out={'status':'BUILT_H1_PURCHASE_NOT_LIVE' if len(locations)==4 else 'DRAFT_UNBOUND_DLC6_LOCATIONS','files':[{'relative':str(p.relative_to(target/'package')).replace('\\','/'),'sha256':sha(p)} for p in package.glob('*.reds')],'source_pins':pins,'resources':{},'boots':[],'locations_count':len(locations),'catalogue':str(catalogue.relative_to(ROOT)).replace('\\','/'),'locations_contract':args.locations,'relationship_devices_contract':str(relationship.relative_to(ROOT)).replace('\\','/'),'relationship_devices_count':len(relationship_devices),'relationship_device_scope':'Five typed exact Judy/River/Panam devices only; Panam marker excluded; Kerry devices untouched.','currency_writes':0,'native_purchase_fact_writes':0,'generic_door_egress_preserved':True,'persistent_fields':[],'game_writes':0}
    (target/'component.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
    print(target.relative_to(ROOT))
if __name__=='__main__':main()
