# -*- coding: utf-8 -*-
"""GEPH > Conectar conta WhatsApp: pede o codigo de vinculacao ao agente (onboarding/start).

Fontes PHVCL em CP1252 + CRLF, sem BOM. Cada troca exige exatamente 1 ocorrencia.
"""
from __future__ import annotations

from pathlib import Path

PHVCL = Path(r"C:\CBuilder5\Projects\Lib\phvcl")

CLIENT_H_OLD = """  bool CreatePanelTicket(AnsiString UsuarioGeph, AnsiString &OutPanelUrl);
"""
CLIENT_H_NEW = """  bool CreatePanelTicket(AnsiString UsuarioGeph, AnsiString &OutPanelUrl);
  bool StartOnboarding(AnsiString &OutUrl);
"""

CLIENT_CPP_OLD = """  OutPanelUrl = JsonStringValue(R, "panel_url");
  if(OutPanelUrl.IsEmpty())
   {
    LastError = "Não foi possível montar o acompanhamento de envios.";
    return false;
   }
  return true;
}
//---------------------------------------------------------------------------
"""
CLIENT_CPP_NEW = CLIENT_CPP_OLD + """// Agente gera o codigo de vinculacao e devolve {HUB}/onboarding?installation_id=&pair_code=.
// Agente anterior a 0.4.0 nao tem a rota: HTTP 404.
bool TWhatsMetaClient::StartOnboarding(AnsiString &OutUrl)
{
  OutUrl = "";
  AnsiString R = HttpPostJson("/v1/whatsapp/onboarding/start", "{}");
  if(LastError.Pos("404") > 0)
   {
    LastError = "O serviço de envio WhatsApp deste computador está desatualizado.\\r\\n"
                "Instale a versão mais recente do WHATSPH.";
    return false;
   }
  if(R.IsEmpty())
   {
    if(LastError.IsEmpty())
     LastError = "O serviço de envio WhatsApp não respondeu.";
    return false;
   }
  OutUrl = JsonStringValue(R, "onboarding_url");
  if(OutUrl.IsEmpty())
   {
    AnsiString Detail = JsonStringValue(R, "detail");
    if(Detail.IsEmpty())
     Detail = R.SubString(1, 300);
    LastError = Detail;
    return false;
   }
  return true;
}
//---------------------------------------------------------------------------
"""

UI_OLD = """void WhatsMetaAbrirConectar(void)
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
}
"""
UI_NEW = """void WhatsMetaAbrirConectar(void)
{
  TWhatsMetaClient Cli;
  if(!loadCli(Cli))
   {
    ShowMensagem("WhatsApp: " + Cli.LastError);
    return;
   }
  if(!Cli.HealthOk())
   {
    ShowMensagem("O serviço de envio WhatsApp está parado. Não é possível conectar a conta.");
    return;
   }
  if(Cli.IsConnected())
   {
    AnsiString Ja =
     "A conta WhatsApp deste escritório já está conectada.\\r\\n\\r\\n"
     "Conecte de novo só para trocar o número ou se o suporte pedir.\\r\\n\\r\\n"
     "Conectar de novo mesmo assim?";
    if(ShowMensagemBox(Ja.c_str(), "Conectar conta WhatsApp",
     MB_YESNO | MB_DEFBUTTON2) == IDNO)
     return;
   }
  AnsiString Aviso =
   "Será aberto o navegador para conectar o WhatsApp Business deste escritório.\\r\\n\\r\\n"
   "Tenha em mãos o celular com o app WhatsApp Business do número do escritório\\r\\n"
   "e o acesso ao Facebook de quem administra a empresa.\\r\\n\\r\\n"
   "Ao terminar o cadastro na página, aguarde até 1 minuto e confira em\\r\\n"
   "Situação do WhatsApp se a conta aparece conectada.";
  if(ShowMensagemBox(Aviso.c_str(), "Conectar conta WhatsApp",
   MB_YESNO | MB_DEFBUTTON1) == IDNO)
   return;
  AnsiString Url;
  if(!Cli.StartOnboarding(Url))
   {
    ShowMensagem("Não foi possível iniciar o cadastro do WhatsApp.\\r\\n" + Cli.LastError);
    return;
   }
  if(ShellExecute(NULL, "open", Url.c_str(), NULL, NULL, SW_SHOWNORMAL) <= (HINSTANCE)32)
   ShowMensagem("Não foi possível abrir o navegador.\\r\\nEndereço: " + Url);
}
"""


def crlf(text: str) -> str:
    return text.replace("\n", "\r\n")


def patch(path: Path, old: str, new: str) -> None:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise SystemExit(f"{path.name}: tem BOM UTF-8")
    text = raw.decode("cp1252")
    old_c, new_c = crlf(old), crlf(new)
    if new_c in text:
        print(f"{path.name}: ja aplicado")
        return
    count = text.count(old_c)
    if count != 1:
        raise SystemExit(f"{path.name}: trecho antigo encontrado {count}x (esperado 1)")
    path.write_bytes(text.replace(old_c, new_c).encode("cp1252"))
    print(f"{path.name}: OK")


def main() -> int:
    patch(PHVCL / "WhatsMetaClient.h", CLIENT_H_OLD, CLIENT_H_NEW)
    patch(PHVCL / "WhatsMetaClient.cpp", CLIENT_CPP_OLD, CLIENT_CPP_NEW)
    patch(PHVCL / "WhatsMetaUi.cpp", UI_OLD, UI_NEW)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
