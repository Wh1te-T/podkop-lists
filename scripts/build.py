#!/usr/bin/env python3
"""
Сборка списков исключений для Podkop из данных lib4u/amnezia-tunneling-ru.

Вход:  temp/amnezia.json, temp/amnezia-ip-lite.json
       custom/*.lst (необязательные ручные правки)
Выход: lists/russia_domains.{lst,json}, lists/russia_subnets.{lst,json}
"""
import ipaddress
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMP = ROOT / "temp"
OUT = ROOT / "lists"
CUSTOM = ROOT / "custom"

MIN_DOMAINS = 1000
MIN_SUBNETS = 200

DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z][a-z0-9-]{0,62}$"
)

JUNK_SUFFIXES = (".arpa", ".local", ".lan", ".internal", ".localdomain",
                 ".localhost", ".invalid", ".example", ".test")
JUNK_EXACT = {"asusrouter.com", "miwifi.com", "hiwifi.com",
              "mcc250.pub.3gppnetwork.org", "instant.arubanetworks.com"}


def read_lst(name):
    path = CUSTOM / name
    if not path.exists():
        return set()
    items = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip().lower()
        if line:
            items.add(line)
    return items


def is_junk(d):
    return d in JUNK_EXACT or d.startswith("localhost.") or d.endswith(JUNK_SUFFIXES)


def collapse_subdomains(domains):
    """Убирает поддомены, если родитель уже в списке (domain_suffix покрывает их)."""
    kept = set()
    for d in sorted(domains, key=lambda x: x.count(".")):
        labels = d.split(".")
        if not any(".".join(labels[i:]) in kept for i in range(1, len(labels))):
            kept.add(d)
    return sorted(kept)


def build_domains():
    data = json.loads((TEMP / "amnezia.json").read_text(encoding="utf-8"))
    raw = {str(i.get("hostname", "")).strip().lower().rstrip(".") for i in data} - {""}

    exclude = read_lst("exclude_domains.lst")
    include = read_lst("include_domains.lst")

    valid = {d for d in raw if DOMAIN_RE.match(d) and not is_junk(d)}
    dropped = len(raw) - len(valid)
    valid |= {d for d in include if DOMAIN_RE.match(d)}
    valid = {d for d in valid
             if d not in exclude and not any(d.endswith("." + e) for e in exclude)}

    domains = collapse_subdomains(valid)
    print(f"Домены: в источнике {len(raw)}, отброшено служебных {dropped}, "
          f"итог после схлопывания поддоменов {len(domains)}")
    return domains


def build_subnets():
    data = json.loads((TEMP / "amnezia-ip-lite.json").read_text(encoding="utf-8"))
    exclude = read_lst("exclude_subnets.lst")
    include = read_lst("include_subnets.lst")

    nets, foreign, bad = set(), 0, 0
    for item in data:
        try:
            net = ipaddress.ip_network(str(item.get("hostname", "")).strip(), strict=False)
        except ValueError:
            bad += 1
            continue
        if net.version != 4 or not net.is_global:
            bad += 1
            continue
        if net.prefixlen > 24:
            foreign += 1
            continue
        nets.add(net)

    for value in include:
        try:
            nets.add(ipaddress.ip_network(value, strict=False))
        except ValueError:
            print(f"  ! некорректная подсеть в include_subnets.lst: {value}")

    excluded = []
    for value in exclude:
        try:
            excluded.append(ipaddress.ip_network(value, strict=False))
        except ValueError:
            pass
    nets = {n for n in nets if not any(n.overlaps(e) for e in excluded)}

    result = [str(n) for n in ipaddress.collapse_addresses(nets)]
    print(f"Подсети: в источнике {len(data)}, отброшено зарубежных/узких {foreign}, "
          f"некорректных {bad}, итог {len(result)}")
    return result


def write(name, items, key):
    (OUT / f"{name}.lst").write_text("\n".join(items) + "\n", encoding="utf-8")
    ruleset = {"version": 3, "rules": [{key: items}]}
    (OUT / f"{name}.json").write_text(
        json.dumps(ruleset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    OUT.mkdir(exist_ok=True)
    domains = build_domains()
    subnets = build_subnets()

    if len(domains) < MIN_DOMAINS or len(subnets) < MIN_SUBNETS:
        print(f"ОШИБКА: подозрительно мало записей (домены {len(domains)}, "
              f"подсети {len(subnets)}). Публикация отменена.", file=sys.stderr)
        sys.exit(1)

    write("russia_domains", domains, "domain_suffix")
    write("russia_subnets", subnets, "ip_cidr")


if __name__ == "__main__":
    main()
