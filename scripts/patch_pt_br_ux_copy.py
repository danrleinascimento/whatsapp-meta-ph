# -*- coding: utf-8 -*-
"""Portuguesizar textos ao usuario (CP1252). Escapes C++: \\\\r\\\\n no source Python."""
from __future__ import annotations

from pathlib import Path


def read(p: Path) -> str:
    return p.read_bytes().decode("cp1252")


def write(p: Path, t: str) -> None:
    t = t.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\r\n")
    p.write_bytes(t.encode("cp1252"))


def must_replace(t: str, old: str, new: str, label: str) -> str:
    if old not in t:
        raise SystemExit(f"missing [{label}]: {old[:80]!r}")
    return t.replace(old, new)


def patch_dfm() -> None:
    p = Path(r"C:\CBuilder5\Projects\GEPH\Princ.dfm")
    t = read(p)
    t = must_replace(
        t,
        "        Caption = 'Status WhatsApp &Meta'\r\n"
        "        Hint = 'Status do agente WHATSPH / Cloud API'\r\n",
        "        Caption = 'Situacao do &WhatsApp'\r\n"
        "        Hint = 'Mostra se a conta WhatsApp do escritorio esta conectada'\r\n",
        "dfm status",
    )
    t = must_replace(
        t,
        "        Caption = '&Painel WHATSPH'\r\n"
        "        Hint = 'Historico de mensagens enviadas (ticket)'\r\n",
        "        Caption = '&Acompanhar envios WhatsApp'\r\n"
        "        Hint = 'Abre o historico de boletos e mensagens enviados'\r\n",
        "dfm painel",
    )
    t = must_replace(
        t,
        "        Caption = 'Conectar WhatsApp &Cloud API'\r\n"
        "        Hint = 'Abre Embedded Signup no hub (WABA do escritorio)'\r\n",
        "        Caption = 'Conectar conta &WhatsApp'\r\n"
        "        Hint = 'Abre o cadastro da conta WhatsApp Business do escritorio'\r\n",
        "dfm conectar",
    )
    write(p, t)
    print("dfm OK")


def patch_ui() -> None:
    p = Path(r"C:\CBuilder5\Projects\Lib\phvcl\WhatsMetaUi.cpp")
    t = read(p)
    # C++ string newlines as \\r\\n in this Python source
    t = t.replace(
        'ShowMensagem("WHATSPH: " + Cli.LastError)',
        'ShowMensagem("WhatsApp: " + Cli.LastError)',
    )
    t = must_replace(
        t,
        '    AnsiString M = "Agente WHATSPH offline ou servico parado.\\r\\n";\r\n'
        '    M += "Verifique o servico PHWhatsMeta e http://127.0.0.1:8765/health";',
        '    AnsiString M = "O servico de envio WhatsApp esta parado ou inacessivel.\\r\\n";\r\n'
        '    M += "Verifique o servico no computador do escritorio (porta 8765).";',
        "ui offline",
    )
    t = must_replace(
        t,
        '    ShowMensagem("WHATSPH: falha ao ler status.\\r\\n" + Cli.LastError);',
        '    ShowMensagem("Nao foi possivel consultar a situacao do WhatsApp.\\r\\n" + Cli.LastError);',
        "ui status fail",
    )
    t = must_replace(
        t,
        '  AnsiString M = "WHATSPH / WhatsApp Meta\\r\\n\\r\\n";\r\n'
        '  M += "Agente: online\\r\\n";\r\n'
        '  M += "Status: " + St + "\\r\\n";\r\n'
        '  M += Conn ? "Conectado: SIM\\r\\n" : "Conectado: NAO\\r\\n";\r\n'
        '  if(!Phone.IsEmpty())\r\n'
        '   M += "Telefone: " + Phone + "\\r\\n";\r\n'
        '  if(!Cli.InstallationId.IsEmpty())\r\n'
        '   M += "Installation: " + Cli.InstallationId + "\\r\\n";\r\n'
        "  ShowMensagem(M);",
        '  AnsiString M = "Situacao do WhatsApp\\r\\n\\r\\n";\r\n'
        '  M += "Servico de envio: em funcionamento\\r\\n";\r\n'
        "  if(Conn)\r\n"
        '   M += "Conta: conectada\\r\\n";\r\n'
        "  else\r\n"
        '   M += "Conta: nao conectada\\r\\n";\r\n'
        "  if(!St.IsEmpty())\r\n"
        "   {\r\n"
        "    AnsiString StPt = St;\r\n"
        '    if(St.UpperCase() == "CONNECTED")\r\n'
        '     StPt = "conectada";\r\n'
        '    else if(St.UpperCase() == "DISCONNECTED")\r\n'
        '     StPt = "desconectada";\r\n'
        '    M += "Detalhe: " + StPt + "\\r\\n";\r\n'
        "   }\r\n"
        "  if(!Phone.IsEmpty())\r\n"
        '   M += "Telefone: " + Phone + "\\r\\n";\r\n'
        "  if(!Cli.InstallationId.IsEmpty())\r\n"
        '   M += "Escritorio: " + Cli.InstallationId + "\\r\\n";\r\n'
        "  ShowMensagem(M);",
        "ui status body",
    )
    t = must_replace(
        t,
        '    ShowMensagem("Agente WHATSPH offline. Nao e possivel abrir o painel.");',
        '    ShowMensagem("O servico de envio WhatsApp esta parado. Nao e possivel abrir o acompanhamento.");',
        "ui painel off",
    )
    t = must_replace(
        t,
        '    ShowMensagem("Falha ao criar ticket do painel.\\r\\n" + Cli.LastError);',
        '    ShowMensagem("Nao foi possivel abrir o acompanhamento de envios.\\r\\n" + Cli.LastError);',
        "ui ticket",
    )
    t = t.replace(
        'ShowMensagem("Nao foi possivel abrir o navegador.\\r\\nURL: " + Url);',
        'ShowMensagem("Nao foi possivel abrir o navegador.\\r\\nEndereco: " + Url);',
    )
    t = must_replace(
        t,
        '  AnsiString Aviso =\r\n'
        '   "Sera aberto o navegador para conectar o WhatsApp Business (Cloud API)\\r\\n"\r\n'
        '   "deste escritorio (installation: " + Inst + ").\\r\\n\\r\\n"\r\n'
        '   "Conclua o Embedded Signup e, se solicitado, informe o pair_code no agente.";\r\n'
        '  if(ShowMensagemBox(Aviso.c_str(), "Conectar WhatsApp Meta",\r\n'
        "   MB_YESNO | MB_DEFBUTTON1) == IDNO)\r\n",
        '  AnsiString Aviso =\r\n'
        '   "Sera aberto o navegador para conectar a conta WhatsApp Business\\r\\n"\r\n'
        '   "deste escritorio (" + Inst + ").\\r\\n\\r\\n"\r\n'
        '   "Conclua o cadastro na pagina. Se aparecer um codigo de vinculacao,\\r\\n"\r\n'
        '   "guarde-o - o servico do escritorio usa esse codigo automaticamente.";\r\n'
        '  if(ShowMensagemBox(Aviso.c_str(), "Conectar conta WhatsApp",\r\n'
        "   MB_YESNO | MB_DEFBUTTON1) == IDNO)\r\n",
        "ui conectar",
    )
    write(p, t)
    print("ui OK")


def patch_preview() -> None:
    p = Path(r"C:\CBuilder5\Projects\Lib\phvcl\Preview.cpp")
    t = read(p)
    t = must_replace(
        t,
        '        Pergunta =\r\n'
        '         "ATENCAO: WhatsApp Meta (Cloud API) esta CONECTADO.\\r\\n\\r\\n"\r\n'
        '         "Confirma envio em grupo dos boletos via Meta?\\r\\n"\r\n'
        '         "Cada boleto sera enviado como PDF pela Cloud API.\\r\\n\\r\\n"\r\n'
        '         "Sim = Meta Cloud API\\r\\n"\r\n'
        '         "Nao = outras opcoes (legado Whats.exe ou envio unitario)";\r\n'
        '        TituloDlg = "WhatsApp Meta";\r\n',
        '        Pergunta =\r\n'
        '         "ATENCAO: A conta WhatsApp do escritorio esta CONECTADA.\\r\\n\\r\\n"\r\n'
        '         "Confirma o envio em grupo dos boletos pelo WhatsApp?\\r\\n"\r\n'
        '         "Cada boleto sera enviado como PDF.\\r\\n\\r\\n"\r\n'
        '         "Sim = enviar pelo WhatsApp oficial\\r\\n"\r\n'
        '         "Nao = outras opcoes (modo antigo ou um boleto por vez)";\r\n'
        '        TituloDlg = "Envio WhatsApp";\r\n',
        "prev dlg1",
    )
    t = must_replace(
        t,
        '        Pergunta =\r\n'
        '         "ATENCAO: Confirma envio em grupo via WhatsApp dos boletos com numero cadastrado?\\r\\n\\r\\n"\r\n'
        '         "(Meta Cloud API indisponivel ou desconectado - fluxo legado Whats.exe)";\r\n'
        '        TituloDlg = "WhatsApp";\r\n',
        '        Pergunta =\r\n'
        '         "ATENCAO: Confirma envio em grupo via WhatsApp dos boletos com numero cadastrado?\\r\\n\\r\\n"\r\n'
        '         "(Conta WhatsApp oficial indisponivel - sera usado o modo antigo)";\r\n'
        '        TituloDlg = "Envio WhatsApp";\r\n',
        "prev dlg2",
    )
    t = must_replace(
        t,
        '        if(ShowMensagemBox(\r\n'
        '         "Usar envio em grupo LEGADO (Whats.exe / FTP)?\\r\\n\\r\\n"\r\n'
        '         "Sim = Whats.exe\\r\\n"\r\n'
        '         "Nao = abrir envio unitario (um PDF, tambem tenta Meta)",\r\n'
        '         "WhatsApp", MB_YESNO | MB_DEFBUTTON2) == IDYES)\r\n',
        '        if(ShowMensagemBox(\r\n'
        '         "Usar o modo antigo de envio em grupo?\\r\\n\\r\\n"\r\n'
        '         "Sim = modo antigo\\r\\n"\r\n'
        '         "Nao = enviar um PDF por vez (WhatsApp oficial, se disponivel)",\r\n'
        '         "Envio WhatsApp", MB_YESNO | MB_DEFBUTTON2) == IDYES)\r\n',
        "prev dlg3",
    )
    t = t.replace(
        'ShowMensagem("WHATSPH: " + Cli.LastError);',
        'ShowMensagem("WhatsApp: " + Cli.LastError);',
    )
    t = t.replace(
        'Em = "Agente offline ou WhatsApp Meta desconectado";',
        'Em = "Servico parado ou conta WhatsApp desconectada";',
    )
    t = t.replace(
        'ShowMensagem("Nao e possivel enviar via Meta.\\r\\n" + Em);',
        'ShowMensagem("Nao e possivel enviar pelo WhatsApp oficial.\\r\\n" + Em);',
    )
    t = t.replace(
        'Log->Add("Envio WhatsApp Meta (Cloud API) em grupo - " +',
        'Log->Add("Envio WhatsApp oficial em grupo - " +',
    )
    t = t.replace(
        'Log->Add("Installation: " + Cli.InstallationId);',
        'Log->Add("Escritorio: " + Cli.InstallationId);',
    )
    t = t.replace('Log->Add("OK Meta boleto "', 'Log->Add("OK boleto "')
    t = t.replace('Log->Add("ERRO Meta codigo "', 'Log->Add("ERRO codigo "')
    t = t.replace('Log->Add("Resumo Meta: OK="', 'Log->Add("Resumo: OK="')
    t = t.replace(
        'AnsiString MensaLog = "WhatsMeta grupo boletos. OK="',
        'AnsiString MensaLog = "WhatsApp grupo boletos. OK="',
    )
    t = t.replace(
        'ShowMensagem("WhatsApp Meta (grupo) finalizado.\\r\\nOK: " + IntToStr(Ok) +',
        'ShowMensagem("Envio WhatsApp em grupo finalizado.\\r\\nConcluidos: " + IntToStr(Ok) +',
    )
    write(p, t)
    print("preview OK")


def patch_senwa() -> None:
    p = Path(r"C:\CBuilder5\Projects\Lib\phvcl\SenWA.cpp")
    t = read(p)
    t = t.replace(
        'OutErro = "Meta Cloud API exige telefone com 11 digitos (DDD+numero).";',
        'OutErro = "Para enviar pelo WhatsApp informe telefone com 11 digitos (DDD+numero).";',
    )
    t = t.replace(
        'OutErro = "Agente WHATSPH offline ou WhatsApp Meta desconectado";',
        'OutErro = "Servico de envio parado ou conta WhatsApp desconectada";',
    )
    t = must_replace(
        t,
        '         ShowMensagem(\r\n'
        '          "WhatsApp Meta esta CONECTADO.\\r\\n"\r\n'
        '          "Informe telefone com 11 digitos (DDD+numero) para enviar via Cloud API.");\r\n',
        '         ShowMensagem(\r\n'
        '          "A conta WhatsApp do escritorio esta conectada.\\r\\n"\r\n'
        '          "Informe o telefone com 11 digitos (DDD+numero) para enviar.");\r\n',
        "senwa tel",
    )
    t = t.replace(
        'ShowMensagem("Relatorio enviado via WhatsApp Meta (Cloud API).");',
        'ShowMensagem("Relatorio enviado pelo WhatsApp.");',
    )
    t = must_replace(
        t,
        '       ShowMensagem(\r\n'
        '        "Falha no envio via WhatsApp Meta.\\r\\n" + ErroMeta +\r\n'
        '        "\\r\\n\\r\\nNao sera usado Whats.exe automaticamente enquanto Meta estiver conectado.");\r\n',
        '       ShowMensagem(\r\n'
        '        "Falha no envio pelo WhatsApp.\\r\\n" + ErroMeta +\r\n'
        '        "\\r\\n\\r\\nEnquanto a conta estiver conectada, o modo antigo nao sera usado automaticamente.");\r\n',
        "senwa fail",
    )
    write(p, t)
    print("senwa OK")


def main() -> int:
    patch_dfm()
    patch_ui()
    patch_preview()
    patch_senwa()
    # sanity: no Cloud API / WHATSPH / ticket / Embedded in user strings of these files
    for path in [
        Path(r"C:\CBuilder5\Projects\GEPH\Princ.dfm"),
        Path(r"C:\CBuilder5\Projects\Lib\phvcl\WhatsMetaUi.cpp"),
    ]:
        t = read(path)
        for bad in ["Cloud API", "WHATSPH", "Embedded Signup", "pair_code", "WABA", "ticket"]:
            # allow comments? Ui.cpp comments may still have WHATSPH - check captions/ShowMensagem only
            pass
    dfm = read(Path(r"C:\CBuilder5\Projects\GEPH\Princ.dfm"))
    assert "Acompanhar envios WhatsApp" in dfm
    assert "Situacao do &WhatsApp" in dfm
    assert "Conectar conta &WhatsApp" in dfm
    assert "Cloud API" not in dfm
    assert "WHATSPH" not in dfm
    ui = read(Path(r"C:\CBuilder5\Projects\Lib\phvcl\WhatsMetaUi.cpp"))
    assert "Situacao do WhatsApp" in ui
    assert "Installation:" not in ui
    assert "Embedded Signup" not in ui
    print("ALL ASSERTS OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
