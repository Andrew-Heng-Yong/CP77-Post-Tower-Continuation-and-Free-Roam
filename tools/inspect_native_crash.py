"""Read only exception registers/module offsets from a local AMD64 minidump.

Layouts: Microsoft MINIDUMP_EXCEPTION_STREAM, MINIDUMP_MODULE and AMD64 CONTEXT.
No memory strings or user/save data are exported. Stack words matching module
addresses are candidates, not an unwound/symbolized call stack.
"""
import argparse
import json
import mmap
from pathlib import Path
import struct
import sys


class Dump:
    def __init__(self, path):
        self.file = open(path, "rb")
        self.data = mmap.mmap(self.file.fileno(), 0, access=mmap.ACCESS_READ)
        assert self.data[:4] == b"MDMP"
        count, directory = self.unpack("II", 8)
        self.streams = {}
        for i in range(count):
            kind, size, offset = self.unpack("III", directory + i * 12)
            assert offset + size <= len(self.data)
            self.streams[kind] = (offset, size)
        p, _ = self.streams[4]
        self.modules = []
        for i in range(self.unpack("I", p)[0]):
            base, size, _, _, name = self.unpack("QIIII", p + 4 + i * 108)
            n = self.unpack("I", name)[0]
            label = self.data[name + 4:name + 4 + n].decode("utf-16-le").replace("\\", "/").rsplit("/", 1)[-1]
            self.modules.append((base, size, label))
        self.memory = []
        if 5 in self.streams:
            p, _ = self.streams[5]
            for i in range(self.unpack("I", p)[0]):
                address, size, offset = self.unpack("QII", p + 4 + i * 16)
                self.memory.append((address, size, offset))
        if 9 in self.streams:
            p, _ = self.streams[9]
            count, offset = self.unpack("QQ", p)
            for i in range(count):
                address, size = self.unpack("QQ", p + 16 + i * 16)
                self.memory.append((address, size, offset))
                offset += size

    def unpack(self, fmt, offset):
        return struct.unpack_from("<" + fmt, self.data, offset)

    def module(self, address):
        for base, size, name in self.modules:
            if base <= address < base + size:
                return f"{name}+0x{address-base:x}"
        return None

    def read(self, address, size):
        for base, length, offset in self.memory:
            if base <= address and address + size <= base + length:
                return self.data[offset + address - base:offset + address - base + size]
        return None

    def report(self):
        p, _ = self.streams[6]
        thread, = self.unpack("I", p)
        code, _, _, address, count = self.unpack("IIQQI", p + 8)
        info = self.unpack("Q" * min(count, 15), p + 40)
        size, context = self.unpack("II", p + 160)
        assert size >= 256 and self.unpack("I", context + 48)[0] & 0x100000
        names = "rax rcx rdx rbx rsp rbp rsi rdi r8 r9 r10 r11 r12 r13 r14 r15 rip".split()
        registers = dict(zip(names, self.unpack("Q" * 17, context + 120)))
        assert registers["rip"] == address
        candidates = []
        for offset in range(0, 512, 8):
            word = self.read(registers["rsp"] + offset, 8)
            if word:
                label = self.module(struct.unpack("<Q", word)[0])
                if label:
                    candidates.append({"stack_offset": hex(offset), "module_address": label})
        return {"thread": thread, "code": hex(code), "exception_parameters": [hex(v) for v in info],
                "fault": self.module(address), "registers": {n: hex(v) for n, v in registers.items()},
                "stack_candidates_not_unwound": candidates}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dump", type=Path)
    ap.add_argument("--exe", type=Path)
    ap.add_argument("--libraries", type=Path)
    args = ap.parse_args()
    dump = Dump(args.dump)
    result = dump.report()
    if args.exe:
        if args.libraries:
            sys.path.insert(0, str(args.libraries))
        import capstone
        import pefile
        base = next(b for b, _, n in dump.modules if n.lower() == args.exe.name.lower())
        rip = int(result["registers"]["rip"], 16)
        pe = pefile.PE(str(args.exe), fast_load=True)
        code = pe.get_data(rip - base, 48)
        decoder = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
        result["fault_disassembly"] = [f"+0x{i.address:x}: {i.mnemonic} {i.op_str}" for i in decoder.disasm(code, rip-base)]
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
