# Read only named facts and four source-selected journal roots in the existing save pair.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out=Join-Path $PSScriptRoot 'stage_facts_01.json'
if (Test-Path -LiteralPath $out) { throw 'Fresh evidence required' }
$query=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'fact_query.json') -Raw | ConvertFrom-Json
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$readerType=[WolvenKit.RED4.Save.IO.CyberpunkSaveReader]
$readerHash=(Get-FileHash -LiteralPath $readerType.Assembly.Location).Hash
if ($readerHash -cne 'EF17F40D73F207F0F71F1F41A70A4549A19792D438F680A9BFBB4800D2EE2987') { throw 'Reader drift' }
$hashMethod=@([WolvenKit.RED4.Save.Fact].GetMethods() | Where-Object { $_.Name -eq 'op_Implicit' -and $_.ReturnType -eq [uint32] })
if ($hashMethod.Count -ne 1) { throw 'Ambiguous fact hash method' }
$factKeys=@{}
foreach ($name in $query.facts) {
    $fact=[WolvenKit.RED4.Save.Fact]::op_Implicit([string]$name)
    $key=[uint32]$hashMethod[0].Invoke($null,[object[]]@($fact))
    if ($factKeys.ContainsKey($key)) { throw 'Fact hash collision' }
    $factKeys[$key]=[string]$name
}
$journalKeys=@{}
foreach ($row in $query.journals) {
    $key=[WolvenKit.Core.Murmur3.Murmur32]::Hash([string]$row.path,[uint32]0x5EEDBA5E,[Text.Encoding]::UTF8)
    if ($journalKeys.ContainsKey($key)) { throw 'Journal hash collision' }
    $journalKeys[$key]=$row
}
$pins=@{'ManualSave-31'='2E0F3C99AF3E98601CFC6363BBC068635D0C50ABB32F8E81B2A57B056B02F43D';'ManualSave-32'='B5698BC909DD2CDDF34BA39E0DDE26E4480DD1769F9B4EE626717D8DBD2A622F'}
$saves=@(foreach ($slot in @('ManualSave-31','ManualSave-32')) {
    $path=Join-Path 'C:/Users/Ayong/Saved Games/CD Projekt Red/Cyberpunk 2077' ($slot+'/sav.dat')
    for ($item=Get-Item -LiteralPath $path -Force; $null -ne $item;) {
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Linked save refused' }
        $item=if ($item -is [IO.FileInfo]) { $item.Directory } else { $item.Parent }
    }
    if ((Get-FileHash -LiteralPath $path).Hash -cne $pins[$slot]) { throw 'Save fixture drift' }
    $bytes=[IO.File]::ReadAllBytes($path)
    if ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)) -cne $pins[$slot]) { throw 'Save changed during copy' }
    $memory=[IO.MemoryStream]::new($bytes,$false)
    $reader=$readerType::new($memory)
    try {
        $save=$null
        if ($reader.ReadFile([ref]$save).ToString() -cne 'NoError' -or $save.FileHeader.SaveVersion -ne 277) { throw 'Unsupported save' }
        $quests=@($save.Nodes | Where-Object Name -CEQ 'questSystem')
        $journal=@($save.Nodes | Where-Object Name -CEQ 'JournalManager')
        if ($quests.Count -ne 1 -or $journal.Count -ne 1) { throw 'Ambiguous native roots' }
        $db=@($quests[0].Children | Where-Object Name -CEQ 'FactsDB')
        if ($db.Count -ne 1 -or $db[0].Children.Count -ne 10) { throw 'Unexpected fact tables' }
        $facts=[ordered]@{}
        foreach ($name in $query.facts) { $facts[[string]$name]=$null }
        foreach ($entry in $db[0].Children[0].Value.FactEntries) {
            $key=[uint32]$hashMethod[0].Invoke($null,[object[]]@($entry.FactName))
            if ($factKeys.ContainsKey($key)) {
                $name=$factKeys[$key]
                if ($null -ne $facts[$name]) { throw 'Duplicate fact key' }
                $facts[$name]=[uint32]$entry.Value
            }
        }
        $journals=@(foreach ($entry in $journal[0].Value.Entries) {
            $raw=[byte[]]$entry.UnkownBytes
            if ($raw.Length -ne 15) { throw 'Unexpected journal entry framing' }
            $key=[BitConverter]::ToUInt32($raw,0)
            if ($journalKeys.ContainsKey($key)) {
                @{id=$journalKeys[$key].id;path=$journalKeys[$key].path;state_u32=[BitConverter]::ToUInt32($raw,4);raw15=[Convert]::ToHexString($raw)}
            }
        })
        if ((Get-FileHash -LiteralPath $path).Hash -cne $pins[$slot]) { throw 'Save changed during read' }
        @{slot=$slot;save_sha256=$pins[$slot];facts=$facts;journals=$journals;unchanged=$true}
    } finally { $reader.Dispose();$memory.Dispose() }
})
@{status='READ_ONLY_SOURCE_SELECTED_FACTS';reader_sha256=$readerHash;query_sha256=(Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'fact_query.json')).Hash;saves=$saves;save_writes=0;game_calls=0;limits='Null means no serialized named fact. Absent journal rows are not an Inactive enum. Live state may have advanced after MS32.'} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $out -Encoding utf8NoBOM
Write-Output 'Paired-save source-selected projection complete; both files unchanged.'
