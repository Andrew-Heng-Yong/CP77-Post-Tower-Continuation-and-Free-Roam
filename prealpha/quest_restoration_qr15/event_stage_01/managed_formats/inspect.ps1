# Managed type and method-body inspection only; no save read or parser invocation.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = (Get-Item -LiteralPath (Join-Path $PSScriptRoot '../../../..')).FullName
$output = Join-Path $PSScriptRoot 'formats_01.json'
if (Test-Path -LiteralPath $output) { throw 'Fresh output required' }
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$assembly = [WolvenKit.RED4.Save.PersistencySystem2Parser].Assembly
$assemblyHash = (Get-FileHash -LiteralPath $assembly.Location).Hash
if ($assemblyHash -cne 'EF17F40D73F207F0F71F1F41A70A4549A19792D438F680A9BFBB4800D2EE2987') { throw 'Reader assembly drift' }
$opcodes = @{}
foreach ($field in [Reflection.Emit.OpCodes].GetFields([Reflection.BindingFlags]'Static,Public')) {
    $opcode = $field.GetValue($null)
    if ($opcode -is [Reflection.Emit.OpCode]) { $opcodes[([int]$opcode.Value -band 0xFFFF)] = $opcode }
}
function Read-MethodIL([Reflection.MethodBase]$Method) {
    $body = $Method.GetMethodBody()
    if ($null -eq $body) { return @{type=$Method.DeclaringType.FullName;method=$Method.ToString();no_body=$true} }
    $il = $body.GetILAsByteArray()
    $position = 0
    $rows = [Collections.Generic.List[object]]::new()
    while ($position -lt $il.Length) {
        $offset = $position
        $code = [int]$il[$position++]
        if ($code -eq 0xFE) { $code = 0xFE00 + [int]$il[$position++] }
        if (-not $opcodes.ContainsKey($code)) { throw "Unknown opcode at $offset" }
        $op = $opcodes[$code]
        $kind = $op.OperandType.ToString()
        $size = switch ($kind) {
            'InlineNone' { 0 }; 'ShortInlineVar' { 1 }; 'ShortInlineI' { 1 }; 'ShortInlineBrTarget' { 1 }
            'InlineVar' { 2 }; 'InlineI8' { 8 }; 'InlineR' { 8 }
            'InlineSwitch' { 4 + 4 * [BitConverter]::ToInt32($il, $position) }
            default { 4 }
        }
        if ($size -lt 0 -or $position + $size -gt $il.Length) { throw 'Malformed managed method body' }
        $operand = if ($size) { [Convert]::ToHexString($il[$position..($position + $size - 1)]) } else { '' }
        $memberType = ''
        if ($kind -in @('InlineField','InlineMethod','InlineTok','InlineType')) {
            $member = $Method.Module.ResolveMember([BitConverter]::ToInt32($il, $position))
            $operand = $member.ToString()
            if ($null -ne $member.DeclaringType) { $memberType = $member.DeclaringType.FullName }
        } elseif ($kind -eq 'InlineString') {
            $operand = $Method.Module.ResolveString([BitConverter]::ToInt32($il, $position))
        } elseif ($kind -eq 'InlineI') { $operand = [BitConverter]::ToInt32($il, $position) }
        elseif ($kind -eq 'ShortInlineI') { $operand = [int]$il[$position]; if ($operand -gt 127) { $operand -= 256 } }
        elseif ($kind -eq 'InlineBrTarget') { $operand = $position + $size + [BitConverter]::ToInt32($il, $position) }
        elseif ($kind -eq 'ShortInlineBrTarget') { $delta = [int]$il[$position]; if ($delta -gt 127) { $delta -= 256 }; $operand = $position + $size + $delta }
        $position += $size
        $rows.Add(@{ offset = $offset; opcode = $op.Name; operand = $operand; member_type = $memberType })
    }
    @{ type = $Method.DeclaringType.FullName; method = $Method.ToString(); il_hex = [Convert]::ToHexString($il); instructions = $rows.ToArray(); decoded_bytes = $position }
}
$selectedNames = @('QueuedData','CustomArray','EventManager','NodeInstanceDataManager','QuestPrefabsHandler','QuestPhaseFreezer','QuestDebugLogManager','QuestSceneDataHelper','PlayerObjectListenerMapper','DelaySystemCore','DelaySystemDelayedStructs')
$types = @($assembly.GetTypes() | Where-Object {
    $_.Namespace -like 'WolvenKit.RED4.Save*' -and ($_.Name.Replace('Parser','').Split('+')[0] -in $selectedNames -or ($null -ne $_.DeclaringType -and $_.DeclaringType.Name -in $selectedNames))
})
if ($types.Count -gt 100) { throw 'Unbounded type selection' }
$inventory = @(); $methods = @()
foreach ($type in $types | Sort-Object FullName) {
    $declared = @($type.GetMethods([Reflection.BindingFlags]'Instance,Static,Public,NonPublic,DeclaredOnly'))
    $inventory += @{ type=$type.FullName; properties=@($type.GetProperties() | ForEach-Object { $_.ToString() }); methods=@($declared | ForEach-Object { $_.ToString() }) }
    foreach ($method in $declared) {
        if ($method.Name -in @('Read','ReadEntry','ReadNode','ReadData')) { $methods += Read-MethodIL $method }
    }
}
@{status='MANAGED_IL_AND_TYPE_SHAPES_ONLY';assembly=$assembly.Location;assembly_sha256=$assemblyHash;inventory=$inventory;methods=$methods;save_reads=0;parser_invocations=0;game_calls=0;runtime_changes=0} |
    ConvertTo-Json -Depth 14 | Set-Content -LiteralPath $output -Encoding utf8NoBOM
@{status='INSPECTED';types=$types.Count;methods=$methods.Count;output=$output} | ConvertTo-Json
