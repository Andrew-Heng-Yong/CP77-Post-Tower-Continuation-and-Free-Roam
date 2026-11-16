"""Stage only the registration and script bridge over the exact v0.1.1 inputs."""

import argparse
from hashlib import file_digest
import json
from pathlib import Path
import re
import shutil


HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / "universal_resume_checkpoint_rtti_20261114_01"
ORIGINAL = HERE.parent / "universal_resume_checkpoint_20261114_01"
PREVIOUS_BUILD_SHA = "539D481C6DE25953EA48AC9FD690EA087B325E3A9890E652951D0F560B9DA0C0"
PREVIOUS_CANDIDATE_SHA = "84EA250DAFDBBFF10AABC0C6947B0FFF7C943D97D71BF6593524CD80A7A0005D"
HISTORY = "r6/scripts/PTFR_Consolidated/PTFR_HistorySnapshotHS1.reds"
LUA = "bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_HistorySnapshotHS1/init.lua"
DLL = "red4ext/plugins/PTFR_ExecutionCheckpoint/PTFR_ExecutionCheckpoint.dll"


def sha(path):
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest().upper()


def pinned(path, expected):
    assert sha(path) == expected, path
    return path


def read_json(path):
    return json.loads(path.read_bytes())


def write_json(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, indent=2) + "\n")


def check_overlay(source, edits):
    def replace_once(text, expected, replacement):
        assert text.count(expected) == 1, expected
        return text.replace(expected, replacement, 1)

    result = source
    for before, after in edits:
        result = replace_once(result, before, after)
    revert = result
    for before, after in reversed(edits):
        revert = replace_once(revert, after, before)
    assert revert == source
    return result


def previous_candidate():
    folder = PREVIOUS / "candidate_02"
    receipt = read_json(pinned(folder / "receipt.json", PREVIOUS_CANDIDATE_SHA))
    assert set(receipt["files"]) == {HISTORY, LUA, DLL}
    return folder, receipt


def stage_history(original):
    newline = "\r\n" if b"\r\n" in original else "\n"
    source = original.decode("utf-8").replace("\r\n", "\n")
    bridge = (HERE / "checkpoint_bridge.reds").read_text(encoding="utf-8").rstrip()
    begin = source.index("  private func ReadExecution(ticket:")
    end = source.index("  private func ReadExecutionPresentation(", begin)
    declaration = (
        "public static native func ReadExecutionCheckpoint(quests: ref<QuestsSystem>, "
        "delay: ref<DelaySystem>, clock: ref<TimeSystem>, ticket: Int32, route: Int32, "
        "historyRevision: Int32, presentation: array<Uint64>) -> array<Uint64>\n"
        "public static native func DecodeExecutionCheckpoint(data: array<Uint64>) -> String\n\n"
    )
    before_attempt = """    let execution = this.ReadExecution(ticket,route,this.revision+1,this.ReadExecutionPresentation(player));
    if ArraySize(execution)==0 && this.executionCheckpointAttempts<2 {
      this.executionCheckpointAttempts+=1;
      return;
    }
"""
    after_attempt = """    let reader = Reflection.GetGlobalFunction(n"PTFR.HistorySnapshotHS1.ReadExecutionCheckpoint");
    let decoder = Reflection.GetGlobalFunction(n"PTFR.HistorySnapshotHS1.DecodeExecutionCheckpoint");
    let execution: array<Uint64>;
    if IsDefined(reader) && IsDefined(decoder) {
      execution = this.ReadExecution(reader, ticket, route, this.revision + 1, this.ReadExecutionPresentation(player));
      if ArraySize(execution) == 0 && this.executionCheckpointAttempts < 2 {
        this.executionCheckpointAttempts += 1;
        return;
      }
    }
"""
    # Anchor the declaration removal to its following class so it remains reversible.
    class_decl = "public class CaptureArchiveHS3 extends ScriptableSystem {\n"
    updated = check_overlay(source, [
        (declaration + class_decl, class_decl),
        (source[begin:end], bridge + "\n\n"),
        ("  private func StoreExecutionCheckpoint(ticket: Int32, route: Int32, capture: array<Uint64>) -> Void {",
         "  private func StoreExecutionCheckpoint(ticket: Int32, route: Int32, capture: array<Uint64>,\n"
         "                                        decoder: ref<ReflectionStaticFunc>) -> Void {"),
        ("    let encoded = DecodeExecutionCheckpoint(capture);",
         "    let encoded = this.DecodeExecution(decoder, capture);"),
        ("    let encoded = DecodeExecutionCheckpoint(this.executionCheckpointState);",
         "    let decoder = Reflection.GetGlobalFunction(n\"PTFR.HistorySnapshotHS1.DecodeExecutionCheckpoint\");\n"
         "    let encoded = this.DecodeExecution(decoder, this.executionCheckpointState);"),
        (before_attempt, after_attempt),
        ("    this.StoreExecutionCheckpoint(ticket,route,execution);",
         "    this.StoreExecutionCheckpoint(ticket, route, execution, decoder);"),
    ])
    persisted_pattern = r"\bpersistent let \S+:[^;]+;"
    assert re.findall(persisted_pattern, updated) == re.findall(persisted_pattern, source)
    ack = 'SetFact(n"PTFRHS3_GateResult",1)'
    assert source.count(ack) == updated.count(ack) == 2
    assert updated.index("this.StoreExecutionCheckpoint(ticket, route, execution, decoder)") < updated.rindex(ack)
    return updated.replace("\n", newline).encode("utf-8")


def stage_native(original):
    start = original.index("void RegisterReader()\n")
    end = original.index("bool VerifyFile(", start)
    registration = (HERE / "RegisterReader.inc").read_text(encoding="utf-8").rstrip()
    return check_overlay(original, [
        (original[start:end], registration + "\n\n"),
        ("    if (reason != RED4ext::v1::EMainReason::Load || !api || !api->hooking || !api->logger)\n"
         "        return false;\n"
         "    const auto rtti = RED4ext::CRTTISystem::Get();\n"
         "    if (!rtti)\n"
         "        return false;",
         "    if (reason != RED4ext::v1::EMainReason::Load || !api || !api->hooking || !api->logger ||\n"
         "        !api->gameStates || !api->gameStates->Add)\n"
         "        return false;"),
        ("    image = reinterpret_cast<const std::uint8_t*>(GetModuleHandleW(nullptr));\n    try\n",
         "    image = reinterpret_cast<const std::uint8_t*>(GetModuleHandleW(nullptr));\n"
         "    RED4ext::v1::GameState running{&OnRunning, nullptr, nullptr};\n"
         "    if (!sdk->gameStates->Add(plugin, RED4ext::EGameStateType::Running, &running))\n"
         "    {\n"
         "        sdk->logger->Warn(plugin, \"PTFR checkpoint could not register its running-state callback\");\n"
         "        return true;\n"
         "    }\n"
         "    try\n"),
        ("    rtti->AddPostRegisterCallback(&RegisterReader);\n    return true;\n}\n\nRED4EXT_C_EXPORT void",
         "    return true;\n}\n\nRED4EXT_C_EXPORT void"),
        ("    info->version = RED4EXT_V1_SEMVER(0, 1, 1);",
         "    info->version = RED4EXT_V1_SEMVER(0, 1, 2);"),
    ])


def prepare(attempt):
    stock_receipt = pinned(PREVIOUS / "build_02/build.json", PREVIOUS_BUILD_SHA)
    stock = {row["name"]: row["sha256"] for row in read_json(stock_receipt)}
    previous_path, candidate = previous_candidate()
    original_native = pinned(PREVIOUS / "source_01/NativeCheckpoint.cpp", stock["NativeCheckpoint.cpp"])
    native = stage_native(original_native.read_text(encoding="utf-8"))
    history = stage_history(pinned(previous_path / "files" / HISTORY, candidate["files"][HISTORY]).read_bytes())
    for sibling, header in (("universal_resume_boundary_20261114_01", "TimerRecord.hpp"),
                            ("universal_resume_eagles_20261114_01", "GameTimeWait.hpp")):
        pinned(HERE.parent / sibling / header, stock[header])

    out = HERE / f"source_{attempt:02d}"
    out.mkdir(exist_ok=False)
    (out / "NativeCheckpoint.cpp").write_text(native, encoding="utf-8", newline="\n")
    (out / Path(HISTORY).name).write_bytes(history)
    for name in ("Checkpoint.hpp", "CheckpointChecks.cpp"):
        shutil.copyfile(pinned(PREVIOUS / "source_01" / name, stock[name]), out / name)
        pinned(out / name, stock[name])
    inputs = {path.name: sha(path) for path in out.iterdir()}
    for name in ("CheckpointRegistration.hpp", "RegisterReader.inc", "checkpoint_bridge.reds"):
        inputs[name] = sha(HERE / name)
    write_json(out / "receipt.json", {"sources": inputs, "previous_build": PREVIOUS_BUILD_SHA,
                                      "previous_candidate": PREVIOUS_CANDIDATE_SHA})
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt", type=int, choices=range(1, 100), required=True)
    args = parser.parse_args()
    print(prepare(args.attempt))
