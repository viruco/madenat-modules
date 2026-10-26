#!/usr/bin/env python3
"""Test the exact regex from madenat_guia_processing.py against sample inputs."""
import re
import sys

# Line 1931 from madenat_guia_processing.py (on disk, updated)
regex_new = r'((?:MC|OC|Orden)\s*[:.\-]?\s*[A-Z0-9]+(?:[\s\-][A-Z0-9]+)+)'

# Line 1922 from the ORIGINAL code (before Fase 2B fix)
regex_old = r'(?:MC|OC|Orden)[\s\.\-:]*([A-Z0-9]+(?:\s*[-]\s*[A-Z0-9]+)+)'

tests = [
    'MC 2506-01',
    'mc 2506-01',
    'MC-2506-01',
    'OC 2506-01',
    'MC 0708-236',
    'Orden 80123456',
    '2506-01',
    'Nº OC: MC 2506-01',
]

print("=" * 70)
print("OLD regex: r'(?:MC|OC|Orden)[\s\.\-:]*([A-Z0-9]+(?:\s*[-]\s*[A-Z0-9]+)+)'")
print("           (non-capturing MC/OC/Orden — LOSES the prefix)")
print("=" * 70)
for t in tests:
    m = re.search(regex_old, t, re.I)
    if m:
        # group(1) only captures the digits part
        print(f"  IN: {t!r:24s} => group(0)={m.group(0)!r:20s} group(1)={m.group(1)!r}")
    else:
        print(f"  IN: {t!r:24s} => NO MATCH")

print()
print("=" * 70)
print("NEW regex: r'((?:MC|OC|Orden)\s*[:.\-]?\s*[A-Z0-9]+(?:[\s\-][A-Z0-9]+)+)'")
print("           (capturing group wraps the whole match INCLUDING MC/OC)")
print("=" * 70)
for t in tests:
    m = re.search(regex_new, t, re.I)
    if m:
        raw = m.group(1).strip()
        canon = re.sub(r'\s+', ' ', raw)
        print(f"  IN: {t!r:24s} => group(0)={m.group(0)!r:20s} group(1)={canon!r}")
    else:
        print(f"  IN: {t!r:24s} => NO MATCH")

print()
print("CONCLUSION: OLD regex loses MC/OC prefix, NEW regex preserves it.")
print("The module UPGRADE must be run for changes to take effect in Odoo.")