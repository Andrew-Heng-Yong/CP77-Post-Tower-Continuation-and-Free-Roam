# Inspect the pinned managed reader's IL only. Does not read a save or invoke a parser.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = (Get-Item -LiteralPath (Join-Path $PSScriptRoot '../../../../..')).FullName
$output = Join-Path $PSScriptRoot 'parser_il_02.json'
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
    $clauses = @($body.ExceptionHandlingClauses | ForEach-Object { @{flags=$_.Flags.ToString();try_offset=$_.TryOffset;try_length=$_.TryLength;handler_offset=$_.HandlerOffset;handler_length=$_.HandlerLength} })
    @{ type = $Method.DeclaringType.FullName; method = $Method.ToString(); il_hex = [Convert]::ToHexString($il); instructions = $rows; decoded_bytes = $position; exception_clauses=$clauses }
}
$types = @($assembly.GetTypes() | Where-Object { $_.FullName -like 'WolvenKit.RED4.Save.PersistencySystem2*' -or $_.FullName -eq 'WolvenKit.RED4.Save.PS2Entry' })
$inventory = @(); $methods = @()
foreach ($type in $types | Sort-Object FullName) {
    $selected = @($type.GetMethods([Reflection.BindingFlags]'Instance,Static,Public,NonPublic,DeclaredOnly'))
    $inventory += @{type=$type.FullName; methods=@($selected | ForEach-Object {$_.ToString()}); properties=@($type.GetProperties() | ForEach-Object {$_.ToString()})}
    foreach ($method in $selected) {
        if ($method.Name -in @('Read','ReadEntry','get_Id','set_Id','get_Data','set_Data')) { $methods += Read-MethodIL $method }
    }
    foreach ($method in $type.GetConstructors([Reflection.BindingFlags]'Instance,Static,Public,NonPublic')) { $methods += Read-MethodIL $method }
}
$parserRead = [WolvenKit.RED4.Save.PersistencySystem2Parser].GetMethod('Read')
$parserIL = $parserRead.GetMethodBody().GetILAsByteArray()
if ($parserIL[158] -ne 0x28) { throw 'Pinned Create call site changed' }
$factory = $parserRead.Module.ResolveMethod([BitConverter]::ToInt32($parserIL,159))
$methods += Read-MethodIL $factory
@{assembly=$assembly.Location; assembly_sha256=$assemblyHash;status='MANAGED_IL_ONLY_NO_PARSER_INVOCATION';inventory=$inventory;methods=$methods;game_calls=0;save_reads=0;parser_calls=0;runtime_changes=0} |
    ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $output -Encoding utf8NoBOM
@{output=$output;types=$types.Count;methods=$methods.Count} | ConvertTo-Json
