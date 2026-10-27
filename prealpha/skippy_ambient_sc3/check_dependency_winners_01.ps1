Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$out=Join-Path $PSScriptRoot 'candidate_02/dependency_winners_01.json'
if(Test-Path -LiteralPath $out){throw 'Preserve evidence'}
$resources=@('base\quest\minor_quests\mq007\phases\mq007_gameplay_comments.questphase','base\quest\minor_quests\mq007\phases\mq007_expression_facts_reset.questphase','base\quest\minor_quests\mq007\scenes\mq007_02_skippy_reactions.scene','base\quest\minor_quests\mq007\scenes\mq007_04_skippy_return.scene')
$keys=@{};foreach($r in $resources){$keys[[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($r).ToString()]=$r}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$archives=@(Get-ChildItem -LiteralPath 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\mod' -Filter '*.archive' -File)
$hits=@()
foreach($f in $archives){$a=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($f.FullName,$hs,[ref]$a).ToString() -cne 'NoError'){throw ('Unreadable archive '+$f.Name)};foreach($e in $a.Files.Values){$k=$e.Key.ToString();if($keys.ContainsKey($k)){$hits+=@{archive=$f.Name;resource=$keys[$k]}}}}
if($hits.Count){throw ('Native Skippy dependencies overridden: '+($hits|ConvertTo-Json))}
$result=@{status='PASS_NO_INSTALLED_MOD_OVERRIDES';archives=$archives.Count;resources=$resources;hits=$hits;game_writes=0}
[IO.File]::WriteAllText($out,($result|ConvertTo-Json -Depth 10)+"`n",[Text.UTF8Encoding]::new($false))
$result|ConvertTo-Json -Depth 10
