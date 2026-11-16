"""Stage a narrowly scoped successor while keeping candidate 02 immutable."""

from hashlib import file_digest
import json
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / "universal_resume_checkpoint_20261114_01"
SOURCE = HERE / "source_01"
STOCK_BUILD_SHA = "70796B77FF8927556A665B3D9404933B077252B7160A50102488A9A013E048BC"


def sha(path):
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest().upper()


def pinned(path, expected):
    assert sha(path) == expected, path
    return path


def replace_once(text, before, after):
    assert text.count(before) == 1, before
    return text.replace(before, after, 1)


def main():
    build = pinned(PREVIOUS / "build_04/build.json", STOCK_BUILD_SHA)
    files = {row["name"]: row["sha256"] for row in json.loads(build.read_bytes())}
    old = pinned(PREVIOUS / "NativeCheckpoint.cpp", files["NativeCheckpoint.cpp"]).read_text(encoding="utf-8")
    for name in ("Checkpoint.hpp", "CheckpointChecks.cpp"):
        pinned(PREVIOUS / name, files[name])
    for sibling, header in (("universal_resume_boundary_20261114_01", "TimerRecord.hpp"),
                            ("universal_resume_eagles_20261114_01", "GameTimeWait.hpp")):
        pinned(HERE.parent / sibling / header, files[header])
    start = old.index("void RegisterReader()\n")
    end = old.index("bool VerifyFile(", start)
    registration = (HERE / "RegisterReader.inc").read_text(encoding="utf-8").rstrip()
    native = old[:start] + registration + "\n\n" + old[end:]
    changes = [
        ('#include "Checkpoint.hpp"', '#include "Checkpoint.hpp"\n#include "../CheckpointRegistration.hpp"'),
        ('#include "../universal_resume_boundary_20261114_01/TimerRecord.hpp"',
         '#include "../../universal_resume_boundary_20261114_01/TimerRecord.hpp"'),
        ('#include "../universal_resume_eagles_20261114_01/GameTimeWait.hpp"',
         '#include "../../universal_resume_eagles_20261114_01/GameTimeWait.hpp"'),
        ("std::atomic<bool> enabled{};", "std::atomic<bool> enabled{};\nstd::atomic<bool> hooksReady{};"),
        ("GetModuleHandleW(nullptr));\n    rtti->AddPostRegisterCallback(&RegisterReader);\n    try",
         "GetModuleHandleW(nullptr));\n    try"),
        ("        enabled.store(Attach());", "        hooksReady.store(Attach());"),
        ("    if (!enabled.load())\n        sdk->logger->Warn(plugin, \"PTFR execution capture unavailable for this runtime or archive\");",
         "    if (!hooksReady.load())\n        sdk->logger->Warn(plugin, \"PTFR execution capture unavailable for this runtime or archive\");\n"
         "    rtti->AddPostRegisterCallback(&RegisterReader);"),
        ("    info->version = RED4EXT_V1_SEMVER(0, 1, 0);", "    info->version = RED4EXT_V1_SEMVER(0, 1, 1);"),
    ]
    for before, after in changes:
        native = replace_once(native, before, after)
    reverted = native
    for before, after in reversed(changes):
        reverted = replace_once(reverted, after, before)
    assert replace_once(reverted, registration + "\n\n", old[start:end]) == old

    SOURCE.mkdir(exist_ok=False)
    (SOURCE / "NativeCheckpoint.cpp").write_text(native, encoding="utf-8", newline="\n")
    for name in ("Checkpoint.hpp", "CheckpointChecks.cpp"):
        shutil.copyfile(PREVIOUS / name, SOURCE / name)
        pinned(SOURCE / name, files[name])
    print("Staged the registration-only source changes and verified the original capture code.")


if __name__ == "__main__":
    main()
