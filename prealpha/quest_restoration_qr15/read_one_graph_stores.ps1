param([Parameter(Mandatory=$true)][ValidateSet('ManualSave-23','AutoSave-8')][string]$Slot,
      [Parameter(Mandatory=$true)][ValidatePattern('^stores_[a-z0-9_]+$')][string]$OutputName)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out=Join-Path $PSScriptRoot $OutputName
if(Test-Path -LiteralPath $out){throw 'Fresh output directory required'}
$src=Join-Path 'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077' ($Slot+'/sav.dat')
$meta=Join-Path (Split-Path $src -Parent) 'metadata.9.json'
foreach($p in @($src,$meta)){
 $item=Get-Item -LiteralPath $p
 while($null -ne $item){
  if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked save input refused'}
  $item=if($item -is [IO.DirectoryInfo]){$item.Parent}else{$item.Directory}
 }
}
$before=(Get-FileHash -LiteralPath $src).Hash
$metaBefore=(Get-FileHash -LiteralPath $meta).Hash
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$memory=[IO.MemoryStream]::new()
$file=[IO.File]::Open($src,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
try{$file.CopyTo($memory)}finally{$file.Dispose()}
if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory.ToArray())) -cne $before){throw 'Unstable snapshot'}
$memory.Position=0
$save=$null;$reader=[WolvenKit.RED4.Save.IO.CyberpunkSaveReader]::new($memory)
try{$parsed=$reader.ReadFile([ref]$save).ToString()}finally{$memory.Dispose()}
if($parsed -cne 'NoError'){throw "Read failed: $parsed"}
$quest=@($save.Nodes|Where-Object Name -ceq 'questSystem')
if($quest.Count -ne 1){throw 'Expected exactly one native questSystem root'}
$db=@($quest[0].Children|Where-Object Name -ceq 'FactsDB')
if($db.Count -ne 1){throw 'Expected exactly one native FactsDB child'}
$tables=@($db[0].Children)
if($tables.Count -ne 10){throw 'Unexpected native fact-store shape'}
$hashMethod=@([WolvenKit.RED4.Save.Fact].GetMethods()|Where-Object {$_.Name -eq 'op_Implicit' -and $_.ReturnType -eq [uint32]})
if($hashMethod.Count -ne 1){throw 'Ambiguous fact conversion'}
$rows=@();$store=0
foreach($t in $tables){
 $store++
 if($t.Value -isnot [WolvenKit.RED4.Save.FactsTable]){throw 'Unexpected fact-table parser type'}
 $facts=@()
 foreach($e in $t.Value.FactEntries){
  $key=[uint32]$hashMethod[0].Invoke($null,[object[]]@($e.FactName))
  $facts+=@{key_u32=[string]$key;value_u32=[uint32]$e.Value}
 }
 $rows+=@{physical_child_ordinal=$store;name=$t.Name;entries=$facts;entry_count=$facts.Count}
}
if((Get-FileHash -LiteralPath $src).Hash -cne $before -or (Get-FileHash -LiteralPath $meta).Hash -cne $metaBefore){throw 'Source changed during read'}
New-Item -ItemType Directory -Path $out|Out-Null
[IO.File]::WriteAllText((Join-Path $out 'facts.json'),(@{status='READ_ONLY_PHYSICAL_NATIVE_FACT_TABLES';slot=$Slot;source=$src;sha256=$before;metadata_path=$meta;metadata_sha256=$metaBefore;parser_assembly=[WolvenKit.RED4.Save.FactsTable].Assembly.Location;parser_sha256=(Get-FileHash -LiteralPath ([WolvenKit.RED4.Save.FactsTable].Assembly.Location)).Hash;tables=$rows;source_unchanged=$true;source_writes=0;game_calls=0;limits='Physical serialization order retained. Store/state semantics require separate source proof. Most-recent filename/metadata is not exact loaded-body binding. Nonzero graph values are not automatically visited/running/retired evidence.'}|ConvertTo-Json -Depth 12),[Text.UTF8Encoding]::new($false))
@{slot=$Slot;tables=$rows.Count;counts=@($rows|ForEach-Object {$_.entry_count});source_unchanged=$true;output=$out}|ConvertTo-Json -Depth 3
