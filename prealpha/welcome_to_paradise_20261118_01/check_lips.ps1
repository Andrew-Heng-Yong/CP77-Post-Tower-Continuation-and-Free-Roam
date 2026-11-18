Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$work=Join-Path $PSScriptRoot 'work'
$out=Join-Path $work 'lipmap_comparison'
if (Test-Path $out) {throw 'Fresh comparison required'}
$null=New-Item -ItemType Directory $out
$extra=Get-Content (Join-Path $work 'extra_01/providers.json') -Raw | ConvertFrom-Json
$native='base\localization\en-us.lipmap';$combined='towercontinued\sidejob_repair_sr1\en-us.lipmap'
foreach ($pair in @(@('original',$native),@('installed',$combined))) {
    $hit=@($extra.hits | Where-Object depot -ceq $pair[1])
    if ($hit.Count -ne 1 -or (Get-FileHash $hit[0].raw).Hash -cne $hit[0].sha256) {throw 'Lipmap source drift'}
    Export-Cr2wJson (Read-Cr2wFile $hit[0].raw) (Join-Path $out ($pair[0]+'.json'))
}
