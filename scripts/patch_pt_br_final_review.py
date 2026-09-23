# -*- coding: utf-8 -*-
"""Revisao final: bug D:\\PHSFTW no SenWA + acentos PT + local-dev oculto."""
from __future__ import annotations

from pathlib import Path


def read_cp(p: Path) -> str:
    return p.read_bytes().decode("cp1252").replace("\r\n", "\n").replace("\r", "\n")


def write_cp(p: Path, t: str) -> None:
    p.write_bytes(t.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\r\n").encode("cp1252"))


def must_replace(t: str, old: str, new: str, label: str) -> str:
    if old not in t:
        raise SystemExit(f"MISSING [{label}]: {old[:100]!r}")
    return t.replace(old, new)


def main() -> int:
    # ----- SenWA: bug D:\ + acentos -----
    sen = Path(r"C:\CBuilder5\Projects\Lib\phvcl\SenWA.cpp")
    t = read_cp(sen)
    t = must_replace(
        t,
        '''  if(!Cli.LoadFromWhatsPhEnv(vg.DiretorioPrincipal))
   {
    if(!Cli.LoadFromWhatsPhEnv("C:\\\\PHSFTW"))
     {
      OutErro = Cli.LastError;
      return false;
     }
   }''',
        '''  if(!Cli.LoadFromWhatsPhEnv(vg.DiretorioPrincipal))
   {
    if(!Cli.LoadFromWhatsPhEnv("C:\\\\PHSFTW"))
     {
      if(!Cli.LoadFromWhatsPhEnv("D:\\\\PHSFTW"))
       {
        OutErro = Cli.LastError;
        return false;
       }
     }
   }''',
        "SenWA D:",
    )
    for old, new in [
        (
            'OutErro = "Para enviar pelo WhatsApp informe telefone com 11 digitos (DDD+numero).";',
            'OutErro = "Para enviar pelo WhatsApp informe telefone com 11 dígitos (DDD+número).";',
        ),
        (
            'OutErro = "Servico de envio parado ou conta WhatsApp desconectada";',
            'OutErro = "Serviço de envio parado ou conta WhatsApp desconectada.";',
        ),
        (
            '''          "A conta WhatsApp do escritorio esta conectada.\\r\\n"
          "Informe o telefone com 11 digitos (DDD+numero) para enviar.");''',
            '''          "A conta WhatsApp do escritório está conectada.\\r\\n"
          "Informe o telefone com 11 dígitos (DDD+número) para enviar.");''',
        ),
        (
            'ShowMensagem("Relatorio enviado pelo WhatsApp.");',
            'ShowMensagem("Relatório enviado pelo WhatsApp.");',
        ),
        (
            '''        "Falha no envio pelo WhatsApp.\\r\\n" + ErroMeta +
        "\\r\\n\\r\\nEnquanto a conta estiver conectada, o modo antigo nao sera usado automaticamente.");''',
            '''        "Falha no envio pelo WhatsApp.\\r\\n" + ErroMeta +
        "\\r\\n\\r\\nEnquanto a conta estiver conectada, o modo antigo não será usado automaticamente.");''',
        ),
        (
            'AnsiString MensaLog = "WhatsApp OK.\\r\\nRelatorio: " + NomeRelatorio + "\\r\\n";',
            'AnsiString MensaLog = "WhatsApp OK.\\r\\nRelatório: " + NomeRelatorio + "\\r\\n";',
        ),
    ]:
        if old not in t:
            print("WARN SenWA:", old[:70])
        else:
            t = t.replace(old, new)
            print("OK SenWA")
    write_cp(sen, t)

    # ----- Client -----
    cli = Path(r"C:\CBuilder5\Projects\Lib\phvcl\WhatsMetaClient.cpp")
    c = read_cp(cli)
    for old, new in [
        (
            'LastError = "Configuracao do WhatsApp incompleta neste computador.";',
            'LastError = "Configuração do WhatsApp incompleta neste computador.";',
        ),
        (
            'LastError = "Configuracao do WhatsApp nao encontrada neste computador.";',
            'LastError = "Configuração do WhatsApp não encontrada neste computador.";',
        ),
        (
            'LastError = "O servico de envio WhatsApp nao respondeu.";',
            'LastError = "O serviço de envio WhatsApp não respondeu.";',
        ),
        (
            'LastError = "Nao foi possivel montar o acompanhamento de envios.";',
            'LastError = "Não foi possível montar o acompanhamento de envios.";',
        ),
    ]:
        c = must_replace(c, old, new, "Client")
    write_cp(cli, c)
    print("Client OK")

    # ----- Ui -----
    ui = Path(r"C:\CBuilder5\Projects\Lib\phvcl\WhatsMetaUi.cpp")
    u = read_cp(ui)
    u = must_replace(
        u,
        '''void WhatsMetaAbrirConectar(void)
{
  TWhatsMetaClient Cli;
  if(!loadCli(Cli))
   {
    ShowMensagem("WhatsApp: " + Cli.LastError);
    return;
   }
  AnsiString Inst = Cli.InstallationId;
  if(Inst.IsEmpty())
   Inst = "local-dev";
  AnsiString Hub = Cli.HubBaseUrl;
  if(Hub.IsEmpty())
   Hub = "https://whatsapp-meta-ph-wzewk.ondigitalocean.app";
  AnsiString Url = Hub + "/onboarding?installation_id=" + Inst;
  AnsiString Aviso =
   "Sera aberto o navegador para conectar a conta WhatsApp Business\\r\\n"
   "deste escritorio (" + Inst + ").\\r\\n\\r\\n"
   "Conclua o cadastro na pagina. Se aparecer um codigo de vinculacao,\\r\\n"
   "guarde-o - o servico do escritorio usa esse codigo automaticamente.";
  if(ShowMensagemBox(Aviso.c_str(), "Conectar conta WhatsApp",
   MB_YESNO | MB_DEFBUTTON1) == IDNO)
   return;
  if(ShellExecute(NULL, "open", Url.c_str(), NULL, NULL, SW_SHOWNORMAL) <= (HINSTANCE)32)
   ShowMensagem("Nao foi possivel abrir o navegador.\\r\\nEndereco: " + Url);
}''',
        '''void WhatsMetaAbrirConectar(void)
{
  TWhatsMetaClient Cli;
  if(!loadCli(Cli))
   {
    ShowMensagem("WhatsApp: " + Cli.LastError);
    return;
   }
  AnsiString InstUrl = Cli.InstallationId;
  if(InstUrl.IsEmpty())
   InstUrl = "local-dev";
  AnsiString InstShow = Cli.InstallationId;
  if(InstShow.IsEmpty())
   InstShow = "este computador";
  AnsiString Hub = Cli.HubBaseUrl;
  if(Hub.IsEmpty())
   Hub = "https://whatsapp-meta-ph-wzewk.ondigitalocean.app";
  AnsiString Url = Hub + "/onboarding?installation_id=" + InstUrl;
  AnsiString Aviso =
   "Será aberto o navegador para conectar a conta WhatsApp Business\\r\\n"
   "deste escritório (" + InstShow + ").\\r\\n\\r\\n"
   "Conclua o cadastro na página. Se aparecer um código de vinculação,\\r\\n"
   "guarde-o - o serviço do escritório usa esse código automaticamente.";
  if(ShowMensagemBox(Aviso.c_str(), "Conectar conta WhatsApp",
   MB_YESNO | MB_DEFBUTTON1) == IDNO)
   return;
  if(ShellExecute(NULL, "open", Url.c_str(), NULL, NULL, SW_SHOWNORMAL) <= (HINSTANCE)32)
   ShowMensagem("Não foi possível abrir o navegador.\\r\\nEndereço: " + Url);
}''',
        "Ui Conectar",
    )
    for old, new in [
        (
            '''    AnsiString M = "O servico de envio WhatsApp esta parado ou inacessivel.\\r\\n";
    M += "Verifique se o programa de envio WhatsApp esta em execucao neste computador.";''',
            '''    AnsiString M = "O serviço de envio WhatsApp está parado ou inacessível.\\r\\n";
    M += "Verifique se o programa de envio WhatsApp está em execução neste computador.";''',
        ),
        (
            'ShowMensagem("Nao foi possivel consultar a situacao do WhatsApp.\\r\\n" + Cli.LastError);',
            'ShowMensagem("Não foi possível consultar a situação do WhatsApp.\\r\\n" + Cli.LastError);',
        ),
        (
            '''  AnsiString M = "Situacao do WhatsApp\\r\\n\\r\\n";
  M += "Servico de envio: em funcionamento\\r\\n";
  if(Conn)
   M += "Conta: conectada\\r\\n";
  else
   M += "Conta: nao conectada\\r\\n";''',
            '''  AnsiString M = "Situação do WhatsApp\\r\\n\\r\\n";
  M += "Serviço de envio: em funcionamento\\r\\n";
  if(Conn)
   M += "Conta: conectada\\r\\n";
  else
   M += "Conta: não conectada\\r\\n";''',
        ),
        (
            '   M += "Escritorio: " + Cli.InstallationId + "\\r\\n";',
            '   M += "Escritório: " + Cli.InstallationId + "\\r\\n";',
        ),
        (
            'ShowMensagem("O servico de envio WhatsApp esta parado. Nao e possivel abrir o acompanhamento.");',
            'ShowMensagem("O serviço de envio WhatsApp está parado. Não é possível abrir o acompanhamento.");',
        ),
        (
            'ShowMensagem("Nao foi possivel abrir o acompanhamento de envios.\\r\\n" + Cli.LastError);',
            'ShowMensagem("Não foi possível abrir o acompanhamento de envios.\\r\\n" + Cli.LastError);',
        ),
        (
            'ShowMensagem("Nao foi possivel abrir o navegador.\\r\\nEndereco: " + Url);',
            'ShowMensagem("Não foi possível abrir o navegador.\\r\\nEndereço: " + Url);',
        ),
    ]:
        u = must_replace(u, old, new, "Ui")
    write_cp(ui, u)
    print("Ui OK")

    # ----- Preview -----
    prev = Path(r"C:\CBuilder5\Projects\Lib\phvcl\Preview.cpp")
    p = read_cp(prev)
    for old, new in [
        (
            '''         Pergunta =
          "ATENCAO: A conta WhatsApp do escritorio esta CONECTADA.\\r\\n\\r\\n"
          "Confirma o envio em grupo dos boletos pelo WhatsApp?\\r\\n"
          "Cada boleto sera enviado como PDF.\\r\\n\\r\\n"
          "Sim = enviar pelo WhatsApp oficial\\r\\n"
          "Nao = outras opcoes (modo antigo ou um boleto por vez)";''',
            '''         Pergunta =
          "ATENÇÃO: A conta WhatsApp do escritório está CONECTADA.\\r\\n\\r\\n"
          "Confirma o envio em grupo dos boletos pelo WhatsApp?\\r\\n"
          "Cada boleto será enviado como PDF.\\r\\n\\r\\n"
          "Sim = enviar pelo WhatsApp oficial\\r\\n"
          "Não = outras opções (modo antigo ou um boleto por vez)";''',
        ),
        (
            '''         Pergunta =
          "ATENCAO: Confirma envio em grupo via WhatsApp dos boletos com numero cadastrado?\\r\\n\\r\\n"
          "(Conta WhatsApp oficial indisponivel - sera usado o modo antigo)";''',
            '''         Pergunta =
          "ATENÇÃO: Confirma envio em grupo via WhatsApp dos boletos com número cadastrado?\\r\\n\\r\\n"
          "(Conta WhatsApp oficial indisponível - será usado o modo antigo)";''',
        ),
        (
            '''         if(ShowMensagemBox(
          "Usar o modo antigo de envio em grupo?\\r\\n\\r\\n"
          "Sim = modo antigo\\r\\n"
          "Nao = enviar um PDF por vez (WhatsApp oficial, se disponivel)",
          "Envio WhatsApp", MB_YESNO | MB_DEFBUTTON2) == IDYES)''',
            '''         if(ShowMensagemBox(
          "Usar o modo antigo de envio em grupo?\\r\\n\\r\\n"
          "Sim = modo antigo\\r\\n"
          "Não = enviar um PDF por vez (WhatsApp oficial, se disponível)",
          "Envio WhatsApp", MB_YESNO | MB_DEFBUTTON2) == IDYES)''',
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
            '''    Log->Add("Relatorio: " + PHR->Report->Titulo);
    Log->Add("Escritorio: " + Cli.InstallationId);''',
            '''    Log->Add("Relatório: " + PHR->Report->Titulo);
    Log->Add("Escritório: " + Cli.InstallationId);''',
        ),
    ]:
        p = must_replace(p, old, new, "Preview")
    write_cp(prev, p)
    print("Preview OK")

    # ----- dfm hint -----
    dfm = Path(r"C:\CBuilder5\Projects\GEPH\Princ.dfm")
    d = read_cp(dfm)
    d = must_replace(
        d,
        "Hint = 'Abre o cadastro da conta WhatsApp Business do escritorio'",
        "Hint = 'Abre o cadastro da conta WhatsApp Business do escritório'",
        "dfm",
    )
    assert "Situação do &WhatsApp" in d
    assert "histórico" in d
    assert "escritório" in d
    write_cp(dfm, d)
    print("dfm OK")

    # ----- sanity -----
    bad = ("Cloud API", "Embedded Signup", "WABA", "pair_code", "porta 8765")
    for path in (ui, cli, sen, prev, dfm):
        text = read_cp(path)
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
                for b in bad + ("WHATSPH", "ticket"):
                    if b in line:
                        raise SystemExit(f"JARGON {path.name}: {line}")
    u2 = read_cp(ui)
    # local-dev so pode existir em InstUrl, mas nao em Aviso/Show/InstShow
    aviso = u2[u2.find("AnsiString Aviso") : u2.find("ShowMensagemBox(Aviso")]
    if "local-dev" in aviso:
        raise SystemExit("local-dev no aviso ao usuario")
    s2 = read_cp(sen)
    if 'LoadFromWhatsPhEnv("D:\\\\PHSFTW")' not in s2:
        raise SystemExit("SenWA sem D:\\\\PHSFTW")
    print("ALL REVIEW OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
