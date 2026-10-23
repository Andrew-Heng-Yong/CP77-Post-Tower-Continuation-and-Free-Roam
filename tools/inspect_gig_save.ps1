param(
    [Parameter(Mandatory=$true)][string[]]$SavePaths,
    [string]$CataloguePath = 'research/gig_restoration/state_probe_catalogue.json',
    [string]$OutputPath = 'research/gig_restoration/save_audit_20261008.json'
)
# Offline evidence only. Never instantiate a save writer or open a source for writing.
$ErrorActionPreference = 'Stop'
$workspaceRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$outputFull = [IO.Path]::GetFullPath((Join-Path $workspaceRoot $OutputPath))
$researchRoot = [IO.Path]::GetFullPath((Join-Path $workspaceRoot 'research/gig_restoration')) + [IO.Path]::DirectorySeparatorChar
if (!$outputFull.StartsWith($researchRoot, [StringComparison]::OrdinalIgnoreCase) -or [IO.Path]::GetExtension($outputFull) -ne '.json') {
    throw 'Output must be a JSON report under research/gig_restoration.'
}
if (Test-Path -LiteralPath $outputFull) { throw 'Refusing to overwrite an existing audit report.' }
$catalogueFull = (Resolve-Path -LiteralPath (Join-Path $workspaceRoot $CataloguePath)).Path
$catalogue = Get-Content -LiteralPath $catalogueFull -Raw | ConvertFrom-Json
$names = @($catalogue.fact_names)
if (!$names.Count -or ($names | Where-Object { $_ -isnot [string] -or $_ -notmatch '^[A-Za-z0-9_]+$' })) { throw 'Invalid fact-name catalogue.' }
$names = @($names | Sort-Object -Unique)
$wkRoot = 'C:/Users/Ayong/Documents/WolvenKit-8.20.0'
foreach ($assembly in @('WolvenKit.Core.dll','WolvenKit.Common.dll','WolvenKit.RED4.dll')) {
    [void][Reflection.Assembly]::LoadFrom((Join-Path $wkRoot $assembly))
}
$factHashMethod = [WolvenKit.RED4.Save.Fact].GetMethods() | Where-Object { $_.Name -eq 'op_Implicit' -and $_.ReturnType -eq [uint32] }
if (@($factHashMethod).Count -ne 1) { throw 'Fact hash conversion not uniquely available.' }
$wanted = @{}
foreach ($name in $names) {
    $fact = [WolvenKit.RED4.Save.Fact]::op_Implicit($name)
    $hash = [uint32]$factHashMethod.Invoke($null,[object[]]@($fact))
    if ($wanted.ContainsKey($hash)) { throw "Requested fact-name hash collision: $name" }
    $wanted[$hash] = $name
}
$samples = [Collections.Generic.List[object]]::new()
foreach ($source in $SavePaths) {
    $sourceFull = (Resolve-Path -LiteralPath $source).Path
    if ([IO.Path]::GetFileName($sourceFull) -ne 'sav.dat') { throw 'Expected explicit sav.dat input.' }
    $metadataPath = Join-Path ([IO.Path]::GetDirectoryName($sourceFull)) 'metadata.9.json'
    $saveHash = (Get-FileHash -LiteralPath $sourceFull -Algorithm SHA256).Hash
    $metadataHash = (Get-FileHash -LiteralPath $metadataPath -Algorithm SHA256).Hash
    $metadata = (Get-Content -LiteralPath $metadataPath -Raw | ConvertFrom-Json).Data.metadata
    $factRows = [ordered]@{}
    foreach ($name in $names) { $factRows[$name] = [Collections.Generic.List[object]]::new() }
    $stream = [IO.File]::Open($sourceFull,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
    try {
        $reader = [WolvenKit.RED4.Save.IO.CyberpunkSaveReader]::new($stream)
        $save = $null
        $parseResult = $reader.ReadFile([ref]$save).ToString()
        if ($parseResult -ne 'NoError') { throw "Save parser refused $sourceFull : $parseResult" }
        $pending = [Collections.Generic.Stack[object]]::new()
        foreach ($node in $save.Nodes) { $pending.Push(@{node=$node;path=$node.Name}) }
        $tables = 0
        while ($pending.Count) {
            $item = $pending.Pop()
            $node = $item.node
            if ($node.Value -is [WolvenKit.RED4.Save.FactsTable]) {
                $tables++
                foreach ($entry in $node.Value.FactEntries) {
                    $hash = [uint32]$factHashMethod.Invoke($null,[object[]]@($entry.FactName))
                    if ($wanted.ContainsKey($hash)) {
                        $factRows[$wanted[$hash]].Add([ordered]@{table_path=$item.path;table_ordinal=$tables;value=[uint32]$entry.Value;hash=[string]$hash})
                    }
                }
            }
            foreach ($child in $node.Children) { $pending.Push(@{node=$child;path=($item.path+'/'+$child.Name)}) }
        }
        $finished = @($metadata.finishedQuests -split '\s+' | Where-Object { $_ })
        $samples.Add([ordered]@{
            source=$sourceFull;sha256=$saveHash;metadata_sha256=$metadataHash;parse_result=$parseResult
            slot=$metadata.name;timestamp=$metadata.timestampString;game_version=$metadata.gameVersion
            playthrough_id=$metadata.playthroughID;point_of_no_return_id=$metadata.pointOfNoReturnId
            play_time=$metadata.playTime;playthrough_time=$metadata.playthroughTime
            body_metadata=$metadata.strength;tracked_metadata=$metadata.trackedQuestEntry
            tower_finished_metadata=($finished -contains 'q307')
            finished_gigs_metadata=@($finished | Where-Object { $_ -like 'sts_*' })
            fact_tables=$tables;facts=$factRows
            journal_decoded=$false;unchanged_after_read=$true
        })
    } finally { $stream.Dispose() }
    if ((Get-FileHash -LiteralPath $sourceFull -Algorithm SHA256).Hash -ne $saveHash -or
        (Get-FileHash -LiteralPath $metadataPath -Algorithm SHA256).Hash -ne $metadataHash) {
        throw "Source changed during audit; no result will be saved: $sourceFull"
    }
}
$report = [ordered]@{
    status='READ_ONLY_OFFLINE_SAMPLES_NOT_CURRENT_RUNTIME_OR_RESTORATION_ADMISSION'
    catalogue_path=$catalogueFull;catalogue_sha256=(Get-FileHash -LiteralPath $catalogueFull -Algorithm SHA256).Hash
    parser_sha256=(Get-FileHash -LiteralPath (Join-Path $wkRoot 'WolvenKit.RED4.dll') -Algorithm SHA256).Hash
    fact_names=$names;samples=@($samples.ToArray())
    limitations=@(
        'Absent serialized facts are not asserted to be zero in the live game.'
        'All matching table values are retained; precedence is not guessed.'
        'A finished fact or metadata entry does not independently establish reward delivery.'
        'Shared playthrough/PONR identifiers support comparison but do not prove exact save ancestry.'
        'No journal-byte state interpretation, item/device/actor scan or live owner check is performed here.'
        'No mutation or restoration is permitted by this report; zero start/progress markers alone do not prove untouched.'
    )
    source_writes=0;game_writes=0
}
$encoded = $report | ConvertTo-Json -Depth 16
[IO.File]::WriteAllText($outputFull,$encoded,[Text.UTF8Encoding]::new($false))
"Saved read-only gig facts: $($samples.Count) samples, $($names.Count) requested names. Sources unchanged."
