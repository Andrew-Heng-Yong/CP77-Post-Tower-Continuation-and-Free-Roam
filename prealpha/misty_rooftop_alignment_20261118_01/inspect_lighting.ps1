# Capture current providers for the roof lighting volumes and the pickup variant.
param([switch]$PickupRanges)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$before = Join-Path $workspace 'prealpha/misty_rooftop_seat_repair_20261118_01/installed_manifest.json'
if ((Get-FileHash $before).Hash -cne '9374EE66A5D4D83030A732B22AC1C3280EBDF72D9E7793F67BF7D8AB936B53F6') { throw 'Manifest drift' }
$m = Get-Content $before -Raw | ConvertFrom-Json
$out = Join-Path $PSScriptRoot $(if ($PickupRanges) { 'work/pickup_ranges_01' } else { 'work/lighting_01' })
if (Test-Path -LiteralPath $out) { throw 'Fresh research output required' }
$tool = Join-Path $workspace 'prealpha/world_overlap_20261116_01/work/tooling/wolvenkit_10_0_0_beta_1/package'
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot $tool
$names = [WolvenKit.Common.Services.HashService]::new()
$names.Load()
$targets = @{}
$sectors = @('exterior_-7_4_0_2', 'exterior_-13_9_0_1', 'exterior_-24_18_0_0')
if ($PickupRanges) {
    $block = Join-Path $workspace 'prealpha/misty_rooftop_lift_20261117_01/work/native_01/36/base/worlds/03_night_city/_compiled/default/blocks/all.streamingblock.json'
    if ((Get-FileHash -LiteralPath $block).Hash -cne '7B6904BF851CF1D91B89C065D0A9B3C026AB4B6007B65F0D9C30FD5DDDD926D5') { throw 'Sector descriptor drift' }
    $ranges = @{}
    foreach ($descriptor in (Get-Content -LiteralPath $block -Raw | ConvertFrom-Json -AsHashtable -Depth 100).Data.RootChunk.descriptors) {
        $indices = @($descriptor.variants | Where-Object { $_.name.'$value' -ceq 'Q307_AV' } | ForEach-Object {
            if ($_.enabledByDefault -ne 0 -or $_.variantId -ne 194410905 -or $_.parentVariantID -ne 0 -or
                !$_.nodeRef.'$value'.EndsWith('/#loc_q115_mystic_mistys_ripperdoc_roof_lighting')) { throw 'Unexpected pickup variant owner' }
            $_.rangeIndex
        })
        if ($indices.Count) { $ranges[$descriptor.data.DepotPath.'$value'] = $indices }
    }
    $sectors = @($ranges.Keys | ForEach-Object { [IO.Path]::GetFileNameWithoutExtension($_) })
}
foreach ($sector in $sectors) {
    $depot = "base\worlds\03_night_city\_compiled\default\$sector.streamingsector"
    $targets[[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot)] = $depot
}
$seen = 0
$captured = @(foreach ($relative in 'archive/pc','mods') {
    $root = Join-Path $m.game_root $relative
    if (!(Test-Path -LiteralPath $root)) { continue }
    if (@(Get-ChildItem -LiteralPath $root -Force -Recurse -Attributes ReparsePoint).Count) { throw 'Linked archive tree' }
    foreach ($arcFile in Get-ChildItem -LiteralPath $root -File -Recurse -Filter '*.archive') {
        $seen++
        $archive = $null
        if (([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($arcFile.FullName,$names,[ref]$archive).ToString() -cne 'NoError') { throw "Unreadable archive $arcFile" }
        foreach ($key in $targets.Keys) {
            if (!$archive.Files.ContainsKey($key)) { continue }
            $dest = Join-Path $out ($arcFile.Name + '/' + [IO.Path]::GetFileName($targets[$key]))
            [void][IO.Directory]::CreateDirectory((Split-Path -Parent $dest))
            $mem = [IO.MemoryStream]::new()
            try {
                $archive.Files[$key].Extract($mem)
                [IO.File]::WriteAllBytes($dest,$mem.ToArray())
                $mem.Position = 0
                $reader = [WolvenKit.RED4.Archive.IO.CR2WReader]::new($mem)
                $reader.add_ParsingError([WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($problem)
                    return $problem -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs]
                })
                $cr = $null
                if ($reader.ReadFile([ref]$cr,$true).ToString() -cne 'NoError') { throw 'Sector decode failed' }
                if ($PickupRanges -and $arcFile.Name -ceq 'ep1_1_nightcity.archive') {
                    $s = $cr.RootChunk
                    $listed = @(foreach ($range in $ranges[$targets[$key]]) {
                        foreach ($instance in $s.VariantNodes[$range - 1]) {
                            $node = $s.Nodes[[int]$instance.NodeIdx.ToString()].Chunk
                            @{range=$range;type=$node.GetType().Name;name=$node.DebugName.ToString();node=[int]$instance.NodeIdx.ToString()}
                        }
                    })
                    ConvertTo-Json -Depth 4 -InputObject $listed | Set-Content -LiteralPath ($dest+'.json') -Encoding utf8NoBOM
                } elseif (!$PickupRanges) {
                    Export-Cr2wJson $cr ($dest+'.json')
                } else { continue }
            } finally { $mem.Dispose() }
            @{depot=$targets[$key];archive=$arcFile.FullName;raw=$dest;sha256=(Get-FileHash -LiteralPath $dest).Hash;
              json=($dest+'.json');json_sha256=(Get-FileHash -LiteralPath ($dest+'.json')).Hash}
        }
    }
})
@{archives_checked=$seen;providers=$captured} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $out 'providers.json') -Encoding utf8NoBOM
Write-Output "Captured $($captured.Count) providers across $seen archives."
