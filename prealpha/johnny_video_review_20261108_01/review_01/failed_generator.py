"""Record the contextual review of returned notes without authoring game edits."""
from pathlib import Path
import collections
import gzip
import hashlib
import json
import sqlite3

HERE=Path(__file__).resolve().parent;WS=HERE.parents[1]
NAMES={'mq029_tourist':'The Highwayman','mq017_streetkid':'Small Man, Big Mouth','mq042_nomad':"These Boots Are Made for Walkin'",
       'mq040_biosculpt':'Raymond Chandler Evening','mq018_writer':'Killing in the Name'}

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def write(p,d):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,indent=2,ensure_ascii=False);f.write('\n')

def main():
    out=HERE/'review_01';assert not out.exists();out.mkdir()
    data=read(HERE/'matching_01/candidates.json');sources=read(HERE/'source_01/manifest.json')
    callers=read(HERE/'analysis_01/scene_callers.json');models=read(HERE/'analysis_01/models.json')
    receipt=read(HERE/'intake_01/receipt.json');assert sha(receipt['snapshot'])==receipt['notes_sha256']
    dbpath=WS/'prealpha/johnny_dialogue_index_20261107_02/index_05/dialogue.sqlite3'
    assert sha(dbpath)=='A60FEA94BDD5C7777484710E57753F558C80CFD36E553BE03DF02CB8EF459D2E'
    db=sqlite3.connect(dbpath.as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
    checks=[]
    def check(name,condition):
        assert condition,name
        checks.append(name)
    qualified={key for s in callers['scenes'] for key in s['dialogue_event_keys']}
    events={e['item_key']:e for e in data['dialogue'] if e['item_key'] in qualified}
    rows={s['depot']:s for s in sources['resources']}
    check('Exact fresh current sources and no provider ambiguity',sources['status']=='PASS_BATCH2_CURRENT_PRIVATE_PROVIDERS' and len(rows)==41 and not sources['issues'])
    for s in sources['resources']:
        check(s['depot']+' exact captured bytes',sha(s['raw'])==s['sha256'] and sha(s['json'])==s['json_sha256'])
    selected={};note_matches=[]
    def choose(e,reason,note_line):
        row=selected.setdefault(e['item_key'],{'event':e,'source':rows[e['depot']],'reasons':[],'note_lines':[]})
        if reason not in row['reasons']:row['reasons'].append(reason)
        if note_line not in row['note_lines']:row['note_lines'].append(note_line)
    for note in data['quote_matches']:
        best=note['candidates'][0]
        check('Quote line '+str(note['note_line'])+' source match',best['score']>=.8 and best['item_key'] in events)
        target=events[best['item_key']]
        # Identical localization records copied into alternative entry routes
        # represent the same quoted line. Preserve each physical event identity.
        aliases=[e for e in events.values() if e['quest']==target['quest'] and e['loc_id']==target['loc_id'] and e['speaker_role']==target['speaker_role']]
        for e in aliases:choose(e,'EXPLICIT_USER_QUOTE_SAME_LINE_ALL_CONNECTED_OCCURRENCES',note['note_line'])
        note_matches.append({**note,'reviewed_event_keys':[e['item_key'] for e in aliases],
                             'match_review':'Speaker, full canonical text/variants, scene and local context reviewed; spelling/ellipsis differences accepted. Same-line aliases explicit.'})
    direct_keys=set(selected)
    blocks=[
        ('mq018_05_brooklyn.scene',['73','75','77'],163,'Entire post-router two-option Johnny exchange, including both reply branches and its shared farewell.'),
        ('mq018_06_solar.scene',['80','84'],172,'Whole post-router Talk to Johnny section, including both option replies.'),
        ('mq018_07_protein.scene',['24','84','86','88'],177,'Billboard post-router Talk to Johnny section, both belief-option branches and the shared amusement-park reply.'),
        ('mq018_02_fortuneteller.scene',['39','66','137','245','249','252','266'],178,
         'Fortuneteller discovery/Johnny menu and post-hack Johnny reactions. Preserve explicitly retained V discovery, bot dialogue, payment and actual device outcomes.')]
    expanded=[]
    for suffix,sections,note_line,reason in blocks:
        keys=[]
        for e in events.values():
            if not e['depot'].endswith(suffix) or e['node_id'] not in sections or e['speaker_role'] not in ['V','JOHNNY']:continue
            if suffix=='mq018_02_fortuneteller.scene' and e['node_id']=='39' and e['speaker_role']=='V':continue
            choose(e,'EXPLICIT_WHOLE_EXCHANGE_REQUEST: '+reason,note_line);keys.append(e['item_key'])
        expanded.append({'scene_suffix':suffix,'sections':sections,'note_line':note_line,'reason':reason,'event_keys':keys})
    selected_choices=[]
    for suffix,node in [('mq018_05_brooklyn.scene','71'),('mq018_06_solar.scene','78'),('mq018_07_protein.scene','82'),('mq018_02_fortuneteller.scene','109')]:
        options=[c for c in data['choices'] if c['depot'].endswith(suffix) and c['node_id']==node]
        check(suffix+'/'+node+' exactly two requested dialogue options',len(options)==2)
        selected_choices += [{'choice':c,'disposition':'USER_REQUESTED_JOHNNY_CONVERSATION_OPTION_REMOVAL','source':rows[c['depot']]} for c in options]
    omitted=[e for e in events.values() if e['speaker_role']=='JOHNNY' and e['item_key'] not in selected]
    associated=[]
    for e in events.values():
        if e['item_key'] in selected or e['speaker_role']!='V':continue
        if (e['quest']=='mq017_streetkid' and e['depot'].endswith('mq017_streetkid_01a_johnny.scene')) or (
            e['quest']=='mq040_biosculpt' and e['node_id'] in ['13','14','30','267','40','186']) or (
            e['quest']=='mq018_writer' and e['depot'].endswith('mq018_02_fortuneteller.scene') and e['node_id']=='259' and e['event_ordinal']==3):
            associated.append(e)
    keep,=[e for e in events.values() if e['depot'].endswith('mq018_02_fortuneteller.scene') and e['node_id']=='39' and e['speaker_role']=='V']
    check('Explicit V discovery line retained',keep['item_key'] not in selected)
    keep_choices=[c for c in data['choices'] if c['depot'].endswith('mq018_02_fortuneteller.scene') and c['node_id'] in ['64','1078']]
    bridge,=[c for c in data['choices'] if c['depot'].endswith('mq018_02_fortuneteller.scene') and c['node_id']=='809']
    check('Native device and payment choices retained',len(keep_choices)==4 and not {c['choice_key'] for c in keep_choices}&{c['choice']['choice_key'] for c in selected_choices})
    fortune_dep=bridge['depot'];g=models[fortune_dep]['model']['graphs']['scene']
    for edge in [['64','0:0','80','0:1'],['64','0:1','82','0:1'],['809','0:0','872','0:0'],['872','0:0','1900','0:1']]:
        check('Native bot outcome edge '+str(edge),edge in g['edges'])
    check('Disabled/trolled facts are native choice writes',g['nodes']['80']['payload']['questNode']['type']['factName']=='mq018_swedenborg_disabled' and
          g['nodes']['82']['payload']['questNode']['type']['factName']=='mq018_swedenborg_trolled')
    providers={}
    # Check exact event/speaker/localization identities against the fresh raw
    # scene and retained external subtitle providers, including both V voices.
    for e in [r['event'] for r in selected.values()]+omitted+associated+[keep]:
        rsrc=models[e['depot']]['source'];doc=read(rsrc['json'])
        root=doc['Data']['RootChunk'];line,=[x for x in root['screenplayStore']['lines'] if str(x['itemId']['id'])==e['line_id']]
        check(e['item_key']+' exact localization identity',str(line['locstringId']['ruid'])==e['loc_id'])
        speaker=str(line['speaker']['id'])
        if e['speaker_role']=='V':
            check(e['item_key']+' player binding',speaker in {str(x['actorId']['id']) for x in root['playerActors']})
        elif e['speaker_role']=='JOHNNY':
            actor,=[x for x in root['actors'] if str(x['actorId']['id'])==speaker]
            check(e['item_key']+' Johnny binding',actor['actorName'].lower().startswith('johnny'))
        for loc in e['localization']:
            rid=loc['provider_resource_id']
            if rid not in providers:
                resource=dict(db.execute('SELECT * FROM resources WHERE resource_id=?',(rid,)).fetchone())
                check(rid+' retained localization provider pins',sha(resource['raw_path'])==resource['raw_sha256'] and sha(resource['json_path'])==resource['json_sha256'])
                p=Path(resource['json_path'])
                if p.suffix=='.gz':
                    with gzip.open(p,'rt',encoding='utf-8-sig') as f:obj=json.load(f)
                else:obj=read(p)
                providers[rid]={'resource':resource,'obj':obj}
            obj=providers[rid]['obj']
            for part in loc['source_path'].lstrip('/').split('/'):
                part=part.replace('~1','/').replace('~0','~');obj=obj[int(part)] if isinstance(obj,list) else obj[part]
            check(str(loc['text_id'])+' exact source subtitle',obj==loc['text'])
    counts=[]
    for qid,title in NAMES.items():
        cut=[r['event'] for r in selected.values() if r['event']['quest']==qid]
        counts.append({'quest':qid,'title':title,'selected_johnny':sum(e['speaker_role']=='JOHNNY' for e in cut),
                       'selected_v':sum(e['speaker_role']=='V' for e in cut),'additional_johnny':sum(e['quest']==qid for e in omitted)})
    check('Selected scope has 118 source events',len(selected)==118 and sum(c['selected_johnny'] for c in counts)==72 and sum(c['selected_v'] for c in counts)==46)
    check('Seventeen remaining Johnny occurrences require separate decision',len(omitted)==17)
    check('Fourteen associated V occurrences kept as proposals',len(associated)==14)
    # Native handoff contracts for the user-requested rewiring.
    contracts=[]
    for suffix,nodes in [('mq017_streetkid_03_confront_thugs.scene',['507','508','619','589','1024','1311']),
                         ('mq042_nomad_02_car_found.scene',['561','781']),
                         ('mq018_02_fortuneteller.scene',['967','803','1119','1380','1392','1385','1395'])]:
        dep,=[d for d in models if d.endswith(suffix)];gg=models[dep]['model']['graphs']['scene']
        for nid in nodes:
            contracts.append({'depot':dep,'node':nid,'payload':gg['nodes'][nid]['payload'],
                              'edges':[edge for edge in gg['edges'] if edge[0]==nid or edge[2]==nid]})
    review={'schema':1,'status':'NOTES_REVIEWED_NO_GAME_IMPLEMENTATION','recorded_date':'2026-11-08',
        'intake_receipt_sha256':sha(HERE/'intake_01/receipt.json'),'source_capture_sha256':sha(HERE/'source_01/manifest.json'),
        'source_callers_sha256':sha(HERE/'analysis_01/scene_callers.json'),'source_index_sha256':sha(dbpath),
        'notes_quotes':note_matches,'selected_spoken_events':list(selected.values()),'whole_exchange_expansions':expanded,
        'selected_dialogue_options':selected_choices,'explicit_retained_V':keep,'retained_device_and_payment_choices':keep_choices,
        'leave_connected_option':{'source_choice':bridge,'native_semantics':'809 -> 872 -> 1900 retains the leave-connected outcome.',
            'proposal':'Preserve this outcome as a bot/device choice, e.g. Leave it connected, while removing the Johnny-addressed label and following speech.',
            'status':'ADAPTATION_PROPOSAL_NOT_IMPLEMENTED'},
        'additional_johnny_not_selected':omitted,'associated_V_not_selected':associated,'per_quest_counts':counts,
        'deduplication':'Three clockwork note copies select one shared source event. Raymond arrival/Stop right there quotes select the same localization line in four connected scene-node copies.',
        'broad_scope_interpretation':'Before Go to signal source refers to the post-hack Brooklyn Johnny exchange and its options. Independent earlier router clues and Nancy calls are retained unless separately quoted.',
        'retiming_constraint':'Remove speech-only delays and Johnny acquisition/focus/workspots; preserve native actor/player actions, following/failure distances, hacking/payment, facts, device decisions, rewards, cut/interruption and completion outputs.',
        'source_handoff_contracts':contracts,'retained_subtitle_providers':[v['resource'] for v in providers.values()],
        'video_validation':'All five supplied YouTube pages failed direct fetch. Review uses user notes and source graphs; video route/complete choice coverage is not independently certified.',
        'holds':['Additional 17 Johnny and 14 associated V events are proposals only, pending user decision.',
                 'Preserve/reword the leave-connected bot outcome when removing Johnny choices; do not silently remove that outcome.',
                 'No edits, cooking, package, installation or saved-owner transition qualification included in this review.'],
        'game_writes':0,'save_writes':0,'implementation_authorized':False}
    write(out/'review.json',review)
    extra=['ADDITIONAL SOURCE LINES NOT YET SELECTED — BATCH 2','',
           'Your quoted cuts and whole-exchange requests are already mapped separately.',
           'These are additional Johnny lines found in the connected current sources.',
           'There are 17 event occurrences (one Raymond line is reused twice).',
           'The 14 accompanying V occurrences below are proposals, not approved cuts.',
           'You can approve a whole listed exchange or mark only specific lines.','']
    for qid,title in NAMES.items():
        js=[e for e in omitted if e['quest']==qid]
        if not js:continue
        extra+=['='*70,title.upper()]
        for e in js:
            text=(e['variants'].get('male') or [e['text']])[0]
            extra += ['Johnny: '+text,'  Source: '+e['depot'].split('\\')[-1]+' section '+e['node_id']]
        vs=[e for e in associated if e['quest']==qid]
        if vs:
            extra += ['','Associated V responses to consider:']
            for e in vs:extra.append('V: '+(e['variants'].get('male') or [e['text']])[0]+'  [section '+e['node_id']+']')
        extra.append('')
    extra+=['OUTCOME CHOICE TO PRESERVE','',
            'Killing in the Name: "Chill. Not gonna ruin your fun." is addressed to Johnny,',
            'but also selects leaving the bot connected. Proposed replacement: a bot/device',
            'choice such as "Leave it connected", with the same native outcome.',
            'Keep the real bot payment, Disconnect from Net and Modify to generate nonsense',
            'choices. Keep V: "Wait... What the hell\'s this?".']
    (out/'Additional_lines_to_review.txt').write_text('\n'.join(extra)+'\n',encoding='utf-8')
    report='''# Returned five-quest notes — source review

All 73 quoted note entries match source dialogue after accounting for spelling, ellipses and wording variants. The three repeated “like clockwork” entries collapse to one shared V event. The Raymond arrival narration and “Stop right there” have four connected copies of the same localization records; the proposal covers those copies explicitly.

The source-checked interpretation selects **72 Johnny events, 46 V events and eight dialogue options**. This includes both branches of the exchanges you explicitly requested in full. The other NPC dialogue and device/payment choices remain. The counts are proposed edit targets, not implemented changes.

| Quest | Johnny selected | V selected | Additional Johnny not yet selected |
| --- | ---: | ---: | ---: |
'''
    for c in counts:report+=f"| {c['title']} | {c['selected_johnny']} | {c['selected_v']} | {c['additional_johnny']} |\n"
    report+='''
## What still needs a decision

There are **17 additional Johnny occurrences** and **14 associated V responses** outside the interpreted requests. The [additional-lines file](Additional_lines_to_review.txt) contains their exact source wording. Small Man, Big Mouth has an entire early Johnny conversation before the Kirk meeting, including two reply branches. Raymond has alternate target/approach and ripperdoc-exit narration. Killing in the Name has arrival/ambient bot comments and the other post-quest outcome remark. None is silently added to your selected cuts.

Killing in the Name also has a third outcome hidden behind Johnny-addressed wording: **“Chill. Not gonna ruin your fun.” leaves the bot connected**. Removing that choice outright would drop an outcome. The proposal is to present the same native choice at the bot, with wording such as “Leave it connected”, while removing its Johnny dialogue. Keep the real payment, disconnect and modify choices.

## Rewiring interpretation

- **The Highwayman:** remove the two Johnny exchanges and their speech-only time. Preserve garage/photo inspection, body investigation, clues and bike access. Both selected V lines are honored even where they describe the situation.
- **Small Man, Big Mouth:** after opening the truck, bypass the Johnny talk gate to the original return-to-Kirk continuation. After the gangoons, bypass the final Johnny conversation to the native completion path. Preserve discovery, container/player actions, combat and rewards. The separately omitted early conversation remains a review item.
- **These Boots Are Made for Walkin’:** your notes cover all three Johnny ending branches. Remove their speech-only waits and the shared selected “clockwork” line; bypass the Talk to Johnny objective. Preserve Lana choices, payment, car ownership/unlock and the genuine ending callbacks.
- **Raymond Chandler Evening:** “none” means no requested gameplay sequence rewrite. Remove selected narration/replies and Johnny presentation; preserve Cynthia’s route, following distances/failure handling, investigation, NPC conversations and Pepe outcomes. Alternate narration/replies are listed separately for review.
- **Killing in the Name:** bypass the post-router Johnny talk gates at Brooklyn, solar plant, billboard and the bot. Keep actual router discovery/hacking and the next signal objectives. At the bot, retain V’s **“Wait... What the hell’s this?”**, bot speech, payment and all three device outcomes. Once the native hack/outcome step completes, proceed directly to **Call Nancy** without another Johnny conversation. Nancy’s actual call/acknowledgement and quest completion remain native. “Every dialogue before Go to signal’s source” is scoped to that post-hack Johnny exchange; unrelated earlier clues and Nancy dialogue are not swept into it.

Johnny entity/shadow, digital spawn effects, title/scanner presence, cigarette and smoke remain cleanup targets throughout the affected scenes. An empty remnant field or “none” in that field is not a request to leave Johnny visible.

## Evidence and limits

Fresh capture decoded **41 current private resources** across **134 archive indices**, with exact expected payload hashes and unique providers. Connected phase inputs account for all **89 indexed Johnny events** in these five quest closures. Raw event IDs, line IDs, actor/player bindings and both V subtitle variants were checked. Retained subtitle provider raw/export hashes and exact text pointers were checked. This is structural source qualification, not condition feasibility, saved-owner retirement, world placement or live behavior proof.

The supplied YouTube pages failed direct fetch; no claim of independently watched videos or complete video branch coverage is made. The review relies on your transcription and the game sources. Retiming must retain non-dialogue player/NPC actions and native callbacks rather than setting every edited scene duration to zero.

Your edited file is preserved in [intake](../intake_01/user_notes_received.txt). [Exact review targets and keeps](review.json), [caller evidence](../analysis_01/scene_callers.json), [source capture](../source_01/manifest.json), [verification](verification.json). No game resources, installed files, saves or facts changed. This task reviews the notes; it does not build or install the five-quest change.
'''
    (out/'REVIEW.md').write_text(report,encoding='utf-8')
    write(out/'verification.json',{'status':'PASS_RETURNED_NOTES_SOURCE_AND_SCOPE_REVIEW','checks':len(checks),'details':checks,
        'review_sha256':sha(out/'review.json'),'report_sha256':sha(out/'REVIEW.md'),'additional_lines_sha256':sha(out/'Additional_lines_to_review.txt'),
        'quoted_notes':73,'selected_spoken_events':118,'selected_johnny':72,'selected_v':46,'selected_options':8,
        'additional_unselected_johnny':17,'associated_unselected_v':14,'explicit_keeps':1,'game_writes':0,'save_writes':0})
    cp=read(HERE/'checkpoint.json');cp.update(status='RETURNED_NOTES_REVIEWED_ADDITIONAL_BRANCH_DECISIONS_PENDING',
        intake='intake_01/receipt.json',notes_review='review_01/REVIEW.md',exact_review='review_01/review.json',review_verification='review_01/verification.json',
        additional_review='review_01/Additional_lines_to_review.txt',selected_spoken_events=118,selected_johnny_events=72,selected_v_events=46,
        selected_dialogue_options=8,additional_johnny_pending=17,associated_v_pending=14,implementation_authorized=False,
        next_action='User reviews the 17 additional Johnny occurrences/14 associated V replies and the leave-connected bot choice adaptation. Prepare a successor only after the affected decisions are settled and implementation requested.')
    (HERE/'checkpoint.json').write_text(json.dumps(cp,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({'status':'PASS','checks':len(checks),'quotes':73,'selected_spoken':118,'additional_johnny':17,'associated_v':14,'choices':8,'game_writes':0}))

if __name__=='__main__':main()
