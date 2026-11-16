"""Stage the boxing admission against the installed RD3 package."""
import importlib.util
import shutil
import sqlite3
import sys
from pathlib import Path

from capture import HERE, ROOT, BASELINE_SHA, baseline, read, sha, write

RED = 'r6/scripts/PTFR_Consolidated'
S22 = RED + '/PTFR_SideJobsS22.reds'
HS1 = RED + '/PTFR_HistorySnapshotHS1.reds'
ARCHIVE = 'archive/pc/mod/zzzz_PTFR_Combined.archive'


def once(source, old, new):
    assert source.count(old) == 1, old
    return source.replace(old, new, 1)


def source_pins(contract, game):
    database = ROOT / 'prealpha/quest_resume_registry_20261112_01/registry_02/registry.sqlite3'
    with sqlite3.connect(database.as_uri() + '?mode=ro', uri=True) as db:
        db.row_factory = sqlite3.Row
        rows = []
        for rid in contract['provider_ids']:
            row = dict(db.execute(
                'select rid,depot,key,archive,sha256,export_path,export_sha256 from resources where rid=?',
                (rid,),
            ).fetchone())
            assert Path(row['archive']).is_relative_to(game)
            assert sha(row['export_path']) == row['export_sha256'], row['depot']
            rows.append(row)
    return rows


def generated_reader(contract):
    # The pinned generator has no build actions at import.
    root = ROOT / 'prealpha/resume_dispatcher_rd1_20261112_01'
    sys.path.insert(0, str(root))
    spec = importlib.util.spec_from_file_location('rd1_contract_emitter', root / 'generate_contracts.py')
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    return generator.emit_reader(contract, 4)


def main():
    manifest, game = baseline()
    contract = read(HERE / 'contract.json')
    package = HERE / 'candidate_01' / 'package'
    evidence = HERE / 'evidence_01'
    assert not package.parent.exists()
    pins = source_pins(contract, game)
    for row in manifest['core_files']:
        destination = package / row['path']
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(game / row['path'], destination)
        assert sha(destination) == row['sha256']
    write(evidence / 'sources.json', pins)
    write(evidence / 'baseline.json', manifest)

    s22 = (package / S22).read_text(encoding='utf-8-sig')
    anchor = '    let sample: SideJobSampleS22;\n    let jm = GameInstance.GetJournalManager(this.GetGameInstance());'
    branch = '''    if i == 0 && ResumeDispatcherRD1.Journal(this.GetGameInstance(),
      "quests/minor_quest/mq025_psycho_brawl", "gameJournalQuest") == 4 {
      return this.ReadBoxingRD4();
    }
'''
    s22 = once(s22, anchor, branch + anchor)
    method = '''  private func ReadBoxingRD4() -> SideJobSampleS22 {
    let sample: SideJobSampleS22;
    let game = this.GetGameInstance();
    let observed = ResumeContractsRD1.Read4(game, false);
    let history = SnapshotStateHS1.Get(game);
    sample.states = observed.values;
    sample.reason = observed.reason;
    if !IsDefined(history) { return sample; }
    let live = ResumeDispatcherRD1.Journal(game, "quests/minor_quest/mq025_psycho_brawl", "gameJournalQuest");
    let decision = ResumeDispatcherRD1.Decide(history.HistoryRootRD1("mq025_psycho_brawl"), live,
      this.Own(0, "Issued"), false, this.Common(), false, observed.valid);
    sample.valid = Equals(decision, ResumeDecisionRD1.EarnedStage);
    return sample;
  }
'''
    s22 = once(s22, '  private func Same(a: SideJobSampleS22,', method + '  private func Same(a: SideJobSampleS22,')
    hs1 = (package / HS1).read_text(encoding='utf-8-sig')
    hs1 = once(hs1, 'public abstract class ResumeContractsRD1 {\n',
               'public abstract class ResumeContractsRD1 {\n' + generated_reader(contract) + '\n')
    for relative, source in ((S22, s22), (HS1, hs1)):
        original = (game / relative).read_bytes()
        newline = '\r\n' if b'\r\n' in original else '\n'
        codec = 'utf-8-sig' if original.startswith(b'\xef\xbb\xbf') else 'utf-8'
        (package / relative).write_bytes(source.replace('\n', newline).encode(codec))
    write(evidence / 'script_stage.json', {'baseline_manifest_sha256': BASELINE_SHA,
        'contract_sha256': sha(HERE / 'contract.json'), 'changed_paths': [HS1, S22]})
    print('Staged boxing script predicates against the verified RD3 installation.')


if __name__ == '__main__':
    main()
