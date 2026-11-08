"""Preserve user-supplied read-only CET observations, without game/save access."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def main():
    out=H/'observations/brendan_getters_01';assert not out.exists();out.mkdir(parents=True)
    sources=[Path(r'C:\Users\Ayong\AppData\Local\Temp\codex-clipboard-503c2b4a-1894-4253-8f4b-8889f7aaba56.png'),Path(r'C:\Users\Ayong\AppData\Local\Temp\codex-clipboard-fe0a9d25-c334-4f53-9061-40256060b87f.png')]
    images=[]
    for source,name in zip(sources,['facts.png','journals.png']):
        target=out/name;target.write_bytes(source.read_bytes());assert sha(target)==sha(source)
        images.append({'original_path':str(source),'preserved_path':str(target),'sha256':sha(target)})
    data={'status':'NO_READY_BRENDAN_FIXTURE_ESTABLISHED','date':'2026-11-03','provenance':'User-executed CET getter commands and supplied screenshots. No assistant game/CUA/API operation.',
        'save_identity':{'requested':'ManualSave-24, 2Nov16:37:02','confirmed':'NOT_CONFIRMED_BY_USER_OR_SCREENSHOT','scope':'Findings apply to the loaded state shown, not independently bound to a saved slot/body.'},
        'facts_visible':{'mq037_brendan_introduced':0,'mq037_01_05Sure':0,'mq037_clerk_convinced':0,'mq037_done':0,'PTFRS23_MQ037_Issued':1,'PTFRS23_MQ037_Entered':1,'PTFRS23_MQ037_Finished':0},
        'fact_not_readable':{'mq037_vandal_painted_brendan':'Value cropped at right edge; do not infer zero.'},
        'journal_getter_observations':[{'id':id,'path':'quests/minor_quest/'+id,'class':'gameJournalQuest','displayed_state':'gameJournalEntryState : Inactive (1)'}for id in ['mq037_brendan_dumpster','mq037_brendan_hooligan001','mq037_brendan']],
        'interpretation':{'current_journal_state':'All three queried entries are Inactive; no active/completed entry is shown.',
            'native_earned_history':'NOT_ESTABLISHED. Inactive entries and current zero facts do not prove a never-started pre-Tower history.',
            'private_receipts':'Issued1/Entered1 are present, Finished0. This contradicts a clean unadmitted negative fixture but is not actual executing-owner, native earned-history, reward or completion proof.',
            'earned_descendant_test':'No genuine earned progressed descendant fixture established.',
            'fresh_containment_test':'No clean genuinely never-started/unadmitted fixture established.',
            'gameplay_defect':'NOT_DEMONSTRATED','next':'No additional Brendan CET checks or special gameplay test requested. Do not reset receipts/facts, force entry or manufacture earned history.'},
        'limits':['Direct getter snapshots, not native callbacks or a sampled change sequence.','No exact quest graph/listener/controller/owner liveness proof.','No native-write ordering or full historical inference.','Original QR12 inventory, completion, review and preservation records remain immutable; their before/after window predates subsequent human game use.'],
        'images':images,'assistant_game_launches':0,'assistant_game_CUA_or_API_calls':0,'assistant_runtime_or_save_changes':0}
    (out/'result.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    (out/'REPORT.md').write_text('# Brendan getter observation — 3 November 2026\n\nAll three native Brendan journal entries read Inactive(1). Visible native facts read0; private Issued/Entered read1 and Finished0. The vandal fact value is cropped and remains unreadable.\n\nThe user did not separately confirm the requested ManualSave-24 slot; these are loaded-state observations only. No earned or active descendant fixture is established, and the private receipts prevent treating this as a clean unadmitted negative fixture. Neither Inactive nor current0 proves never-earned pre-Tower history. No quest defect or executing-owner state is proved.\n\nNo further Brendan command or special test is requested. Keep native/private progress intact and wait for genuine new supported history/stage evidence. Read-only getters do not start a quest. Original QR12 evidence remains unchanged; this later observation does not extend the earlier preservation window over human gameplay. Exact image/source hashes and observations are in result.json.\n',encoding='utf-8')
    print({'status':data['status'],'journal_entries_inactive':3,'images_preserved':len(images),'save_identity_confirmed':False})
if __name__=='__main__':main()
