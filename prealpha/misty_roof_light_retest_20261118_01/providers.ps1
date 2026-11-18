# Capture the two current visual sectors and verify their provider lists.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ws = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$manifest = Join-Path $ws 'prealpha/misty_roof_chair_prompt_20261118_01/installed_manifest.json'
if ((Get-FileHash $manifest).Hash -cne '775D0F839EC4C782692C068548A61FD7D05D9C06155B1AD4CF337DD46D5E74E9') { throw 'Installed manifest drift' }
$base = Get-Content $manifest -Raw | ConvertFrom-Json
$out = Join-Path $PSScriptRoot 'work/inputs'
if (Test-Path $out) { throw 'Fresh capture required' }
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$names = [WolvenKit.Common.Services.HashService]::new()
$names.Load()
$targets = @{}
foreach ($depot in 'base\worlds\03_night_city\_compiled\default\exterior_-1_0_0_6.streamingsector',
                   'base\worlds\03_night_city\_compiled\default\exterior_-7_4_0_2.streamingsector') {
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
            @{depot=$name;archive=$file.Name;raw=$raw;sha256=(Get-FileHash $raw).Hash}
        }
    }
})
@{archives=$count;hits=$records} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $out 'providers.json') -Encoding utf8NoBOM
Write-Output "Captured $($records.Count) providers across $count archives."
