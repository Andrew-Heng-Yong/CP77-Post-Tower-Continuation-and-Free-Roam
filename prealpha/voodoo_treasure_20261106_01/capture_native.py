"""Regenerate the Voodoo Treasure native device and loot trace from pinned PE bytes."""

import argparse
import json
import struct
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "quest_restoration_qr15/saved_graph_state_01"))
from inspect_native import Image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="native_trace.json")
    args = parser.parse_args()
    output = HERE / args.out
    assert output.parent == HERE and not output.exists()
    image = Image()

    def qword(rva):
        return struct.unpack_from("<Q", image.data, image.off(rva))[0]

    def cstr(rva):
        start = image.off(rva)
        return image.data[start:image.data.index(0, start)].decode("ascii")

    assert cstr(0x307F760) == "controller"
    assert cstr(0x307F8C0) == "GetQuestActionByNameToNative"
    assert cstr(0x3330B38) == "gameDeviceComponentPS"
    assert cstr(0x3315AD0) == "gameeventsReloadLootEvent"
    assert cstr(0x327B948) == "gameILootManager"
    assert cstr(0x3271CB0) == "gameLootManager"
    assert qword(0x36343D8 + 0x1B0) - image.base == 0x408DB4
    assert qword(0x3644630) - image.base == 0x19523C0
    assert qword(0x365AE50 + 0xD8) - image.base == 0xBE7C40
    assert qword(0x307CAC0 + 0x290) - image.base == 0x884090
    assert qword(0x307CAC0 + 0x258) - image.base == 0x1527428
    assert qword(0x30CE310 + 0x1D0) - image.base == 0x218DBF0
    addresses = [
        0x1073750, 0x107389C, 0x8029A0, 0x24D0206, 0x408DB4, 0x21659C0,
        0x409328, 0x173C60C, 0x803200,
        0x1527428, 0x7AF278, 0x7AF3AC, 0x2B3A064, 0x2B39FEC, 0x19523C0, 0x1717DAC,
        0xF05C44, 0x1157F90, 0x11575D8, 0x2AE4DF4, 0x884090, 0x2185270,
        0x162EAE8, 0x16324C0, 0x15DEB3C, 0xBE7C40, 0x218DBF0, 0x218DC06, 0x218DD49,
    ]
    with output.open("x", encoding="utf-8") as stream:
        json.dump({
            "exe_sha256": image.sha, "image_base": hex(image.base),
            "device_component": "controller", "reload_event": "gameeventsReloadLootEvent",
            "functions": [image.disasm(rva) for rva in addresses],
            "scope": "Static pinned PE bytes. Callback execution, inventory results and saved history are separate evidence.",
        }, stream, indent=2)
    print(f"{len(addresses)} native addresses captured")


if __name__ == "__main__":
    main()
