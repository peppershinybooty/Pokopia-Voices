#!/usr/bin/env python3
"""Fix the chunk tags and checksums in a Pokopia .fdata archive after replacing sound banks.

Every compressed IDRK entry in a .fdata is checked by the game when it loads:

  - each zlib chunk starts with a u16 size and an 8-byte tag, a checksum of the chunk's compressed bytes
  - the 4 bytes right after the 0x30-byte entry header are a CRC32 of the entry's whole compressed block

If you swap in new audio but keep the old values (which is what happens when you reuse the game's chunk
headers), the game sometimes hangs on a black screen after the save loads. It's random because it depends
on what gets loaded first, so a build can look fine for a while.

This walks every entry in the file and rewrites both values in place. Entries that are already correct
(all of the game's own) come out byte-for-byte the same, so it's safe to run on the whole archive.

    python3 fix_fdata_checks.py path/to/0x05d525ae.fdata

Run it on the modded archive before turning it into a .pkmod. root.rdb doesn't need any changes.

The tag algorithm is the one documented in eArmada8's yumia_fdata_tools (Atelier Yumia uses the same
archive format). It matches every one of the 132,998 chunks in Pokopia's own sound archive.
"""
import struct
import sys
import zlib

SEEDS = struct.unpack("<32Q", bytes.fromhex(
    "d0976d0204710db3f564b89d4faf15d97786d3ff495737578ee2066fa7a26a5a"
    "40f55496ed8b85ef33571d405a987947faf12fa86af7682d0a96a7ff5666ff73"
    "4321221e77914caaf3c8bb18416f2111aad75d6c1cb92c555c09be2a6057c0bd"
    "a4c6a44026d4afa6850c498e70fa2475243f03ea4ee28750dbdffe2179647ecd"
    "9741fac8fa38997d0ddf42cf383bcba649c292e87ceac0f0a58c0bc297f25fa1"
    "151c5bab14000fa0305490a7d7d98ea68e06903172b6ccf4ec4df696897f8d9a"
    "836926573a207a855ca7ba81dbe1a87eee0fd5be99dbf9e0a7d905e50990cb96"
    "7d870d7e3ed1e7841fb57880caaab3b1acdfc5ebe8e864aae98391f1fa3986e7"))


def chunk_tag(z):
    n = len(z)
    seed = SEEDS[n & 31]
    word = lambda o: struct.unpack_from("<Q", z, o)[0]
    if n < 16:
        length = n & ~7
        start = n ^ seed if n < 8 else (seed ^ word(0)) % n
    else:
        length = min((seed ^ word(8)) & 31, n) & ~7
        start = (seed ^ word(0)) % n
    start &= ~7
    if start + length > n:
        start = 0
    h = seed
    for i in range(start, start + length, 8):
        h = (h + word(i)) & 0xFFFFFFFFFFFFFFFF
    return struct.pack("<Q", h)


def fix(path):
    data = bytearray(open(path, "rb").read())
    entries = changed = 0
    at = data.find(b"IDRK0000")
    while at >= 0:
        esz, csz, usz = struct.unpack_from("<QQQ", data, at + 8)
        if 0 < csz < esz and csz != usz and at + esz <= len(data):
            start = at + esz - csz
            p = start
            while True:
                (n,) = struct.unpack_from("<H", data, p)
                if n == 0:
                    break
                tag = chunk_tag(bytes(data[p + 10:p + 10 + n]))
                if data[p + 2:p + 10] != tag:
                    data[p + 2:p + 10] = tag
                    changed += 1
                p += 10 + n
            crc = struct.pack("<I", zlib.crc32(data[start:at + esz]))
            if data[at + 0x30:at + 0x34] != crc:
                data[at + 0x30:at + 0x34] = crc
                changed += 1
            entries += 1
            at = data.find(b"IDRK0000", at + esz)
        else:
            at = data.find(b"IDRK0000", at + 8)
    if changed:
        open(path, "wb").write(data)
    print(f"{path}: {entries} entries checked, {changed} values fixed")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for p in sys.argv[1:]:
        fix(p)
