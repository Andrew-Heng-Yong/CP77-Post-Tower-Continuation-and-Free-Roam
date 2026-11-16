"""Create the next five-quest manual notes and a source-backed review list.

Reads the sealed index and selection registry. Writes only this fresh task's
documents/evidence; no source resource, build, installation, fact or save edits.
"""
from pathlib import Path
import collections
import hashlib
import json
import re
import sqlite3

HERE=Path(__file__).resolve().parent
WS=HERE.parents[1]
DB=WS/'prealpha/johnny_dialogue_index_20261107_02/index_05/dialogue.sqlite3'
REG=WS/'research/gig_restoration/lore_whitelists_v6_2_sidejobs.json'
POLICY=WS/'prealpha/johnny_dialogue_scope_audit_20261107_01/scope_policy.json'
CURRENT=WS/'prealpha/sweet_dreams_sd1/deployment_01/installed_manifest_01.json'
NEXT=['mq029_tourist','mq017_streetkid','mq042_nomad','mq040_biosculpt','mq018_writer']


def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def write(p,d):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,indent=2,ensure_ascii=False);f.write('\n')


def main():
    out=HERE/'output_01';assert not out.exists();out.mkdir()
    registry={r['id']:r for r in read(REG)['decision_registry']}
    included={i:r for i,r in registry.items() if r['decision']=='INCLUDE'}
    assert sha(DB)=='A60FEA94BDD5C7777484710E57753F558C80CFD36E553BE03DF02CB8EF459D2E'
    db=sqlite3.connect(DB.resolve().as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
    grouped=collections.defaultdict(list)
    for row in db.execute("""SELECT s.resource_id,s.item_key,s.depot,r.scope,r.archive,r.raw_sha256
        FROM search_items s JOIN resources r USING(resource_id)
        WHERE s.kind='DIALOGUE_EVENT' AND s.speaker_role='JOHNNY' ORDER BY s.depot,s.item_key"""):
        dep=row['depot']
        # Match actual path components, not a bare substring such as mq303/q303.
        components=dep.split('\\')
        match=None
        for component in components:
            candidates=[i for i in included if (i.startswith(('sts_','mws_')) and
                        (component==i or component.startswith(i+'_')))]
            if candidates:
                match=max(candidates,key=len);break
            m=re.fullmatch(r'(mq\d{3}|sq\d{3})',component)
            if m:
                family=m.group(1)
                if family=='mq025':match='mq025_psycho_brawl'
                elif family=='sq025':match='sq025_delamain'
                elif family=='sq023':match='sq023_family'
                else:
                    choices=[i for i in included if i.startswith(family+'_')]
                    if len(choices)==1:match=choices[0]
                break
        if match:grouped[match].append(dict(row))
    records=[]
    for qid,events in sorted(grouped.items()):
        if qid=='sq023_family':
            members=['sq023_hit_order','sq023_bd_passion','sq023_real_passion']
            assert all(i in included for i in members)
            title='Sinnerman / There Is A Light That Never Goes Out / They Won\'t Go When I Go'
            note='Shared SQ023 family; map each event to its actual job and connected branch before editing.'
        else:
            members=[qid];title=included[qid]['title'];note=''
        if qid=='sq025_delamain':
            title='Delamain quest chain (SQ025)'
            note='Indexed crash and later core scenes. Review Human Nature / Don\'t Lose Your Mind job boundaries; do not assign the same events to every Epistrophy job or Tune Up.'
        if qid=='mq025_psycho_brawl':
            title='Beat on the Brat — finale'
            note='Johnny source is mq025_08_finale.scene; this is not a finding against every individual fight.'
        if qid=='mq017_streetkid':note='Streetkid route only.'
        if qid=='mq042_nomad':note='Nomad route only.'
        if qid=='mq041_corpo':note='Corpo route only.'
        status=('COMPLETE_USER_ACCEPTED_KM2' if qid=='mq016_bartmoss' else
                'SD1_INSTALLED_LIVE_TEST_PENDING' if qid=='mq036_overload' else
                'NEXT_FIVE_QUEST_REVIEW' if qid in NEXT else 'SOURCE_IDENTIFIED_REVIEW_PENDING')
        by_resource={}
        for e in events:
            key=e['resource_id']
            by_resource.setdefault(key,{k:e[k] for k in ['resource_id','depot','scope','archive','raw_sha256']})
        records.append({'id':qid,'title':title,'registry_ids':members,'status':status,'note':note,
                        'qualification':'INCLUDE selection plus indexed bound Johnny speech; exact caller/branch review still required except where separately evidenced.',
                        'sources':list(by_resource.values()),'event_keys':[e['item_key'] for e in events]})
    byid={r['id']:r for r in records}
    assert len(NEXT)==len(set(NEXT))==5 and all(q in byid for q in NEXT)
    assert not any(r['id'] in {'q303','mq303_addict','mq023_bootleg','q115','q307'} for r in records)
    assert not {'mq016_bartmoss','mq036_overload'} & set(NEXT)
    services=[]
    for name in ['karim','ronald','yoko']:
        rows=[dict(r) for r in db.execute("""SELECT DISTINCT s.depot,r.raw_sha256,r.scope FROM search_items s JOIN resources r USING(resource_id)
            WHERE s.kind='DIALOGUE_EVENT' AND s.speaker_role='JOHNNY' AND s.depot=?""",
            ('towercontinued\\b0_story_eight\\'+name+'.scene',))]
        if rows:services.append({'name':name,'sources':rows,'qualification':'Standalone service candidate; do not re-include an excluded quest solely because the service shares its scene.'})
    text=['JOHNNY REMOVAL REVIEW LIST — 8 NOVEMBER 2026','',
          'Known selected quest content with bound Johnny speech in the verified source index.',
          'This is a review queue, not a claim that every listed branch runs on your current save.',
          'Individual callers, choices and rewiring will be checked before implementation.',
          'The full post-Tower denominator, shared/ambient coverage and indirect V-only reactions',
          'remain open. A quest absent here is not certified Johnny-free.','',
          'ALREADY HANDLED','  KOLD MIRAGE — user-accepted complete; no repeat review.',
          '  Sweet Dreams — SD1 cleanup installed; live test pending; no repeat removal notes.','',
          'NEXT FIVE — fill in Five_quest_removal_and_rewire_notes.txt']
    for n,qid in enumerate(NEXT,1):
        row=byid[qid];text.append(f"  {n}. {row['title']}"+(f" — {row['note']}" if row['note'] else ''))
    others=[r for r in records if r['id'] not in NEXT+['mq016_bartmoss','mq036_overload']]
    for label,predicate in [('OTHER SIDE JOBS / SHARED QUEST CHAINS',lambda r:not r['id'].startswith(('sts_','mws_'))),
                            ('BASE-GAME GIGS',lambda r:r['id'].startswith('sts_') and not r['id'].startswith('sts_ep1_')),
                            ('PHANTOM LIBERTY GIGS',lambda r:r['id'].startswith('sts_ep1_')),
                            ('OTHER NAMED ACTIVITIES',lambda r:r['id'].startswith('mws_'))]:
        text+=['',label]
        for row in sorted(filter(predicate,others),key=lambda r:r['title'].casefold()):
            text.append('  - '+row['title']+((' — '+row['note']) if row['note'] else ''))
    text+=['','ADDITIONAL SHARED SERVICE / WORLD REVIEW',
           '  - Karim, Ronald and Yoko service conversations have indexed Johnny speech.',
           '    Review their independent post-Tower callers; this does not re-include',
           "    The Ballad of Buck Ravers or another excluded quest.",
           '  - Shared passenger/world remarks, voiceset dispatches and V-only reactions',
           '    require their own caller review and are not exhausted by this quest list.','',
           'EXCLUDED FROM THIS ASSIGNMENT',
           '  You Know My Name (q303), original Tower/endings/main-story execution,',
           '  and quests excluded by the selection registry. No new restoration or unlock.','',
           'Source-backed identities and limits: ../review_manifest.json']
    checklist=out/'Johnny_quest_review_list.txt';checklist.write_text('\n'.join(text)+'\n',encoding='utf-8')
    hints={
        'mq029_tourist':'Watch the garage/photo and Josie-body investigation. Keep clues, James/Josie discovery and bike access workable.',
        'mq017_streetkid':'Watch Johnny commentary around Kirk and the truck/thug confrontation. Keep the actual meeting, combat and loot outcomes.',
        'mq042_nomad':"Watch V's old car and the Lana conversation. Keep the player's car/ownership outcome choices.",
        'mq040_biosculpt':"Watch the wife-tail and ripperdoc conversations. Keep investigation clues and the player's report/outcome with Pepe.",
        'mq018_writer':'Watch Nancy calls, terminal investigations and the final Swedenborg conversation. Keep searches, hacking, clue/objective changes and the final outcome choices.'}
    lines=['FIVE-QUEST REMOVAL AND REWIRE NOTES — BATCH 2','',
           'Edit this file while watching playthroughs. Add or delete blank rows freely.',
           'Use Johnny: / V: followed by at least five consecutive quoted words.',
           'For a shorter line or OPTION:, copy the whole line/label.',
           'An option and its spoken reply are separate: list both, or write BOTH.',
           'You may write "Remove all Johnny dialogue in this quest" explicitly.',
           'A video URL is useful. A timestamp is needed only to resolve an ambiguous match.','',
           'Rewire notes: describe OLD sequence -> DESIRED sequence, including any',
           'Johnny-dependent wait, Talk prompt, inspect/scan step or forced action to skip.',
           'Say what must still happen (clue, item, choice, objective, door/elevator, outcome).',
           'Write "No rewiring needed" after reviewing it, or "Unsure: ..." if unclear.',
           'Blank fields mean not reviewed; these prompts and examples select no cuts.',
           'Unseen branches and all proposed changes will be checked against game sources.','',
           'Visual cleanup applies to Johnny entity/shadow, spawn/glitch effects, title/name,',
           'scanner identity, cigarette and smoke. Note special locations or timing below.',
           'Existing KOLD MIRAGE and Sweet Dreams notes are preserved separately.']
    for n,qid in enumerate(NEXT,1):
        row=byid[qid]
        lines+=['','='*72,f"{n}. {row['title'].upper()}"]
        if row['note']:lines.append('Route: '+row['note'])
        lines += ['Video URL:','V voice (optional):',
                  'Playthrough search: Cyberpunk 2077 '+row['title']+' full walkthrough','',
                  'Watch points (source-based prompts, not removal selections):',hints[qid],'',
                  'DIALOGUE / OPTIONS TO REMOVE',
                  'Johnny:','V:','OPTION:','',
                  'REWIRE NOTES',
                  'Observed sequence / Johnny dependency:',
                  'Desired sequence (or "No rewiring needed"):',
                  'Clues/items/choices/objectives/outcomes to preserve:','',
                  'VISUAL / INTERACTION REMNANTS',
                  'Location, timestamp or description:','',
                  'UNSEEN BRANCHES / UNSURE CUT BOUNDARIES',
                  'Notes:']
    lines+=['','='*72,'Return this edited file or paste notes in chat. No game IDs are needed.',
            'Review notes do not authorize resetting completed quests or replaying rewards.']
    notes=out/'Five_quest_removal_and_rewire_notes.txt';notes.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    # Keep an immutable original for comparison; the output copy belongs to the user.
    evidence=HERE/'evidence_01';evidence.mkdir()
    (evidence/'original_notes.txt').write_bytes(notes.read_bytes())
    manifest={'schema':1,'recorded_date':'2026-11-08','status':'FIVE_QUEST_USER_REVIEW_NOTES_PREPARED',
        'requested_scope':'Quest removal list and five new quests of editable dialogue/option, presentation and rewiring notes. No implementation.',
        'input_pins':{str(p):sha(p) for p in [DB,REG,POLICY,CURRENT]},'next_quests':NEXT,'quest_groups':records,'service_candidates':services,
        'quest_list':str(checklist),'quest_list_sha256':sha(checklist),'notes':str(notes),'notes_initial_sha256':sha(notes),
        'original_notes':str(evidence/'original_notes.txt'),'source_index_limit':'Pre-JP1 snapshot. KOLD and Sweet handled separately; no replay/edit selection is inferred from old index events.',
        'qualification_limit':'Registry plus source speech is a review lead, not complete post-Tower execution proof. Native/shared caller and job-family boundaries remain explicit.',
        'prior_qualified_five_quest_evidence':str(WS/'prealpha/johnny_dialogue_review_20261107_02/evidence_05/review_manifest.json'),
        'unknown_total_post_tower_coverage':True,'approved_new_removals':0,'approved_new_rewires':0,'game_writes':0,'save_writes':0}
    write(HERE/'review_manifest.json',manifest)
    write(HERE/'review_protocol.json',{'schema':2,'recorded_date':'2026-11-08','status':'CURRENT_FIVE_QUEST_USER_REVIEW',
        'supersedes_for_next_batch':str(WS/'prealpha/johnny_video_review_20261107_01/review_protocol.json'),
        'quest_ids':NEXT,'notes':str(notes),'quote_rule':'Speaker plus at least five consecutive words, or full short line/option. Option and spoken reply separate unless BOTH.',
        'rewire_rule':'User records observed and desired order, dependencies to remove and outcomes to preserve. None/Unsure permitted. Blank fields do not mean no rewire.',
        'visual_targets':['Johnny entity/shadow','spawn/glitch effect','title/name','scanner identity','cigarette','smoke'],
        'selection_rule':'Explicit returned notes select proposals. Template hints/labels/blank fields select nothing. Resolve exact IDs, both V variants, all connected choices and caller context before implementation.',
        'uncertainty_rule':'Unshown branches, ambiguous quotes and mixed-purpose V reactions remain review cases; video omission is not absence proof.',
        'implementation_or_deployment_authorized_by_this_batch':False})
    write(HERE/'checkpoint.json',{'schema':1,'status':'AWAITING_FIVE_QUEST_DIALOGUE_AND_REWIRE_NOTES','recorded_date':'2026-11-08',
        'notes':'output_01/Five_quest_removal_and_rewire_notes.txt','quest_list':'output_01/Johnny_quest_review_list.txt','manifest':'review_manifest.json',
        'protocol':'review_protocol.json','next_quests':NEXT,'installed_baseline':str(CURRENT),'kold_mirage':'COMPLETE_USER_ACCEPTED_KM2',
        'sweet_dreams':'SD1_INSTALLED_LIVE_TEST_PENDING_SUPPORTED_FIXTURE','approved_new_removals':0,'approved_new_rewires':0,
        'next_action':'User reviews five quests and edits speaker/option removal quotes plus rewiring notes. Match returned decisions to source identities/branches before proposing implementation.',
        'game_writes':0,'save_writes':0})
    print(json.dumps({'review_groups':len(records),'next_quests':len(NEXT),'base_gig_groups':sum(r['id'].startswith('sts_') and not r['id'].startswith('sts_ep1_') for r in records),
                      'PL_gig_groups':sum(r['id'].startswith('sts_ep1_') for r in records),'notes_lines':len(lines),'game_writes':0}))


if __name__=='__main__':main()
