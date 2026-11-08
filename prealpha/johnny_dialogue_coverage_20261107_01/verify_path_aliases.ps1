Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$prepared=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'evidence_01/prepared.json') -Raw | ConvertFrom-Json -Depth 100
$missing=(Get-Content -LiteralPath (Join-Path $PSScriptRoot 'evidence_02/summary.json') -Raw | ConvertFrom-Json -Depth 30).missing_requests
$out=Join-Path $PSScriptRoot 'evidence_06'
if(Test-Path -LiteralPath $out){throw 'Use fresh alias evidence'}
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$hashService=[WolvenKit.Common.Services.HashService]::new();$hashService.Load()
$rows=[Collections.Generic.List[object]]::new()
foreach($request in $missing){
    $sanitized=[WolvenKit.RED4.Types.ResourcePath]::SanitizePath($request.depot)
    $key=[WolvenKit.RED4.Types.ResourcePath]::CalculateHash($request.depot,$true)
    $rows.Add(@{depot=$request.depot;raw_key=$request.key;sanitized=$sanitized;resource_key=$key.ToString();
        reasons=$request.reasons;providers=[Collections.Generic.List[object]]::new()})
}
foreach($info in $prepared.archives){
    $file=Get-Item -LiteralPath $info.path
    if($file.Length -ne $info.bytes -or $file.LastWriteTimeUtc.Ticks -ne ([DateTime]$info.mtime_utc).ToUniversalTime().Ticks){throw 'Archive baseline changed'}
    $archive=$null
    $code=([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($info.path,$hashService,[ref]$archive)
    if($code.ToString() -cne 'NoError'){throw 'Archive unreadable'}
    foreach($row in $rows){
        if(!$archive.Files.ContainsKey([uint64]$row.resource_key)){continue}
        $entry=$archive.Files[[uint64]$row.resource_key]
        $memory=[IO.MemoryStream]::new()
        try{$entry.Extract($memory);$bytes=$memory.ToArray()}finally{$memory.Dispose()}
        $row.providers.Add(@{archive=$info.path;depot=$entry.Name;key=$row.resource_key;
            sha256=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))})
    }
}
New-Item -ItemType Directory -Path $out | Out-Null
$serialized=@(foreach($row in $rows){
    @{depot=$row.depot;raw_key=$row.raw_key;sanitized=$row.sanitized;resource_key=$row.resource_key;
      reasons=$row.reasons;providers=$row.providers.ToArray()}
})
@{rows=$serialized;tool_api='WolvenKit 9.1 ResourcePath.SanitizePath and CalculateHash(path,true)';
game_writes=0;save_writes=0} | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $out 'path_aliases.json') -Encoding utf8NoBOM
Write-Output "Checked $($rows.Count) absent raw paths; $(($rows | Where-Object {$_.providers.Count -gt 0}).Count) resolved through ResourcePath normalization"
