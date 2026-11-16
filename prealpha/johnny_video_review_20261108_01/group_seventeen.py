"""Merge the 17 additional review targets into source-backed conversations.

Two preceding / three following spoken lines, any speaker. This is a document
successor; existing transcripts, decisions and game resources stay unchanged.
"""
from pathlib import Path
import hashlib
import json

HERE=Path(__file__).resolve().parent
PREVIOUS=HERE/'context_17_02'
OUT=HERE/'context_17_grouped_01'


def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def write(p,d):
    with Path(p).open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,indent=2,ensure_ascii=False);f.write('\n')


def main():
    assert not OUT.exists();OUT.mkdir()
    old=read(PREVIOUS/'mapping.json');proof=read(PREVIOUS/'verification.json')
    assert sha(PREVIOUS/'mapping.json')==proof['mapping_sha256']
    assert sha(old['document'])==proof['document_sha256']
    for p,h in old['verified_sources'].items():assert sha(p)==h,p
    targets={t['review_number']:t for t in old['targets']}
    events=old['events'];numbers={t['event_key']:n for n,t in targets.items()}
    assert set(targets)==set(range(1,18))
    # Preserve exact per-target evidence, trimming only the requested before count.
    windows=[]
    for n,t in targets.items():
        row={k:v for k,v in t.items() if k not in ['before','after']}
        row['before']=[{**c,'events':c['events'][-2:],'complete':len(c['events'])>=2} for c in t['before']]
        row['after']=[{**c,'events':c['events'][:3],'complete':len(c['events'])>=3} for c in t['after']]
        windows.append(row)
    def section(number,nid=None):
        t=targets[number];root=t['event_key'].split('/root/')[0]
        found=[(k,e) for k,e in events.items() if k.startswith(root+'/root/scene/'+(nid or t['section'])+'/event/')]
        return [k for k,e in sorted(found,key=lambda kv:(float(kv[1]['event']['start_time']),kv[1]['event']['event_ordinal']))]
    def window(n,side):
        contexts=next(t for t in windows if t['review_number']==n)[side]
        assert len(contexts)==1,(n,side)
        return contexts[0]['events']
    def one(n):return targets[n]['event_key']
    common=section(1,'6');branch_a=section(4,'26');branch_b=section(5,'28')
    assert [numbers[k] for k in common if k in numbers]==[1,2,3]
    assert [numbers[k] for k in branch_a if k in numbers]==[4]
    assert [numbers[k] for k in branch_b if k in numbers]==[5,6]
    area=[*window(13,'before'),one(13),*window(14,'before')[-1:],one(14),*window(15,'before')[-1:],one(15)]
    groups=[
        {'title':'SMALL MAN, BIG MOUTH — early Johnny conversation','numbers':[1,2,3,4,5,6],
         'common':common,'branches':[{'label':'OPTION A: "Yeah, I know."','events':branch_a},
                                   {'label':'OPTION B: "Cred stays cred, too."','events':branch_b}],
         'routes':[common+branch_a,common+branch_b],
         'before_boundary':'This conversation starts with #1; no preceding spoken lines are fixed inside it.',
         'after_boundary':'Each reply branch ends here; there are no three further lines in this exchange.'},
        {'title':'RAYMOND CHANDLER EVENING — optional search narration','numbers':[7],
         'routes':[[*window(7,'before'),one(7),*window(7,'after')]],
         'before_boundary':'Separate triggered remark; no preceding spoken lines are fixed inside this exchange.',
         'after_boundary':'This exchange ends after V\'s reply.'},
        {'title':'RAYMOND CHANDLER EVENING — wrong-woman reaction','numbers':[8],
         'routes':[[*window(8,'before'),one(8),*window(8,'after')]],
         'before_boundary':'Separate triggered remark; no preceding spoken lines are fixed inside this exchange.',
         'after_boundary':'This exchange ends after V\'s reply.'},
        {'title':'RAYMOND CHANDLER EVENING — foot-stepping joke','numbers':[9,10],
         'routes':[[*window(n,'before'),one(n),*window(n,'after')] for n in [9,10]],
         'identical_alternatives':True,
         'before_boundary':'Two source branches contain the same exchange; shown once, covering #9 and #10.',
         'after_boundary':'This exchange ends after V\'s reply.'},
        {'title':'RAYMOND CHANDLER EVENING — leaving Cynthia','numbers':[11,12],
         'routes':[[*window(n,'before'),one(n),*window(n,'after')] for n in [11,12]],
         'branch_labels':['ALTERNATIVE A — #11','ALTERNATIVE B — #12'],
         'after_boundary':'Each alternative ends after V\'s reply; they are not one continuous conversation.'},
        {'title':'KILLING IN THE NAME — final signal-area arrival','numbers':[13,14,15],
         'routes':[area],
         'before_boundary':'Only one preceding spoken line belongs to this exchange.',
         'after_boundary':'The exchange ends at #15; another interaction is needed for later dialogue.'},
        {'title':'KILLING IN THE NAME — paid-fortune comment','numbers':[16],
         'routes':[[*window(16,'before'),one(16),*window(16,'after')]],
         'before_boundary':'Only one preceding spoken line belongs to this immediate exchange.',
         'conditional_after':'The following two lines are conditional on choosing "Don\'t have any change." at the bot; they are not an automatic reply.',
         'after_boundary':'No fixed third following line is established before the next payment/topic cycle.'},
        {'title':'KILLING IN THE NAME — after Nancy\'s final call','numbers':[17],
         'routes':[[one(17)]],
         'before_boundary':'A separate Johnny proximity-triggered remark after the call, on the non-exposure branch. No immediate preceding spoken lines are fixed here.',
         'after_boundary':'Standalone remark; no following spoken lines are fixed in this exchange.'},
    ]
    checks=[]
    def check(name,condition):
        assert condition,name
        checks.append(name)
    check('All seventeen occurrence identities represented once as review targets',sorted(n for g in groups for n in g['numbers'])==list(range(1,18)))
    for group in groups:
        covered={n for route in group['routes'] for key in route if (n:=numbers.get(key)) in group['numbers']}
        check(group['title']+' target coverage',covered==set(group['numbers']))
        for route in group['routes']:
            check(group['title']+' unique ordered events within route',len(route)==len(set(route)))
            for key in route:check(key+' exact source-backed transcript event',key in events)
            for pos,key in enumerate(route):
                n=numbers.get(key)
                if n not in group['numbers']:continue
                w=next(t for t in windows if t['review_number']==n)
                before=route[max(0,pos-2):pos];after=route[pos+1:pos+4]
                check(str(n)+' preceding window contained in merged route',any(c['events']==before for c in w['before']))
                check(str(n)+' following window contained in merged route',any(c['events']==after for c in w['after']))
    dup=groups[3]
    for left,right in zip(*dup['routes']):
        check('Identical #9/#10 alternatives share source text and localization identity',events[left]['loc_id']==events[right]['loc_id'] and events[left]['text_variants']==events[right]['text_variants'])
    def render_line(key,aliases=None):
        e=events[key];speaker='J' if e['speaker']=='Johnny' else ('Bot' if e['speaker']=='Fortuneteller' else e['speaker'])
        n=numbers.get(key);tag=' ['+'/'.join(map(str,aliases or [n]))+']' if n else ''
        text=e['text_variants']['male'].replace('\r','').replace('\n',' / ')
        return speaker+tag+': '+text
    text=['17 JOHNNY OCCURRENCES — GROUPED CONVERSATION CONTEXT','',
          'Two preceding and three following spoken lines, counting any speaker.',
          'Connected target windows are combined into one conversation; alternative',
          'choices remain separate. J [number] marks an occurrence from your 1–17 list.',
          'If an exchange starts/ends sooner, only the available lines are shown.',
          'English male-V wording; no new removal decisions are selected by this document.','']
    for group in groups:
        text+=['='*72,group['title'],'']
        if group.get('before_boundary'):text+=['['+group['before_boundary']+']','']
        if 'common' in group:
            text += [render_line(k) for k in group['common']]
            for branch in group['branches']:
                text+=['',branch['label']];text += [render_line(k) for k in branch['events']]
        elif group.get('identical_alternatives'):
            text += [render_line(k,[9,10] if k==one(9) else None) for k in group['routes'][0]]
        elif group.get('branch_labels'):
            for label,route in zip(group['branch_labels'],group['routes']):
                text += [label];text += [render_line(k) for k in route];text.append('')
        else:
            for key in group['routes'][0]:
                if group.get('conditional_after') and key==window(16,'after')[0]:text+=['','['+group['conditional_after']+']']
                text.append(render_line(key))
        if group.get('after_boundary'):text+=['','['+group['after_boundary']+']']
        text.append('')
    path=OUT/'Grouped_context_2_before_3_after.txt';path.write_text('\n'.join(text)+'\n',encoding='utf-8')
    write(OUT/'mapping.json',{'status':'SOURCE_BACKED_MERGED_17_TARGET_CONTEXT','predecessor_mapping':str(PREVIOUS/'mapping.json'),
        'predecessor_mapping_sha256':sha(PREVIOUS/'mapping.json'),'window':'2 preceding / 3 following, any speaker',
        'targets':windows,'groups':groups,'events':events,'document':str(path),'document_sha256':sha(path),
        'limits':'Independent triggers/actions, scene ends and repeated-topic loops remain explicit boundaries. Conditional bot-choice continuation is labelled. No cross-scene immediate chronology is invented.',
        'new_cut_selections':0,'game_writes':0,'save_writes':0})
    # Verify the serialized product, including target-number readback.
    rendered=path.read_text(encoding='utf-8')
    check('Saved transcript readback exact',rendered=='\n'.join(text)+'\n')
    write(OUT/'verification.json',{'status':'PASS_MERGED_TWO_BEFORE_THREE_AFTER','checks':len(checks),'details':checks,
        'groups':len(groups),'source_routes':sum(len(g['routes']) for g in groups),'target_occurrences':17,
        'document_sha256':sha(path),'mapping_sha256':sha(OUT/'mapping.json'),'new_cut_selections':0,'game_writes':0,'save_writes':0})
    cp_path=HERE/'checkpoint.json';cp=read(cp_path);cp.update(additional_context=str(path.relative_to(HERE)),
        additional_context_mapping=str((OUT/'mapping.json').relative_to(HERE)),additional_context_verification=str((OUT/'verification.json').relative_to(HERE)),
        additional_context_window='2 preceding / 3 following spoken lines, any speaker; grouped conversations and separate alternatives')
    cp_path.write_text(json.dumps(cp,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({'status':'PASS','checks':len(checks),'conversation_groups':len(groups),'targets':17,'text_lines':len(text)}))


if __name__=='__main__':main()
