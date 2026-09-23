# -*- coding: utf-8 -*-
from pathlib import Path

# PH.cpp: add USEUNIT WhatsMetaClient before SenWA form
p = Path(r"C:\CBuilder5\Projects\Lib\phvcl\PH.cpp")
t = p.read_text(encoding="cp1252").replace("\r\n", "\n")
needle = 'USEFORM("SenWA.cpp", SendWA1);'
add = 'USEUNIT("WhatsMetaClient.cpp");\nUSEFORM("SenWA.cpp", SendWA1);'
if "WhatsMetaClient.cpp" in t:
    print("PH.cpp already has WhatsMetaClient")
elif needle not in t:
    raise SystemExit("USEFORM SenWA nao encontrado")
else:
    t = t.replace(needle, add, 1)
    p.write_bytes(t.replace("\n", "\r\n").encode("cp1252"))
    print("PH.cpp USEUNIT added")

# PH.bpk: add obj to OBJFILES
bpk = Path(r"C:\CBuilder5\Projects\Lib\phvcl\PH.bpk")
b = bpk.read_text(encoding="utf-8")
if "WhatsMetaClient.obj" in b:
    print("PH.bpk already has WhatsMetaClient.obj")
else:
    b2 = b.replace("..\\bpl\\SenWA.obj", "..\\bpl\\WhatsMetaClient.obj ..\\bpl\\SenWA.obj", 1)
    if b2 == b:
        raise SystemExit("SenWA.obj nao encontrado no bpk")
    bpk.write_text(b2, encoding="utf-8", newline="\r\n")
    print("PH.bpk OBJFILES updated")
