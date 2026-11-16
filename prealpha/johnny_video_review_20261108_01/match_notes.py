"""Produce source candidates for returned quotes; fuzzy matches are not approvals."""
from pathlib import Path
import collections
import difflib
import hashlib
import json
import re
import sqlite3

HERE=Path(__file__).resolve().parent
WS=HERE.parents[1]
QUESTS=['mq029_tourist','mq017_streetkid','mq042_nomad','mq040_biosculpt','mq018_writer']

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,d):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,indent=2,ensure_ascii=False);f.write('\n')
def words(t):return re.findall(r'[a-z0-9]+',t.lower().replace("'",'').replace('’',''))
def similarity(quote,text):
    q,t=words(quote),words(text)
    if not q or not t:return 0
    qstr=' '.join(q);tstr=' '.join(t)
    if qstr in tstr:return 1.0
    score=0
    for size in range(max(1,len(q)-2),min(len(t),len(q)+2)+1):
        for start in range(len(t)-size+1):
            score=max(score,difflib.SequenceMatcher(None,qstr,' '.join(t[start:start+size])).ratio())
    return round(score,4)

def owner(depot):
    for code,qid in [('mq029','mq029_tourist'),('mq017','mq017_streetkid'),('mq042','mq042_nomad'),('mq040','mq040_biosculpt'),('mq018','mq018_writer')]:
        if '\\'+code+'\\' in depot or '\\vehicles\\'+code+'_' in depot:return qid
    raise AssertionError(depot)

def main():
    out=HERE/'matching_01';assert not out.exists();out.mkdir()
    db=sqlite3.connect((WS/'prealpha/johnny_dialogue_index_20261107_02/index_05/dialogue.sqlite3').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
    candidates=[];resources=[];choices=[]
    for request in read(HERE/'source_queries_01.json')['queries']:
        if not request['depot'].endswith('.scene'):continue
        rows=list(db.execute('SELECT * FROM resources WHERE depot=? AND raw_sha256=?',(request['depot'],request['expected_sha256'])))
        assert len(rows)==1,request['depot']
        resource=dict(rows[0]);resources.append(resource)
        qid=owner(request['depot'])
        for row in db.execute("SELECT s.*,e.event_id,e.event_ordinal,e.start_time,e.duration,e.payload_json AS event_payload_json FROM search_items s JOIN events e ON e.event_key=s.item_key WHERE s.resource_id=? AND s.kind='DIALOGUE_EVENT'",(resource['resource_id'],)):
            item=dict(row)
            locs=[dict(r) for r in db.execute("SELECT * FROM localization WHERE loc_id=? AND locale='en_us' AND root_id IS NULL",(item['loc_id'],))]
            variants=collections.defaultdict(set)
            for loc in locs:
                if loc['text']:variants[loc['gender']].add(loc['text'])
            item.update(quest=qid,variants={k:sorted(v) for k,v in variants.items()},localization=locs)
            candidates.append(item)
        for row in db.execute('SELECT * FROM choices WHERE root_id=?',(resource['resource_id']+'/root',)):
            item=dict(row);locs=[dict(r) for r in db.execute("SELECT * FROM localization WHERE root_id=? AND loc_id=? AND locale='en_us'",(item['root_id'],item['loc_id']))]
            item.update(quest=qid,depot=request['depot'],texts=sorted({r['text'] for r in locs if r['text']}),localization=locs)
            choices.append(item)
    notes=(HERE/'intake_01/user_notes_received.txt').read_text(encoding='utf-8-sig').splitlines()
    quotes=[];directives=[];quest=None;section=None
    for num,line in enumerate(notes,1):
        heading=re.match(r'^([1-5])\. ',line)
        if heading:quest=QUESTS[int(heading[1])-1];section=None;continue
        if not quest:continue
        if line in ['DIALOGUE / OPTIONS TO REMOVE','REWIRE NOTES','UNSEEN BRANCHES / UNSURE CUT BOUNDARIES','VISUAL / INTERACTION REMNANTS']:
            section=line;continue
        match=re.match(r'^\s*(J|Johnny|V):\s*(.+)',line,re.I)
        if not match:
            m=re.match(r'^After.*?johnny:\s*(.+)',line,re.I)
            if m:match=('JOHNNY',m[1])
        if match and section=='DIALOGUE / OPTIONS TO REMOVE':
            if isinstance(match,tuple):speaker,quote=match
            else:speaker='V' if match[1].upper()=='V' else 'JOHNNY';quote=match[2]
            ranked=[]
            for item in candidates:
                if item['quest']!=quest or item['speaker_role']!=speaker:continue
                texts={item['text']}|{t for vals in item['variants'].values() for t in vals}
                best=max(((similarity(quote,t),t) for t in texts),key=lambda p:p[0])
                ranked.append({'item_key':item['item_key'],'event_id':item['event_id'],'node':item['node_id'],
                               'depot':item['depot'],'score':best[0],'text':best[1]})
            ranked.sort(key=lambda r:(-r['score'],r['item_key']))
            quotes.append({'note_line':num,'quest':quest,'speaker':speaker,'quote':quote,'candidates':ranked[:3]})
        elif line.strip() and section in ['DIALOGUE / OPTIONS TO REMOVE','REWIRE NOTES']:
            directives.append({'note_line':num,'quest':quest,'section':section,'text':line})
    write(out/'candidates.json',{'status':'SOURCE_CANDIDATES_REQUIRE_CONTEXT_REVIEW','resources':resources,'dialogue':candidates,
         'choices':choices,'quote_matches':quotes,'other_notes':directives,'game_writes':0,'save_writes':0})
    rows=[]
    for quote in quotes:
        best=quote['candidates'][0];rows.append(f"L{quote['note_line']} {quote['quest']} {quote['speaker']} [{best['score']}] {best['node']} {quote['quote']}\n    => {best['text']}\n    {best['item_key']}")
    (out/'match_preview.txt').write_text('\n'.join(rows)+'\n',encoding='utf-8')
    for quest in QUESTS:
        transcript=[]
        for item in sorted((i for i in candidates if i['quest']==quest and i['speaker_role'] in ['V','JOHNNY']),key=lambda i:(i['depot'],int(i['node_id']),int(i['start_time']))):
            texts=item['variants'].get('male') or [item['text']]
            transcript.append(f"{item['depot'].split(chr(92))[-1]} | {item['node_id']}:{item['event_ordinal']} | {item['speaker_role']}: {' / '.join(texts)} | {item['event_id']}")
        (out/(quest+'_transcript.txt')).write_text('\n'.join(transcript)+'\n',encoding='utf-8')
    print(json.dumps({'quotes':len(quotes),'source_dialogue_events':len(candidates),'choices':len(choices),
                     'low_score_quotes':[q['note_line'] for q in quotes if q['candidates'][0]['score']<.8]}))

if __name__=='__main__':main()
