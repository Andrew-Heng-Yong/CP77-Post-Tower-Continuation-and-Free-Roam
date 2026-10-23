"""Check the packaged graph and unchanged full vanilla scene/actor properties."""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
from plan_b0_ordinary_vendor_batch import ROOT, OUT, read, resource, graph_at, nm, edge_set, walk


def canonical(value, handles):
    if isinstance(value, list): return [canonical(v, handles) for v in value]
    if not isinstance(value, dict): return value
    if 'HandleRefId' in value:
        ref=str(value['HandleRefId'])
        return canonical(handles[ref],handles) if ref in handles else {'unresolved':ref}
    if 'HandleId' in value and 'Data' in value: return canonical(value['Data'],handles)
    return {k:canonical(v,handles) for k,v in value.items() if k not in ('sockets','HandleId')}


def handles(root): return {str(v['HandleId']):v['Data'] for v in walk(root) if 'HandleId' in v and 'Data' in v}


def main():
    cohort=read(OUT/'cohort.json');manifest=read(OUT/'validation/build_manifest.json')
    assert len(cohort['sites'])==25
    assert manifest['scene_replacements']==manifest['vanilla_replacements']==[]
    assert hashlib.sha256((OUT/'cohort.json').read_bytes()).hexdigest().upper()==manifest['cohort_sha256']
    archive=ROOT/'build/B0_OrdinaryVendorBatch'/manifest['archive']
    assert hashlib.sha256(archive.read_bytes()).hexdigest().upper()==manifest['sha256']
    xl=(ROOT/'archive/b0_ordinary_vendor_batch/TowerContinued_B0_OrdinaryVendorBatch.archive.xl').read_text()
    assert len(manifest['resources'])==25 and xl.count('- path:')==25
    assert all(p.startswith('towercontinued\\b0_ordinary_vendor_batch\\') and p.endswith('.questphase') and p in xl for p in manifest['resources'])
    existing={(s['spawn']['reference'],s['spawn']['entry']) for s in cohort['existing_owners']}
    new=set()
    for s in cohort['sites']:
        identity=(s['spawn']['reference'],s['spawn']['entry'])
        assert identity not in new|existing
        new.add(identity)
        original=resource(s['source']);oh=handles(original)
        vanilla=nm(graph_at(original,s['graph']))
        root=read(OUT/'validation'/f'{s["id"]}.questphase.json')['Data']['RootChunk'];rh=handles(root)
        outer=nm(root['graph']['Data']);inner=nm(outer[5]['phaseGraph']['Data'])
        for node in (s['scene_node'],s['spawn']['node'],s['despawn']['node'],s['close']['node']):
            assert canonical(inner[node],rh)==canonical(vanilla[node],oh),(s['id'],node,'vanilla payload changed')
        assert inner[s['scene_node']]['sceneFile']['DepotPath']['$value']==s['scene']
        assert set(outer)==set(range(12))
        for n in (2,9):
            c=outer[n]['condition']['Data']
            assert c['$type']=='questLogicalCondition' and c['operation']=='AND'
            facts={v['factName']:(v['comparisonType'],v['value']) for v in walk(c) if v.get('$type')=='questVarComparison_ConditionType'}
            expected={k:('Equal',v) for k,v in manifest['common_guards'].items()}
            expected.update({s['prefix']+'Enabled':('Equal',1),s['gate']:('Greater',0)})
            assert facts==expected
        for n,suffix in ((10,'Entries'),(11,'Exits')):
            v=outer[n]['type']['Data']
            assert v['factName']==s['prefix']+suffix and v['value']==1 and not v['setExactValue']
        assert set(edge_set(root['graph']['Data'],rh))=={
            (0,'Out',1,'In'),(1,'Out',2,'In'),(2,'Out',3,'In'),(3,'Out',9,'In'),
            (9,'True',4,'In'),(9,'False',2,'In'),(4,'Out',10,'In'),(10,'Out',5,'In1'),
            (5,'Out1',6,'In'),(6,'Out',11,'In'),(11,'Out',7,'In'),(7,'Out',8,'In'),(8,'Out',2,'In')}
        assert set(edge_set(outer[5]['phaseGraph']['Data'],rh))=={
            (s['input'],'Out',s['spawn']['node'],'In'),(s['input'],'Out',102,'In'),
            (102,'Out',s['far']['node'],'In'),(s['spawn']['node'],'Out',100,'In'),
            (100,'Out',s['close']['node'],'In'),(s['close']['node'],'Out',101,'In'),
            (101,'Out',s['scene_node'],s['scene_socket']),
            (s['far']['node'],'Out',s['despawn']['node'],'In'),(s['despawn']['node'],'Out',103,'In'),(103,'Out',s['output'],'In')}
        for v in walk(root):
            if v.get('$type')=='questSetVar_NodeType': assert v['factName'].startswith(s['prefix'])
        f=inner[s['far']['node']]['condition']['Data']['type']['Data']
        assert f['factName']==s['prefix']+'Far' and f['value']==1 and f['comparisonType']=='Equal'
        f=outer[8]['condition']['Data']['type']['Data']
        assert f['factName']==s['prefix']+'Far' and f['value']==0
    driver=(ROOT/'redscript/PTFR_B0_OrdinaryVendors/OrdinaryVendorDriver.reds').read_text()
    assert driver.count('player.GetWorldPosition()')==1 and driver.count('this.UpdateSite(q, position,')==25
    # Safety queries are confined to the optional bootstrap attempt, not
    # the per-site distance routine or the regular departure poll.
    assert driver.count('GetSceneSystem')==1 and driver.count('GetWorkspotSystem')==1
    assert driver.count('pending = this.AutoSite(')==25
    assert len(re.findall(r'^    this.AutoSite\(.*true\);',driver,re.M))==25
    assert all(x.startswith('PTFRB0OV') for x in re.findall(r'q.SetFact\(n"([^"]+)"',driver))
    assert 'if nearValue != 1 && old != 1 { return; }' in driver
    assert (ROOT/'build/B0_OrdinaryVendorBatch/offline_test.redscripts').is_file()
    report={'status':'PASS','sites':25,'scene_payloads_unchanged':25,
            'build_manifest_sha256':hashlib.sha256((OUT/'validation/build_manifest.json').read_bytes()).hexdigest().upper(),
            'driver_sha256':hashlib.sha256((ROOT/'redscript/PTFR_B0_OrdinaryVendors/OrdinaryVendorDriver.reds').read_bytes()).hexdigest().upper()}
    (OUT/'validation/graph_test.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: 25 full original scene/spawn/close payloads, exact native links, per-entry guards, counters, no owner overlap, one-position shared driver')


if __name__=='__main__':main()
