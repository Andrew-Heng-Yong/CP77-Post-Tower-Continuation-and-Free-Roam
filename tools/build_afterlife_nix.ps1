param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$scope=Join-Path $WorkspaceRoot 'research\afterlife_world';$out=Join-Path $WorkspaceRoot 'build\AfterlifeR1\nix';$source=Join-Path $out 'source'
New-Item -ItemType Directory -Force $source|Out-Null
$receipt=Get-Content (Join-Path $WorkspaceRoot 'research\b0_story_eight\validation\install_receipt.json') -Raw|ConvertFrom-Json
$oldArchive=@($receipt.files|Where-Object path -Like '*.archive')[0]
if((Get-FileHash $oldArchive.source).Hash -ne $oldArchive.sha256){throw 'S4 baseline archive changed'}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$arc=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($oldArchive.source,$hs,[ref]$arc).ToString() -ne 'NoError' -or $arc.Files.Count -ne 16){throw 'S4 archive baseline invalid'}
$rows=[Collections.Generic.List[object]]::new();$nixDepot='towercontinued\b0_story_eight\nix.questphase'
foreach($e in $arc.Files.Values){
 $dest=Join-Path $source $e.Name;New-Item -ItemType Directory -Force (Split-Path $dest)|Out-Null
 $ms=[IO.MemoryStream]::new();try{$e.Extract($ms);[IO.File]::WriteAllBytes($dest,$ms.ToArray())}finally{$ms.Dispose()}
 $rows.Add([ordered]@{depot=$e.Name;before=(Get-FileHash $dest).Hash;after='';changed=$false})
}
$file=Read-Cr2wFile (Join-Path $source $nixDepot);$guard=(Get-QuestNode $file.RootChunk.Graph.Chunk 2).Condition.Chunk
if($guard.Operation.ToString() -ne 'AND'){throw 'Nix wrapper changed'}
$matches=@()
for($i=0;$i -lt $guard.Conditions.Count;$i++){$c=$guard.Conditions[$i].Chunk;if($c -is [WolvenKit.RED4.Types.questFactsDBCondition] -and $c.Type.Chunk.FactName.ToString() -eq 'mq016_active'){$matches+= $i;if($c.Type.Chunk.ComparisonType.ToString() -ne 'Equal' -or $c.Type.Chunk.Value.ToString() -ne '0'){throw 'Unexpected mq016 guard'}}}
if($matches.Count -ne 1){throw 'Expected exactly one overly broad Nix guard'}
$guard.Conditions.RemoveAt($matches[0])
Write-Cr2wFile $file (Join-Path $source $nixDepot)
Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $nixDepot)) (Join-Path $scope 'nix_repaired_phase.json')
foreach($r in $rows){$r.after=(Get-FileHash (Join-Path $source $r.depot)).Hash;$r.changed=$r.after -ne $r.before}
if(@($rows|Where-Object changed).Count -ne 1 -or @($rows|Where-Object changed)[0].depot -ne $nixDepot){throw 'Unexpected S4 payload delta'}
$archive=Join-Path $out 'TowerContinued_B0_StoryEight.archive';$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError' -or $packed.Files.Count -ne 16){throw 'Packed archive invalid'}
foreach($e in $packed.Files.Values){$ms=[IO.MemoryStream]::new();try{$e.Extract($ms);$r=@($rows|Where-Object depot -eq $e.Name);if($r.Count -ne 1 -or [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($ms.ToArray())) -ne $r[0].after){throw 'Packed payload mismatch'}}finally{$ms.Dispose()}}
$report=[ordered]@{status='BUILT_NIX_GUARD_REPAIR_LIVE_PENDING';archive=$archive;sha256=(Get-FileHash $archive).Hash;previous_sha256=$oldArchive.sha256;source_root=$source;resource_deltas=@($rows);removed_condition='mq016_active == 0';preserved='All genuine Tower/main-root-killed, availability, explicit QuestOwns, suspension, scene, phone and service gates. No fact reset.';script=(Join-Path $WorkspaceRoot 'redscript\PTFR_B0_StoryEight\StoryEightDriver.reds');script_sha256=(Get-FileHash (Join-Path $WorkspaceRoot 'redscript\PTFR_B0_StoryEight\StoryEightDriver.reds')).Hash;previous_script_sha256=@($receipt.files|Where-Object path -Like '*.reds')[0].sha256}
[IO.File]::WriteAllText((Join-Path $scope 'nix_manifest.json'),($report|ConvertTo-Json -Depth 7),[Text.UTF8Encoding]::new($false))
'Built Nix: 1 wrapper condition removed; 15 other payloads byte-identical.'
