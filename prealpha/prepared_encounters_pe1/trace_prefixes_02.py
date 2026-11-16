"""Trace each admission's actual native prefix up to player/progress boundaries."""
from pathlib import Path
from collections import defaultdict,Counter
import gzip
import json
import re
import sys
from inventory import HERE,WS,CACHE,read,sha,write
sys.path.insert(0,str(WS/'tools/parity_audit'))
from model import Resource
from common import walk,value


class Models:
    def __init__(self):
        self.inventory=read(HERE/'inventory_01.json')
        self.current={r['depot']:r for r in self.inventory['resources']}
        self.fresh={r['depot']:r for r in read(HERE/'fresh_01/manifest.json')['resources']}
        self.native=read(CACHE)
        self.cache={};self.pins={}
    def get(self,d):
        if d in self.cache:return self.cache[d]
        r=self.current.get(d)
        if r and r['reuse']=='FRESH_EXPORT_REQUIRED':
            source=self.fresh[d];assert sha(source['json'])==source['json_sha256']
            m=Resource(read(source['json'])).normalize();pin=(source['json'],source['json_sha256'])
        else:
            source=r if r else self.native.get(d)
            if not source:return None
            path=source.get('model',source.get('normalized_model'))
            digest=source.get('model_sha256',source.get('normalized_sha256'))
            assert sha(path)==digest
            m=json.loads(gzip.decompress(Path(path).read_bytes()));pin=(path,digest)
        if d in self.current:assert not m.get('errors'),(d,m.get('errors'))
        self.cache[d]=m;self.pins[d]=pin
        return m


def player_boundary(n):
    if n['type']=='questSceneNodeDefinition':return 'SCENE_ENTRY'
    if n['type']!='questPauseConditionNodeDefinition':return None
    for c in walk(n['payload']):
        kind=c.get('$type')
        if kind=='questTriggerCondition' and c.get('type')!='IsOutside':return 'PLAYER_OR_WORLD_INTERACTION_WAIT'
        if kind=='questDistanceComparison_ConditionType' and c.get('comparisonType') not in ['Greater','GreaterOrEqual']:return 'PLAYER_PROXIMITY_WAIT'
        if kind=='questCharacterCondition' and c.get('type',{}).get('$type') not in ['questCharacterSpawned_ConditionType']:return 'CHARACTER_EVENT_WAIT'
        if kind=='questObjectCondition':
            sub=c.get('type',{}).get('$type')
            if sub not in ['questObjectSpawned_ConditionType','questEntityReady_ConditionType']:return 'OBJECT_INTERACTION_WAIT'
        if kind in ['questPlayerCondition','questInputActionCondition','questInteractionCondition','questUICondition']:return 'PLAYER_INTERACTION_WAIT'
    return None


def main():
    output=HERE/'prefixes_02.json';assert not output.exists()
    scan=read(HERE/'scan_01.json');models=Models();traces=[]
    for guard in scan['guards']:
        # Native/owned busy-state gates are not a new-owner admission.
        own_zero=any(r['factName'].startswith('PTFR') and r['factName'].endswith(('_Issued','_Started','_ParentEntered','_OwnerActive','_Request')) and r['value']==0 for r in guard['other_reads'])
        if not own_zero:continue
        interested={f for f in guard['zero_facts'] if not f.startswith(('q307_','q305_','holo_','phonecall_','sa_ep1_courier_')) and re.search(r'(?:_active|_started|_start|_start_community|_community_start|_init|_initialized|_ready|_enabled)$',f)}
        if not interested:continue
        start=models.get(guard['depot'])['graphs'][guard['graph']]
        queue=[(guard['depot'],guard['graph'],e[2],e[3],()) for e in start['edges'] if e[0]==guard['node'] and e[1] not in ('False','CutSource') and e[3]!='CutDestination']
        seen=set();effects=[];writes=[];boundaries=[];unresolved=[]
        while queue:
            d,gp,i,socket,stack=queue.pop()
            key=(d,gp,i,socket,stack)
            if key in seen:continue
            if len(seen)>16000:
                unresolved.append({'reason':'PREFIX_BOUND_REACHED'});break
            seen.add(key)
            m=models.get(d)
            if m and m.get('errors'):
                unresolved.append({'depot':d,'reason':'NATIVE_MODEL_ERRORS','errors':m['errors']});continue
            if not m or gp not in m['graphs'] or i not in m['graphs'][gp]['nodes']:
                unresolved.append({'depot':d,'graph':gp,'node':i,'reason':'UNRESOLVED_NODE'});continue
            g=m['graphs'][gp];n=g['nodes'][i]
            address={'depot':d,'graph':gp,'node':i,'socket':socket,'type':n['type']}
            why=player_boundary(n)
            if n['type']=='questJournalNodeDefinition' and socket not in ('In','Inactive'):
                journals=[x for x in walk(n['payload']) if x.get('$type')=='gameJournalPath']
                if any(value(j.get('className')) not in ['gameJournalPointOfInterestMappin','gameJournalQuestMapPin','gameJournalQuestGuidanceMarker'] for j in journals):why='JOURNAL_PROGRESS_WRITE'
            if why:
                boundaries.append(address|{'reason':why});continue
            for w in n.get('writes',[]):
                if w['factName'] in interested and w['value']>0:writes.append(address|{'write':w})
            if n['type'] not in ['questInputNodeDefinition','questOutputNodeDefinition','questPhaseNodeDefinition','questPauseConditionNodeDefinition','questConditionNodeDefinition','questLogicalHubNodeDefinition','questLogicalAndNodeDefinition','questLogicalXorNodeDefinition','questDeletionMarkerNodeDefinition']:
                effects.append(address|{'payload':n['payload']})
            if n['type']=='questOutputNodeDefinition':
                if stack:
                    parent_d,parent_gp,parent_i=stack[-1]
                    parent=models.get(parent_d)['graphs'][parent_gp]
                    out_socket=str(value(n['payload'].get('socketName','')))
                    for e in parent['edges']:
                        if e[0]==parent_i and e[1]==out_socket and e[3]!='CutDestination':queue.append((parent_d,parent_gp,e[2],e[3],stack[:-1]))
                continue
            if n['type']=='questPhaseNodeDefinition':
                target=str(value(n['payload'].get('phaseResource',{}).get('DepotPath','0')))
                if target.lower() in ['0','none','']:
                    child_d,child_gp=d,gp+'/'+i
                else:child_d,child_gp=target,'root'
                child=models.get(child_d)
                if child and child.get('errors'):
                    unresolved.append(address|{'reason':'NATIVE_MODEL_ERRORS','target':child_d,'errors':child['errors']})
                elif child and child_gp in child['graphs']:
                    entries=child['graphs'][child_gp]['entries']
                    if socket in entries:
                        if len(stack)<24:queue.append((child_d,child_gp,entries[socket],'',stack+((d,gp,i),)))
                        else:unresolved.append(address|{'reason':'CALL_DEPTH_BOUND'})
                    else:unresolved.append(address|{'reason':'MISSING_INPUT','target':child_d,'input':socket,'entries':entries})
                else:unresolved.append(address|{'reason':'MISSING_PHASE','target':child_d,'child_graph':child_gp})
                continue
            for e in g['edges']:
                if e[0]==i and e[1]!='CutSource' and e[3]!='CutDestination':queue.append((d,gp,e[2],e[3],stack))
        candidates=sorted({w['write']['factName'] for w in writes})
        traces.append({'guard':{k:guard[k] for k in ['depot','graph','node','zero_facts','journal_paths']},'interested_flags':sorted(interested),'pre_interaction_positive_writes':writes,'candidate_setup_flags':candidates,'prefix_effects':effects,'boundaries':boundaries,'unresolved':unresolved,'visited_addresses':len(seen),'scope':'May-path source traversal to first interaction/progress boundary. Predicate/dominator and effect review are required before approving candidates.'})
    result={'status':'ACTUAL_PRIVATE_ENTRY_PREFIXES_TRACED','traces':traces,'phase_model_pins':{d:{'path':p,'sha256':h} for d,(p,h) in models.pins.items()},'guard_traces':len(traces),'candidate_setup_flags':sorted({f for t in traces for f in t['candidate_setup_flags']}),'unresolved_traces':sum(bool(t['unresolved']) for t in traces),'game_writes':0,'save_writes':0}
    write(output,result)
    print(json.dumps({'traces':len(traces),'candidate_flags':len(result['candidate_setup_flags']),'unresolved_traces':result['unresolved_traces']}))
    for t in traces:
        if t['candidate_setup_flags']:print(t['guard']['depot'],t['guard']['graph'],t['guard']['node'],t['candidate_setup_flags'],'effects',len(t['prefix_effects']),'unresolved',len(t['unresolved']))


if __name__=='__main__':
    main()
