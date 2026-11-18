# Read the instances in the retained pickup variant, including its flight areas.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$capture = Join-Path $ws 'prealpha/misty_rooftop_alignment_20261118_01/work/pickup_ranges_01'
$out = Join-Path $PSScriptRoot 'work/sector_details'
if (Test-Path $out) { throw 'Fresh output required' }
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'prealpha/world_overlap_20261116_01/work/tooling/wolvenkit_10_0_0_beta_1/package')
$records = Get-Content (Join-Path $capture 'providers.json') -Raw | ConvertFrom-Json
[void][IO.Directory]::CreateDirectory($out)
foreach ($p in $records.providers) {
    if ((Get-FileHash $p.raw).Hash -cne $p.sha256) { throw 'Source drift' }
    $s = [IO.File]::OpenRead($p.raw)
    try {
        $reader = [WolvenKit.RED4.Archive.IO.CR2WReader]::new($s)
        $reader.add_ParsingError([WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e)
            return $e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs]
        })
        $file=$null
        if ($reader.ReadFile([ref]$file,$true).ToString() -cne 'NoError') { throw 'Sector decode failed' }
        Export-Cr2wJson $file (Join-Path $out ([IO.Path]::GetFileName($p.raw)+'.json'))
    } finally { $s.Dispose() }
}
