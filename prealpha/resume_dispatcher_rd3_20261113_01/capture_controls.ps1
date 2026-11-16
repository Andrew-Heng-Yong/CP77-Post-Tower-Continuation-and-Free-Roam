# Read-only component/identity projection of four pinned historical fixtures.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$output=Join-Path $PSScriptRoot 'saves_02'
if(Test-Path -LiteralPath $output){throw 'Fresh output required'}
$plan=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'evidence_01/controls.json') -Raw|ConvertFrom-Json
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$parserHash=(Get-FileHash -LiteralPath ([WolvenKit.RED4.Save.IO.CyberpunkSaveReader].Assembly.Location)).Hash
if($parserHash -cne 'EF17F40D73F207F0F71F1F41A70A4549A19792D438F680A9BFBB4800D2EE2987'){throw 'Parser drift'}
function Plain([string]$path){
 for($item=Get-Item -LiteralPath $path;$null -ne $item;){
  if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked input/output refused'}
  $item=if($item -is [IO.FileInfo]){$item.Directory}else{$item.Parent}
 }
}
Plain $PSScriptRoot
$toHash=@([WolvenKit.RED4.Save.Fact].GetMethods()|Where-Object {$_.Name -eq 'op_Implicit' -and $_.ReturnType -eq [uint32]})[0]
$factKeys=@{};foreach($name in $plan.facts){$f=[WolvenKit.RED4.Save.Fact]::op_Implicit([string]$name);$key=[uint32]$toHash.Invoke($null,[object[]]@($f));if($factKeys.ContainsKey($key)){throw 'Selected fact collision'};$factKeys[$key]=$name}
$journalKeys=@{};foreach($path in $plan.journals){$key=[WolvenKit.Core.Murmur3.Murmur32]::Hash($path,[uint32]0x5EEDBA5E,[Text.Encoding]::UTF8);if($journalKeys.ContainsKey($key)){throw 'Selected journal collision'};$journalKeys[$key]=$path}
New-Item -ItemType Directory -Path $output|Out-Null
foreach($inputSave in $plan.saves){
 Plain $inputSave.source;Plain $inputSave.metadata
 if((Get-FileHash -LiteralPath $inputSave.source).Hash -cne $inputSave.source_sha256 -or (Get-FileHash -LiteralPath $inputSave.metadata).Hash -cne $inputSave.metadata_sha256){throw 'Pinned save drift'}
 $bytes=[IO.File]::ReadAllBytes($inputSave.source)
 if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)) -cne $inputSave.source_sha256){throw 'Input changed during read'}
 $headerMemory=[IO.MemoryStream]::new($bytes,$false);$headerReader=[WolvenKit.RED4.Save.IO.CyberpunkSaveReader]::new($headerMemory);$header=$null
 try{if($headerReader.ReadFileInfo([ref]$header).ToString() -cne 'NoError' -or $header.SaveVersion -lt 139){throw 'Unsupported native save schema'}}finally{$headerReader.Dispose();$headerMemory.Dispose()}
 $memory=[IO.MemoryStream]::new($bytes,$false);$reader=[WolvenKit.RED4.Save.IO.CyberpunkSaveReader]::new($memory);$save=$null
 try{
  if($reader.ReadFile([ref]$save).ToString() -cne 'NoError'){throw 'Save parse failed'}
  $roots=@($save.Nodes|Where-Object Name -ceq 'questSystem');if($roots.Count -ne 1){throw 'Quest root ambiguous'};$root=$roots[0]
  $facts=@($root.Children|Where-Object Name -ceq 'FactsDB');if($facts.Count -ne 1 -or $facts[0].Children.Count -ne 10){throw 'Native store shape changed'}
  $values=[ordered]@{};foreach($name in $plan.facts){$values[$name]=$null}
  foreach($entry in $facts[0].Children[0].Value.FactEntries){$key=[uint32]$toHash.Invoke($null,[object[]]@($entry.FactName));if($factKeys.ContainsKey($key)){$values[$factKeys[$key]]=[uint32]$entry.Value}}
  $journal=@($save.Nodes|Where-Object Name -ceq 'JournalManager');if($journal.Count -ne 1){throw 'Journal root ambiguous'}
  $journalRows=@(foreach($entry in $journal[0].Value.Entries){$raw=[byte[]]$entry.UnkownBytes;if($raw.Length -ne 15){throw 'Journal format drift'};$key=[BitConverter]::ToUInt32($raw,0);if($journalKeys.ContainsKey($key)){@{path=$journalKeys[$key];hash_u32=$key;raw15=[Convert]::ToHexString($raw);state_u32=[BitConverter]::ToUInt32($raw,4)}}})
  $names=@('customArray','eventManager','questPhaseFreezer','questPrefabsHandler','QueuedData')
  $nodes=@(foreach($name in $names){$found=@($root.Children|Where-Object Name -ceq $name);if($found.Count -ne 1 -or $found[0].Children.Count -ne 0 -or $found[0].TrailingSize -ne 0 -or $found[0].DataSize -ne $found[0].Size){throw 'Ambiguous component span'};$found[0]})
  if(($nodes|Measure-Object Size -Sum).Sum -gt 1048576){throw 'Capture exceeds bounded size'}
  $slotOutput=Join-Path $output $inputSave.slot;New-Item -ItemType Directory -Path $slotOutput|Out-Null
  $stream=[IO.MemoryStream]::new($bytes,$false);$binary=[IO.BinaryReader]::new($stream);$settings=$null;$decompressed=$null;$spans=@();$controlCount=0
  try{
   $decompressed=[WolvenKit.RED4.Save.Compression]::Decompress($binary,[ref]$settings);$view=[IO.BinaryReader]::new($decompressed,[Text.Encoding]::UTF8,$true)
   try{
    foreach($node in @($root)+$nodes+@($facts[0])+@($facts[0].Children)){$decompressed.Position=$node.Offset;if($view.ReadInt32() -ne $node.Id){throw 'Offset/ID control failed'};$controlCount++}
    foreach($node in $nodes){
     $decompressed.Position=$node.Offset;$raw=$view.ReadBytes($node.Size);if($raw.Length -ne $node.Size){throw 'Short component read'}
     if($node.Name -in @('customArray','eventManager')){
      $stride=if($node.Name -eq 'customArray'){2}else{16};$count=[BitConverter]::ToUInt32($raw,4)
      if(8+[long]$stride*$count -ne $raw.Length -or $count -ne $node.Value.Unknown.Count){throw 'Native/managed framing differs'}
      for($i=0;$i -lt $count;$i++){
       if($stride -eq 2){if([BitConverter]::ToUInt16($raw,8+2*$i) -ne $node.Value.Unknown[$i]){throw 'Path word mismatch'}}else{
        $at=8+16*$i;$r=$node.Value.Unknown[$i]
        if([BitConverter]::ToUInt64($raw,$at) -ne $r.Unknown1 -or [BitConverter]::ToUInt32($raw,$at+8) -ne $r.Unknown2 -or [BitConverter]::ToUInt16($raw,$at+12) -ne $r.Unknown3 -or [BitConverter]::ToUInt16($raw,$at+14) -ne $r.Unknown4){throw 'Native/managed handler mismatch'}
       }
      }
      $controlCount++
     }
     $dest=Join-Path $slotOutput ($node.Name+'.bin');[IO.File]::WriteAllBytes($dest,$raw)
     $spans+=@{name=$node.Name;id=$node.Id;offset=$node.Offset;size=$node.Size;path=$dest;sha256=(Get-FileHash -LiteralPath $dest).Hash}
    }
    $custom=@($nodes|Where-Object Name -ceq 'customArray')[0];$start=[long]$facts[0].Offset+$facts[0].Size;$length=[long]$custom.Offset-$start
    if($length -le 0 -or $length -gt 65536){throw 'Unexpected exact root-array gap'}
    $decompressed.Position=$start;$gap=$view.ReadBytes([int]$length);[IO.File]::WriteAllBytes((Join-Path $slotOutput 'root_resources.bin'),$gap)
   }finally{$view.Dispose()}
  }finally{if($null -ne $decompressed){$decompressed.Dispose()};$binary.Dispose()}
  if((Get-FileHash -LiteralPath $inputSave.source).Hash -cne $inputSave.source_sha256 -or (Get-FileHash -LiteralPath $inputSave.metadata).Hash -cne $inputSave.metadata_sha256){throw 'Save changed during capture'}
  @{status='READ_ONLY_NATIVE_HANDLER_FIXTURE';slot=$inputSave.slot;source=$inputSave.source;source_sha256=$inputSave.source_sha256;metadata_sha256=$inputSave.metadata_sha256;save_version=$header.SaveVersion;game_version=$header.GameVersion;root_gap_hex=[Convert]::ToHexString($gap);nodes=$spans;controls=$controlCount;facts=$values;journals=$journalRows;source_unchanged=$true;parser_sha256=$parserHash;tool_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash;save_writes=0;game_calls=0}|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $slotOutput 'manifest.json') -Encoding utf8NoBOM
  Write-Output "Captured $($inputSave.slot): $controlCount controls; $($spans.Count) bounded spans."
 }finally{$reader.Dispose();$memory.Dispose()}
}
