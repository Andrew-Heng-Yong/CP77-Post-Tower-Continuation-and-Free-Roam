Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ws = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$path = '$/03_night_city/c_pacifica/coastview/cvi_ce_prefabMZQN2IY/#ce_pac_cvi_116/cs_goons_cars_com'
$hash = [WolvenKit.RED4.Types.NodeRef]::CalculateHash($path)
Write-Output ([ordered]@{ref=$path; hash=$hash.ToString(); expected='13399962301655001666'} | ConvertTo-Json)
