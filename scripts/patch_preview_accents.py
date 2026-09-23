# -*- coding: utf-8 -*-
from pathlib import Path


def read_cp(p):
    return Path(p).read_bytes().decode("cp1252").replace("\r\n", "\n").replace("\r", "\n")


def write_cp(p, t):
    Path(p).write_bytes(t.replace("\n", "\r\n").encode("cp1252"))


def main():
    prev = Path(r"C:\CBuilder5\Projects\Lib\phvcl\Preview.cpp")
    p = read_cp(prev)
    reps = [
        (
            '        Pergunta =\n'
            '         "ATENCAO: A conta WhatsApp do escritorio esta CONECTADA.\\r\\n\\r\\n"\n'
            '         "Confirma o envio em grupo dos boletos pelo WhatsApp?\\r\\n"\n'
            '         "Cada boleto sera enviado como PDF.\\r\\n\\r\\n"\n'
            '         "Sim = enviar pelo WhatsApp oficial\\r\\n"\n'
            '         "Nao = outras opcoes (modo antigo ou um boleto por vez)";',
            '        Pergunta =\n'
            '         "ATENÇÃO: A conta WhatsApp do escritório está CONECTADA.\\r\\n\\r\\n"\n'
            '         "Confirma o envio em grupo dos boletos pelo WhatsApp?\\r\\n"\n'
            '         "Cada boleto será enviado como PDF.\\r\\n\\r\\n"\n'
            '         "Sim = enviar pelo WhatsApp oficial\\r\\n"\n'
            '         "Não = outras opções (modo antigo ou um boleto por vez)";',
        ),
        (
            '        Pergunta =\n'
            '         "ATENCAO: Confirma envio em grupo via WhatsApp dos boletos com numero cadastrado?\\r\\n\\r\\n"\n'
            '         "(Conta WhatsApp oficial indisponivel - sera usado o modo antigo)";',
            '        Pergunta =\n'
            '         "ATENÇÃO: Confirma envio em grupo via WhatsApp dos boletos com número cadastrado?\\r\\n\\r\\n"\n'
            '         "(Conta WhatsApp oficial indisponível - será usado o modo antigo)";',
        ),
        (
            '        if(ShowMensagemBox(\n'
            '         "Usar o modo antigo de envio em grupo?\\r\\n\\r\\n"\n'
            '         "Sim = modo antigo\\r\\n"\n'
            '         "Nao = enviar um PDF por vez (WhatsApp oficial, se disponivel)",\n'
            '         "Envio WhatsApp", MB_YESNO | MB_DEFBUTTON2) == IDYES)',
            '        if(ShowMensagemBox(\n'
            '         "Usar o modo antigo de envio em grupo?\\r\\n\\r\\n"\n'
            '         "Sim = modo antigo\\r\\n"\n'
            '         "Não = enviar um PDF por vez (WhatsApp oficial, se disponível)",\n'
            '         "Envio WhatsApp", MB_YESNO | MB_DEFBUTTON2) == IDYES)',
        ),
        (
            'Em = "Servico parado ou conta WhatsApp desconectada";',
            'Em = "Serviço parado ou conta WhatsApp desconectada.";',
        ),
        (
            'ShowMensagem("Nao e possivel enviar pelo WhatsApp oficial.\\r\\n" + Em);',
            'ShowMensagem("Não é possível enviar pelo WhatsApp oficial.\\r\\n" + Em);',
        ),
        (
            '    Log->Add("Relatorio: " + PHR->Report->Titulo);\n'
            '    Log->Add("Escritorio: " + Cli.InstallationId);',
            '    Log->Add("Relatório: " + PHR->Report->Titulo);\n'
            '    Log->Add("Escritório: " + Cli.InstallationId);',
        ),
    ]
    for i, (old, new) in enumerate(reps):
        if old not in p:
            if new in p:
                print("ALREADY", i)
                continue
            raise SystemExit(f"MISSING {i}: {old[:90]!r}")
        p = p.replace(old, new)
        print("OK", i)
    write_cp(prev, p)

    dfm = Path(r"C:\CBuilder5\Projects\GEPH\Princ.dfm")
    d = read_cp(dfm)
    old = "Hint = 'Abre o cadastro da conta WhatsApp Business do escritorio'"
    new = "Hint = 'Abre o cadastro da conta WhatsApp Business do escritório'"
    if old in d:
        d = d.replace(old, new)
        write_cp(dfm, d)
        print("dfm OK")
    else:
        print("dfm skip/already")

    # sanity
    ui = read_cp(r"C:\CBuilder5\Projects\Lib\phvcl\WhatsMetaUi.cpp")
    sen = read_cp(r"C:\CBuilder5\Projects\Lib\phvcl\SenWA.cpp")
    cli = read_cp(r"C:\CBuilder5\Projects\Lib\phvcl\WhatsMetaClient.cpp")
    p2 = read_cp(prev)
    d2 = read_cp(dfm)

    assert "InstShow" in ui and "InstUrl" in ui
    aviso = ui[ui.find("AnsiString Aviso") : ui.find("ShowMensagemBox(Aviso")]
    assert "local-dev" not in aviso
    assert 'LoadFromWhatsPhEnv("D:\\\\PHSFTW")' in sen
    assert "Configuração do WhatsApp" in cli
    assert "Situação do &WhatsApp" in d2
    assert "histórico" in d2
    assert "escritório" in d2
    assert "ATENÇÃO" in p2
    assert "Enviados com sucesso" in p2
    assert "Não é possível enviar pelo WhatsApp oficial" in p2

    bad = ("Cloud API", "Embedded Signup", "WABA", "pair_code", "porta 8765", "ticket")
    for path, text in [
        ("Ui", ui),
        ("Client", cli),
        ("SenWA", sen),
        ("Preview", p2),
        ("dfm", d2),
    ]:
        for line in text.splitlines():
            if line.strip().startswith("//"):
                continue
            if "WHATSPH\\.env" in line or "/v1/panel/ticket" in line:
                continue
            if any(
                m in line
                for m in (
                    "ShowMensagem",
                    "ShowMensagemBox",
                    "LastError =",
                    "OutErro =",
                    "Caption =",
                    "Hint =",
                )
            ):
                for b in bad + ("WHATSPH",):
                    if b in line:
                        raise SystemExit(f"JARGON {path}: {line}")
    print("ALL OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
