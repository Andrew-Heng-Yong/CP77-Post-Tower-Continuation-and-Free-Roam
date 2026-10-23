"""Source-derived fresh-only S28 vehicle contracts; no game or save writes."""
import hashlib,json,sys,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
from catalog_gig_rollout_r2 import walk,value
from test_rite_g2 import SafeResource
from audit_activity_batches_b1 import flatten
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def rel(p):return str(Path(p).relative_to(ROOT)).replace('\\','/')
def graphs(p):
    r=SafeResource(read(p));return {g['path']:g for g in flatten(r,r.obj['Data']['RootChunk'])}
def catalog(p):
    data=read(p);handles={x['HandleId']:x['Data'] for x in walk(data) if 'HandleId' in x and 'Data' in x};out={}
    def visit(w,parts):
        n=w.get('Data',handles.get(w.get('HandleRefId'),w));ident=n.get('id','');parts=parts+([ident] if ident else [])
        if n.get('$type','').startswith('gameJournal'):out['/'.join(parts)]=n['$type']
        for c in n.get('entries',[]):visit(c,parts)
    visit(data['Data']['RootChunk']['entry'],[]);return out
def main():
    out=HERE/'contracts_01.json';proof=ROOT/'research/sidejobs_s28/vehicles/plan_01.json';assert not out.exists() and not proof.exists()
    pins={};index={}
    for p in ['research/omitted_jobs_audit/native_screen_03.json','research/omitted_jobs_audit/review_02/native_audit_02.json']:
        pins[p]=sha(ROOT/p);index.update(read(ROOT/p)['resources'])
    def native(dep):
        p=ROOT/index[dep]['source'];raw=Path(str(p).replace('\\json\\','\\raw\\')[:-5]);assert sha(p)==index[dep]['sha256']
        pins[rel(p)]=sha(p);pins[rel(raw)]=sha(raw)
        return {'depot':dep,'json':rel(p),'raw':rel(raw),'json_sha256':sha(p),'raw_sha256':sha(raw)},read(p)
    jp='research/sidejobs_s24/ep1/native_02/json/base/journal/cooked_journal.journal.json';pins[jp]=sha(ROOT/jp);pins[jp.replace('/json/','/raw/')[:-5]]=sha(ROOT/(jp.replace('/json/','/raw/')[:-5]));cat=catalog(ROOT/jp)
    jobs=[('mq029_tourist','The Highwayman',r'base\quest\minor_quests\mq029\mq029_tourist.questphase','Vehicle.v_sportbike2_arch_tyger_player'),('mq050_ken_block_tribute',"I'm in Love with My Car",r'base\quest\minor_quests\mq050\mq050.questphase','Vehicle.v_sport2_quadra_type66_nomad_tribute')]
    plans=[];owners=[]
    for ident,title,main_depot,vehicle in jobs:
        queue=[main_depot];resources={};objects={}
        while queue:
            dep=queue.pop(0)
            if dep in resources:continue
            assert dep in index,('unresolved native reference',dep)
            resource,obj=native(dep);resources[dep]=resource;objects[dep]=obj
            refs={value(v) for n in walk(obj) for k,v in n.items() if k=='DepotPath' and isinstance(value(v),str) and value(v).endswith(('.questphase','.scene'))}
            queue.extend(sorted(refs-set(resources)))
        root='quests/minor_quest/'+ident;assert cat[root]=='gameJournalQuest'
        journals=[{'path':p,'class':c,'states':[1]} for p,c in cat.items() if p==root or p.startswith(root+'/')]
        prefix='mq029_' if ident=='mq029_tourist' else 'mq050_';facts={}
        for obj in objects.values():
            for n in walk(obj):
                for field in ('factName','factName1','factName2'):
                    f=value(n.get(field))
                    if isinstance(f,str) and f.startswith(prefix):facts[f]=0
        owner={'id':ident,'title':title,'tag':'PTFRS28_'+ident,'journals':journals,'facts_equal':dict(sorted(facts.items())),'fact_ranges':{},'inventory_zero':[],'vehicle_zero':[{'record':vehicle,'hash':str(zlib.crc32(vehicle.encode())|(len(vehicle.encode())<<32))}], 'resume':'DEFER any completed, progressed, existing-owner, earned-item/vehicle or unknown state; no restart/reset/reward replay','depot':'towercontinued\\sidejobs_s28\\vehicles\\'+ident+'_entry.questphase'}
        if ident=='mq050_ken_block_tribute':
            item='Keycards.mq050_car_keys';h=zlib.crc32(item.encode())|(len(item.encode())<<32);assert h==99716362400
            owner['inventory_zero']=[{'record':item,'hash':str(h)}];owner['fact_ranges']={'q101_done':{'min':1,'max':2147483647}}
            parent='research/races_r1/parents_01/json/base/quest/bugfixing/quest_bugfixing.questphase.json';parent_gp='root/3';parent_node=67;prereq=71
        else:
            parent='research/sidejobs_s25/families/native_03/json/base/quest/minor_quests/minorquests.questphase.json';parent_gp='root';parent_node=26;prereq=None
        pins[parent]=sha(ROOT/parent);parent_raw=parent.replace('/json/','/raw/')[:-5];pins[parent_raw]=sha(ROOT/parent_raw)
        gs=graphs(ROOT/parent);node=next(n for n in gs[parent_gp]['nodes'] if n['id']==parent_node);assert node['phaseResource']['DepotPath']['$value']==main_depot
        plans.append({'id':ident,'title':title,'main':main_depot,'parent':{'json':parent,'raw':parent_raw,'graph':parent_gp,'node':parent_node,'prerequisite_node':prereq},'resources':list(resources.values()),'graphs':{d:list(graphs(ROOT/r['json']).values()) for d,r in resources.items() if d.endswith('.questphase')},'native_vehicle_reward':vehicle,'inventory_zero':owner['inventory_zero'],'entry':'In1','output':'Out1'})
        owners.append(owner)
    pins[rel(Path(__file__))]=sha(Path(__file__))
    common={'PostTowerFreeRoamActive':1,'PTFRP0_DR13':1,'PTFRPA2_Finished':1,'PTFRPA2_Fault':0,'q307_done':1,'q307_finished':1,'q307_2079':1,'q307_main_game_killed':1,'q307_ep1_killed':1,'q307_active':0,'q307_debug_reset':0,'q115_point_of_no_return':0,'q305_johnny_scene_active':0}
    contract={'status':'SOURCE_CONTRACT_FRESH_ONLY_NATIVE_BUILD_PENDING','owners':owners,'common_equal':common,'source_pins':pins,'native_resources':{r['depot']:r for j in plans for r in j['resources']},'vehicle_api':'VehicleSystem.IsVehiclePlayerUnlocked(TweakDBID); unknown context fails closed','native_vehicle_gate':'To be source-proven separately; do not equate availability/summonability with durable entitlement by name.'}
    out.write_text(json.dumps(contract,indent=2)+'\n');proof.parent.mkdir(parents=True,exist_ok=True);proof.write_text(json.dumps({'jobs':plans,'source_pins':pins},indent=2)+'\n')
    print(json.dumps({'contract':rel(out),'sha256':sha(out),'jobs':[(o['id'],len(o['journals']),len(o['facts_equal']),o['inventory_zero'],o['vehicle_zero']) for o in owners]}))
if __name__=='__main__':main()
