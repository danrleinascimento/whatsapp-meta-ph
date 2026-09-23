# -*- coding: utf-8 -*-
"""Cria/atualiza WhatsMeta UI + FetchStatus em CP1252/CRLF."""
from __future__ import annotations

from pathlib import Path

PHVCL = Path(r"C:\CBuilder5\Projects\Lib\phvcl")


def write_cp1252(path: Path, text: str) -> None:
    data = text.replace("\r\n", "\n").replace("\n", "\r\n").encode("cp1252", errors="strict")
    path.write_bytes(data)
    print("OK", path.name, "bytes", len(data))


# --- WhatsMetaClient.h ---
write_cp1252(
    PHVCL / "WhatsMetaClient.h",
    r"""//---------------------------------------------------------------------------
#ifndef WhatsMetaClientH
#define WhatsMetaClientH
//---------------------------------------------------------------------------
#include <vcl.h>
//---------------------------------------------------------------------------
// Cliente HTTP do agente WHATSPH (127.0.0.1:8765).
// FastAPI + header X-PH-Api-Key. Sem App Secret Meta no C++.
// Comentarios em ASCII (BCB5 / CP1252).
//---------------------------------------------------------------------------
class TWhatsMetaClient
{
public:
  AnsiString BaseUrl;
  AnsiString ApiKey;
  AnsiString InstallationId;
  int TimeoutMs;
  AnsiString LastError;

  TWhatsMetaClient();

  bool LoadFromWhatsPhEnv(AnsiString PhsftwRoot);
  bool HealthOk();
  bool IsConnected();
  bool FetchStatus(
    AnsiString &OutStatus,
    AnsiString &OutDisplayPhone,
    bool &OutConnected
  );

  bool SendDocument(
    AnsiString ToPhone,
    AnsiString FilePath,
    AnsiString Caption,
    AnsiString UsuarioGeph,
    AnsiString DiretorioPrincipal,
    AnsiString DiretorioSecundario
  );

  bool CreatePanelTicket(AnsiString UsuarioGeph, AnsiString &OutPanelUrl);

private:
  AnsiString HttpGet(AnsiString Path);
  AnsiString HttpPostJson(AnsiString Path, AnsiString JsonBody);
  AnsiString JsonEscape(AnsiString S);
  bool JsonBoolTrue(AnsiString Json, AnsiString Key);
  AnsiString JsonStringValue(AnsiString Json, AnsiString Key);
};
//---------------------------------------------------------------------------
#endif
""",
)

# Read existing cpp and patch carefully via full rewrite of key parts - write full file
write_cp1252(
    PHVCL / "WhatsMetaClient.cpp",
    r"""//---------------------------------------------------------------------------
#include <vcl.h>
#pragma hdrstop

#include "WhatsMetaClient.h"
#include <IdHTTP.hpp>
#include <IdException.hpp>
#include <stdio.h>
//---------------------------------------------------------------------------
#pragma package(smart_init)
//---------------------------------------------------------------------------
TWhatsMetaClient::TWhatsMetaClient()
{
  BaseUrl = "http://127.0.0.1:8765";
  ApiKey = "";
  InstallationId = "";
  TimeoutMs = 120000;
  LastError = "";
}
//---------------------------------------------------------------------------
static AnsiString TrimLineKeyValue(AnsiString Line, AnsiString Key)
{
  Line = Line.Trim();
  if(Line.Length() == 0 || Line[1] == '#')
   return "";
  AnsiString Pref = Key + "=";
  if(Line.Pos(Pref) != 1)
   return "";
  return Line.SubString(Pref.Length() + 1, Line.Length()).Trim();
}
//---------------------------------------------------------------------------
bool TWhatsMetaClient::LoadFromWhatsPhEnv(AnsiString PhsftwRoot)
{
  LastError = "";
  if(PhsftwRoot.IsEmpty())
   {
    LastError = "PHSFTW root vazio";
    return false;
   }
  if(PhsftwRoot[PhsftwRoot.Length()] != '\\')
   PhsftwRoot += "\\";
  AnsiString EnvPath = PhsftwRoot + "WHATSPH\\.env";
  if(!FileExists(EnvPath))
   {
    LastError = "Arquivo nao encontrado: " + EnvPath;
    return false;
   }
  TStringList *L = new TStringList();
  try
   {
    L->LoadFromFile(EnvPath);
    for(int i = 0; i < L->Count; i++)
     {
      AnsiString V;
      V = TrimLineKeyValue(L->Strings[i], "PH_API_KEY");
      if(V != "")
       ApiKey = V;
      V = TrimLineKeyValue(L->Strings[i], "PORT");
      if(V != "")
       BaseUrl = "http://127.0.0.1:" + V;
      V = TrimLineKeyValue(L->Strings[i], "INSTALLATION_ID");
      if(V != "")
       InstallationId = V;
     }
   }
  __finally
   {
    delete L;
   }
  if(ApiKey.IsEmpty())
   {
    LastError = "PH_API_KEY ausente no .env WHATSPH";
    return false;
   }
  return true;
}
//---------------------------------------------------------------------------
AnsiString TWhatsMetaClient::JsonEscape(AnsiString S)
{
  AnsiString O = "";
  for(int i = 1; i <= S.Length(); i++)
   {
    char C = S[i];
    if(C == '\\' || C == '"')
     O += AnsiString("\\") + C;
    else if(C == '\r')
     O += "\\r";
    else if(C == '\n')
     O += "\\n";
    else if(C == '\t')
     O += "\\t";
    else
     O += C;
   }
  return O;
}
//---------------------------------------------------------------------------
bool TWhatsMetaClient::JsonBoolTrue(AnsiString Json, AnsiString Key)
{
  AnsiString Needle = "\"" + Key + "\":true";
  if(Json.Pos(Needle) > 0)
   return true;
  Needle = "\"" + Key + "\": true";
  return Json.Pos(Needle) > 0;
}
//---------------------------------------------------------------------------
AnsiString TWhatsMetaClient::JsonStringValue(AnsiString Json, AnsiString Key)
{
  AnsiString Needle = "\"" + Key + "\":\"";
  int P = Json.Pos(Needle);
  if(P <= 0)
   {
    Needle = "\"" + Key + "\": \"";
    P = Json.Pos(Needle);
    if(P <= 0)
     return "";
   }
  int Start = P + Needle.Length();
  AnsiString Out = "";
  for(int i = Start; i <= Json.Length(); i++)
   {
    char C = Json[i];
    if(C == '\\' && i < Json.Length())
     {
      Out += Json[i + 1];
      i++;
      continue;
     }
    if(C == '"')
     break;
    Out += C;
   }
  return Out;
}
//---------------------------------------------------------------------------
AnsiString TWhatsMetaClient::HttpGet(AnsiString Path)
{
  LastError = "";
  TIdHTTP *Http = new TIdHTTP(NULL);
  AnsiString Body = "";
  try
   {
    Http->ReadTimeout = TimeoutMs;
    Http->Request->CustomHeaders->Values["X-PH-Api-Key"] = ApiKey;
    try
     {
      Body = Http->Get(BaseUrl + Path);
     }
    catch(const Exception &E)
     {
      LastError = E.Message;
      Body = "";
     }
   }
  __finally
   {
    delete Http;
   }
  return Body;
}
//---------------------------------------------------------------------------
AnsiString TWhatsMetaClient::HttpPostJson(AnsiString Path, AnsiString JsonBody)
{
  LastError = "";
  TIdHTTP *Http = new TIdHTTP(NULL);
  TStringStream *Req = new TStringStream(JsonBody);
  TStringStream *Resp = new TStringStream("");
  AnsiString Body = "";
  try
   {
    Http->ReadTimeout = TimeoutMs;
    Http->Request->ContentType = "application/json";
    Http->Request->CustomHeaders->Values["X-PH-Api-Key"] = ApiKey;
    try
     {
      Http->Post(BaseUrl + Path, Req, Resp);
      Body = Resp->DataString;
     }
    catch(const Exception &E)
     {
      LastError = E.Message;
      try { Body = Resp->DataString; } catch(...) {}
     }
   }
  __finally
   {
    delete Resp;
    delete Req;
    delete Http;
   }
  return Body;
}
//---------------------------------------------------------------------------
bool TWhatsMetaClient::HealthOk()
{
  AnsiString R = HttpGet("/health");
  if(R.IsEmpty())
   return false;
  return R.Pos("\"status\":\"ok\"") > 0 || R.Pos("\"status\": \"ok\"") > 0;
}
//---------------------------------------------------------------------------
bool TWhatsMetaClient::IsConnected()
{
  AnsiString R = HttpGet("/v1/whatsapp/status");
  if(R.IsEmpty())
   return false;
  return JsonBoolTrue(R, "connected");
}
//---------------------------------------------------------------------------
bool TWhatsMetaClient::FetchStatus(
  AnsiString &OutStatus,
  AnsiString &OutDisplayPhone,
  bool &OutConnected
)
{
  OutStatus = "";
  OutDisplayPhone = "";
  OutConnected = false;
  AnsiString R = HttpGet("/v1/whatsapp/status");
  if(R.IsEmpty())
   return false;
  OutConnected = JsonBoolTrue(R, "connected");
  OutStatus = JsonStringValue(R, "status");
  if(OutStatus.IsEmpty())
   OutStatus = OutConnected ? "CONNECTED" : "DISCONNECTED";
  OutDisplayPhone = JsonStringValue(R, "display_phone");
  return true;
}
//---------------------------------------------------------------------------
bool TWhatsMetaClient::SendDocument(
  AnsiString ToPhone,
  AnsiString FilePath,
  AnsiString Caption,
  AnsiString UsuarioGeph,
  AnsiString DiretorioPrincipal,
  AnsiString DiretorioSecundario
)
{
  AnsiString Json = "{";
  Json += "\"to\":\"" + JsonEscape(ToPhone) + "\",";
  Json += "\"file_path\":\"" + JsonEscape(FilePath) + "\",";
  Json += "\"caption\":\"" + JsonEscape(Caption) + "\",";
  Json += "\"usuario_geph\":\"" + JsonEscape(UsuarioGeph) + "\",";
  Json += "\"sistema_origem\":\"GEPH\",";
  Json += "\"diretorio_principal\":\"" + JsonEscape(DiretorioPrincipal) + "\",";
  Json += "\"diretorio_secundario\":\"" + JsonEscape(DiretorioSecundario) + "\"";
  Json += "}";

  AnsiString R = HttpPostJson("/v1/whatsapp/send-document", Json);
  if(R.IsEmpty())
   {
    if(LastError.IsEmpty())
     LastError = "Resposta vazia do agente WHATSPH";
    return false;
   }
  if(JsonBoolTrue(R, "ok"))
   return true;
  AnsiString Detail = JsonStringValue(R, "detail");
  if(Detail.IsEmpty())
   Detail = JsonStringValue(R, "error");
  if(Detail.IsEmpty())
   Detail = R.SubString(1, 300);
  LastError = Detail;
  return false;
}
//---------------------------------------------------------------------------
bool TWhatsMetaClient::CreatePanelTicket(AnsiString UsuarioGeph, AnsiString &OutPanelUrl)
{
  OutPanelUrl = "";
  AnsiString Json = "{\"usuario_geph\":\"" + JsonEscape(UsuarioGeph) + "\"}";
  AnsiString R = HttpPostJson("/v1/panel/ticket", Json);
  if(R.IsEmpty())
   return false;
  OutPanelUrl = JsonStringValue(R, "panel_url");
  if(OutPanelUrl.IsEmpty())
   {
    LastError = "panel_url ausente na resposta";
    return false;
   }
  return true;
}
//---------------------------------------------------------------------------
""",
)

write_cp1252(
    PHVCL / "WhatsMetaUi.h",
    r"""//---------------------------------------------------------------------------
#ifndef WhatsMetaUiH
#define WhatsMetaUiH
//---------------------------------------------------------------------------
#include <Classes.hpp>
#include <Controls.hpp>
//---------------------------------------------------------------------------
// UI helpers WHATSPH (Status / Abrir painel). ASCII comments. CP1252.
PACKAGE void WhatsMetaMostrarStatus(void);
PACKAGE void WhatsMetaAbrirPainel(void);
PACKAGE void WhatsMetaInstalarBotoesPreview(TWinControl *Parent, TControl *Anchor);
//---------------------------------------------------------------------------
#endif
""",
)

write_cp1252(
    PHVCL / "WhatsMetaUi.cpp",
    r"""//---------------------------------------------------------------------------
#include <vcl.h>
#pragma hdrstop

#include "WhatsMetaUi.h"
#include "WhatsMetaClient.h"
#include "SvcConf.h"
#include "miscelan.h"
#include <Buttons.hpp>
#include <ShellAPI.h>
//---------------------------------------------------------------------------
#pragma package(smart_init)
//---------------------------------------------------------------------------
static bool loadCli(TWhatsMetaClient &Cli)
{
  if(Cli.LoadFromWhatsPhEnv(vg.DiretorioPrincipal))
   return true;
  return Cli.LoadFromWhatsPhEnv("C:\\PHSFTW");
}
//---------------------------------------------------------------------------
void WhatsMetaMostrarStatus(void)
{
  TWhatsMetaClient Cli;
  if(!loadCli(Cli))
   {
    ShowMensagem("WHATSPH: " + Cli.LastError);
    return;
   }
  if(!Cli.HealthOk())
   {
    AnsiString M = "Agente WHATSPH offline ou servico parado.\r\n";
    M += "Verifique o servico PHWhatsMeta e http://127.0.0.1:8765/health";
    if(!Cli.LastError.IsEmpty())
     M += "\r\n" + Cli.LastError;
    ShowMensagem(M);
    return;
   }
  AnsiString St, Phone;
  bool Conn = false;
  if(!Cli.FetchStatus(St, Phone, Conn))
   {
    ShowMensagem("WHATSPH: falha ao ler status.\r\n" + Cli.LastError);
    return;
   }
  AnsiString M = "WHATSPH / WhatsApp Meta\r\n\r\n";
  M += "Agente: online\r\n";
  M += "Status: " + St + "\r\n";
  M += Conn ? "Conectado: SIM\r\n" : "Conectado: NAO\r\n";
  if(!Phone.IsEmpty())
   M += "Telefone: " + Phone + "\r\n";
  if(!Cli.InstallationId.IsEmpty())
   M += "Installation: " + Cli.InstallationId + "\r\n";
  ShowMensagem(M);
}
//---------------------------------------------------------------------------
void WhatsMetaAbrirPainel(void)
{
  TWhatsMetaClient Cli;
  if(!loadCli(Cli))
   {
    ShowMensagem("WHATSPH: " + Cli.LastError);
    return;
   }
  if(!Cli.HealthOk())
   {
    ShowMensagem("Agente WHATSPH offline. Nao e possivel abrir o painel.");
    return;
   }
  AnsiString Url;
  AnsiString User = vg.NomeUsuario;
  if(User.IsEmpty())
   User = "GEPH";
  if(!Cli.CreatePanelTicket(User, Url))
   {
    ShowMensagem("Falha ao criar ticket do painel.\r\n" + Cli.LastError);
    return;
   }
  if(ShellExecute(NULL, "open", Url.c_str(), NULL, NULL, SW_SHOWNORMAL) <= (HINSTANCE)32)
   ShowMensagem("Nao foi possivel abrir o navegador.\r\nURL: " + Url);
}
//---------------------------------------------------------------------------
class TWhatsMetaBtnHandler : public TObject
{
public:
  void __fastcall StatusClick(TObject *Sender)
  {
    WhatsMetaMostrarStatus();
  }
  void __fastcall PainelClick(TObject *Sender)
  {
    WhatsMetaAbrirPainel();
  }
};
static TWhatsMetaBtnHandler *GMetaBtnHandler = NULL;
static bool GMetaBtnsInstalled = false;
//---------------------------------------------------------------------------
void WhatsMetaInstalarBotoesPreview(TWinControl *Parent, TControl *Anchor)
{
  if(GMetaBtnsInstalled || Parent == NULL || Anchor == NULL)
   return;
  GMetaBtnsInstalled = true;
  if(GMetaBtnHandler == NULL)
   GMetaBtnHandler = new TWhatsMetaBtnHandler();

  TSpeedButton *B1 = new TSpeedButton(Parent);
  B1->Parent = Parent;
  B1->Flat = true;
  B1->Caption = "Meta";
  B1->Hint = "Status WhatsApp Meta (WHATSPH)";
  B1->ShowHint = true;
  B1->Width = 40;
  B1->Height = Anchor->Height;
  B1->Top = Anchor->Top;
  B1->Left = Anchor->Left + Anchor->Width + 4;
  B1->OnClick = GMetaBtnHandler->StatusClick;

  TSpeedButton *B2 = new TSpeedButton(Parent);
  B2->Parent = Parent;
  B2->Flat = true;
  B2->Caption = "Painel";
  B2->Hint = "Abrir painel WHATSPH (ticket GEPH)";
  B2->ShowHint = true;
  B2->Width = 48;
  B2->Height = Anchor->Height;
  B2->Top = Anchor->Top;
  B2->Left = B1->Left + B1->Width + 2;
  B2->OnClick = GMetaBtnHandler->PainelClick;
}
//---------------------------------------------------------------------------
""",
)

print("WhatsMeta sources written")
