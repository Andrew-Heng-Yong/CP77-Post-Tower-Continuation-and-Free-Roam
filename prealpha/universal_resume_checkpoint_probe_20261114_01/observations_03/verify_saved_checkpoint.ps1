# Read a post-Tower manual save and compare its serialized checkpoint words
# with the exact export from the 22:43:25 Reed capture. Read-only inputs.
param([Parameter(Mandatory)][ValidatePattern('^ManualSave-[0-9]+$')][string]$Slot)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'

$workspace=(Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../..')).Path
$manifest=Get-Content -LiteralPath (Join-Path $PSScriptRoot '../deployment_01/installed_manifest_01.json') -Raw | ConvertFrom-Json
$recovery=Join-Path $workspace 'recovery/ms26_v014_reed_checkpoint_20261114_01'
$receipt=Get-Content -LiteralPath (Join-Path $recovery 'receipt.json') -Raw | ConvertFrom-Json
$export=Join-Path $recovery ([IO.Path]::GetFileName($receipt.backup))
$save=Join-Path $manifest.save_root "$Slot/sav.dat"
$metadata=Join-Path $manifest.save_root "$Slot/metadata.9.json"
foreach($path in $save,$metadata,$export){
    for($item=Get-Item -LiteralPath $path;$null -ne $item;){
        if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){throw "Linked input refused: $($item.FullName)"}
        if($item -is [IO.FileInfo]){$item=$item.Directory}else{$item=$item.Parent}
    }
}
$before=(Get-FileHash -LiteralPath $save).Hash
$metaBefore=(Get-FileHash -LiteralPath $metadata).Hash
$meta=(Get-Content -LiteralPath $metadata -Raw | ConvertFrom-Json).Data.metadata
if($meta.name -cne $Slot -or $meta.playthroughID -cne '6a8b8f76f827ff5f' -or $meta.finishedQuests -cnotmatch '\bq307\b' -or
   $meta.isEndGameSave -or $meta.isForced -or $meta.isCheckpoint){throw 'Expected a normal post-Tower manual save in the MS26 playthrough'}
$expected=[IO.File]::ReadAllBytes($export)
if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($expected)) -cne $receipt.sha256){throw 'Pinned cutoff export mismatch'}
$length=32+$expected.Length
$packed=[byte[]]::new(8*(1+[int][Math]::Ceiling($length/8.0)))
[Array]::Copy([BitConverter]::GetBytes([uint64]$length),0,$packed,0,8)
[Array]::Copy([Text.Encoding]::ASCII.GetBytes($receipt.id),0,$packed,8,32)
[Array]::Copy($expected,0,$packed,40,$expected.Length)

. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$memory=[IO.MemoryStream]::new()
$stream=[IO.File]::Open($save,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
try{$stream.CopyTo($memory)}finally{$stream.Dispose()}
if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory.ToArray())) -cne $before){throw 'Save body changed before parse'}
$memory.Position=0
$body=$null
try{$result=([WolvenKit.RED4.Save.IO.CyberpunkSaveReader]::new($memory)).ReadFile([ref]$body).ToString()}
finally{$memory.Dispose()}
if($result -cne 'NoError'){throw "Save parse failed: $result"}
$containers=@($body.Nodes | Where-Object Name -CEQ 'ScriptableSystemsContainer')
if($containers.Count -ne 1){throw 'Expected one scriptable systems container'}
$archive=@($containers[0].Value.Content.Chunks | Where-Object {
    $_ -is [WolvenKit.RED4.Types.IDynamicClass] -and $_.ClassName.ToString() -ceq 'PTFR.HistorySnapshotHS1.CaptureArchiveHS3'
})
if($archive.Count -ne 1){throw 'Expected one saved CaptureArchiveHS3 system'}
$system=$archive[0]
$id=$system.GetProperty('executionCheckpointId')
$words=$system.GetProperty('executionCheckpointState')
$ticket=[int]$system.GetProperty('executionCheckpointTicket')
$route=[int]$system.GetProperty('executionCheckpointRoute')
if($id.GetRedHash() -ne [WolvenKit.RED4.Types.CName]::CalculateHash($receipt.id) -or
   $ticket -ne $receipt.ticket -or $route -ne $receipt.route){throw 'Saved checkpoint identity, ticket or route differs'}
if($words.Count -ne ($packed.Length/8)){throw "Saved checkpoint word count differs: $($words.Count)"}
for($i=0;$i -lt $words.Count;$i++){
    if([uint64]$words[$i] -ne [BitConverter]::ToUInt64($packed,8*$i)){throw "Saved checkpoint bytes differ at word $i"}
}
if((Get-FileHash -LiteralPath $save).Hash -cne $before -or (Get-FileHash -LiteralPath $metadata).Hash -cne $metaBefore){
    throw 'Save input changed during verification'
}
[ordered]@{
    status='SAVED_CHECKPOINT_BYTES_MATCH'; slot=$Slot; timestamp=$meta.timestampString; playthrough_id=$meta.playthroughID
    save_sha256=$before; metadata_sha256=$metaBefore; checkpoint_id=$receipt.id; ticket=$ticket; route=$route
    payload_bytes=$expected.Length; payload_sha256=$receipt.sha256; packed_words=$words.Count
    parser_sha256=(Get-FileHash -LiteralPath ([WolvenKit.RED4.Save.IO.CyberpunkSaveReader].Assembly.Location)).Hash
} | ConvertTo-Json -Depth 4
