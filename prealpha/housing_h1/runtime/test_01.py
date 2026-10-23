"""Independent v1 save/receipt policy model, source gates, and old-schema comparison.

JSON round trips model saved values, not the engine's binary save serialization.
The full SCC check separately verifies actual supported persistent types and API use.
"""
import copy, hashlib, importlib.util, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GAME = Path('C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077')
IDS = ['h10', 'northside', 'japantown', 'glen', 'corpo']
RESULTS = []
def check(label, value):
    assert value, label
    RESULTS.append(label)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def roundtrip(obj): return json.loads(json.dumps(obj))
def compatible(old, new):
    return all(k in new and new[k]['parent'] == v['parent'] and new[k]['fields'][:len(v['fields'])] == v['fields'] for k, v in old.items())
def record(id):
    return dict(id=id, lossApplied=False, purchaseState=0, debitAttempts=0, quotedPrice=0, balanceBefore=0, balanceAfter=0, debitReturned=False, sourceDoor=0, preTowerFact=-1, captureKnown=False)
def valid(r):
    if r['id'] not in IDS or r['purchaseState'] not in range(5) or r['preTowerFact'] not in [-1,0,1] or (r['captureKnown'] and r['preTowerFact'] < 0): return False
    if r['purchaseState'] == 0: return (r['debitAttempts'],r['quotedPrice'],r['balanceBefore'],r['balanceAfter'],r['debitReturned'],r['sourceDoor']) == (0,0,0,0,False,0)
    if not r['lossApplied'] or r['debitAttempts'] != 1 or r['quotedPrice'] <= 0 or r['balanceBefore'] < r['quotedPrice'] or r['balanceAfter'] < -1 or not r['sourceDoor']: return False
    return r['purchaseState'] not in [2,3] or (r['debitReturned'] and r['balanceAfter'] == r['balanceBefore']-r['quotedPrice'])
def reload_receipt(r):
    r=roundtrip(r)
    if valid(r) and r['purchaseState']==1: r['purchaseState']=4
    return r
def paid(r): return valid(r) and r['purchaseState'] in [2,3]
def can_buy(r, *, safe=True, ready=True, finished=True, q101=True, access=0):
    return valid(r) and r['lossApplied'] and r['purchaseState']==0 and r['debitAttempts']==0 and safe and ready and finished and access==0 and (r['id']=='h10' or q101)
def buy(r, balance, quote, expected, *, location=True, safe=True, ready=True, q101=True, result=True, delta=None, interrupt=None):
    r=copy.deepcopy(r)
    if not can_buy(r,safe=safe,ready=ready,q101=q101) or not location or quote<=0 or quote!=expected or balance<quote: return r,balance,0
    r.update(quotedPrice=quote,balanceBefore=balance,balanceAfter=-1,sourceDoor=123,debitAttempts=1,purchaseState=1)
    if interrupt=='before': return r,balance,0
    after=balance-(quote if delta is None else delta)
    if interrupt=='after': return r,after,1
    r.update(debitReturned=result,balanceAfter=after,purchaseState=2 if result and after==balance-quote else 4)
    return r,after,1
def loss_permit(r, safe=True, menu=False): return safe and not menu and not r['lossApplied'] and r['purchaseState']==0
def freeze(observed=True, age=1, ready=True, previous=True, teardown=False, delayed=False, same=True):
    return observed and 0<=age<=2.5 and ready and previous and not teardown and not delayed and same
def method(source, name):
    start=re.search(r'\bfunc '+re.escape(name)+r'\([^\n]*?\)\s*->\s*[^\{]+\{',source)
    assert start,name
    depth=1
    for i in range(start.end(),len(source)):
        if source[i]=='{': depth+=1
        elif source[i]=='}':
            depth-=1
            if depth==0: return source[start.end():i]
    raise AssertionError(name)

def main(component_path):
    cpath=Path(component_path).resolve(); c=read(cpath); out=cpath.parent
    for rel,digest in c['source_pins'].items(): check('source pin '+rel,sha(ROOT/rel)==digest)
    source=(out/'package'/c['files'][0]['relative']).read_text(encoding='utf-8-sig')
    check('packaged source',sha(out/'package'/c['files'][0]['relative'])==c['files'][0]['sha256'])
    contract=read(ROOT/c['save_contract']); check('contract binding',sha(ROOT/c['save_contract'])==c['save_contract_sha256'])
    parser_path=ROOT/'research/housing_h1/compatibility/inventory_01.py'
    spec=importlib.util.spec_from_file_location('inventory',parser_path); parser=importlib.util.module_from_spec(spec);spec.loader.exec_module(parser)
    types={'PTFR.Housing.'+n:{'parent':p,'fields':parser.fields(b)} for n,p,b in parser.blocks(source) if parser.fields(b)}
    check('permanent serialized contract',types==contract['serialized_types'])
    check('five IDs permanent',contract['property_ids_in_permanent_order']==IDS)
    check('no Kerry mutable row','kerry' not in source.lower())
    check('one debit call only',source.count('.RemoveItem(')==1)
    check('no reward/grant/refund API',not re.search(r'\b(GiveItem|AddItem|RemoveAllItems|SetFact)\(',source))
    check('only own fact writer callsites',all(x.startswith('PTFRH1_') for x in re.findall(r'this.SetOwn\("([^\"]*)',source)))
    for name in ['Poll','Restored','Reconcile','Publish','Initialize','ObserveHistory','FreezeCapture']:
        body=method(source,name);check(name+' never pays','RemoveItem' not in body and 'this.Purchase(' not in body)
    body=method(source,'Purchase')
    check('source inside debit boundary',body.count('HousingPurchaseLocation.Validate(')==2)
    check('quote inside debit boundary',body.count('HousingPrice.Quote(')==2)
    check('eligibility inside debit boundary',body.count('this.CanPurchase(')==2)
    check('pending before debit',body.index('record.purchaseState = 1')<body.index('transaction.RemoveItem'))
    check('exact receipt required','record.debitReturned && record.balanceAfter == before - price' in body)
    check('DLC6 native prerequisite','this.Fact("q101_done") >= 1' in method(source,'CanPurchase'))
    check('no UI menu veto on explicit confirmation','IsInMenu' not in method(source,'CanPurchase')+method(source,'Purchase')+method(source,'SafeActor'))
    check('migration defers menus','IsInMenu' in method(source,'MigrationContext'))
    check('migration does not await Finished','PTFRPA2_Finished' not in method(source,'MigrationContext'))
    check('capture allows active q307','q307_active' not in method(source,'BeforeTower') and 'q307_tomorrow' not in method(source,'BeforeTower'))
    check('capture timely','age <= 2.5' in method(source,'FreezeCapture'))
    check('load loses transient certificate','this.lastCapture = -100.0' in method(source,'Restored') and 'FreezeCapture(false)' in method(source,'Restored'))
    check('boundary callback explicit','FreezeCapture(true)' in method(source,'OnBoundary'))
    check('quarantine preserves entitlement','_Entitled' not in method(source,'Quarantine'))
    check('quarantine masks known operations',all(s in method(source,'Quarantine') for s in ['_LossPermit','_AccessPermit','_PurchaseReady']))
    check('no automatic reset/repair','this.schemaVersion = 1' in method(source,'Initialize') and 'this.schemaVersion = 0' not in source)
    for id in IDS:
        r=record(id);check(id+' fresh receipt',valid(r))
        check(id+' preloss cannot buy',not can_buy(r));check(id+' initial loss eligible',loss_permit(r))
        check(id+' menu defers loss',not loss_permit(r,menu=True))
        r['lossApplied']=True
        check(id+' reload no repeated loss',not loss_permit(roundtrip(r)))
        for kwargs in [{'location':False},{'safe':False},{'ready':False}]:
            after,money,calls=buy(r,100000,25000,25000,**kwargs)
            check(id+' refusal '+str(kwargs),after==r and money==100000 and calls==0)
        for money,quote,expected in [(24999,25000,25000),(100000,25000,20000),(100000,-1,-1),(100000,0,0)]:
            after,newmoney,calls=buy(r,money,quote,expected)
            check(id+' refused quote/balance '+str((money,quote,expected)),after==r and newmoney==money and calls==0)
        if id!='h10':
            after,money,calls=buy(r,100000,25000,25000,q101=False)
            check(id+' normal native prerequisite',after==r and money==100000 and calls==0)
        bought,money,calls=buy(r,100000,25000,25000)
        check(id+' exact paid receipt',paid(bought) and money==75000 and calls==1)
        for cycle in range(3):
            bought=reload_receipt(bought)
            after,m2,calls=buy(bought,money,25000,25000)
            check(id+' paid reload '+str(cycle),after==bought and m2==money and calls==0 and not loss_permit(bought))
        bought['purchaseState']=3
        check(id+' native ack preserves receipt',paid(reload_receipt(bought)))
        for point in ['before','after']:
            pending,money,calls=buy(r,100000,25000,25000,interrupt=point)
            uncertain=reload_receipt(pending)
            after,m2,newcalls=buy(uncertain,money,25000,25000)
            check(id+' interrupted '+point,uncertain['purchaseState']==4 and not paid(uncertain) and after==uncertain and m2==money and newcalls==0)
        for result,delta in [(False,25000),(True,24999),(True,25001),(False,0)]:
            uncertain,money,calls=buy(r,100000,25000,25000,result=result,delta=delta)
            check(id+' uncertain '+str((result,delta)),uncertain['purchaseState']==4 and not can_buy(reload_receipt(uncertain)) and not paid(uncertain))
        for field,value in [('debitAttempts',1),('quotedPrice',1),('balanceBefore',1),('balanceAfter',-1),('debitReturned',True),('sourceDoor',123)]:
            partial=copy.deepcopy(r);partial[field]=value
            check(id+' partial unpaid '+field,not valid(partial) and reload_receipt(partial)==partial and not can_buy(partial))
        for field,value in [('lossApplied',False),('debitAttempts',0),('quotedPrice',0),('balanceBefore',1),('balanceAfter',0),('debitReturned',False),('sourceDoor',0)]:
            broken=copy.deepcopy(bought);broken[field]=value
            check(id+' corrupt paid '+field,not valid(broken) and reload_receipt(broken)==broken and not paid(broken) and not can_buy(broken))
        for known in [True,False]:
            historic=copy.deepcopy(r);historic.update(captureKnown=known,preTowerFact=1 if known else -1)
            check(id+' provenance never substitutes purchase eligibility '+str(known),not can_buy(historic,ready=False))
    check('fresh cutoff witness',freeze())
    for k,v in [('observed',False),('age',3),('age',-1),('ready',False),('previous',False),('teardown',True),('delayed',True),('same',False)]: check('unknown cutoff '+str((k,v)),not freeze(**{k:v}))
    check('reload past boundary unknown despite old samples',not freeze(observed=False,ready=True))
    # Forward schema compatibility permits additions without changing old positions/types.
    later=copy.deepcopy(types)
    later['PTFR.Housing.HousingState']['fields'].append({'name':'futureInertRevision','type':'Int32'})
    check('additive stable v1 schema accepted',compatible(types,later))
    for mutation in ['remove_type','rename_field','change_type','reorder','insert_before']:
        broken=copy.deepcopy(types); key='PTFR.Housing.HousingRecord'
        if mutation=='remove_type': del broken[key]
        elif mutation=='rename_field': broken[key]['fields'][0]['name']='homeId'
        elif mutation=='change_type': broken[key]['fields'][0]['type']='String'
        elif mutation=='reorder': broken[key]['fields'].reverse()
        else: broken[key]['fields'].insert(0,{'name':'extra','type':'Bool'})
        check('incompatible stable change rejected '+mutation,not compatible(types,broken))
    inventory=read(ROOT/'research/housing_h1/compatibility/schema_inventory_01.json')
    integration=ROOT/'prealpha/housing_h1/integration/build/integration_02/package'
    current={}; allpins={}
    for rel,digest in inventory['installed_script_pins'].items():
        check('old installed source intact '+rel,sha(GAME/rel)==digest)
        candidate=integration/rel
        if not candidate.exists(): candidate=GAME/rel
        allpins[str(candidate)]=sha(candidate)
        text=candidate.read_text(encoding='utf-8-sig');m=re.search(r'^module\s+(\S+)',text,re.M)
        for n,p,b in parser.blocks(text):
            f=parser.fields(b)
            if f: current[m.group(1)+'.'+n]={'parent':p,'fields':f}
    old={k:{'parent':v['parent'],'fields':v['fields']} for k,v in inventory['serialized_types'].items()}
    check('all old serialized types/fields preserved',compatible(old,current))
    entryrel='r6/scripts/PTFR_PreAlpha/PA1/PreAlphaEntry.reds'
    before=(GAME/entryrel).read_text(encoding='utf-8-sig');after=(integration/entryrel).read_text(encoding='utf-8-sig')
    for n in ['Catalogue','ShapeValid','Freeze','Certified','Dispatch']:
        check('old catalogue/certificate method unchanged '+n,method(before,n)==method(after,n))
    for rel,v in inventory['catalogue_sources_to_preserve'].items():
        candidate=integration/rel
        if candidate.exists():
            check('catalogue fingerprints preserved '+rel,sorted(set(re.findall(r'n?"([A-F0-9]{64})"',candidate.read_text(encoding='utf-8-sig'))))==v['quoted_fingerprints'])
        else: check('catalogue source unchanged '+rel,sha(GAME/rel)==v['sha256'])
    # Egress is a separate native capability, not inferred from entitlement.
    devices=ROOT/'prealpha/housing_h1/purchase/build/purchase_05/package/r6/scripts/TowerContinued_Housing_H1/HousingDevices.reds'
    devtext=devices.read_text(encoding='utf-8-sig')
    check('legacy indoor save exit hooks absent',not any(x in devtext for x in ['OnToggle','OnForceOpen','OnSetOpened']))
    check('native door actions preserved','wrappedMethod(outActions, context)' in devtext)
    check('restore clears stale purchase callback','HousingPurchaseUI.Reset(this.GetGameInstance())' in method(source,'Restored'))
    result={'status':'PASS_H1_SAVE_POLICY_NOT_LIVE','component_sha256':sha(cpath),'checks':len(RESULTS),'check_names':RESULTS,
            'old_serialized_types':len(old),'old_persistent_fields':sum(len(v['fields']) for v in old.values()),
            'new_serialized_types':len(types),'new_persistent_fields':sum(len(v['fields']) for v in types.values()),
            'source_pins':{str(Path(__file__).relative_to(ROOT)):sha(__file__),str(devices.relative_to(ROOT)):sha(devices)},
            'old_overlay_pins':allpins,'scope':'Independent policy model with JSON save round trips plus actual source/schema checks; not an engine save load or gameplay test.',
            'limitations':['Native owner IDs and phase paths require native component proof.','Future stable builds must rerun compatibility checks; no claim that an arbitrary future implementation is compatible.','Unsupported future-schema access preservation is mirror-only; new operations are refused.']}
    target=out/'tests.json';assert not target.exists();target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['status','checks','old_serialized_types','old_persistent_fields','new_persistent_fields']}))

if __name__=='__main__': main(sys.argv[1])
