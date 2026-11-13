#!/usr/bin/env python3
import shutil
import struct
import zlib

RAW_IN = "S34ML04G300Bxx00@BGA63.BIN"
RAW_OUT = "S34ML04G300Bxx00_patched.BIN"

UPDATES = {
    "bootdelay": "5",                     # Allows time to hit a key in U-Boot
    "rokuconsole": "console=ttyS0,115200", # Fixes the disabled serial baud rate
    "rokuloglevel": "loglevel=7",         # Maximizes kernel logging verbosity
    "outputmode": "1080p60hz",            # Sets stable default resolution
    "panel_type": "7",
    "init_display": "run init_display",   # Cleans up the fused/garbled factory string
    "rokusplash": "on",
}

POLY = 0x402B
alpha_to = list(range(16384))
index_of = list(range(16384))
x = 1
for i in range(16383):
    alpha_to[i] = x
    index_of[x] = i
    x <<= 1
    if x & 0x4000:
        x ^= POLY
index_of.__setitem__(0, -1)

g = list((1,))
for i in range(1, 16):
    roots = set()
    r = (2 * i - 1) % 16383
    while r not in roots:
        roots.add(r)
        r = (r * 2) % 16383
    for rt in roots:
        ng = list(range(len(g) + 1))
        for k in range(len(ng)):
            ng[k] = 0
        for j, c in enumerate(g):
            ng[j + 1] ^= c
            if c != 0:
                ng[j] ^= alpha_to[(index_of[c] + rt) % 16383]
        g = ng
    if len(g) - 1 == 112:
        break

GEN = sum((1 << j) for j, c in enumerate(g) if c)
MASK = bytes.fromhex("d82644657f2f2b971b6c533a999e")

def calc_aml_bch8(data512, user2=b"\xff\xff"):
    rem = 0
    for b in data512 + user2:
        for bit in range(8):
            fb = ((rem >> 111) ^ ((b >> (7 - bit)) & 1)) & 1
            rem = (rem << 1) & ((1 << 112) - 1)
            if fb:
                rem ^= GEN
    raw_ecc = bytes((rem >> (112 - 8 * (i + 1))) & 0xFF for i in range(14))
    return bytes(a ^ b for a, b in zip(raw_ecc, MASK))

def main():
    shutil.copyfile(RAW_IN, RAW_OUT)
    with open(RAW_OUT, "r+b") as f:
        env_buf = bytearray()
        for p in range(3712, 3712 + 32):
            f.seek(p * 2176)
            pp = f.read(2176)
            for s in range(4):
                env_buf.extend(pp[s * 528 : s * 528 + 512])

        old_crc = struct.unpack("<I", env_buf[:4])[0]
        assert (zlib.crc32(env_buf[4:0x10000]) & 0xFFFFFFFF) == old_crc, "Initial CRC32 mismatch!"

        entries = []
        seen = set()
        for item in env_buf[4:0x10000].split(b"\x00"):
            if not item:
                break
            k, _, v = item.decode("latin1").partition("=")
            if k in UPDATES:
                if UPDATES[k] is not None:
                    entries.append(f"{k}={UPDATES[k]}".encode("latin1"))
                seen.add(k)
            else:
                entries.append(item)

        for k, v in UPDATES.items():
            if k not in seen and v is not None:
                entries.append(f"{k}={v}".encode("latin1"))

        body = b"\x00".join(entries) + b"\x00\x00"
        assert len(body) <= 0x10000 - 4, "ENV payload exceeds 64 KiB!"
        body = body.ljust(0x10000 - 4, b"\x00")
        new_crc = zlib.crc32(body) & 0xFFFFFFFF
        new_env = struct.pack("<I", new_crc) + body
        print(f"[+] Updated ENV CRC32: {hex(old_crc)} -> {hex(new_crc)}")

        for p_idx in range(32):
            phys_page = 3712 + p_idx
            f.seek(phys_page * 2176)
            pp = bytearray(f.read(2176))
            for s in range(4):
                sec_off = (p_idx * 4 + s) * 512
                d512 = new_env[sec_off : sec_off + 512]
                user2 = bytes(pp[s * 528 + 512 : s * 528 + 514])
                ecc14 = calc_aml_bch8(d512, user2)
                pp[s * 528 : s * 528 + 512] = d512
                pp[s * 528 + 514 : s * 528 + 528] = ecc14
            f.seek(phys_page * 2176)
            f.write(pp)

    print(f"[+] Successfully wrote ECC-verified image: {RAW_OUT}")

if __name__ == "__main__":
    main()
