# Read-only metro projection of the paired baseline and post-Tower saves.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$root = 'C:/Users/Ayong/Saved Games/CD Projekt Red/Cyberpunk 2077'
$out = Join-Path $PSScriptRoot 'work/facts.json'
if (Test-Path -LiteralPath $out) { throw 'Fresh evidence output required' }
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$readerType = [WolvenKit.RED4.Save.IO.CyberpunkSaveReader]
$parserHash = (Get-FileHash -LiteralPath $readerType.Assembly.Location -Algorithm SHA256).Hash
if ($parserHash -cne 'EF17F40D73F207F0F71F1F41A70A4549A19792D438F680A9BFBB4800D2EE2987') { throw 'Save reader drift' }
$contractFile = Join-Path $PSScriptRoot 'fields.json'
$contract = Get-Content -LiteralPath $contractFile -Raw | ConvertFrom-Json
$pathKeys = @{}
foreach ($item in $contract.journals) {
    $key = [WolvenKit.Core.Murmur3.Murmur32]::Hash([string]$item, [uint32]0x5EEDBA5E, [Text.Encoding]::UTF8)
    if ($pathKeys.ContainsKey($key)) { throw 'Journal path hash collision' }
    $pathKeys[$key] = [string]$item
}
$names = @($contract.facts)
$toHash = @([WolvenKit.RED4.Save.Fact].GetMethods() | Where-Object { $_.Name -eq 'op_Implicit' -and $_.ReturnType -eq [uint32] })
if ($toHash.Count -ne 1) { throw 'Ambiguous fact hash method' }
$factKeys = @{}
foreach ($name in $names) {
    $fact = [WolvenKit.RED4.Save.Fact]::op_Implicit($name)
    $key = [uint32]$toHash[0].Invoke($null, [object[]]@($fact))
    if ($factKeys.ContainsKey($key)) { throw 'Fact hash collision' }
    $factKeys[$key] = $name
}
function Plain([string]$path) {
    for ($item = Get-Item -LiteralPath $path -Force; $null -ne $item;) {
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Linked input: $path" }
        $item = if ($item -is [IO.FileInfo]) { $item.Directory } else { $item.Parent }
    }
}
$rows = @(foreach ($slot in @('ManualSave-31','ManualSave-32','AutoSave-10','AutoSave-16')) {
    $folder = Join-Path $root $slot
    $savePath = Join-Path $folder 'sav.dat'
    $metaPath = Join-Path $folder 'metadata.9.json'
    Plain $savePath; Plain $metaPath
    $saveHash = (Get-FileHash -LiteralPath $savePath -Algorithm SHA256).Hash
    $metaHash = (Get-FileHash -LiteralPath $metaPath -Algorithm SHA256).Hash
    $bytes = [IO.File]::ReadAllBytes($savePath)
    if ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)) -cne $saveHash) { throw 'Input changed while copying' }
    $memory = [IO.MemoryStream]::new($bytes, $false)
    $reader = $readerType::new($memory)
    try {
        $save = $null
        if ($reader.ReadFile([ref]$save).ToString() -cne 'NoError' -or $save.FileHeader.SaveVersion -ne 277) { throw "Save parse/version failed: $slot" }
        $rootNodes = @($save.Nodes | Where-Object Name -CEQ 'questSystem')
        $journalNodes = @($save.Nodes | Where-Object Name -CEQ 'JournalManager')
        if ($rootNodes.Count -ne 1 -or $journalNodes.Count -ne 1) { throw 'Ambiguous native roots' }
        $db = @($rootNodes[0].Children | Where-Object Name -CEQ 'FactsDB')
        if ($db.Count -ne 1 -or $db[0].Children.Count -ne 10) { throw 'Unexpected fact store' }
        $facts = [ordered]@{}
        foreach ($name in $names) { $facts[$name] = $null }
        foreach ($entry in $db[0].Children[0].Value.FactEntries) {
            $key = [uint32]$toHash[0].Invoke($null, [object[]]@($entry.FactName))
            if ($factKeys.ContainsKey($key)) {
                $name = $factKeys[$key]
                if ($null -ne $facts[$name]) { throw "Duplicate fact: $name" }
                $facts[$name] = [uint32]$entry.Value
            }
        }
        $journals = @(foreach ($entry in $journalNodes[0].Value.Entries) {
            $raw = [byte[]]$entry.UnkownBytes
            if ($raw.Length -ne 15) { throw 'Unexpected journal framing' }
            $key = [BitConverter]::ToUInt32($raw, 0)
            if ($pathKeys.ContainsKey($key)) { @{ path=$pathKeys[$key]; state_u32=[BitConverter]::ToUInt32($raw,4); raw15=[Convert]::ToHexString($raw) } }
        })
        $meta = (Get-Content -LiteralPath $metaPath -Raw | ConvertFrom-Json).Data.metadata
        if ((Get-FileHash -LiteralPath $savePath -Algorithm SHA256).Hash -cne $saveHash -or (Get-FileHash -LiteralPath $metaPath -Algorithm SHA256).Hash -cne $metaHash) { throw 'Input changed during read' }
        @{ slot=$slot; save_sha256=$saveHash; metadata_sha256=$metaHash; timestamp=$meta.timestampString; playthrough_id=$meta.playthroughID; point_of_no_return_id=$meta.pointOfNoReturnId; end_game=$meta.isEndGameSave; location=$meta.locationName; tracked=$meta.trackedQuestEntry; facts=$facts; journals=$journals }
    } finally { $reader.Dispose(); $memory.Dispose() }
})
if ($rows[0].playthrough_id -cne $rows[1].playthrough_id -or $rows[0].point_of_no_return_id -cne $rows[1].point_of_no_return_id) { throw 'Save lineage mismatch' }
$result = @{ status='READ_ONLY_NCART_PROJECTION'; parser_sha256=$parserHash; source_catalogue_sha256=(Get-FileHash -LiteralPath $contractFile -Algorithm SHA256).Hash; saves=$rows; limits=@('Null fact or absent journal row means not serialized, not a proven runtime zero/Inactive.','This projection does not identify executing graph owner, item state, live map rendering or post-save interaction.'); save_writes=0; game_calls=0 }
[IO.File]::WriteAllText($out, ($result | ConvertTo-Json -Depth 10), [Text.UTF8Encoding]::new($false))
Write-Output "NCART save projection complete: $out"
