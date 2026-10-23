param([string]$Revision='s221_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly
if($Revision -cnotmatch '^s221_\d{2}$'){throw 'Invalid revision'}
$out=Join-Path $PSScriptRoot ('build/'+$Revision)
if(Test-Path -LiteralPath $out){throw 'Immutable build exists'}
$priorRel='prealpha/sidejobs_s22b/build/s22_03'
$prior=Join-Path $workspace $priorRel
$oldManifest=Join-Path $prior 'build.json'
if((Get-FileHash -LiteralPath $oldManifest).Hash -cne '0BEC19BF535031E465DA85F4864A2D0E4CAE15AB462DA1DFBC9E0AE8C024A08C'){throw 'Prior build changed'}
$old=Get-Content -LiteralPath $oldManifest -Raw|ConvertFrom-Json
$dm=Get-Content -LiteralPath (Join-Path $workspace 'prealpha/sidejobs_s22/delamain_v2/build/delamain_07/build.json') -Raw|ConvertFrom-Json
$pins=[ordered]@{}
foreach($p in $old.source_pins.PSObject.Properties){
 if((Get-FileHash -LiteralPath (Join-Path $workspace $p.Name)).Hash -cne $p.Value){throw "Prior source drift: $($p.Name)"};$pins[$p.Name]=$p.Value
}
foreach($p in @('prealpha/sidejobs_s221/build.ps1',($priorRel+'/build.json'),'prealpha/sidejobs_s22/delamain_v2/build/delamain_07/build.json')){$pins[$p]=(Get-FileHash -LiteralPath (Join-Path $workspace $p)).Hash}
New-Item -ItemType Directory $out,(Join-Path $out 'source'),(Join-Path $out 'readback')|Out-Null
$targets=@('towercontinued\sidejobs_s22\delamain\support.questphase','towercontinued\sidejobs_s22\delamain\owner.questphase')
$resources=[ordered]@{};$changes=@()
foreach($p in $old.resources.PSObject.Properties){
 $src=Join-Path (Join-Path $prior 'source') $p.Name
 if((Get-FileHash -LiteralPath $src).Hash -cne $p.Value){throw 'Prior resource drift'}
 $pins[$priorRel+'/source/'+$p.Name.Replace('\','/')]=$p.Value
 $dst=Join-Path (Join-Path $out 'source') $p.Name
 New-Item -ItemType Directory (Split-Path $dst -Parent) -Force|Out-Null
 if($p.Name -cin $targets){
  $r=Read-Cr2wFile $src
  foreach($id in @(1002,1003)){
   $node=Get-QuestNode $r.RootChunk.Graph.Chunk $id
   $condition=$node.Condition.Chunk
   $idle=@($condition.Conditions|Where-Object {$_.Chunk -is [WolvenKit.RED4.Types.questLogicalCondition] -and $_.Chunk.Conditions.Count -eq 73})
   if($idle.Count -ne 1){throw 'Expected exactly one 57 flags + 16 history-pairs condition'}
   $list=$idle[0].Chunk.Conditions;$removed=@()
   for($i=$list.Count-1;$i -ge 0;$i--){
    $c=$list[$i].Chunk
    if($c -is [WolvenKit.RED4.Types.questFactsDBCondition] -and $c.Type.Chunk -is [WolvenKit.RED4.Types.questVarVsVarComparison_ConditionType]){
     $t=$c.Type.Chunk;$a=$t.FactName1.ToString();$b=$t.FactName2.ToString()
     if($t.ComparisonType.ToString() -cne 'Equal' -or @($dm.phone_balances|Where-Object {$_[0] -ceq $a -and $_[1] -ceq $b}).Count -ne 1){throw 'Unexpected comparison; refusing broader edit'}
     $removed+=,@($a,$b);$list.RemoveAt($i)
    }
   }
   if($removed.Count -ne 16 -or $list.Count -ne 57){throw 'Incorrect gate change'}
   $changes+=,@{resource=$p.Name;node=$id;removed_history_equalities=$removed;remaining_busy_flags=57}
  }
  Write-Cr2wFile $r $dst
 }else{Copy-Item -LiteralPath $src -Destination $dst}
 $resources[$p.Name]=(Get-FileHash -LiteralPath $dst).Hash
 Export-Cr2wJson (Read-Cr2wFile $dst) (Join-Path $out ('readback/'+$p.Name.Replace('\','_')+'.json'))
}
if($changes.Count -ne 4){throw 'Wrong change count'}
$name='000_TowerContinued_SideJobs_S22.archive';$archive=Join-Path $out $name
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new((Join-Path $out 'source')),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError' -or $packed.Files.Count -ne 8){throw 'Packed scope mismatch'}
foreach($entry in $packed.Files.Values){
 if(!$resources.Contains($entry.Name)){throw 'Unexpected packed resource'}
 $mem=[IO.MemoryStream]::new();try{$entry.Extract($mem);if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray())) -cne $resources[$entry.Name]){throw 'Packed bytes mismatch'}}finally{$mem.Dispose()}
}
$result=[ordered]@{status='BUILT_S221_PHONE_GATE_LIVE_PENDING';relative='archive/pc/mod/'+$name;old_sha256=$old.files[0].sha256;sha256=(Get-FileHash -LiteralPath $archive).Hash;prior_manifest=$priorRel+'/build.json';prior_sha256=(Get-FileHash -LiteralPath $oldManifest).Hash;resources=$resources;boots=$old.boots;injections=$old.injections;changes=$changes;source_pins=$pins;packed_readback=$true;archive_replacements=1;additions=0;scripts_changed=0;native_counter_writes=0;native_cleanup_unchanged=$true;owner_ids_unchanged=$true;scope='Remove only historical call-count equality from four S22 Delamain preflight conditions. Keep 57 busy flags, all progress/journal/common guards and stock cleanup. No new injection, owner restart or progress reset.'}
[IO.File]::WriteAllText((Join-Path $out 'build.json'),($result|ConvertTo-Json -Depth 40),[Text.UTF8Encoding]::new($false))
@{status=$result.status;build=$out;sha256=(Get-FileHash -LiteralPath (Join-Path $out 'build.json')).Hash}|ConvertTo-Json
