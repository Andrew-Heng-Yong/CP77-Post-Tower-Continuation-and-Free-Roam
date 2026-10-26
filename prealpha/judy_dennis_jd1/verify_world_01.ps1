Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$W=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $W 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $W 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$raw=Join-Path $W 'research/sidejobs_s28/vehicles/world_03/raw/ep1_1_nightcity_always_loaded_2.streamingsector'
$archive='C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/archive/pc/ep1/ep1_1_nightcity.archive'
$depot='base\worlds\03_night_city\_compiled\default\always_loaded_2.streamingsector'
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$a=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$a).ToString() -ne 'NoError'){throw 'Archive failed'}
$key=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot)
$mem=[IO.MemoryStream]::new();try{$a.Files[$key].Extract($mem);$hash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray()))}finally{$mem.Dispose()}
if((Get-FileHash $raw).Hash -cne $hash){throw 'Current world source differs'}
$s=[IO.File]::OpenRead($raw)
try{
 $r=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($s)
 $r.add_ParsingError([WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e)return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])})
 $f=$null;if($r.ReadFile([ref]$f,$true).ToString() -ne 'NoError'){throw 'Parse failed'}
 $source=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'JudyDoorJD1.reds') -Raw
 $door=@($f.RootChunk.NodeRefs|Where-Object {$_.ToString().EndsWith('/#sq026_dvc_judys_door_apartment')})
 if($door.Count -ne 1 -or !$source.Contains($door[0].ToString())){throw 'Door binding mismatch'}
 $rows=@($f.RootChunk.NodeData.Data|Where-Object {$_.QuestPrefabRefHash.ToString().EndsWith('/#sq026_spwn_player_judys_apartment')})
 if($rows.Count -ne 1){throw 'Interior anchor ambiguous'}
 $position=@([double]$rows[0].Position.X.ToString(),[double]$rows[0].Position.Y.ToString(),[double]$rows[0].Position.Z.ToString())
 $expected=@(-902.682373,1855.74219,42.3472099)
 for($i=0;$i -lt 3;$i++){if([math]::Abs($position[$i]-$expected[$i]) -gt 0.001){throw 'Interior position mismatch'}}
 $out=Join-Path $PSScriptRoot 'candidate_01/world_proof_01.json';if(Test-Path $out){throw 'Use successor'}
 @{status='PASS_CURRENT_NATIVE_DOOR_REFERENCE_AND_INTERIOR_ANCHOR';archive=$archive;depot=$depot;sha256=$hash;door=$door[0].ToString();anchor=$rows[0].QuestPrefabRefHash.ToString();position=$position;limits='Read-only sector provenance; live door orientation, collision and egress remain untested.'}|ConvertTo-Json -Depth 6|Set-Content -LiteralPath $out -Encoding utf8
 'PASS_CURRENT_NATIVE_DOOR_REFERENCE_AND_INTERIOR_ANCHOR'
}finally{$s.Dispose()}
