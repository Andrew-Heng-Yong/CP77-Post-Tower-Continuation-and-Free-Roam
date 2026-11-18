"""Fit the donor's entry animation to the rooftop chair and check packed transforms."""

import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SEAT = ROOT.parent / "misty_rooftop_seat_20261117_01"
PREVIOUS = ROOT.parent / "misty_rooftop_seat_repair_20261118_01"
BASE = PREVIOUS / "installed_manifest.json"
BASE_HASH = "9374EE66A5D4D83030A732B22AC1C3280EBDF72D9E7793F67BF7D8AB936B53F6"
BEFORE = PREVIOUS / "work/pack_01/packed.scene.json"
PLACEMENT = SEAT / "work/scene_01/manifest.json"
ASSETS = ROOT / "work/pack_01"
DEPOT = r"towercontinued\misty_rooftop_seat\sit.scene"
ARCHIVE = "archive/pc/mod/zzzz_PTFR_Combined.archive"


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest().upper()


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def root(path):
    return read(path)["Data"]["RootChunk"]


def node(scene, number):
    result, = (h["Data"] for h in scene["sceneGraph"]["Data"]["graph"] if h["Data"]["nodeId"]["id"] == number)
    return result


def entry(scene):
    event, = (h["Data"] for h in node(scene, 8)["events"] if h["Data"]["$type"] == "scnPlaySkAnimEvent")
    assert event["rootMotionData"]["placementMode"] == "Blend" and event["rootMotionData"]["enabled"] == 1
    return event["rootMotionData"]


def pose(transform):
    pos, rot = transform["position"], transform["orientation"]
    assert rot["i"] == rot["j"] == 0 and abs(math.hypot(rot["k"], rot["r"]) - 1) < 1e-6
    return complex(pos["X"], pos["Y"]), pos["Z"], complex(rot["r"], rot["k"]) ** 2


def express_in(frame, target):
    return ((target[0] - frame[0]) / frame[2], target[1] - frame[1], target[2] / frame[2])


def compose(frame, local):
    return frame[0] + frame[2] * local[0], frame[1] + local[1], frame[2] * local[2]


def close(left, right):
    assert max(abs(a-b) for a, b in zip(left, right, strict=True)) < 0.0004, (left, right)


def prepare_geometry():
    assert sha(BASE) == BASE_HASH
    assert sha(BEFORE) == "16E8DB0FBD28FD6F97D545A4ADF52F44C05AE0BF3390377A3CF4F5ACC1FB1937"
    assert sha(PLACEMENT) == "D887323DDC0DFCE82F8D9A70847BE2CF370B858737F46BEF95A8ECDD125C9CEF"
    donors = read(SEAT / "work/native_01/providers.json")["hits"]
    chair, = [h for h in donors if h["depot"].endswith(r"\sq028_kerry_villa_sit.scene")]
    assert sha(Path(chair["raw"])) == "360699A5277BF21CCBBC097D325F698A08ED1F4F0EFE3ED049CFDDC5027F9110"
    assert sha(Path(chair["json"])) == chair["json_sha256"]
    native, before, geometry = root(Path(chair["json"])), root(BEFORE), read(PLACEMENT)
    donor_seat, = native["workspotInstances"]
    seat, = before["workspotInstances"]
    assert entry(before) == entry(native)
    assert donor_seat["originMarker"]["nodeRef"]["$value"] == entry(native)["originMarker"]["nodeRef"]["$value"] == "0"
    assert seat["originMarker"]["nodeRef"]["$value"] == geometry["anchor_ref"]
    phase, = [r for r in geometry["resources"] if r["depot"].endswith("gate.questphase")]
    assert sha(Path(phase["json"])) == phase["json_sha256"]
    scene_node, = [h["Data"] for h in root(Path(phase["json"]))["graph"]["Data"]["nodes"] if "sceneFile" in h["Data"]]
    assert scene_node["sceneLocation"]["nodeRef"]["$value"] == geometry["anchor_ref"]
    close(compose(pose(geometry["anchor"]), pose(seat["localTransform"])), pose(geometry["seat"]))
    # The authored chair and entry are in the same scene frame. Preserve the
    # full chair-to-entry translation and rotation in the new chair frame.
    offset = express_in(pose(donor_seat["localTransform"]), pose(entry(native)["originOffset"]))
    aligned = compose(pose(seat["localTransform"]), offset)
    angle = math.atan2(aligned[2].imag, aligned[2].real) / 2
    return {"x": aligned[0].real, "y": aligned[0].imag, "z": aligned[1],
            "k": math.sin(angle), "r": math.cos(angle)}, offset, geometry


def verify_packed():
    _, expected, geometry = prepare_geometry()
    before, after = root(BEFORE), root(ASSETS / "packed.scene.json")
    seated = after["workspotInstances"][0]
    assert seated["originMarker"]["nodeRef"]["$value"] == entry(after)["originMarker"]["nodeRef"]["$value"] == "0"
    motion = entry(after)["originOffset"]
    frame = pose(geometry["anchor"])
    actual_entry = compose(frame, pose(motion))
    chair = compose(frame, pose(seated["localTransform"]))
    close(chair, pose(geometry["seat"]))
    close(express_in(chair, actual_entry), expected)
    assert node(after, 33)["events"][0]["Data"]["rootMotionData"]["placementMode"] == "PlayAtActorPosition"
    assert len(after["resouresReferences"]["gameplayAnimSets"]) == len(after["resouresReferences"]["gameplayAnimNames"]) == 2
    # After checking both edits geometrically, require complete structural equality elsewhere.
    seated["originMarker"]["nodeRef"] = before["workspotInstances"][0]["originMarker"]["nodeRef"]
    entry(after)["originOffset"] = entry(before)["originOffset"]
    assert before == after
    print("Verified chair-relative entry, seated and exit placement, both animation sets and the full scene diff.")


if __name__ == "__main__":
    import sys
    if sys.argv[1:] == ["--geometry"]:
        print(json.dumps(prepare_geometry()[0]))
    elif not sys.argv[1:]:
        verify_packed()
    else:
        raise SystemExit("Use --geometry or no arguments")
