# -*- coding: utf-8 -*-
"""Patch Preview.cpp / PH.cpp / PH.bpk para WhatsMetaUi (CP1252)."""
from pathlib import Path

PHVCL = Path(r"C:\CBuilder5\Projects\Lib\phvcl")


def load(path: Path) -> str:
    return path.read_text(encoding="cp1252").replace("\r\n", "\n")


def save(path: Path, text: str) -> None:
    path.write_bytes(text.replace("\n", "\r\n").encode("cp1252"))
    print("OK", path.name)


# Preview.cpp
prev = load(PHVCL / "Preview.cpp")
if 'WhatsMetaUi.h' not in prev:
    old = '#include "NavWhats.h"\n'
    new = '#include "NavWhats.h"\n#include "WhatsMetaUi.h"\n'
    if old not in prev:
        raise SystemExit("NavWhats include nao encontrado em Preview.cpp")
    prev = prev.replace(old, new, 1)

marker = "    AtualizaPos();\n}"
insert = (
    "    AtualizaPos();\n"
    "    // Botoes WHATSPH: Status (Meta) e Abrir painel.\n"
    "    WhatsMetaInstalarBotoesPreview(SpeedButton6->Parent, SpeedButton6);\n"
    "}"
)
# FormShow ends with AtualizaPos(); } - first occurrence in FormShow
# Be careful - AtualizaPos appears elsewhere. Use unique FormShow ending context.
unique = (
    "    PageAtual=1;\n"
    "    AjustaZoom(100+((Resolucao-1)*10));\n"
    "    Update();\n"
    "    AtualizaPos();\n"
    "}"
)
unique_new = (
    "    PageAtual=1;\n"
    "    AjustaZoom(100+((Resolucao-1)*10));\n"
    "    Update();\n"
    "    AtualizaPos();\n"
    "    // Botoes WHATSPH: Status (Meta) e Abrir painel.\n"
    "    WhatsMetaInstalarBotoesPreview(SpeedButton6->Parent, SpeedButton6);\n"
    "}"
)
if "WhatsMetaInstalarBotoesPreview" in prev:
    print("Preview.cpp ja tem WhatsMetaInstalarBotoesPreview")
elif unique not in prev:
    raise SystemExit("bloco FormShow final nao encontrado")
else:
    prev = prev.replace(unique, unique_new, 1)
    save(PHVCL / "Preview.cpp", prev)

# PH.cpp
ph = load(PHVCL / "PH.cpp")
if "WhatsMetaUi.cpp" not in ph:
    needle = 'USEUNIT("WhatsMetaClient.cpp");'
    if needle not in ph:
        raise SystemExit("USEUNIT WhatsMetaClient nao encontrado")
    ph = ph.replace(
        needle,
        'USEUNIT("WhatsMetaClient.cpp");\nUSEUNIT("WhatsMetaUi.cpp");',
        1,
    )
    save(PHVCL / "PH.cpp", ph)
else:
    print("PH.cpp ja tem WhatsMetaUi")

# PH.bpk
bpk = Path(r"C:\CBuilder5\Projects\Lib\phvcl\PH.bpk").read_text(encoding="utf-8")
if "WhatsMetaUi.obj" not in bpk:
    bpk2 = bpk.replace(
        "..\\bpl\\WhatsMetaClient.obj",
        "..\\bpl\\WhatsMetaClient.obj ..\\bpl\\WhatsMetaUi.obj",
        1,
    )
    if bpk2 == bpk:
        raise SystemExit("WhatsMetaClient.obj nao encontrado no bpk")
    Path(r"C:\CBuilder5\Projects\Lib\phvcl\PH.bpk").write_text(bpk2, encoding="utf-8", newline="\r\n")
    print("OK PH.bpk")
else:
    print("PH.bpk ja tem WhatsMetaUi.obj")

print("DONE patches")
