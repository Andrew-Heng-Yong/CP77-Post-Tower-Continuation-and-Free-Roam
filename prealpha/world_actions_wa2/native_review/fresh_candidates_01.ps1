param([string]$Run='01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$folder=Join-Path $ws 'prealpha/world_actions_wa2/candidate_01/source'
$out=Join-Path $PSScriptRoot ('fresh_candidates_'+$Run)
if(Test-Path -LiteralPath $out){throw 'Preserve existing independent evidence'}
[void][IO.Directory]::CreateDirectory($out)
$rows=@();$hashes=@{}
function RefScan($v){
 if($null -eq $v){return}
 if($v -is [System.Collections.IDictionary]){
  if($v.Contains('$type') -and $v['$type'] -eq 'NodeRef'){
   $r=[string]$v['$value'];if($r -ne '0' -and !$hashes.ContainsKey($r)){$hashes[$r]=[WolvenKit.RED4.Types.NodeRef]::CalculateHash($r).ToString()}
  }
  foreach($k in $v.Keys){RefScan $v[$k]}
 }elseif($v -is [System.Collections.IEnumerable] -and $v -isnot [string]){foreach($x in $v){RefScan $x}}
}
foreach($f in @(Get-ChildItem -LiteralPath $folder -Recurse -File -Filter 'group_*_action.questphase')){
 $group=[int]([regex]::Match($f.Name,'group_(\d+)_').Groups[1].Value)
 $file=Read-Cr2wFile $f.FullName;$g=$file.RootChunk.Graph.Chunk;$l=(Get-QuestNode $g 10).PhaseGraph.Chunk
 $cid=60000;if($group -eq 172){$cid=64};if($group -eq 173){$cid=61}
 $c=(Get-QuestNode $l $cid).PhaseGraph.Chunk
 $json=Join-Path $out ($f.Name+'.json');Export-Cr2wJson $file $json
 RefScan (Get-Content -LiteralPath $json -Raw|ConvertFrom-Json -AsHashtable)
 $rows+=@{group=$group;path=$f.FullName;resource=('towercontinued/world_actions_wa2/'+$f.Name);sha256=(Get-FileHash -LiteralPath $f.FullName).Hash;fresh_json=$json;fresh_json_sha256=(Get-FileHash -LiteralPath $json).Hash;root_edges=@(Get-GraphEdges $g);loop_edges=@(Get-GraphEdges $l);controller_edges=@(Get-GraphEdges $c);controller_nodes=@($c.Nodes|ForEach-Object {"$($_.Chunk.Id):$($_.Chunk.GetType().Name)"})}
}
$manifest=Get-Content -LiteralPath (Join-Path $ws 'prealpha/world_workspots_w2/manifest_03.json') -Raw|ConvertFrom-Json
foreach($r in $manifest.groups){foreach($ref in $r.community_refs){if(!$hashes.ContainsKey([string]$ref)){$hashes[[string]$ref]=[WolvenKit.RED4.Types.NodeRef]::CalculateHash([string]$ref).ToString()}}}
[IO.File]::WriteAllText((Join-Path $out 'proof.json'),(@{status='INDEPENDENT_FRESH_CANDIDATE_GRAPH_AND_NODEREF_HASH_READBACK';resources=$rows;node_ref_hashes=$hashes;game_writes=0;save_writes=0}|ConvertTo-Json -Depth 20)+"`n",[Text.UTF8Encoding]::new($false))
Write-Output ('Fresh action resources: '+$rows.Count)
