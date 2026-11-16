"""Generate the current history and inventory checks for the existing U9 scheduler."""
import importlib.util
from verify_entrance import HERE, baseline, read, sha, write

ACTIVITY = 'r6/scripts/PTFR_Consolidated/PTFR_ActivityStateR3.reds'


def replace_once(source, old, new):
    assert source.count(old) == 1, old
    return source.replace(old, new, 1)


def main():
    manifest, game = baseline()
    stage = read(HERE / 'evidence_01/admission.json')
    journals = [{**row, 'history': [row['history']], 'live': [row['live']]} for row in stage['journals']]
    tag = stage['tag']
    ignored = {tag+'ResumeRequested', tag+'ResumePermit', 'PTFRU9_Retaliation_maelstroms_Issued',
               'PTFRU9_Retaliation_Issued'} | stage['history_facts'].keys()
    receipts = [k for k, v in stage['native_facts'].items() if k not in ignored and v == 0
                and k.startswith(('PTFRG2_', tag))]
    live = {k: v for k, v in stage['native_facts'].items() if k not in ignored and k not in receipts}
    contract = {'id': stage['id'], 'journals': journals, 'fixed_facts': stage['history_facts'],
                'choice_facts': [], 'counter_facts': [], 'live_only_facts': live,
                'own_receipts': receipts, 'other_owner_receipts': [], 'item': None, 'handoff': []}
    root = HERE.parent / 'resume_dispatcher_rd1_20261112_01'
    import sys
    sys.path.insert(0, str(root))
    spec = importlib.util.spec_from_file_location('rd1_reader', root / 'generate_contracts.py')
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    reader = generator.emit_reader(contract, 5).replace('Read5(game: GameInstance,requireHandoff: Bool)', 'Read(game: GameInstance)')
    reader = replace_once(reader, '    result.valid=true;', '''    let player=GetPlayer(game);let tx=GameInstance.GetTransactionSystem(game);
    if !IsDefined(player) || !IsDefined(tx) { return result; }
    let cards=tx.GetItemQuantity(player,ItemID.CreateQuery(t"Keycards.nid_05_keycard"));
    ArrayPush(result.values,cards);if cards!=1 { result.reason="Clinic keycard missing or ambiguous.";return result; }
    result.valid=true;''')
    for path, state in stage['live_phone'].items():
        check = f'    if ResumeDispatcherRD1.Journal(game,"{path}","gameJournalPhoneMessage")!={state} {{ return result; }}\n'
        reader = replace_once(reader, '    let player=GetPlayer(game);', check + '    let player=GetPlayer(game);')

    source_file = game / ACTIVITY
    data = source_file.read_bytes()
    source = source_file.read_text(encoding='utf-8-sig')
    marker = 'public class NativeGigsU9 extends ScriptableSystem {\n'
    source = replace_once(source, marker, 'public abstract class RiteResumeRD5 {\n' + reader + '\n}\n\n' + marker + '''  private let ritePrevious: ref<ResumeObservationRD1>;
  private func PollRiteResume(safe: Bool) -> Void {
    let id="sts_wat_nid_05";
    if this.Own(id,"ParentEntered")!=0 || this.Own(id,"Started")!=0 { return; }
    let current: ref<ResumeObservationRD1>;
    if safe && this.Own(id,"Ready")==1 && this.Own(id,"Revision")==1 && this.OldUnused(NativeGigDataU9.Index(id)) && this.RetaliationAdmissible("maelstroms") {
      current=RiteResumeRD5.Read(this.GetGameInstance());
    }
    let qualified=ResumeDispatcherRD1.Same(this.ritePrevious,current);
    this.ritePrevious=current;
    let permit=0;
    if qualified && this.Own(id,"ResumeRequested")>=0 && this.Own(id,"ResumeRequested")<=1 {
      let requested=this.Own(id,"ResumeRequested")==1 || this.Set(id,"ResumeRequested",1);
      if requested && (this.Own("Retaliation","Request")==1 || this.Set("Retaliation","Request",1)) &&
        (this.Own("Retaliation_maelstroms","Request")==1 || this.Set("Retaliation_maelstroms","Request",1)) &&
        this.Own("Retaliation","Issued")==1 && this.Own("Retaliation_maelstroms","Issued")==1 {
        permit=1;
      }
    }
    if this.Own(id,"ResumePermit")!=permit { this.Set(id,"ResumePermit",permit); }
  }
''')
    start = source.index(marker)
    prefix, scheduler = source[:start], source[start:]
    scheduler = replace_once(scheduler, 'public func Restored() -> Void { this.epoch+=1;', '''public func Restored() -> Void {
    this.ritePrevious=null;
    if this.Own("sts_wat_nid_05","ParentEntered")==0 && this.Own("sts_wat_nid_05","ResumePermit")==1 {
      this.Set("sts_wat_nid_05","ResumePermit",0);
    }
    this.epoch+=1;''')
    scheduler = replace_once(scheduler, '    if this.Own("Retaliation","Request")==1 &&',
                             '    this.PollRiteResume(safe);\n    if this.Own("Retaliation","Request")==1 &&')
    path = HERE / 'candidate_01/package' / ACTIVITY
    assert not path.exists()
    path.parent.mkdir(parents=True)
    newline = '\r\n' if b'\r\n' in data else '\n'
    path.write_bytes((prefix+scheduler).replace('\n', newline).encode('utf-8-sig' if data.startswith(b'\xef\xbb\xbf') else 'utf-8'))
    assert sha(source_file) == next(f['sha256'] for f in manifest['core_files'] if f['path']==ACTIVITY)
    write(HERE / 'evidence_01/script_stage.json', {'baseline_source_sha256': sha(source_file),
          'staged_source_sha256': sha(path), 'admission_sha256': sha(HERE/'evidence_01/admission.json')})


if __name__ == '__main__':
    main()
