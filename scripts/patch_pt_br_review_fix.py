# -*- coding: utf-8 -*-
"""Fix remaining user-facing strings (CP1252 accents + softer errors)."""
from __future__ import annotations

from pathlib import Path


def read(p: Path) -> str:
    return p.read_bytes().decode("cp1252")


def write(p: Path, t: str) -> None:
    t = t.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\r\n")
    Path(p).write_bytes(t.encode("cp1252"))


def main() -> int:
    # --- Client ---
    p = Path(r"C:\CBuilder5\Projects\Lib\phvcl\WhatsMetaClient.cpp")
    t = read(p)
    reps = [
        (
            'LastError = "PHSFTW root vazio";',
            'LastError = "Pasta do sistema nao informada.";',
        ),
        (
            'LastError = "PH_API_KEY ausente em: " + EnvPath;',
            'LastError = "Configuracao do WhatsApp incompleta neste computador.";',
        ),
        (
            'LastError = "WHATSPH\\.env nao encontrado (C:\\PHSFTW ou D:\\PHSFTW)";',
            'LastError = "Configuracao do WhatsApp nao encontrada neste computador.";',
        ),
        (
            'LastError = "Resposta vazia do agente WHATSPH";',
            'LastError = "O servico de envio WhatsApp nao respondeu.";',
        ),
        (
            'LastError = "panel_url ausente na resposta";',
            'LastError = "Nao foi possivel montar o acompanhamento de envios.";',
        ),
    ]
    # Also old FileExists message if still present
    if 'LastError = "Arquivo nao encontrado: "' in t:
        t = t.replace(
            'LastError = "Arquivo nao encontrado: " + EnvPath;',
            'LastError = "Configuracao do WhatsApp nao encontrada neste computador.";',
        )
    for old, new in reps:
        if old not in t:
            print("WARN missing:", old[:60])
        else:
            t = t.replace(old, new)
            print("OK", new[:50])
    write(p, t)

    # --- Dfm accents ---
    dfm = Path(r"C:\CBuilder5\Projects\GEPH\Princ.dfm")
    d = read(dfm)
    # Build with real cp1252 chars via unicode then encode
    old = (
        "        Caption = 'Situacao do &WhatsApp'\r\n"
        "        Hint = 'Mostra se a conta WhatsApp do escritorio esta conectada'\r\n"
    )
    new = (
        "        Caption = 'Situação do &WhatsApp'\r\n"
        "        Hint = 'Mostra se a conta WhatsApp do escritório está conectada'\r\n"
    )
    if old not in d:
        raise SystemExit("dfm status block missing")
    d = d.replace(old, new)
    old = (
        "        Caption = '&Acompanhar envios WhatsApp'\r\n"
        "        Hint = 'Abre o historico de boletos e mensagens enviados'\r\n"
    )
    new = (
        "        Caption = '&Acompanhar envios WhatsApp'\r\n"
        "        Hint = 'Abre o histórico de boletos e mensagens enviados'\r\n"
    )
    d = d.replace(old, new)
    write(dfm, d)
    print("dfm accents OK")

    # --- Ui: softer offline + no redundant Detalhe ---
    ui = Path(r"C:\CBuilder5\Projects\Lib\phvcl\WhatsMetaUi.cpp")
    u = read(ui)
    u = u.replace(
        '    M += "Verifique o servico no computador do escritorio (porta 8765).";',
        '    M += "Verifique se o programa de envio WhatsApp esta em execucao neste computador.";',
    )
    old = (
        '  if(!St.IsEmpty())\r\n'
        '   {\r\n'
        '    AnsiString StPt = St;\r\n'
        '    if(St.UpperCase() == "CONNECTED")\r\n'
        '     StPt = "conectada";\r\n'
        '    else if(St.UpperCase() == "DISCONNECTED")\r\n'
        '     StPt = "desconectada";\r\n'
        '    M += "Detalhe: " + StPt + "\\r\\n";\r\n'
        '   }\r\n'
    )
    new = (
        '  if(!St.IsEmpty() && St.UpperCase() != "CONNECTED" && St.UpperCase() != "DISCONNECTED")\r\n'
        '   M += "Detalhe: " + St + "\\r\\n";\r\n'
    )
    if old not in u:
        raise SystemExit("ui detalhe block missing")
    u = u.replace(old, new)
    write(ui, u)
    print("ui OK")

    # --- Preview summary labels ---
    prev = Path(r"C:\CBuilder5\Projects\Lib\phvcl\Preview.cpp")
    pr = read(prev)
    pr = pr.replace(
        'ShowMensagem("Envio WhatsApp em grupo finalizado.\\r\\nConcluidos: " + IntToStr(Ok) +\r\n'
        '     "\\r\\nErro: " + IntToStr(Erro) + "\\r\\nPulados: " + IntToStr(Pulados));',
        'ShowMensagem("Envio WhatsApp em grupo finalizado.\\r\\nEnviados com sucesso: " + IntToStr(Ok) +\r\n'
        '     "\\r\\nCom falha: " + IntToStr(Erro) + "\\r\\nIgnorados: " + IntToStr(Pulados));',
    )
    write(prev, pr)
    print("preview summary OK")

    # verify
    c = read(p)
    assert "WHATSPH" not in c or "WHATSPH\\.env" in c  # path candidates may remain
    # LastError lines must not have WHATSPH/PH_API_KEY/panel_url
    for line in c.splitlines():
        if "LastError" in line and (
            "WHATSPH" in line or "PH_API_KEY" in line or "panel_url" in line
        ):
            raise SystemExit("bad LastError: " + line)
    d2 = read(dfm)
    assert "Situação do &WhatsApp" in d2
    assert "escritório" in d2
    assert "histórico" in d2
    print("ALL OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
