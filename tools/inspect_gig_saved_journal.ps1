param(
    [string[]]$SaveNames = @('AutoSave-12', 'PointOfNoReturnSave-1'),
    [string]$OutputPath = 'research/gig_restoration/saved_journal_evidence.json',
    [string[]]$CandidateIds = @()
)
$ErrorActionPreference = 'Stop'
$wkRoot = 'C:\Users\Ayong\Documents\WolvenKit-8.20.0'
$saveRoot = 'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077'
$evidenceRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\research\gig_restoration')) + [IO.Path]::DirectorySeparatorChar
$outputFullPath = [IO.Path]::GetFullPath($OutputPath)
if (-not $outputFullPath.StartsWith($evidenceRoot, [StringComparison]::OrdinalIgnoreCase) -or [IO.Path]::GetExtension($outputFullPath) -ne '.json') {
    throw 'Output must be a JSON research artifact beneath research/gig_restoration.'
}
if (Test-Path -LiteralPath $outputFullPath) { throw 'Refusing to overwrite existing journal evidence.' }
foreach ($assembly in @('WolvenKit.Core.dll', 'WolvenKit.Common.dll', 'WolvenKit.RED4.dll')) {
    [void][Reflection.Assembly]::LoadFrom((Join-Path $wkRoot $assembly))
}
$journalFile = 'research/gig_restoration/journal_sources/json/base/journal/cooked_journal.journal.json'
$journal = Get-Content -LiteralPath $journalFile -Raw | ConvertFrom-Json -Depth 100
$paths = [Collections.Generic.List[object]]::new()
function Visit-Journal($wrapper, [string]$parent) {
    $entry = if ($wrapper.Data) { $wrapper.Data } else { $wrapper }
    $path = if ($parent -and $entry.id) { $parent + '/' + $entry.id } elseif ($entry.id) { $entry.id } else { $parent }
    if ($path) {
        $hash = [WolvenKit.Core.Murmur3.Murmur32]::Hash($path, [uint32]0x5EEDBA5E, [Text.Encoding]::UTF8)
        $paths.Add([pscustomobject]@{ Path=$path; Type=$entry.'$type'; Hash=$hash })
    }
    foreach ($child in $entry.entries) { Visit-Journal $child $path }
}
Visit-Journal $journal.Data.RootChunk.entry ''
$selected = @($paths | Where-Object { $_.Path -match '/sts_wat_nid_02(/|$)' -or ($_.Type -eq 'gameJournalQuest' -and $_.Path -match '/sts_(wat_lch_05|pac_cvi_02)$') })
if ($CandidateIds.Count -gt 0) {
    foreach ($candidateId in $CandidateIds) {
        if ($candidateId -notmatch '^sts_[a-z]{3}_[a-z]{3}_\d+$' -or
            -not @($paths | Where-Object { $_.Type -eq 'gameJournalQuest' -and $_.Path.EndsWith('/'+$candidateId) }).Count) {
            throw "Not a known bounded base-game gig ID: $candidateId"
        }
    }
    $candidatePattern = '/(' + (($CandidateIds | ForEach-Object { [regex]::Escape($_) }) -join '|') + ')(/|$)'
    $selected = @($paths | Where-Object { $_.Path -match $candidatePattern })
}
$hashCollisions = @($paths | Group-Object Hash | Where-Object Count -gt 1 | ForEach-Object {
    [pscustomobject]@{ Hash=$_.Name; Paths=@($_.Group.Path) }
})
$selectedHashCollisions = @($hashCollisions | Where-Object { [uint32]$_.Hash -in $selected.Hash })
$rows = [Collections.Generic.List[object]]::new()
foreach ($saveName in $SaveNames) {
    if ($saveName -notin @('AutoSave-12', 'PointOfNoReturnSave-1', 'ManualSave-6')) { throw 'Only reviewed bounded save names are permitted.' }
    $saveFile = Join-Path (Join-Path $saveRoot $saveName) 'sav.dat'
    $before = (Get-FileHash -LiteralPath $saveFile -Algorithm SHA256).Hash
    $stream = [IO.File]::Open($saveFile, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::ReadWrite)
    try {
        $reader = [WolvenKit.RED4.Save.IO.CyberpunkSaveReader]::new($stream)
        $save = $null
        $result = $reader.ReadFile([ref]$save)
        if ($result.ToString() -ne 'NoError') { throw "Save read failed: $result" }
        $journalNodes = @($save.Nodes | Where-Object Name -eq 'JournalManager')
        if ($journalNodes.Count -ne 1) { throw 'Expected exactly one JournalManager node.' }
        $data = $journalNodes[0].Value
        $entries = @($data.Entries | ForEach-Object {
            $raw = [byte[]]$_.UnkownBytes
            if ($raw.Length -ne 15) { throw 'Unexpected opaque entry length.' }
            [pscustomobject]@{ Raw15=[Convert]::ToHexString($raw); UInt32At0=[BitConverter]::ToUInt32($raw,0); UInt32At4=[BitConverter]::ToUInt32($raw,4) }
        })
        $matches = @($selected | ForEach-Object {
            $currentPath = $_
            [pscustomobject]@{
                Path=$currentPath.Path; Type=$currentPath.Type; CalculatedJournalHash=$currentPath.Hash
                RawMatches=@($entries | Where-Object UInt32At0 -eq $currentPath.Hash)
                StateInterpretation='UNVERIFIED: no state label is assigned to raw offset 4.'
            }
        })
        $rows.Add([pscustomobject]@{
            SaveName=$saveName; BeforeHash=$before; Result=$result.ToString()
            JournalNodeSize=$journalNodes[0].Size; OpaqueEntryCount=$data.Entries.Count
            TrackedHashCandidate=$data.Unk1_TrackedQuestPath
            Matches=$matches
            UInt32At4Distribution=@($entries | Group-Object UInt32At4 | Sort-Object Count -Descending | Select-Object Name,Count)
        })
    } finally {
        $stream.Dispose()
        $after = (Get-FileHash -LiteralPath $saveFile -Algorithm SHA256).Hash
        if ($before -ne $after) { throw "Save changed during read: $saveName" }
    }
    $rows[$rows.Count - 1] | Add-Member -NotePropertyName AfterHash -NotePropertyValue $after
}
$parser = [WolvenKit.RED4.Save.JournalManagerParser].GetMethod('Read')
$module = $parser.Module
$knownCalls = @(
    [pscustomobject]@{ Token='0x0A00006B'; Resolved=$module.ResolveMethod(0x0A00006B).ToString() },
    [pscustomobject]@{ Token='0x0601C829'; Resolved=$module.ResolveMethod(0x0601C829).ToString() }
)
$output = [ordered]@{
    Scope='Read-only bounded saved-journal byte research; not a runtime-state classifier.'
    SaveWrites=0; GameWrites=0
    AssemblyName=[WolvenKit.RED4.Save.JournalManagerParser].Assembly.FullName
    AssemblyHash=(Get-FileHash -LiteralPath (Join-Path $wkRoot 'WolvenKit.RED4.dll') -Algorithm SHA256).Hash
    JournalSourceHash=(Get-FileHash -LiteralPath $journalFile -Algorithm SHA256).Hash
    ParserReadIL=[Convert]::ToHexString($parser.GetMethodBody().GetILAsByteArray())
    ParserEntryConstruction='IL offset 0x1E ldc.i4.s 15, followed by BinaryReader.ReadBytes and Entry1.set_UnkownBytes.'
    ParserResolvedCalls=$knownCalls
    NativeEnumValues=@([WolvenKit.RED4.Types.Enums+gameJournalEntryState].GetEnumNames() | ForEach-Object {
        [pscustomobject]@{ Name=$_; Value=[int]([WolvenKit.RED4.Types.Enums+gameJournalEntryState]$_) }
    })
    PathHash='Murmur3 x86 32-bit, UTF-8 full slash-separated journal path, seed 0x5EEDBA5E; primary ArchiveXL/RED4ext source.'
    JournalPathsExamined=$paths.Count
    SelectedPathHashCollisions=$selectedHashCollisions
    SelectedPaths=$selected
    Saves=@($rows)
    Limits=@(
        'WolvenKit names the 15 bytes UnkownBytes; matching at offset 0 plus plausible integer values at offset 4 does not establish the saved state layout.',
        'No runtime GetEntryByString/GetEntryHash/GetEntryState comparison has been performed.',
        'The cooked journal is not a complete runtime merged-journal census; no selected collision only applies to this source tree.',
        'No prior-stage provenance is recovered by this raw comparison, and shared metadata identifiers do not prove exact ancestry.'
    )
    ReadOnlyNativeVerification=@(
        'GetEntryByString(full source path, exact source class) resolves the selected entry; verify non-null.',
        'GetEntryHash(resolved entry) supplies the native hash. It is Int32; compare its 32-bit bit pattern to the unsigned calculated hash.',
        'GetEntryState(resolved entry) supplies the actual state; compare only after identifying the exact loaded save.',
        'Use only getters; do not call ChangeEntryState, TrackEntry, SetEntryVisited, SetFact or quest activation methods.'
    )
    PrimarySources=@(
        'https://raw.githubusercontent.com/WolvenKit/WolvenKit/main/WolvenKit.RED4/Save/Parser/JournalManagerParser.cs',
        'https://raw.githubusercontent.com/psiberx/cp2077-archive-xl/main/src/App/Extensions/Journal/Extension.cpp',
        'https://raw.githubusercontent.com/WopsS/RED4ext.SDK/master/include/RED4ext/Hashing/Murmur3.hpp'
    )
}
$output | ConvertTo-Json -Depth 25 | Set-Content -LiteralPath $OutputPath -Encoding utf8NoBOM
@($rows | ForEach-Object { [pscustomobject]@{ Save=$_.SaveName; Before=$_.BeforeHash; After=$_.AfterHash; Entries=$_.OpaqueEntryCount; MatchedPaths=@($_.Matches | Where-Object { $_.RawMatches.Count -gt 0 }).Count } }) | ConvertTo-Json
