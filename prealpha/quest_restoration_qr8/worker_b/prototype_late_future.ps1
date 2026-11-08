param([string]$OutputName='proposal_late_future_01')
# PRIVATE NONPRODUCTION proof. No registration, candidate, package, deployment or save writes.
$ErrorActionPreference='Stop'
$ws=(Get-Location).Path;$taskDir=Join-Path $ws 'prealpha/quest_restoration_qr8/worker_b';$out=Join-Path $taskDir $OutputName
if(Test-Path -LiteralPath $out){throw 'Fresh output required'}
New-Item -ItemType Directory -Path $out|Out-Null
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$pin=Get-Content -Raw -LiteralPath (Join-Path $taskDir 'readback_01/manifest.json')|ConvertFrom-Json|Where-Object {$_.depot -ceq 'towercontinued\quest_restoration_qr7\ronald_news_future.questphase'}
if((Get-FileHash -LiteralPath $pin.raw).Hash -cne $pin.raw_sha256){throw 'Canonical source drift'}
$file=Read-Cr2wFile $pin.raw;$g=(Get-QuestNode $file.RootChunk.Graph.Chunk 202).PhaseGraph.Chunk
function Logical($op,$parts){$c=[WolvenKit.RED4.Types.questLogicalCondition]::new();$c.Operation=[Enum]::Parse([WolvenKit.RED4.Types.Enums+questLogicalOperation],$op);foreach($p in $parts){Add-RedHandle $c.Conditions $p};return $c}
$rows=@();$ids=@(200,201,202,203);$cases=@('12','08','03','01')
for($i=0;$i -lt 4;$i++){
 $n=Get-QuestNode $g $ids[$i];$old=$n.Condition.Chunk;$quest='sts_ep1_'+$cases[$i];$arm='PTFRQR7_RonaldNews_Armed_'+$quest
 if($old.Conditions.Count -ne 3 -or $old.Conditions[0].Chunk.Type.Chunk.FactName.ToString() -cne ($quest+'_done') -or $old.Conditions[0].Chunk.Type.Chunk.Value -ne 0){throw 'Expected original gate shape changed'}
 $done=Logical 'OR' @($old.Conditions[0].Chunk.DeepCopy(),(New-FactCondition $arm 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal)))
 $gate=Logical 'AND' @($done,$old.Conditions[1].Chunk.DeepCopy(),$old.Conditions[2].Chunk.DeepCopy())
 Set-RedHandleProperty $n Condition $gate
 $rows+=@{quest_id=$quest;graph='root/202';node=$ids[$i];change='done0 OR exact real QR7 Armed1; native done>=1 listener remains untouched';preserved=@('sent0','original ParentEntered0 OR Armed1','real future-arm wait','all native timing/requests/SMS/cleanup/terminal identities')}
}
$raw=Join-Path $out 'ronald_news_future.NONPRODUCTION.questphase';$json=$raw+'.json';Write-Cr2wFile $file $raw;Export-Cr2wJson (Read-Cr2wFile $raw) $json
@{status='PRIVATE_PROPOSAL_REQUIRES_INDEPENDENT_SOURCE_AND_COORDINATOR_APPROVAL';source=$pin;intended_depot=$pin.depot;raw=$raw;raw_sha256=(Get-FileHash -LiteralPath $raw).Hash;json=$json;json_sha256=(Get-FileHash -LiteralPath $json).Hash;changes=$rows;unchanged_registration=$true;new_namespaces=0;production_writes=0;scope='Only the original first evaluation of each unchanged admission-node identity, seeing a genuine QR7 future-entry receipt plus native sent0. Root issuance/admission/edges unchanged; no restarted helper or reopened skipped branch. A saved owner still waiting before gate evaluation can use this path; an already-processed branch is not revisited. No enrollment/contact repair, timer adoption, reset or synthetic ACK.'}|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $out 'NOT_FOR_INTEGRATION.json') -Encoding utf8
Write-Output 'Private four-gate proposal serialized/read back; not integrated'
