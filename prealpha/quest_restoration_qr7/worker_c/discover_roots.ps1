param([string]$Output='root_names_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$W=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
$O=Join-Path $PSScriptRoot $Output
if(Test-Path -LiteralPath $O){throw 'Fresh worker output required'}
. (Join-Path $W 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $W 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
Add-Type -TypeDefinition @'
public static class QR7RootNames {
 public static string[] Find(object service) {
  var field=service.GetType().GetField("_hashes",System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Instance);
  var dictionary=(System.Collections.IDictionary)field.GetValue(service);
  var paths=new System.Collections.Generic.List<string>();
  foreach(System.Collections.DictionaryEntry pair in dictionary) {
   var name=pair.Value.ToString();
   if(name.EndsWith(".game",System.StringComparison.OrdinalIgnoreCase)) paths.Add(name);
  }
  paths.Sort();return paths.ToArray();
 }
}
'@
$svc=[WolvenKit.Common.Services.HashService]::new();$svc.Load();$svc.Loaded.GetAwaiter().GetResult()
$names=[QR7RootNames]::Find($svc)
[IO.Directory]::CreateDirectory($O)|Out-Null
@{status='HASH_DICTIONARY_GAME_RESOURCE_NAMES_ONLY';paths=$names;count=$names.Count;code_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash;tool_sha256=(Get-FileHash -LiteralPath (Join-Path $W 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package/WolvenKit.Common.dll')).Hash;limits=@('Hash dictionary presence is not provider existence or game startup authority.')}|ConvertTo-Json -Depth 10|Set-Content -LiteralPath (Join-Path $O 'names.json') -Encoding utf8NoBOM
@{names=$names.Count;output=$O}|ConvertTo-Json -Compress
