"""Read exact CR2W sector placements without coercing unsupported worldNode classes."""

import argparse
import hashlib
import json
import struct
from pathlib import Path


HERE = Path(__file__).resolve().parent
SHORT = {
    "#q304_dvc_slider_stash_door",
    "#q304_dvc_slider_stash_terminal",
    "#q304_dvc_slider_stash",
    "#q304_slider_stash_loot",
    "#q304_mp_slider_stash_area",
}
MASK = (1 << 64) - 1


def hash_bytes(data):
    return hashlib.sha256(data).hexdigest().upper()


def read_pinned(path, expected):
    data = Path(path).read_bytes()
    if hash_bytes(data) != expected:
        raise ValueError(f"Input drift: {path}")
    return data


def node_hash(ref):
    result = 0xCBF29CE484222325
    for byte in ref.replace("#", "").encode():
        result = ((result ^ byte) * 0x100000001B3) & MASK
    return result


def vlq(data, pos):
    first = data[pos]
    pos += 1
    value = first & 63
    if first & 64:
        for shift in range(6, 34, 7):
            byte = data[pos]
            pos += 1
            value |= (byte & 127) << shift
            if byte < 128:
                break
        else:
            raise ValueError("Unterminated signed VLQ")
    return (-value if first & 128 else value), pos


class Sector:
    def __init__(self, data):
        if data[:4] != b"CR2W" or struct.unpack_from("<I", data, 4)[0] != 195:
            raise ValueError("Unsupported CR2W header")
        self.data = data
        strings_at, self.strings_size, _ = struct.unpack_from("<III", data, 40)
        self.strings_at = strings_at
        self.names = [self.string(offset) for offset, _ in self.table(1, "<II")]
        self.imports = [self.string(offset) for offset, _, _ in self.table(2, "<IHH")]
        self.exports = self.table(4, "<HHIIIII")
        self.buffers = self.table(5, "<IIIIII")

    def table(self, index, layout):
        offset, count, _ = struct.unpack_from("<III", self.data, 40 + index * 12)
        size = struct.calcsize(layout)
        assert offset + count * size <= len(self.data)
        return list(struct.iter_unpack(layout, self.data[offset:offset + count * size]))

    def string(self, offset):
        start = self.strings_at + offset
        end = self.data.index(0, start, self.strings_at + self.strings_size)
        return self.data[start:end].decode()

    def chunk(self, handle):
        assert 0 < handle <= len(self.exports)
        name, _, _, size, pos, _, _ = self.exports[handle - 1]
        assert 0 < size and pos + size <= len(self.data)
        return self.names[name], self.data[pos:pos + size]

    def properties(self, data):
        assert data[0] == 0
        pos, fields = 1, {}
        while name := struct.unpack_from("<H", data, pos)[0]:
            _, kind, size = struct.unpack_from("<HHI", data, pos)
            assert size >= 4 and pos + 4 + size <= len(data)
            key = self.names[name]
            assert key not in fields
            fields[key] = self.names[kind], data[pos + 8:pos + 4 + size]
            pos += 4 + size
        return fields, pos + 2

    def root(self):
        kind, data = self.chunk(1)
        assert kind == "worldStreamingSector"
        _, pos = self.properties(data)
        version, section_size, buffer = struct.unpack_from("<III", data, pos)
        assert version == 0x44 and pos + 4 + section_size == len(data) and buffer == 0x80000001
        count, pos = vlq(data, pos + 12)
        assert 0 < count < len(self.exports)
        handles = struct.unpack_from(f"<{count}I", data, pos)
        assert all(0 < h <= len(self.exports) for h in handles)
        count, pos = vlq(data, pos + 4 * count)
        assert 0 < count < 100_000
        refs = []
        for _ in range(count):
            length, pos = vlq(data, pos)
            assert -4096 < length < 0 and pos - length <= len(data)
            refs.append(data[pos:pos - length].decode())
            pos -= length
        return handles, refs, data[pos:]

    def bind(self, handle):
        kind, node = self.chunk(handle)
        fields, end = self.properties(node)
        assert end == len(node)
        out = {
            "node_type": kind,
            "export_index": handle - 1,
            "properties": {name: {"type": kind, "hex": raw.hex()} for name, (kind, raw) in fields.items()},
        }
        if "debugName" in fields:
            assert fields["debugName"][0] == "CName"
            out["debug_name"] = self.names[struct.unpack("<H", fields["debugName"][1])[0]]
        if "entityTemplate" in fields:
            assert fields["entityTemplate"][0] == "raRef:entEntityTemplate"
            index, = struct.unpack("<H", fields["entityTemplate"][1])
            assert 0 < index <= len(self.imports)
            out["template"] = self.imports[index - 1]
        if "instanceData" in fields:
            assert fields["instanceData"][0] == "handle:entEntityInstanceData"
            index, = struct.unpack("<I", fields["instanceData"][1])
            instance_kind, instance = self.chunk(index)
            assert instance_kind == "entEntityInstanceData"
            props, end = self.properties(instance)
            assert end == len(instance) and props["buffer"][0] == "DataBuffer"
            pointer, = struct.unpack("<I", props["buffer"][1])
            assert pointer & 0x80000000
            number = pointer & 0x7FFFFFFF
            assert 0 < number <= len(self.buffers)
            out["instance_buffer_number"] = number
        return out


def decode(row):
    raw = read_pinned(row["source"]["captured"], row["source"]["sha256"])
    setups = read_pinned(row["buffer_path"], row["sha256"])
    sector = Sector(raw)
    handles, refs, tail = sector.root()
    _, _, offset, disk_size, size, _ = sector.buffers[0]
    assert (offset, disk_size, size) == (row["offset"], row["disk_size"], row["size"])
    assert len(setups) == size and size % 0x90 == 0
    selected = {node_hash(ref): ref for ref in refs if ref.rsplit("/", 1)[-1] in SHORT}
    assert selected == {int(ref["hash"]): ref["ref"] for ref in row["refs"]}
    matches = []
    for pos in range(0, size, 0x90):
        global_id, proxy_id = struct.unpack_from("<QQ", setups, pos + 0x58)
        packed, = struct.unpack_from("<Q", setups, pos + 0x70)
        index = packed & 0x7FFFF
        assert index < len(handles)
        if global_id in selected:
            matches.append({
                "ref": selected[global_id],
                "global_node_id": str(global_id),
                "proxy_node_id": str(proxy_id),
                "setup_index": pos // 0x90,
                "node_index": index,
                "xyz": struct.unpack_from("<3f", setups, pos),
                **sector.bind(handles[index]),
            })
    assert len({item["ref"] for item in matches}) == len(matches)
    return {
        "source": row["source"],
        "node_count": len(handles),
        "reference_count": len(refs),
        "setup_count": size // 0x90,
        "listed_refs_without_setups": sorted(set(selected.values()) - {m["ref"] for m in matches}),
        "post_refs_tail_hex": tail.hex(),
        "matches": matches,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="bindings_01.json")
    args = parser.parse_args()
    output = HERE / args.out
    assert output.parent == HERE and not output.exists()
    rows = json.loads((HERE / "setups_01/manifest.json").read_text(encoding="utf-8-sig"))
    evidence = [decode(row) for row in rows]
    observed = {m["ref"].rsplit("/", 1)[-1]: m["node_type"] for e in evidence for m in e["matches"]}
    assert observed == {
        "#q304_dvc_slider_stash_door": "worldEntityNode",
        "#q304_dvc_slider_stash_terminal": "worldDeviceNode",
        "#q304_dvc_slider_stash": "worldEntityNode",
        "#q304_slider_stash_loot": "worldEntityNode",
        "#q304_mp_slider_stash_area": "worldTriggerAreaNode",
    }
    with output.open("x", encoding="utf-8") as stream:
        json.dump(evidence, stream, indent=2)
    for item in evidence:
        print(item["source"]["target"]["depot"], item["setup_count"], len(item["matches"]))


if __name__ == "__main__":
    main()
