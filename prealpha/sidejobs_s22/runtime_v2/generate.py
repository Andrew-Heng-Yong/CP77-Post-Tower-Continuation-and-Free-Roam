"""Generate the bounded S22 permission tables and a minimal S21 policy successor."""
import json,hashlib,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
S21=ROOT/'prealpha/sidejobs_s21/SideJobsS2.reds'
S21_SHA='68947EA168C7F3A3AD589BB8E568AF6EF4E1B54F62EB8ACE8190E339F8582C1F'
FILES=[('boxing/contract.json','mq025_psycho_brawl','Beat on the Brat'),('delamain_v2/admission.json','sq025_delamain','Epistrophy'),('ep1_jobs/admission.json','q304_car_retrieval','Moving Heat'),('the_gig/contract.json','sq_q001_wakako','The Gig')]
STATE={'Inactive':1,'Active':2,'Succeeded':3,'Failed':4}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def normalize():
    rows=[]
    for rel,id,title in FILES:
        p=HERE.parent/rel;data=load(p)
        tag=data['tag'];tag=tag if tag.startswith('PTFRS22_') else 'PTFRS22_'+tag
        js=data.get('journals',data.get('journal_guards'))
        assert js and len({x['path'] for x in js})==len(js)
        journals=[]
        for j in js:
            states=j.get('states',j.get('allowed_states',[j.get('state')]));states=[STATE.get(x,x) for x in states]
            assert 1<=len(states)<=2 and set(states)<=set(range(1,5))
            journals.append({'path':j['path'],'class':j['class'],'states':states})
        facts=data.get('fact_equal',data.get('facts_equal',data.get('guard_equal')))
        assert facts and all(isinstance(v,int) and not k.startswith('PTFRS22') for k,v in facts.items())
        assert journals[0]['class']=='gameJournalQuest' and set(journals[0]['states'])<={1,4}
        rows.append({'id':id,'title':title,'tag':tag,'journals':journals,'facts_equal':facts,'source':str(p.relative_to(ROOT)).replace('\\','/'),'source_sha256':sha(p)})
    assert len({x['tag'] for x in rows})==len(rows)
    return rows
def q(s):return json.dumps(s,ensure_ascii=False)
def array_method(name,typ,values):
    vals=[('n'+q(v) if typ=='CName' else q(v)) if isinstance(v,str) else str(v) for v in values]
    return f'  public static func {name}() -> array<{typ}> {{ return ['+', '.join(vals)+']; }\n'
def dispatch(name,typ,count):
    text=f'  public static func {name}(i: Int32) -> array<{typ}> {{\n'
    for i in range(count):text+=f'    if i == {i} {{ return SideJobDataS22.{name}{i}(); }}\n'
    return text+f'    let empty: array<{typ}>; return empty;\n  }}\n'
def data_source(rows):
    s='public abstract class SideJobDataS22 {\n'+f'  public static func Count() -> Int32 {{ return {len(rows)}; }}\n'
    for name,key in [('ID','id'),('Title','title'),('Tag','tag')]:
        s+=f'  public static func {name}(i: Int32) -> String {{\n'
        for i,row in enumerate(rows):s+=f'    if i == {i} {{ return {q(row[key])}; }}\n'
        s+='    return "";\n  }\n'
    s+='  public static func Index(id: String) -> Int32 {\n'
    for i,row in enumerate(rows):s+=f'    if Equals(id, {q(row["id"])}) || Equals(id, {q(row["tag"])}) {{ return {i}; }}\n'
    s+='    return -1;\n  }\n'
    for name,typ in [('Paths','String'),('Classes','String'),('StatesA','Int32'),('StatesB','Int32'),('FactNames','String'),('FactValues','Int32')]:
        s+=dispatch(name,typ,len(rows))
        for i,row in enumerate(rows):
            vals={'Paths':[j['path'] for j in row['journals']],'Classes':[j['class'] for j in row['journals']],'StatesA':[j['states'][0] for j in row['journals']],'StatesB':[j['states'][-1] for j in row['journals']],'FactNames':list(row['facts_equal']),'FactValues':list(row['facts_equal'].values())}[name]
            s+=array_method(name+str(i),typ,vals)
    return s+'}\n'
def s2_successor():
    assert sha(S21)==S21_SHA,'Pinned S21 source changed'
    old=S21.read_text(encoding='utf-8')
    oldbody='''  private func DevelopmentArmed() -> Bool {
    if this.faulted { return false; }
    let prior = PreAlphaEntry.Get(this.GetGameInstance());
    return this.explicitDevelopment || (IsDefined(prior) && prior.DevelopmentArmed());
  }'''
    newbody='''  private func DevelopmentArmed() -> Bool {
    // S22 current policy: automatic, explicitly uncertified post-Tower Inactive
    // admission. CanPermit retains the exact fresh-journal/progress checks.
    return !this.faulted && this.Common();
  }'''
    assert old.count(oldbody)==1
    text=old.replace(oldbody,newbody)
    text=text.replace('Native side jobs S2: historyReady/frozen/certified=','Native side jobs S22 fresh: historyReady/frozen/certified=')
    text=text.replace('Native side job S2 " + id','Native side job S22 fresh " + id')
    text=text.replace('" development=" + ToString(this.DevelopmentArmed())','" currentPostTowerPolicy=" + ToString(this.DevelopmentArmed())')
    text=text.replace(' | No native state reset; original gameplay/rewards.',' | Current Inactive route is uncertified; native freshness and original gameplay/rewards retained.')
    assert text[text.index('public abstract class SideJobDataS2 {'):]==old[old.index('public abstract class SideJobDataS2 {'):]
    return text
def generate(out):
    if any((out/name).exists() for name in ['SideJobsS22.reds','SideJobsS2.reds','manifest.json']):raise RuntimeError('Generated runtime output exists; use a fresh revision')
    out.mkdir(parents=True,exist_ok=True)
    rows=normalize();template=HERE/'SideJobsS22.template.reds'
    txt=template.read_text(encoding='utf-8');assert txt.count('// GENERATED_DATA')==1
    (out/'SideJobsS22.reds').write_text(txt.replace('// GENERATED_DATA',data_source(rows)),encoding='utf-8')
    (out/'SideJobsS2.reds').write_text(s2_successor(),encoding='utf-8')
    pins={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in [Path(__file__),template,S21]}
    # The rollback successor keeps the prior runtime/source/proof immutable.
    prior=HERE.parent/'runtime'
    for name in ['generate.py','SideJobsS22.template.reds','test.py','SideJobsS2.reds','SideJobsS22.reds','manifest.json','test_result_01.json']:
        p=prior/name;pins[str(p.relative_to(ROOT)).replace('\\','/')]=sha(p)
    for row in rows:pins[row['source']]=row['source_sha256']
    m={'status':'GENERATED_NOT_COMPILED_OR_INSTALLED','source_pins':pins,'rows':rows,'files':{name:sha(out/name) for name in ['SideJobsS2.reds','SideJobsS22.reds']},'policy':'Current whitelisted Failed/Inactive bounded routes; pre-ending certification remains separate. Unsupported progress never reset.'}
    (out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8')
    return {'output':str(out),'adapters':len(rows),'files':m['files']}
if __name__=='__main__':print(json.dumps(generate(Path(sys.argv[1]))))
