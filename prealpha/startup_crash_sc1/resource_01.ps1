$ErrorActionPreference='Stop'
$W=Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
. (Join-Path $W 'tools/build_phase2a.ps1') -WorkspaceRoot $W -HelpersOnly -WolvenKitRoot (Join-Path $W 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$want=[Convert]::ToUInt64('831467ae67c510ea',16)
$methods=@($hs.GetType().GetMethods()|Where-Object {$_.Name -match 'Get|Resolve'}|ForEach-Object {$_.ToString()})
$matches=@()
foreach($f in Get-ChildItem -LiteralPath 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\mod' -File -Filter '*.archive') {
 $arc=$null;[void]([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($f.FullName,$hs,[ref]$arc)
 if($arc.Files.ContainsKey($want)){$e=$arc.Files[$want];$matches+=@{archive=$f.FullName;depot=$e.Name;key=$want.ToString()}}
}
@{methods=$methods;matches=$matches}|ConvertTo-Json -Depth 5
