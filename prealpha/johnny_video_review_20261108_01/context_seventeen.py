"""Show three surrounding spoken lines, any speaker, for the 17 review targets.

This reuses pure, source-checked scene readers. It never runs the old generator.
Independent trigger/focus/action waits bound the immediate dialogue windows.
"""
from pathlib import Path
import collections
import importlib.util
import json
import sqlite3
import sys

HERE=Path(__file__).resolve().parent;WS=HERE.parents[1]
sys.path.insert(0,str(WS/'prealpha/johnny_dialogue_review_20261107_02'))
spec=importlib.util.spec_from_file_location('source_context_pure',WS/'prealpha/johnny_dialogue_review_20261107_02/create_review.py')
api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api)


def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,d):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,indent=2,ensure_ascii=False);f.write('\n')


class ImmediateScene(api.Scene):
    def project(self,source):
        connections,ends=super().project(source)
        kept=[]
        for connection in connections:
            waits=[n for n in connection['notes'] if n['kind']=='WAIT' and n['condition'].get('$type')!='questTimeCondition']
            if waits:
                ends.append({'reason':'INDEPENDENT_TRIGGER_FOCUS_OR_ACTION_BOUNDARY','path':connection['path'],'waits':waits})
            else:kept.append(connection)
        self.projections[source]={'connections':kept,'boundaries':ends}
        return kept,ends

    def any_context(self,target,direction,count=3):
        links=self.forward if direction=='after' else self.backward
        stack=[(target,[],[],frozenset({target}))];results={};expansions=0
        while stack:
            current,selected,evidence,seen=stack.pop();expansions+=1
            assert expansions<250000,(target,direction)
            complete=len(selected)==count
            candidates=[] if complete else [e for e in links[current] if e['event_key'] not in seen]
            if complete or not candidates:
                ev=evidence if direction=='after' else list(reversed(evidence))
                start=target if direction=='after' or not selected else selected[-1]
                if self.fact_path_possible(ev,start):
                    results.setdefault(tuple(selected),{'events':selected,'evidence':evidence,'complete':complete,
                        'boundary':None if complete else 'Scene entry/end, separate trigger/action/focus, parallel timing or repeated-topic boundary.'})
                continue
            for link in candidates:
                stack.append((link['event_key'],selected+[link['event_key']],evidence+[link['evidence']],seen|{link['event_key']}))
        result=list(results.values()) or [{'events':[],'evidence':[],'complete':False,'boundary':'No fixed adjacent dialogue sequence established.'}]
        if direction=='before':
            for item in result:item['events'].reverse();item['evidence'].reverse()
        # Do not list a truncated helper route when a fuller equivalent window exists.
        result=[r for r in result if r['complete'] or not any(len(s['events'])>len(r['events']) and
                (s['events'][-len(r['events']):]==r['events'] if direction=='before' and r['events'] else
                 s['events'][:len(r['events'])]==r['events']) for s in result)]
        return sorted(result,key=lambda r:(not r['complete'],r['events']))


def main():
    out=HERE/'context_17_01';assert not out.exists();out.mkdir()
    numbered=read(HERE/'review_02/numbered_17_lines_01.json')['items']
    capture=read(HERE/'source_01/manifest.json');callers=read(HERE/'analysis_01/scene_callers.json')
    sources={r['depot']:r for r in capture['resources']};calls={r['depot']:r for r in callers['scenes']}
    dbpath=WS/'prealpha/johnny_dialogue_index_20261107_02/index_05/dialogue.sqlite3'
    assert api.sha(dbpath)==api.DB_SHA
    db=sqlite3.connect(dbpath.as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
    verified,providers,scenes,event_map={}, {}, {}, {}
    for dep in sorted({n['source_scene'] for n in numbered}):
        source=sources[dep]
        resource=dict(db.execute('SELECT * FROM resources WHERE depot=? AND raw_sha256=?',(dep,source['sha256'])).fetchone())
        resource.update(raw_path=source['raw'],json_path=source['json'],json_sha256=source['json_sha256'])
        row={'resource':resource,'callers':[{'may_reachable_in_phase':c['reachable'],'entry_names':c['inputs']} for c in calls[dep]['callers']]}
        scene=ImmediateScene(row,db,verified,providers)
        scenes[dep]=scene;event_map.update(scene.events)
    targets=[]
    for n in numbered:
        scene=scenes[n['source_scene']];assert n['event_key'] in scene.events
        before=scene.any_context(n['event_key'],'before');after=scene.any_context(n['event_key'],'after')
        targets.append({**n,'before':before,'after':after})
    def branch(ctx):
        labels=[]
        for evidence in ctx['evidence']:
            for note in evidence.get('notes',[]):
                if note['kind']=='CHOICE' and note['label'] not in labels:labels.append(note['label'])
        return ' -> '.join(labels) or 'same exchange / conditional connected source path'
    def line(key,target=False):
        e=event_map[key];v=e['text_variants'];text=v['male'].replace('\r','').replace('\n',' / ')
        return ('>>> ' if target else '    ')+e['speaker']+': '+text
    text=['17 JOHNNY REVIEW OCCURRENCES — THREE BEFORE / THREE AFTER','',
          'All speakers count in both directions. English male-V wording is shown.',
          'Different choice paths are separate alternatives, not one combined playthrough.',
          'Fewer lines means this exchange reaches a source boundary; unrelated dialogue',
          'is not inserted to fill three slots. Numbers match the preceding chat list.',
          'Bold/>>> marks the Johnny line under review. No new cuts are selected here.','']
    for item in targets:
        text+=['='*72,f"#{item['review_number']} — {item['quest']}",item['where'],
               'Scene: '+item['source_scene'].split('\\')[-1]+' | section '+item['section'],'','BEFORE']
        for i,ctx in enumerate(item['before'],1):
            if len(item['before'])>1:text.append('Alternative '+str(i)+': '+branch(ctx))
            text.extend(line(k) for k in ctx['events'])
            if not ctx['complete']:text.append(f"    [Only {len(ctx['events'])} preceding line(s) in this immediate exchange; source boundary.]")
        text+=['','TARGET',line(item['event_key'],True),'','AFTER']
        for i,ctx in enumerate(item['after'],1):
            if len(item['after'])>1:text.append('Alternative '+str(i)+': '+branch(ctx))
            text.extend(line(k) for k in ctx['events'])
            if not ctx['complete']:text.append(f"    [Only {len(ctx['events'])} following line(s) before this exchange ends or needs a separate trigger.]")
        text.append('')
    path=out/'Seventeen_lines_with_3_before_and_3_after.txt';path.write_text('\n'.join(text)+'\n',encoding='utf-8')
    used={t['event_key'] for t in targets}
    for t in targets:
        for ctx in t['before']+t['after']:used.update(ctx['events'])
    write(out/'mapping.json',{'status':'SOURCE_CHECKED_17_IMMEDIATE_CONTEXT_WINDOWS','targets':targets,'events':{k:event_map[k] for k in sorted(used)},
          'verified_sources':verified,'providers':[p['resource'] for p in providers.values()],
          'document':str(path),'document_sha256':api.sha(path),'window':'3 before and 3 after, any speaker',
          'limits':'Immediate scene/control windows; independent triggers/actions/focus, parallel outputs and repeated topics bound context. No engine chronology claim.',
          'game_writes':0,'save_writes':0})
    write(out/'verification.json',{'status':'PASS_17_SOURCE_CONTEXT_WINDOWS_WITH_BOUNDARIES','targets':len(targets),
          'preceding_alternatives':sum(len(t['before']) for t in targets),'following_alternatives':sum(len(t['after']) for t in targets),
          'unique_displayed_events':len(used),'document_sha256':api.sha(path),'mapping_sha256':api.sha(out/'mapping.json'),
          'boundary_windows':sum(not c['complete'] for t in targets for c in t['before']+t['after']),
          'game_writes':0,'save_writes':0})
    cp=read(HERE/'checkpoint.json');cp.update(additional_context='context_17_01/Seventeen_lines_with_3_before_and_3_after.txt',additional_context_mapping='context_17_01/mapping.json')
    (HERE/'checkpoint.json').write_text(json.dumps(cp,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({'targets':len(targets),'before_alternatives':sum(len(t['before']) for t in targets),
                      'after_alternatives':sum(len(t['after']) for t in targets),'lines':len(text),'unique_context_events':len(used)}))

if __name__=='__main__':main()
