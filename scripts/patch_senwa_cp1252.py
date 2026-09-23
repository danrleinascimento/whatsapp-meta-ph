# -*- coding: utf-8 -*-
"""Aplica patch WhatsMeta em SenWA.cpp preservando CP1252."""
from pathlib import Path

path = Path(r"C:\CBuilder5\Projects\Lib\phvcl\SenWA.cpp")
text = path.read_text(encoding="cp1252")

inc_old = (
    '#include "DMLog1.h"\r\n'
    "//---------------------------------------------------------------------------\r\n"
    "#pragma package(smart_init)\r\n"
    '#pragma resource "*.dfm"\r\n'
    "TSendWA1 *SendWA1;\r\n"
    "//---------------------------------------------------------------------------\r\n"
    "__fastcall TSendWA1::TSendWA1(TComponent* Owner)\r\n"
)
if inc_old not in text:
    inc_old = inc_old.replace("\r\n", "\n")
    text_nl = "\n"
else:
    text_nl = "\r\n"

helper = (
    '#include "DMLog1.h"\n'
    '#include "WhatsMetaClient.h"\n'
    "//---------------------------------------------------------------------------\n"
    "#pragma package(smart_init)\n"
    '#pragma resource "*.dfm"\n'
    "TSendWA1 *SendWA1;\n"
    "//---------------------------------------------------------------------------\n"
    "static bool enviarViaWhatsMeta(\n"
    "  AnsiString ArqPdf,\n"
    "  AnsiString Telefone11,\n"
    "  AnsiString Caption,\n"
    "  AnsiString &OutErro\n"
    ")\n"
    "{\n"
    '  OutErro = "";\n'
    "  if(Telefone11.Trim().Length() != 11)\n"
    "   {\n"
    '    OutErro = "Meta Cloud API exige telefone com 11 digitos (DDD+numero).";\n'
    "    return false;\n"
    "   }\n"
    "  TWhatsMetaClient Cli;\n"
    "  if(!Cli.LoadFromWhatsPhEnv(vg.DiretorioPrincipal))\n"
    "   {\n"
    '    if(!Cli.LoadFromWhatsPhEnv("C:\\\\PHSFTW"))\n'
    "     {\n"
    "      OutErro = Cli.LastError;\n"
    "      return false;\n"
    "     }\n"
    "   }\n"
    "  if(!Cli.HealthOk() || !Cli.IsConnected())\n"
    "   {\n"
    "    OutErro = Cli.LastError;\n"
    "    if(OutErro.IsEmpty())\n"
    '     OutErro = "Agente WHATSPH offline ou WhatsApp Meta desconectado";\n'
    "    return false;\n"
    "   }\n"
    '  AnsiString ToPhone = "55" + Telefone11.Trim();\n'
    "  if(Cli.SendDocument(\n"
    "       ToPhone,\n"
    "       ArqPdf,\n"
    "       Caption,\n"
    "       vg.NomeUsuario,\n"
    "       vg.DiretorioPrincipal,\n"
    "       vg.DiretorioSecundario))\n"
    "   return true;\n"
    "  OutErro = Cli.LastError;\n"
    "  return false;\n"
    "}\n"
    "//---------------------------------------------------------------------------\n"
    "__fastcall TSendWA1::TSendWA1(TComponent* Owner)\n"
)

# normalize working text to \n for replace, then write CRLF CP1252
work = text.replace("\r\n", "\n")
inc_old_n = (
    '#include "DMLog1.h"\n'
    "//---------------------------------------------------------------------------\n"
    "#pragma package(smart_init)\n"
    '#pragma resource "*.dfm"\n'
    "TSendWA1 *SendWA1;\n"
    "//---------------------------------------------------------------------------\n"
    "__fastcall TSendWA1::TSendWA1(TComponent* Owner)\n"
)
if inc_old_n not in work:
    raise SystemExit("bloco include nao encontrado em SenWA.cpp")
work = work.replace(inc_old_n, helper, 1)

marker = "Abort();\n\n    TCursor SCursor=Screen->Cursor;"
insert = (
    "Abort();\n"
    "\n"
    "    // Preferencia: Cloud API via agente WHATSPH (se CONECTADO).\n"
    "    // Fallback: fluxo legado FTP + Whats.exe abaixo.\n"
    "    {\n"
    "     AnsiString ErroMeta;\n"
    "     AnsiString CapMeta = Edit1->Text.Trim();\n"
    "     if(CapMeta.IsEmpty())\n"
    "      CapMeta = NomeRelatorio;\n"
    "     if(enviarViaWhatsMeta(ArqRelatorio, MaskEdit1->Text.Trim(), CapMeta, ErroMeta))\n"
    "      {\n"
    '       AnsiString MensaLog = "WhatsMeta Cloud API OK\\r\\nRelatorio: " + NomeRelatorio + "\\r\\n";\n'
    '       MensaLog += "Telefone: " + MaskEdit1->Text.Trim() + "\\r\\n";\n'
    '       vg.IncluiLog(NULL,0,"99999018",MensaLog);\n'
    '       ShowMensagem("Relatorio enviado via WhatsApp Meta (Cloud API).");\n'
    "       Close();\n"
    "       return;\n"
    "      }\n"
    "    }\n"
    "\n"
    "    TCursor SCursor=Screen->Cursor;"
)
if marker not in work:
    raise SystemExit("marker Abort/TCursor nao encontrado")
work = work.replace(marker, insert, 1)

out = work.replace("\n", "\r\n")
path.write_bytes(out.encode("cp1252"))
raw = path.read_bytes()
print("OK SenWA.cpp CP1252 non_ascii=", sum(1 for b in raw if b > 127), "WhatsMeta=", b"WhatsMetaClient" in raw)
