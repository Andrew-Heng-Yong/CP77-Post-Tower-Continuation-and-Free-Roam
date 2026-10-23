param([string]$Revision='snapshot_01')
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
if($Revision -cnotmatch '^snapshot_\d{2}$'){throw 'Bad revision'}
$out=Join-Path $ws ('research/sidejobs_s23/aaron_live_20261016/'+$Revision)
if(Test-Path -LiteralPath $out){throw 'Immutable evidence exists'}
New-Item -ItemType Directory $out,(Join-Path $out 'ManualSave-23'),(Join-Path $out 'logs')|Out-Null
$saveRoot='C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077\ManualSave-23'
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
function Hash($p){(Get-FileHash -LiteralPath $p).Hash}
$copies=@()
$sources=@()
foreach($name in @('sav.dat','metadata.9.json','screenshot.png')){$sources+=,@{source=(Join-Path $saveRoot $name);target=(Join-Path (Join-Path $out 'ManualSave-23') $name)}}
foreach($rel in @('r6/logs/redscript_rCURRENT.log','red4ext/plugins/ArchiveXL/ArchiveXL.log','red4ext/plugins/ArchiveXL/ArchiveXL-2026-10-16-09-24-44.log','red4ext/logs/red4ext-2026-10-16-09-24-42.log','bin/x64/plugins/cyber_engine_tweaks/cyber_engine_tweaks.log','bin/x64/plugins/cyber_engine_tweaks/gamelog.log','bin/x64/plugins/cyber_engine_tweaks/scripting.log')){$sources+=,@{source=(Join-Path $game $rel);target=(Join-Path (Join-Path $out 'logs') ([IO.Path]::GetFileName($rel)))}}
foreach($row in $sources){$h=Hash $row.source;Copy-Item -LiteralPath $row.source -Destination $row.target;if((Hash $row.source) -cne $h -or (Hash $row.target) -cne $h){throw 'Source changed during snapshot'};$copies+=,@{source=$row.source;target=$row.target;sha256=$h}}
$wk='C:\Users\Ayong\Documents\WolvenKit-8.20.0'
foreach($a in @('WolvenKit.Core.dll','WolvenKit.Common.dll','WolvenKit.RED4.dll')){[void][Reflection.Assembly]::LoadFrom((Join-Path $wk $a))}
$contract=Get-Content (Join-Path $ws 'prealpha/sidejobs_s23/ep1/contract.json') -Raw|ConvertFrom-Json
$aaron=@($contract.owners|Where-Object key -eq 'MQ306')[0]
$names=@($aaron.facts_equal.PSObject.Properties.Name)+@('PTFRS23_MQ007_ModeTalkConfirmed','mq007_done','mq007_skippy_owner_known','mq007_skippy_enemies_lethal','mq007_skippy_enemies_non_lethal','mq007_skippy_enemies_total')
foreach($tag in @('PTFRS23_MQ306','PTFRS23_MQ007','PTFRS23_MQ007_RESUME')){foreach($suffix in @('Ready','Permit','Issued','Entered','Finished','Fault','JournalAck')){$names+=($tag+'_'+$suffix)}}
$toHash=[WolvenKit.RED4.Save.Fact].GetMethods()|Where-Object {$_.Name -eq 'op_Implicit' -and $_.ReturnType -eq [uint32]}
$wanted=@{};$values=[ordered]@{}
foreach($name in ($names|Sort-Object -Unique)){$fact=[WolvenKit.RED4.Save.Fact]::op_Implicit($name);$key=[uint32]$toHash.Invoke($null,[object[]]@($fact));if($wanted.ContainsKey($key)){throw 'Fact hash collision'};$wanted[$key]=$name;$values[$name]=@()}
$paths=@($aaron.journals.path)+@('ep1/contacts/aaron','ep1/contacts/aaron/mq306','ep1/contacts/aaron/mq306/02a_ch_dive_reply/ch_01','ep1/contacts/aaron/mq306/02a_ch_dive_reply/ch_02')
$savePath=Join-Path $out 'ManualSave-23/sav.dat';$before=Hash $savePath
$stream=[IO.File]::Open($savePath,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
try{
 $reader=[WolvenKit.RED4.Save.IO.CyberpunkSaveReader]::new($stream);$save=$null
 if($reader.ReadFile([ref]$save).ToString() -ne 'NoError'){throw 'Save parse failed'}
 function Walk($nodes){foreach($node in $nodes){
  if($node.Value -is [WolvenKit.RED4.Save.FactsTable]){foreach($entry in $node.Value.FactEntries){$key=[uint32]$script:toHash.Invoke($null,[object[]]@($entry.FactName));if($script:wanted.ContainsKey($key)){$script:values[$script:wanted[$key]]+=([uint32]$entry.Value)}}}
  if($node.Children.Count){Walk $node.Children}
 }}
 Walk $save.Nodes
 $jn=@($save.Nodes|Where-Object Name -eq 'JournalManager');if($jn.Count -ne 1){throw 'Journal node count'}
 $rawRows=@($jn[0].Value.Entries|ForEach-Object {$b=[byte[]]$_.UnkownBytes;if($b.Length -ne 15){throw 'Opaque layout differs'};@{hash=[BitConverter]::ToUInt32($b,0);raw15=[Convert]::ToHexString($b);raw_offset4=[BitConverter]::ToUInt32($b,4)}})
 $journal=@(foreach($p in ($paths|Sort-Object -Unique)){$h=[WolvenKit.Core.Murmur3.Murmur32]::Hash($p,[uint32]0x5EEDBA5E,[Text.Encoding]::UTF8);@{path=$p;calculated_hash=$h;raw_matches=@($rawRows|Where-Object hash -eq $h)}})
 $journalProperties=@($jn[0].Value.PSObject.Properties|Select-Object Name,TypeNameOfValue)
}finally{$stream.Dispose()}
if((Hash $savePath) -cne $before){throw 'Snapshot changed during read'}
foreach($row in $copies){if((Hash $row.source) -cne $row.sha256){throw 'Source changed during inspection'}}
$installed=@(foreach($f in (Get-Content (Join-Path $ws 'recovery/sidejobs_s23_01/install_receipt.json') -Raw|ConvertFrom-Json).files){$h=Hash (Join-Path $game $f.relative);if($h -cne $f.sha256){throw 'Installed S23 drift'};@{file=$f.relative;sha256=$h}})
$r=@{status='READ_ONLY_SAVED_FACTS_AND_OPAQUE_JOURNAL_NOT_LIVE_API';copies=$copies;source_unchanged=$true;save_sha256=$before;facts=$values;journal=$journal;journal_properties=$journalProperties;installed=$installed;limits=@('Absent serialized facts are not live zero.','Raw offset4 is not a validated saved-state parser. No contact known/phone visibility inference from opaque bytes alone.','No save writer, game launch, native fact write or restoration performed.');inspector_sha256=Hash $PSCommandPath}
[IO.File]::WriteAllText((Join-Path $out 'evidence.json'),($r|ConvertTo-Json -Depth 20),[Text.UTF8Encoding]::new($false))
@{status=$r.status;save_sha256=$before;facts=$values;aaron_raw=@($journal|Where-Object path -like 'ep1/contacts/aaron*');journal_properties=$journalProperties}|ConvertTo-Json -Depth 10
