"""Check the actual aggregate overlay against installed and housing save identities.

This freezes a forward-compatibility baseline; it does not execute or edit a save.
"""
import hashlib, importlib.util, json, re, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
GAME=Path('C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077')
CHECKS=[]; PINS={}
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def check(label, value):
    assert value,label
    CHECKS.append(label)
def pin(p,digest=None):
    p=Path(p).resolve();actual=sha(p)
    check('pin '+str(p),digest is None or actual==digest)
    PINS[str(p)]=actual
    return p
def module_types(text,parser):
    module=re.search(r'^module\s+(\S+)',text,re.M)
    return {(module.group(1)+'.' if module else '')+n:{'parent':p,'fields':parser.fields(b)} for n,p,b in parser.blocks(text) if parser.fields(b)}
def body(text,name):
    m=re.search(r'\bfunc '+re.escape(name)+r'\([^\n]*\)\s*->\s*[^\{]+\{',text);assert m,name
    depth=1
    for i in range(m.end(),len(text)):
        if text[i]=='{':depth+=1
        elif text[i]=='}':
            depth-=1
            if depth==0:return text[m.end():i]
    raise AssertionError(name)
def fact(name,value):
    return {'$type':'questFactsDBCondition','type':{'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':name,'value':value}}
def logical(operation,conditions):return {'$type':'questLogicalCondition','conditions':conditions,'operation':operation}

class Graphs:
    def __init__(self,doc):
        self.handles={};self.graphs={};self.payloads={}
        def scan(x):
            if isinstance(x,dict):
                if 'HandleId' in x and 'Data' in x:self.handles[str(x['HandleId'])]=x['Data']
                for v in x.values():scan(v)
            elif isinstance(x,list):
                for v in x:scan(v)
        scan(doc)
        self.root=doc['Data']['RootChunk']
        self.visit(self.resolve(self.root['graph']),'root')
    def resolve(self,x):
        if isinstance(x,dict) and 'Data' in x and 'HandleId' in x:return x['Data']
        if isinstance(x,dict) and 'HandleRefId' in x:return None if str(x['HandleRefId'])=='-1' else self.handles[str(x['HandleRefId'])]
        return x
    def key(self,x):return str(x.get('HandleId',x.get('HandleRefId')))
    def clean(self,x):
        x=self.resolve(x)
        if isinstance(x,dict):return {k:self.clean(v) for k,v in x.items() if k not in ['HandleId','HandleRefId','sockets','phaseGraph']}
        if isinstance(x,list):return [self.clean(v) for v in x]
        return x
    def visit(self,g,path):
        nodes=[self.resolve(n) for n in g['nodes']];sockets={};ids=[];edges=set()
        for n in nodes:
            sig=[]
            for s in n.get('sockets',[]):
                value=self.resolve(s);name=value['name']['$value'];typ=value['type']
                sockets[self.key(s)]=(n['id'],name,typ);sig.append((name,typ))
            ids.append({'id':n['id'],'type':n['$type'],'sockets':sorted(sig)})
            self.payloads[(path,n['id'])]=self.clean(n)
            if 'phaseGraph' in n and self.resolve(n['phaseGraph']):self.visit(self.resolve(n['phaseGraph']),path+'/'+str(n['id']))
        for n in nodes:
            for s in n.get('sockets',[]):
                for c in self.resolve(s).get('connections',[]):
                    c=self.resolve(c);src=self.key(c['source']);dst=self.key(c['destination'])
                    assert src in sockets and dst in sockets,(path,src,dst)
                    a,b=sockets[src],sockets[dst];edges.add((a[0],a[1],b[0],b[1]))
        self.graphs[path]={'nodes':sorted(ids,key=lambda n:n['id']),'edges':sorted(edges)}

def main(build):
    build=Path(build).resolve();check('build workspace scope',build.is_relative_to(ROOT/'prealpha/housing_h1/build'))
    manifest_path=pin(build/'build.json');m=read(manifest_path)
    check('aggregate status',m['status']=='BUILT_H1_LIVE_PENDING')
    parser_path=pin(ROOT/'research/housing_h1/compatibility/inventory_01.py')
    spec=importlib.util.spec_from_file_location('schema_inventory',parser_path);parser=importlib.util.module_from_spec(spec);spec.loader.exec_module(parser)
    inventory_path=pin(ROOT/'research/housing_h1/compatibility/schema_inventory_01.json');inventory=read(inventory_path)
    contract_path=pin(ROOT/m['persistence_contract'],m['persistence_contract_sha256']);contract=read(contract_path)
    check('permanent contract identity',contract['contract']=='PTFR.Housing/save-v1' and contract['schema_version']==1 and contract['migration_revision']==1)
    check('permanent property slots',contract['property_ids_in_permanent_order']==['h10','northside','japantown','glen','corpo'])
    package=build/'package';replacements={};stage_types={}
    for f in m['files']:
        p=pin(package/f['relative'],f['sha256'])
        if f['action']=='replace':replacements[f['relative']]=p
        if p.suffix=='.reds':stage_types.update(module_types(p.read_text(encoding='utf-8-sig'),parser))
    old_types={};oldfiles={}
    for rel,digest in inventory['installed_script_pins'].items():
        original=pin(GAME/rel,digest);candidate=replacements.get(rel,original)
        text=candidate.read_text(encoding='utf-8-sig');old_types.update(module_types(text,parser));oldfiles[rel]=candidate
    for name,old in inventory['serialized_types'].items():
        check('old saved type '+name,name in old_types)
        new=old_types[name]
        check('old parent '+name,new['parent']==old['parent'])
        check('old field names/types/order '+name,new['fields'][:len(old['fields'])]==old['fields'])
    for name,old in contract['serialized_types'].items():
        check('housing saved type '+name,name in stage_types)
        check('housing saved contract '+name,stage_types[name]==old)
    for rel,baseline in inventory['catalogue_sources_to_preserve'].items():
        p=oldfiles[rel]
        if rel not in replacements:check('saved catalogue bytes '+rel,sha(p)==baseline['sha256'])
        else:check('saved catalogue fingerprints '+rel,sorted(set(re.findall(r'n?"([A-F0-9]{64})"',p.read_text(encoding='utf-8-sig'))))==baseline['quoted_fingerprints'])
    entry='r6/scripts/PTFR_PreAlpha/PA1/PreAlphaEntry.reds'
    old=(GAME/entry).read_text(encoding='utf-8-sig');new=(package/entry).read_text(encoding='utf-8-sig')
    for name in ['Catalogue','ShapeValid','Certified','CaptureBeforeEnding','Freeze','Dispatch','ReadGig','Same']:
        check('entry certificate/catalogue retained '+name,body(old,name)==body(new,name))
    check('development auto admission disabled','return false;' in body(new,'DevelopmentLateEnding'))
    check('established continuation does not certify','EstablishedHandoff' not in body(new,'Certified')+body(new,'Freeze')+body(new,'Dispatch'))
    check('housing transition gates prepared',new.index('housing.HousingReadyForReveal()')<new.index('SetFact(n"PTFRPA2_Prepared", 1)'))
    for rel,digest in inventory['installed_xl_pins'].items():pin(GAME/rel,digest)
    check('old XL boot files not replaced',not any(rel in replacements for rel in inventory['installed_xl_pins']))
    native_row=next(c for c in m['components'] if c['kind']=='native')
    nativepath=pin(ROOT/native_row['manifest'],native_row['sha256']);native=read(nativepath)
    ntpath=pin(ROOT/native_row['tests'],native_row['tests_sha256']);nt=read(ntpath)
    check('native component test pass',nt['status'].startswith('PASS') and nt.get('component_sha256',nt.get('build_sha256'))==sha(nativepath))
    depot='towercontinued\\b0_h10_persistent\\h10_owner.questphase'
    m10depot='towercontinued\\relationship_mirrors\\m10_owner.questphase'
    check('only two known saved-owner overrides',set(native['override_donors'])=={depot,m10depot})
    donor=native['donor']['rows'][0]
    oldraw=pin(ROOT/donor['raw'],donor['raw_sha256']);oldjson=pin(ROOT/donor['json'],donor['json_sha256'])
    pin(nativepath.parent/'source'/depot,native['resources'][depot])
    # The native component must bind the actual override's unique fresh readback.
    rb=pin(ROOT/native['h10_override_readback'],native['h10_override_readback_sha256'])
    before=Graphs(read(oldjson));after=Graphs(read(rb))
    check('saved H10 graph IDs/types/socket identities/edges retained',before.graphs==after.graphs)
    check('saved H10 payload keys retained',set(before.payloads)==set(after.payloads))
    for key,oldpayload in before.payloads.items():
        newer=after.payloads[key]
        if key==('root',2):
            oldrest={k:v for k,v in oldpayload.items() if k!='condition'};newrest={k:v for k,v in newer.items() if k!='condition'}
            check('saved H10 admission node only condition changed',oldrest==newrest)
            condition=newer['condition']
            expected=logical('AND',[oldpayload['condition'],logical('OR',[fact('PTFRH1_Ready',0),fact('PTFRH1_h10_Entitled',1)])])
            check('saved H10 exact pre-policy or entitlement conjunct',condition==expected)
        else:check('saved H10 payload unchanged '+str(key),oldpayload==newer)
    check('saved H10 prefab scope retained',before.clean(before.root.get('phasePrefabs',[]))==after.clean(after.root.get('phasePrefabs',[])))
    check('saved owner not booted again',depot not in m['boots'])
    relationship_donor_rel='research/housing_h1/native/relationship_donors_01/inventory.json'
    relationship_donors_path=pin(ROOT/relationship_donor_rel,native['source_pins'][relationship_donor_rel])
    m10donor=next(r for r in read(relationship_donors_path)['rows'] if r['depot']==m10depot)
    pin(ROOT/m10donor['raw'],m10donor['raw_sha256'])
    m10json=pin(ROOT/m10donor['json'],m10donor['json_sha256'])
    pin(nativepath.parent/'source'/m10depot,native['resources'][m10depot])
    m10rb=pin(ROOT/native['m10_override_readback'],native['m10_override_readback_sha256'])
    m10before=Graphs(read(m10json));m10after=Graphs(read(m10rb))
    check('saved m10 graph IDs/types/socket identities/edges retained',m10before.graphs==m10after.graphs)
    check('saved m10 payload keys retained',set(m10before.payloads)==set(m10after.payloads))
    for key,oldpayload in m10before.payloads.items():
        newer=m10after.payloads[key]
        if key in [('root',7),('root',13)]:
            check('saved m10 only condition changed '+str(key),{k:v for k,v in oldpayload.items() if k!='condition'}=={k:v for k,v in newer.items() if k!='condition'})
            check('saved m10 exact suspension conjunct '+str(key),newer['condition']==logical('AND',[oldpayload['condition'],fact('PTFRRM10_Suspended',0)]))
        else:check('saved m10 payload unchanged '+str(key),oldpayload==newer)
    check('saved m10 prefab scope retained',m10before.clean(m10before.root.get('phasePrefabs',[]))==m10after.clean(m10after.root.get('phasePrefabs',[])))
    check('saved m10 owner not booted again',m10depot not in m['boots'])
    runtime=(package/'r6/scripts/TowerContinued_Housing_H1/HousingState.reds').read_text(encoding='utf-8-sig')
    check('native relationship policy required before reveal','this.Fact("PTFRH1_RelationshipsApplied") != 1' in body(runtime,'HousingReadyForReveal'))
    native_identities={};native_facts=set();all_native_mod_facts=set()
    for dep in m['boots']:
        check('new owner permanent housing namespace '+dep,dep.startswith('towercontinued\\housing_h1\\native\\'))
        name=dep.split('\\')[-1].replace('.questphase','.json')
        docpath=pin(nativepath.parent/'readback'/name)
        graphs=Graphs(read(docpath));native_identities[dep]=graphs.graphs
    for dep in native['resources']:
        if dep==depot:docpath=rb
        elif dep==m10depot:docpath=m10rb
        else:
            name=dep.split('\\')[-1]
            name=name+'.json' if name.endswith('.scene') else name.replace('.questphase','.json')
            docpath=pin(nativepath.parent/'readback'/name)
        native_facts.update(re.findall(r'\bPTFRH1_[A-Za-z0-9_]+\b',docpath.read_text(encoding='utf-8-sig')))
        all_native_mod_facts.update(re.findall(r'\bPTFR[A-Za-z0-9_]+\b',docpath.read_text(encoding='utf-8-sig')))
    report={'status':'PASS_H1_SAVE_COMPATIBILITY_NOT_LIVE','build_sha256':sha(manifest_path),'checker_sha256':sha(__file__),
            'checks':len(CHECKS),'check_names':CHECKS,'contract':str(contract_path),'contract_sha256':sha(contract_path),
            'old_serialized_types':len(inventory['serialized_types']),'old_persistent_fields':sum(len(t['fields']) for t in inventory['serialized_types'].values()),
            'housing_serialized_types':contract['serialized_types'],'old_boot_paths':inventory['native_boot_phase_paths'],
            'new_native_owner_identity_baseline':native_identities,'new_native_fact_names':sorted(native_facts),'native_mod_fact_names':sorted(all_native_mod_facts),'source_pins':PINS,
            'future_release_rule':'Retain serialized type/field names/types/order and fixed slot meanings; preserve saved native IDs/depot paths. Add inert data only, never replay loss/payment/reward/owner creation during migration.',
            'limits':['Source/schema and graph identity checks, not engine binary-save reload or gameplay proof.','Explicit development console APIs remain but automatic development dispatch is disabled.','Forward stable compatibility requires future builds to honor this contract; downgrades are unsupported.']}
    target=build/'compatibility_check.json';assert not target.exists();target.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':report['status'],'checks':len(CHECKS),'new_native_owner_paths':len(native_identities)}))

if __name__=='__main__':main(sys.argv[1])
