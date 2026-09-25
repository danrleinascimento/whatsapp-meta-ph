# -*- coding: utf-8 -*-
"""Auditoria criteriosa PHVCL SendDocument + resumo Meta."""
from __future__ import annotations

import re
from pathlib import Path


def read(p: str) -> str:
    return Path(p).read_bytes().decode("cp1252").replace("\r\n", "\n")


def main() -> int:
    h = read(r"C:\CBuilder5\Projects\Lib\phvcl\WhatsMetaClient.h")
    c = read(r"C:\CBuilder5\Projects\Lib\phvcl\WhatsMetaClient.cpp")
    p = read(r"C:\CBuilder5\Projects\Lib\phvcl\Preview.cpp")
    s = read(r"C:\CBuilder5\Projects\Lib\phvcl\SenWA.cpp")
    errors: list[str] = []
    oks: list[str] = []

    def check(cond: bool, msg: str) -> None:
        (oks if cond else errors).append(msg)

    # Header
    check("AnsiString LastWarning;" in h, "h LastWarning")
    mh = re.search(r"bool SendDocument\((.*?)\);", h, re.S)
    ph = [x.strip() for x in mh.group(1).split(",")] if mh else []
    check(len(ph) == 7 and "BodyName" in ph[-1], f"h 7 params BodyName ({ph})")

    # Cpp
    mc = re.search(r"bool TWhatsMetaClient::SendDocument\((.*?)\)\n\{", c, re.S)
    pc = [x.strip() for x in mc.group(1).split(",")] if mc else []
    check(len(pc) == 7 and "BodyName" in pc[-1], f"cpp 7 params ({pc})")
    check("body_name" in c, "cpp JSON body_name")
    check('JsonStringValue(R, "warning")' in c, "cpp parse warning")
    check("LastWarning = \"\";" in c, "cpp clear LastWarning")
    ctor = c[c.find("TWhatsMetaClient::TWhatsMetaClient()") : c.find("TWhatsMetaClient::TWhatsMetaClient()") + 350]
    check("LastWarning = \"\";" in ctor, "cpp ctor LastWarning")

    # Preview Meta path
    i0 = p.find("bool TPreview1::enviarWhatsGrupoBoletosMeta")
    i1 = p.find("bool TPreview1::enviarWhatsGrupoBoletos(void)")
    meta = p[i0:i1] if i0 >= 0 and i1 > i0 else ""
    check(bool(meta), "preview Meta function found")
    mcall = re.search(r"Cli\.SendDocument\(\s*(.*?)\s*\)", meta, re.S)
    args = [a.strip() for a in mcall.group(1).split(",")] if mcall else []
    check(len(args) == 7, f"preview Meta args={args}")
    check(args and args[-1] == "Nome", "preview last arg Nome")
    check("AVISO Meta:" in meta, "preview AVISO Meta in Meta path")
    check("Aceitos pela Meta:" in meta, "preview Aceitos pela Meta")
    check("Acompanhar envios" in meta, "preview Acompanhar envios")
    check("Enviados com sucesso" not in meta, "preview no Enviados com sucesso in Meta")

    # SenWA
    scall = re.search(r"Cli\.SendDocument\(\s*(.*?)\s*\)", s, re.S)
    sargs = [a.strip() for a in scall.group(1).split(",")] if scall else []
    check(len(sargs) == 7, f"SenWA args={sargs}")
    check(sargs and sargs[-1] == '""', "SenWA empty BodyName")

    # All SendDocument calls must be 7-arg
    for label, text in (("Preview", p), ("SenWA", s)):
        for m in re.finditer(r"SendDocument\(\s*(.*?)\s*\)", text, re.S):
            a = [x.strip() for x in m.group(1).split(",") if x.strip() != ""]
            # split by comma is wrong for nested - but our calls have no nested commas
            a = [x.strip() for x in m.group(1).split(",")]
            if len(a) != 7:
                errors.append(f"{label} SendDocument argc={len(a)}")

    print("OK:")
    for x in oks:
        print(" ", x)
    print("FAIL:")
    for x in errors:
        print(" ", x)
    print(f"summary {len(oks)} ok / {len(errors)} fail")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
