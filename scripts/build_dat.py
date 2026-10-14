#!/usr/bin/env python3

import ipaddress
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LISTS = ROOT / "lists"
CODE = "RU"

DOMAIN_TYPE = {"plain": 0, "keyword": 0, "regexp": 1, "domain": 2, "full": 3}


def varint(n: int) -> bytes:
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


def field_bytes(num: int, data: bytes) -> bytes:
    return varint((num << 3) | 2) + varint(len(data)) + data


def field_varint(num: int, value: int) -> bytes:
    return varint(num << 3) + varint(value)


def read_list(path: Path) -> list[str]:
    seen, out = set(), []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.split("#", 1)[0].strip()
        if s and s not in seen:
            seen.add(s)
            out.append(s)
    return out


def build_site(domains: list[str]) -> bytes:
    body = field_bytes(1, CODE.encode())
    for d in domains:
        kind, _, value = d.partition(":") if ":" in d else ("domain", "", d)
        dtype = DOMAIN_TYPE.get(kind)
        if dtype is None:
            sys.exit(f"неизвестный тип записи: {d}")
        if dtype != 1:
            value = value.lstrip(".").lower()
        dom = (field_varint(1, dtype) if dtype else b"") + field_bytes(2, value.encode())
        body += field_bytes(2, dom)
    return field_bytes(1, body)


def build_ip(subnets: list[str]) -> bytes:
    body = field_bytes(1, CODE.encode())
    for s in subnets:
        try:
            net = ipaddress.ip_network(s, strict=False)
        except ValueError:
            print(f"::warning::пропущена некорректная подсеть: {s}")
            continue
        cidr = field_bytes(1, net.network_address.packed) + field_varint(2, net.prefixlen)
        body += field_bytes(2, cidr)
    return field_bytes(1, body)


def main() -> None:
    domains = read_list(LISTS / "russia_domains.lst")
    subnets = read_list(LISTS / "russia_subnets.lst")
    if len(domains) < 100 or len(subnets) < 50:
        sys.exit("Списки короткие — .dat не обновлен")
    (LISTS / "podkop-ru-site.dat").write_bytes(build_site(domains))
    (LISTS / "podkop-ru-ip.dat").write_bytes(build_ip(subnets))
    print(f"podkop-ru-site.dat: {len(domains)} доменов, podkop-ru-ip.dat: {len(subnets)} подсетей")


if __name__ == "__main__":
    main()
