# Capture the live mesh and check providers for the private scene and placement sector.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ws = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$manifest = Join-Path $ws 'prealpha/misty_roof_lighting_and_seat_20261118_01/installed_manifest.json'
if ((Get-FileHash $manifest).Hash -cne 'C34D07FF41E4714082CAAD9294CE112AFD704EDFF2EB7F7626F5DBCDB2761BF4') { throw 'Installed manifest drift' }
$base = Get-Content $manifest -Raw | ConvertFrom-Json
$out = Join-Path $PSScriptRoot 'work/inputs'
if (Test-Path $out) { throw 'Fresh capture required' }
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$names = [WolvenKit.Common.Services.HashService]::new()
$names.Load()
$targets = @{}
foreach ($depot in 'base\environment\decoration\furniture\outdoor\poor_utility_chair\poor_utility_chair_d.mesh',
                   'base\worlds\03_night_city\_compiled\default\exterior_-25_18_0_0.streamingsector',
                   'towercontinued\misty_rooftop_seat\sit.scene') {
    $targets[[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot)] = $depot
}
$count = 0
$records = @(foreach ($sub in 'archive/pc','mods') {
    $folder = Join-Path $base.game_root $sub
    if (!(Test-Path -LiteralPath $folder)) { continue }
    if (@(Get-ChildItem -LiteralPath $folder -Recurse -Force -Attributes ReparsePoint).Count) { throw 'Linked tree' }
    foreach ($file in Get-ChildItem -LiteralPath $folder -Recurse -Filter '*.archive' -File) {
        $count++
        $a = $null
        if (([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName,$names,[ref]$a).ToString() -cne 'NoError') { throw "Unreadable archive $file" }
        foreach ($key in $targets.Keys) {
            if (!$a.Files.ContainsKey($key)) { continue }
            $name = $targets[$key]
            $raw = Join-Path $out ($file.Name+'/'+[IO.Path]::GetFileName($name))
            [void][IO.Directory]::CreateDirectory((Split-Path $raw -Parent))
            $s = [IO.MemoryStream]::new()
            try { $a.Files[$key].Extract($s); [IO.File]::WriteAllBytes($raw,$s.ToArray()) } finally { $s.Dispose() }
            if ($name.EndsWith('.mesh')) { Export-Cr2wJson (Read-Cr2wFile $raw) ($raw+'.json') }
            @{depot=$name;archive=$file.Name;raw=$raw;sha256=(Get-FileHash $raw).Hash}
        }
    }
})
@{archives=$count;hits=$records} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $out 'providers.json') -Encoding utf8NoBOM
Write-Output "Captured $($records.Count) providers across $count archives."
