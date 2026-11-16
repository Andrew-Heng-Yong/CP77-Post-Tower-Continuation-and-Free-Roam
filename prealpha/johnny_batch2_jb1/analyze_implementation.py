from pathlib import Path
import json

HERE=Path(__file__).resolve().parent;WS=HERE.parents[1]
PRIOR=WS/'prealpha/johnny_video_review_20261108_01'


def main():
    out=HERE/'analysis_02';assert not out.exists();out.mkdir()
    read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
    models=read(PRIOR/'analysis_01/models.json');rev=read(PRIOR/'review_02/review.json');inventory=read(PRIOR/'matching_01/candidates.json')
    selected={r['event']['item_key']:r['event'] for r in rev['selected_spoken_events']}
    for e in rev['additional_johnny_not_selected']+rev['associated_V_not_selected']:selected[e['item_key']]=e
    for e in inventory['dialogue']:
        if e['quest']=='mq018_writer' and e['depot'].endswith('mq018_02_fortuneteller.scene') and e['node_id']=='259' and e['event_ordinal']==0:selected[e['item_key']]=e
    assert len(selected)==150,len(selected)
    (out/'approved_speech.json').write_text(json.dumps({'status':'USER_APPROVED_ALL_89_JOHNNY_AND_61_V_EVENTS','events':list(selected.values()),
        'source_capture':str(PRIOR/'source_01/manifest.json'),'visual_cleanup':True,'raymond_four_V_replies':'Explicit user async reply approved'},indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    for dep in sorted({e['depot'] for e in selected.values()}):
        m=models[dep]['model'];g=m['graphs']['scene'];a=next(a for a in m['metadata']['actors'] if a['actorName'].lower().startswith('johnny'));aid=a['actorId']['id']
        lines=['JOHNNY_ACTOR '+str(aid)+' performer '+str((aid<<8)|1)+' flags '+json.dumps(a['spawnDespawnParams']),
               'ENTRIES '+json.dumps(g['entries']),'EXITS '+json.dumps([(e['name']['$value'],str(e['nodeId']['id'])) for e in m['metadata']['exitPoints']])]
        for nid,n in sorted(g['nodes'].items(),key=lambda x:int(x[0])):
            p=n['payload'];q=p.get('questNode',{});kind=n['type'];brief=kind
            if q:
                brief=q['$type']
                if 'condition' in q:brief+=' '+json.dumps(q['condition'],ensure_ascii=False)
                elif 'type' in q:brief+=' '+json.dumps(q['type'],ensure_ascii=False)
                elif 'paramsV1' in q:brief+=' '+q['paramsV1']['function']+' '+json.dumps(q['entityReference'],ensure_ascii=False)
            if kind=='scnSectionNode':
                sp=[(e['speaker_role'],e['event_id'],e['item_key'] in selected) for e in inventory['dialogue'] if e['depot']==dep and e['node_id']==nid]
                callbacks=[(ev['startTime'],str(ev['osockStamp']['name'])+':'+str(ev['osockStamp']['ordinal'])) for ev in p['events'] if ev['$type']=='scneventsSocket']
                brief+=' ms='+str(p['sectionDuration']['stu'])+' VO='+json.dumps(sp)+' SOCKETS='+json.dumps(callbacks)
            if kind=='scnChoiceNode':
                ch=[c for c in inventory['choices'] if c['depot']==dep and c['node_id']==nid]
                brief+=' '+json.dumps([(c['output_stamp'],c['texts']) for c in ch],ensure_ascii=False)
            if kind=='scnEndNode':brief+=' '+p['type']
            lines += [nid+' '+brief,'  OUT '+json.dumps([e[1:] for e in g['edges'] if e[0]==nid])]
        (out/(dep.split('\\')[-1]+'.txt')).write_text('\n'.join(lines)+'\n',encoding='utf-8')
    cp=HERE/'checkpoint.json';d=read(cp);d.update(open_optional_clarification=None,raymond_four_V_replies='REMOVE_EXPLICIT_USER_APPROVAL',selected_spoken_events=150)
    cp.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Approved speech: 89 Johnny + 61 V. Wrote twelve graph summaries.')


if __name__=='__main__':main()
