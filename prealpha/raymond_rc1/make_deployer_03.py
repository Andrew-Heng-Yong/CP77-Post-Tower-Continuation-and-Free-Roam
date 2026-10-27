"""Adapt the previously fixture-tested atomic CR1 installer to RC2's two files."""
from pathlib import Path

H=Path(__file__).resolve().parent
source=H.parent/'consolidation_repair_cr1/deploy_02.ps1'
out=H/'deploy_03.ps1'
assert not out.exists(),out
text=source.read_text(encoding='utf-8')
edits={
    "'candidate_01'":"'candidate_03'",
    "'install_manifest_02.json'":"'install_manifest_03.json'",
    "'recovery/consolidation_repair_cr1_01'":"'recovery/raymond_rc2_01'",
    "'deploy_fixtures_02'":"'deploy_fixtures_03'",
    "'deployment_tests_02.json'":"'deployment_tests_03.json'",
    "'CR1_CONSOLIDATED_SUCCESSOR_STAGED'":"'RC2_CONSOLIDATED_SUCCESSOR_STAGED'",
    "'CR1_CONSOLIDATED_INSTALLED_LIVE_PENDING'":"'RC2_CONSOLIDATED_INSTALLED_LIVE_PENDING'",
    ".ptfr-cr1-stage":".ptfr-rc2-stage",
    "$m.files.Count -lt 1 -or $m.files.Count -gt 3":"$m.files.Count -ne 2",
    "@('archive/pc/mod/zzzz_PTFR_Combined.archive','archive/pc/mod/zzzz_PTFR_Combined.archive.xl','r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds')":"@('archive/pc/mod/zzzz_PTFR_Combined.archive','r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds')",
}
for before,after in edits.items():
    assert before in text,before
    text=text.replace(before,after)
assert 'CR1_' not in text and 'candidate_01' not in text
out.write_text(text,encoding='utf-8')
print(out)
