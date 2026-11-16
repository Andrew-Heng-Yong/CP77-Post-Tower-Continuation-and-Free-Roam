"""Package and bind the qualified candidate without writing to the game."""
from pathlib import Path

from capture import HERE

ARCHIVE = 'archive/pc/mod/zzzz_PTFR_Combined.archive'
HS1 = 'r6/scripts/PTFR_Consolidated/PTFR_HistorySnapshotHS1.reds'
S22 = 'r6/scripts/PTFR_Consolidated/PTFR_SideJobsS22.reds'
CANDIDATE_ROOT = HERE.with_name('resume_dispatcher_rd3_20261113_01')
EPOCH = 'RD3_EPISTROPHY_NORTHSIDE_RESUME'
BEFORE = 'RD2_THE_GIG_REWARD_RESUME'
SCHEMA = 'PTFR_RD3_EPISTROPHY_NORTHSIDE_RESUME_CORE_V1'
CHANGES = {ARCHIVE, HS1, S22}
PACKAGE = CANDIDATE_ROOT / 'candidate_01/package'
MANIFEST = HERE / 'core_manifest_01.json'
INSTALLER = HERE / 'deploy_core.ps1'
DEPLOYMENT = HERE / 'deployment_01'
PS = Path(r'C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe')

