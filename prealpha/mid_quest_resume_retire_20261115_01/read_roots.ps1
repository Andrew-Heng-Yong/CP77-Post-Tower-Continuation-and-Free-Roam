param([Parameter(Mandatory)][string]$Output)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$workspace = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
$owner = Join-Path $workspace 'prealpha/resume_dispatcher_rd10_kirk_20261113_01/archive_01'
$manifest = Join-Path $owner 'readback.json'
if ((Get-FileHash -LiteralPath $manifest).Hash -cne '5BBD9BB8F04AA5CC235B9845BDE691E2D6105B70E98083B36D7A8F54A3B29B81') { throw 'RD10 member inventory drift' }
$known = (Get-Content -Raw -LiteralPath $manifest | ConvertFrom-Json -AsHashtable).members
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$out = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot $Output))
if ($Output -notmatch '^stage_[0-9]+$' -or (Test-Path -LiteralPath $out)) { throw 'Expected a fresh stage directory' }
[void][IO.Directory]::CreateDirectory($out)
$roots = @($known | Where-Object {$_.depot -match 'sidejobs_s22\\|resume_rd1\\|mq007_resume_boot|mq037.questphase|sts_wat_nid_05_entry|mq017_meet_kirk|sidejobs_s29\\entries\\mq017_streetkid'})
foreach ($root in $roots) {
    $source = Join-Path (Join-Path $owner 'source') $root.depot
    if ((Get-FileHash -LiteralPath $source).Hash -cne $root.sha256) { throw "Source payload drift for $source" }
    $relative = $root.depot.Replace('\', '_') + '.json'
    Export-Cr2wJson (Read-Cr2wFile $source) (Join-Path $out $relative)
}
Write-Output "Read back $($roots.Count) pinned private quest resources."
