# -*- coding: utf-8 -*-
"""Aviso quando conta ja conectada + texto Conectar mais claro (CP1252)."""
from pathlib import Path

UI = Path(r"C:\CBuilder5\Projects\Lib\phvcl\WhatsMetaUi.cpp")


def main() -> int:
    t = UI.read_bytes().decode("cp1252").replace("\r\n", "\n").replace("\r", "\n")
    old = '''void WhatsMetaAbrirConectar(void)
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
}'''
    new = '''void WhatsMetaAbrirConectar(void)
{
  TWhatsMetaClient Cli;
  if(!loadCli(Cli))
   {
    ShowMensagem("WhatsApp: " + Cli.LastError);
    return;
   }
  if(Cli.HealthOk() && Cli.IsConnected())
   {
    AnsiString Ja =
     "A conta WhatsApp deste escritório já está conectada.\\r\\n\\r\\n"
     "Não é necessário cadastrar de novo para enviar boletos.\\r\\n"
     "Use Situação do WhatsApp ou Acompanhar envios.\\r\\n\\r\\n"
     "Abrir o cadastro no navegador mesmo assim?";
    if(ShowMensagemBox(Ja.c_str(), "Conectar conta WhatsApp",
     MB_YESNO | MB_DEFBUTTON2) == IDNO)
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
   "guarde-o - o serviço do escritório usa esse código automaticamente.\\r\\n\\r\\n"
   "Se a página avisar que o cadastro não está liberado, o envio\\r\\n"
   "continua funcionando enquanto a Situação mostrar conta conectada.";
  if(ShowMensagemBox(Aviso.c_str(), "Conectar conta WhatsApp",
   MB_YESNO | MB_DEFBUTTON1) == IDNO)
   return;
  if(ShellExecute(NULL, "open", Url.c_str(), NULL, NULL, SW_SHOWNORMAL) <= (HINSTANCE)32)
   ShowMensagem("Não foi possível abrir o navegador.\\r\\nEndereço: " + Url);
}'''
    if old not in t:
        # try without accents already partially applied
        raise SystemExit("bloco Conectar nao encontrado — conferir arquivo")
    t = t.replace(old, new)
    UI.write_bytes(t.replace("\n", "\r\n").encode("cp1252"))
    print("WhatsMetaUi Conectar OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
