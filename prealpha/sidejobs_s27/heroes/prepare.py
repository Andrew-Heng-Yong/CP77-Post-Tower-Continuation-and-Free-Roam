"""Prepare source-backed Heroes package-route admission; no saves or native writes."""
import argparse,hashlib,json,re
from pathlib import Path
from inspect import ROOT, read, graphs
HERE=Path(__file__).parent

def walk(v):
    if isinstance(v,dict):
        yield v
        for c in v.values(): yield from walk(c)
    elif isinstance(v,list):
        for c in v: yield from walk(c)

def value(v): return v.get('$value') if isinstance(v,dict) else v
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def catalog(path):
    d=read(path);h={x['HandleId']:x['Data'] for x in walk(d) if 'HandleId' in x and 'Data' in x};out={}
    def visit(w,p):
        n=w.get('Data',h.get(w.get('HandleRefId'),w));k=n.get('id','');p=p+([k] if k else [])
        if n.get('$type','').startswith('gameJournal'):out['/'.join(p)]=n['$type']
        for child in n.get('entries',[]):visit(child,p)
    visit(d['Data']['RootChunk']['entry'],[])
    return out

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--revision',default='02');args=parser.parse_args()
    assert re.fullmatch(r'\d{2}',args.revision)
    target=HERE/('contract'+args.revision+'.json')
    if target.exists(): raise RuntimeError('Immutable contract exists')
    parent='research/sidejobs_s27/heroes/native_04/raw/base/quest/side_quests/sidequests.questphase'
    main='research/activity_state_r3/native_sources/raw/base/quest/side_quests/sq018/sq018.questphase'
    intro='research/activity_state_r3/native_sources/raw/base/quest/side_quests/sq018/phases/sq018_00_holocall.questphase'
    scene='research/sidejobs_s24/services/native_01/raw/base/quest/side_quests/sq018/scenes/sq018_00_mama_welles_holocall.scene'
    default='research/sidejobs_s25/families/native_01/raw/base/quest/default_dialogs.questphase'
    default_scene='research/sidejobs_s27/heroes/native_04/raw/base/quest/tertiary_characters/default_dialogues/mama_welles_default.scene'
    journal='research/sidejobs_s24/ep1/native_02/json/base/journal/cooked_journal.journal.json'
    pins={}
    def pin(p): pins[p]=sha(ROOT/p)
    def obj(p):
        pin(p);jp=p.replace('/raw/','/json/')+'.json';pin(jp);return read(ROOT/jp)
    objects=[obj(p) for p in (parent,main,intro,scene,default,default_scene)]
    cat=catalog(ROOT/journal);pin(journal)
    root='quests/side_quest/sq018_jackie'
    journals=[{'path':p,'class':c,'states':[1]} for p,c in cat.items() if p==root or p.startswith(root+'/')]
    phonepaths={}
    for d in walk(objects[3]):
        if d.get('$type')=='gameJournalPath':
            p=d.get('realPath','');c=value(d.get('className'))
            if p.startswith('contacts/mama_welles/sq018_') and cat.get(p)==c:phonepaths[p]=c
    for d in walk(objects[2]):
        if d.get('$type')=='gameJournalPath':
            p=d.get('realPath','');c=value(d.get('className'))
            if p.startswith('contacts/mama_welles/sq018_') and cat.get(p)==c:phonepaths[p]=c
    journals += [{'path':p,'class':c,'states':[1]} for p,c in sorted(phonepaths.items())]
    cap=read(ROOT/'research/sidejobs_s23/live_20261016_01/capture.json')
    job=next(x for x in cap['second']['jobs'] if x['id']=='sq018_jackie')
    facts={f:0 for f in job['facts'] if f.startswith('sq018_')}
    for d in walk(objects[2:4]):
        for k in ('factName','factName1','factName2'):
            f=value(d.get(k))
            if isinstance(f,str) and f.startswith('sq018_'):facts[f]=0
    facts.pop('sq018_enable',None)
    facts.update({'q005_jackie_to_mama':0,'q005_jackie_stay_notell':0,'mama_welles_default_on':0,'mama_welles_dd_holo':0,'phonecall_player_with_mama_welles':0,'mq040_active':0,'pepe_dd_holo':0,'PTFRB0ST_Suspended':0,'PTFRBASE_Suspended':0,'ep1_standalone':0})
    # Native package-only route locks Coyote entrance doors while active. Do not
    # enter while an already-restored physical Pepe scene owns the venue.
    phone=[]
    for stem in ('mama_welles_holocall.questphase','mamma_welles_cleanup.questphase','mama_welles_holocall.scene'):
        p='research/sidejobs_s27/heroes/native_01/raw/base/quest/holocalls/mama_welles/'+stem
        phone.append(obj(p))
    for d in walk(phone):
        for v in d.values():
            f=value(v)
            if isinstance(f,str) and f.startswith(('holo_','audio_')) and f.endswith(('_start_activate','_end_activate','_active','_started')):facts[f]=0
    for f in ('holo_setup_active','holo_setup_started','holo_interrupt_call','holo_active_call_interrupted','holo_reset','holo_force_reset','holo_reset_soft','holo_interrupt_call_manual','holo_interrupt_braindance'):facts[f]=0
    ranges={'sq018_enable':{'min':1,'max':2147483647}}
    owner={'id':'sq018_jackie','ids':['sq018_jackie'],'title':'Heroes (original package route)','key':'HEROES_PACKAGE','tag':'PTFRS27_HEROES_PACKAGE','depot':'towercontinued\\sidejobs_s27\\heroes\\heroes_package.questphase','facts_equal':dict(sorted(facts.items())),'fact_ranges':ranges,'journals':journals,'phone_dependencies':['MAMA'],'native_only_checks':[{'kind':'inventory','source':intro,'graph':'root/47','node':5,'quantity':0,'item_id_hash':120771320143},{'kind':'distance','source':default,'graph':'root/7/27/3','node':58,'condition_index':0,'operator':'Greater','distance':30}],'parent_source':parent,'parent_nodes':[89,119],'parent_edges':[[89,'Out',119,'In']],'entry_source':main,'entry_node':42,'entry':'In','native_outputs':{'success':'Out2','unsupported_funeral':'Out1'},'service_source':default,'service_graph':'root/4','service_nodes':[16,17],'scope':'Wholly unstarted package-outcome route only. Failed/progressed roots are not silently reset; funeral route deferred.'}
    owner['native_only_checks'][1]['graph']='root/7/27/3/16'
    owner['contact_target']='contacts/mama_welles'
    owner['contact_copy']={'source':main,'graph':'root/76','id':4}
    for p in ('prealpha/sidejobs_s27/heroes/prepare.py','prealpha/sidejobs_s27/heroes/inspect.py','prealpha/ncpd_scanner_n1/native_inspect.py','tools/audit_activity_batches_b1.py','research/sidejobs_s23/live_20261016_01/capture.json'):pin(p)
    common=read(ROOT/'prealpha/sidejobs_s24/ep1/contract02.json')['common_equal'];pin('prealpha/sidejobs_s24/ep1/contract02.json')
    native={p.split('/raw/',1)[1].replace('/','\\'):{'raw':p,'raw_sha256':h,'json':p.replace('/raw/','/json/')+'.json','json_sha256':pins[p.replace('/raw/','/json/')+'.json']} for p,h in pins.items() if '/raw/' in p}
    out={'schema':'S27_HEROES_PACKAGE_CONTRACT_1','status':'PREPARED_NOT_LIVE','common_equal':common,'owners':[owner],'source_pins':pins,'native_resources':native,'phone':{'initializer':67,'condition':456,'cleanup':324,'input':'In30','output':'Out30','name':'MAMA','folder':'mama_welles','cleanup_file':'mamma_welles_cleanup.questphase'},'current_capture_control':{'id':job['id'],'rootState':job['rootState'],'sq018_done':job['facts']['sq018_done'],'admit':False}}
    target.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'contract':str(target),'facts':len(facts),'journals':len(journals),'source_pins':len(pins)}))

if __name__=='__main__':main()
