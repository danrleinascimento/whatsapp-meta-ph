# -*- coding: utf-8 -*-
"""Patch Preview/SenWA/WhatsMetaUi for Meta group send. Writes CP1252/CRLF."""
from __future__ import annotations

from pathlib import Path

PHVCL = Path(r"C:\CBuilder5\Projects\Lib\phvcl")


def read_cp1252(path: Path) -> str:
    return path.read_text(encoding="cp1252")


def write_cp1252(path: Path, text: str) -> None:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\r\n")
    path.write_bytes(text.encode("cp1252"))


def patch_whatsmeta_ui() -> None:
    h = read_cp1252(PHVCL / "WhatsMetaUi.h")
    if "WhatsMetaEstaDisponivel" not in h:
        h = h.replace(
            "PACKAGE void WhatsMetaAbrirConectar(void);",
            "PACKAGE void WhatsMetaAbrirConectar(void);\r\n"
            "PACKAGE bool WhatsMetaEstaDisponivel(void);",
        )
        write_cp1252(PHVCL / "WhatsMetaUi.h", h)
        print("Ui.h OK")
    else:
        print("Ui.h skip")

    c = read_cp1252(PHVCL / "WhatsMetaUi.cpp")
    if "WhatsMetaEstaDisponivel" not in c:
        insert = r'''//---------------------------------------------------------------------------
bool WhatsMetaEstaDisponivel(void)
{
  TWhatsMetaClient Cli;
  if(!loadCli(Cli))
   return false;
  if(!Cli.HealthOk())
   return false;
  return Cli.IsConnected();
}
//---------------------------------------------------------------------------
'''
        marker = "void WhatsMetaMostrarStatus(void)"
        if marker not in c:
            raise SystemExit("MostrarStatus missing")
        c = c.replace(marker, insert + marker)
        write_cp1252(PHVCL / "WhatsMetaUi.cpp", c)
        print("Ui.cpp OK")
    else:
        print("Ui.cpp skip")


def patch_preview_h() -> None:
    h = read_cp1252(PHVCL / "Preview.h")
    if "enviarWhatsGrupoBoletosMeta" in h:
        print("Preview.h skip")
        return
    old = (
        "  AnsiString montarMensagemWhatsBoleto(int Indice, PHReport *PR, AnsiString UrlPdf);\r\n"
        "  bool enviarWhatsGrupoBoletos(void);"
    )
    new = (
        "  AnsiString montarMensagemWhatsBoleto(int Indice, PHReport *PR, AnsiString UrlPdf);\r\n"
        "  AnsiString montarCaptionWhatsBoletoMeta(int Indice, PHReport *PR, AnsiString MensagemOpcional);\r\n"
        "  bool enviarWhatsGrupoBoletos(void);\r\n"
        "  bool enviarWhatsGrupoBoletosMeta(void);"
    )
    if old not in h:
        old = old.replace("\r\n", "\n")
        new = new.replace("\r\n", "\n")
    if old not in h:
        raise SystemExit("Preview.h marker not found")
    write_cp1252(PHVCL / "Preview.h", h.replace(old, new))
    print("Preview.h OK")


def patch_preview_cpp() -> None:
    p = PHVCL / "Preview.cpp"
    t = read_cp1252(p)

    if '#include "WhatsMetaClient.h"' not in t:
        t = t.replace(
            '#include "WhatsMetaUi.h"',
            '#include "WhatsMetaUi.h"\r\n#include "WhatsMetaClient.h"',
        )

    # --- SpeedButton6Click group dialog ---
    old_dlg = '''    if(temListasWhatsGrupo())
     {
      if(ShowMensagemBox(
          "ATENCAO: Confirma envio em grupo via WhatsApp dos boletos com numero cadastrado?",
          "WhatsApp", MB_YESNO | MB_DEFBUTTON2) == IDYES)
       {
        if(recusarWhatsGrupoPorLimite(this))
         return;
        // true = mensagem de conclusao exibida: fecha Preview para o
        // ShowModal retornar e CPBoletos exibir ListaEnviadosWhats.txt.
        if(enviarWhatsGrupoBoletos())
         {
          Close();
          return;
         }
        SPageAtual=-1;
        UpDown1->Position=1;
        PageAtual=UpDown1->Position;
        PaintBox1->Invalidate();
        ScrollBox1->VertScrollBar->Position=0;
        ScrollBox1->Update();
        return;
       }
      // Nao: modo antigo Envio Relatorio pelo WhatsApp (TSendWA1).
     }'''

    new_dlg = '''    if(temListasWhatsGrupo())
     {
      bool UsarMeta = WhatsMetaEstaDisponivel();
      AnsiString Pergunta;
      AnsiString TituloDlg;
      if(UsarMeta)
       {
        Pergunta =
         "ATENCAO: WhatsApp Meta (Cloud API) esta CONECTADO.\\r\\n\\r\\n"
         "Confirma envio em grupo dos boletos via Meta?\\r\\n"
         "Cada boleto sera enviado como PDF pela Cloud API.\\r\\n\\r\\n"
         "Sim = Meta Cloud API\\r\\n"
         "Nao = outras opcoes (legado Whats.exe ou envio unitario)";
        TituloDlg = "WhatsApp Meta";
       }
      else
       {
        Pergunta =
         "ATENCAO: Confirma envio em grupo via WhatsApp dos boletos com numero cadastrado?\\r\\n\\r\\n"
         "(Meta Cloud API indisponivel ou desconectado — fluxo legado Whats.exe)";
        TituloDlg = "WhatsApp";
       }
      if(ShowMensagemBox(Pergunta.c_str(), TituloDlg.c_str(),
       MB_YESNO | MB_DEFBUTTON2) == IDYES)
       {
        if(recusarWhatsGrupoPorLimite(this))
         return;
        // true = mensagem de conclusao: fecha Preview (CPBoletos / log).
        bool OkGrupo = UsarMeta ? enviarWhatsGrupoBoletosMeta()
                                : enviarWhatsGrupoBoletos();
        if(OkGrupo)
         {
          Close();
          return;
         }
        SPageAtual=-1;
        UpDown1->Position=1;
        PageAtual=UpDown1->Position;
        PaintBox1->Invalidate();
        ScrollBox1->VertScrollBar->Position=0;
        ScrollBox1->Update();
        return;
       }
      // Nao + Meta ok: oferecer legado explicitamente.
      if(UsarMeta)
       {
        if(ShowMensagemBox(
         "Usar envio em grupo LEGADO (Whats.exe / FTP)?\\r\\n\\r\\n"
         "Sim = Whats.exe\\r\\n"
         "Nao = abrir envio unitario (um PDF, tambem tenta Meta)",
         "WhatsApp", MB_YESNO | MB_DEFBUTTON2) == IDYES)
         {
          if(recusarWhatsGrupoPorLimite(this))
           return;
          if(enviarWhatsGrupoBoletos())
           {
            Close();
            return;
           }
          SPageAtual=-1;
          UpDown1->Position=1;
          PageAtual=UpDown1->Position;
          PaintBox1->Invalidate();
          ScrollBox1->VertScrollBar->Position=0;
          ScrollBox1->Update();
          return;
         }
       }
      // Nao: envio unitario TSendWA1 (abaixo).
     }'''

    # In the Python source above I used \\r\\n which becomes \r\n in the string - good for C++ source as \r\n escapes in string literals.
    # Wait - in new_dlg I used "\\r\\n" in a regular (non-raw) string - that becomes \r\n in the output file which is correct for C++ "a\r\nb".

    if "enviarWhatsGrupoBoletosMeta()" in t and "WhatsApp Meta (Cloud API) esta CONECTADO" in t:
        print("Preview dialog skip")
    else:
        if old_dlg not in t:
            # try with actual file newlines
            old_n = old_dlg.replace("\n", "\r\n") if "\r\n" not in old_dlg else old_dlg
            # file was read with universal? read_text keeps \r\n as \n on some? pathlib read_text on Windows with cp1252 - keeps \n only if file has \n?
            # Actually read_text doesn't convert. File has \r\n. So t has \r\n.
            old_dlg_crlf = old_dlg.replace("\n", "\r\n")
            new_dlg_crlf = new_dlg.replace("\n", "\r\n")
            if old_dlg_crlf not in t:
                # show nearby for debug
                idx = t.find("temListasWhatsGrupo()")
                print(repr(t[idx:idx+400]))
                raise SystemExit("SpeedButton6 dialog block not found")
            t = t.replace(old_dlg_crlf, new_dlg_crlf)
        else:
            t = t.replace(old_dlg, new_dlg)
        print("Preview dialog OK")

    # --- montarCaption + enviarWhatsGrupoBoletosMeta before enviarWhatsGrupoBoletos ---
    if "enviarWhatsGrupoBoletosMeta" in t and "montarCaptionWhatsBoletoMeta" in t:
        print("Preview Meta fn skip")
    else:
        meta_fns = r'''//---------------------------------------------------------------------------
AnsiString TPreview1::montarCaptionWhatsBoletoMeta(int Indice, PHReport *PR, AnsiString MensagemOpcional)
{
  AnsiString Msg = "";
  if(MensagemOpcional.Trim() != "")
   Msg = MensagemOpcional.Trim() + "\r\n";
  Msg += "Boleto\r\n";

  if(PR->CompetenciaBoleto && Indice < PR->CompetenciaBoleto->Count)
   {
    AnsiString Competencia = FormData(PR->CompetenciaBoleto->Strings[Indice]);
    if(Competencia.Trim() != "")
     Msg += "Competencia: " + Competencia + "\r\n";
   }

  if(PR->DataVencimentoBoleto && Indice < PR->DataVencimentoBoleto->Count)
   {
    AnsiString DataVenc = FormData(PR->DataVencimentoBoleto->Strings[Indice]);
    if(DataVenc.Trim() != "")
     Msg += "Vencimento: " + DataVenc + "\r\n";
   }

  if(PR->LinksNfse && Indice < PR->LinksNfse->Count)
   {
    AnsiString LinkNfse = obterLinkNfseWhats(PR->LinksNfse->Strings[Indice]);
    if(LinkNfse != "")
     Msg += "Segue sua NFS-e: " + LinkNfse + "\r\n";
   }

  Msg += "Segue PDF do boleto em anexo.";
  if(Msg.Length() > 1000)
   Msg = Msg.SubString(1, 1000);
  return Msg;
}
//---------------------------------------------------------------------------
bool TPreview1::enviarWhatsGrupoBoletosMeta(void)
{
  if(recusarWhatsGrupoPorLimite(this))
   return false;
  AnsiString MensagemOpcional = "";
  if(!pedirMensagemOpcionalWhatsGrupo(MensagemOpcional))
   return false;

  TWhatsMetaClient Cli;
  if(!Cli.LoadFromWhatsPhEnv(vg.DiretorioPrincipal))
   {
    if(!Cli.LoadFromWhatsPhEnv("C:\\PHSFTW"))
     {
      if(!Cli.LoadFromWhatsPhEnv("D:\\PHSFTW"))
       {
        ShowMensagem("WHATSPH: " + Cli.LastError);
        return false;
       }
     }
   }
  if(!Cli.HealthOk() || !Cli.IsConnected())
   {
    AnsiString Em = Cli.LastError;
    if(Em.IsEmpty())
     Em = "Agente offline ou WhatsApp Meta desconectado";
    ShowMensagem("Nao e possivel enviar via Meta.\r\n" + Em);
    return false;
   }

  AnsiString arqLog = vg.DiretorioPrincipal + "ListaEnviadosWhats.txt";
  DeleteFile(arqLog);
  TStringList *Log = new TStringList;
  int QPagsSave = PHR->Report->QPagsArqs;
  int Ok = 0;
  int Erro = 0;
  int Pulados = 0;

  TCursor SCursor = Screen->Cursor;
  Screen->Cursor = crHourGlass;
  try
   {
    Log->Add("Envio WhatsApp Meta (Cloud API) em grupo - " +
     FormatDateTime("dd/mm/yyyy hh:nn:ss", Now()));
    Log->Add("Relatorio: " + PHR->Report->Titulo);
    Log->Add("Installation: " + Cli.InstallationId);
    Log->Add("");

    PHReport *PR = PHR->Report;
    for(int i = 0; i < PR->WhatsSave->Count; i++)
     {
      AnsiString Whats = PR->WhatsSave->Strings[i].Trim();
      AnsiString Codigo = PR->CodigosBoletoSave->Strings[i];
      AnsiString Nome = "";
      if(PR->NomesSave && i < PR->NomesSave->Count)
       Nome = PR->NomesSave->Strings[i];

      if(!whatsAppValido(Whats))
       {
        Pulados++;
        Log->Add("PULADO codigo " + Codigo + " '" + Nome +
         "' - WhatsApp invalido/ausente: '" + Whats + "'");
        continue;
       }

      AnsiString FileName = vg.DiretorioPrincipal + "__RELTEMPWHATSM_" +
       IntToStr(vg.CodigoUsuario) + "_" + Codigo + ".PDF";
      DeleteFile(FileName);
      try
       {
        try
         {
          PR->QPagsArqs = 1;
          PR->PAGESAVEFIXAINICIAL = i + 1;
          PR->PAGESAVEFIXAFINAL = i + 1;
          PR->SaveToFile(FileName);
          PR->PAGESAVEFIXAINICIAL = 0;
          PR->PAGESAVEFIXAFINAL = 0;

          AnsiString Cap = montarCaptionWhatsBoletoMeta(i, PR, MensagemOpcional);
          AnsiString ToPhone = "55" + Whats;
          if(Cli.SendDocument(
               ToPhone,
               FileName,
               Cap,
               vg.NomeUsuario,
               vg.DiretorioPrincipal,
               vg.DiretorioSecundario))
           {
            Ok++;
            Log->Add("OK Meta boleto " + Codigo + " '" + Nome +
             "', numero " + ToPhone);
            if(PR->EventoWhatsOk)
             PR->EventoWhatsOk(PR, Codigo);
           }
          else
           {
            Erro++;
            Log->Add("ERRO Meta codigo " + Codigo + " '" + Nome +
             "': " + Cli.LastError);
           }
         }
        catch(Exception &E)
         {
          Erro++;
          PR->PAGESAVEFIXAINICIAL = 0;
          PR->PAGESAVEFIXAFINAL = 0;
          Log->Add("ERRO preparando codigo " + Codigo + " '" + Nome +
           "': " + E.Message);
         }
       }
      __finally
       {
        DeleteFile(FileName);
       }
      Application->ProcessMessages();
     }

    Log->Add("");
    Log->Add("Resumo Meta: OK=" + IntToStr(Ok) + " ERRO=" + IntToStr(Erro) +
     " PULADOS=" + IntToStr(Pulados));
    Log->SaveToFile(arqLog);

    AnsiString MensaLog = "WhatsMeta grupo boletos. OK=" + IntToStr(Ok) +
     " ERRO=" + IntToStr(Erro) + " PULADOS=" + IntToStr(Pulados);
    vg.IncluiLog(NULL, 0, "99999018", MensaLog);

    ShowMensagem("WhatsApp Meta (grupo) finalizado.\r\nOK: " + IntToStr(Ok) +
     "\r\nErro: " + IntToStr(Erro) + "\r\nPulados: " + IntToStr(Pulados));
    return true;
   }
  __finally
   {
    PHR->Report->QPagsArqs = QPagsSave;
    PHR->Report->PAGESAVEFIXAINICIAL = 0;
    PHR->Report->PAGESAVEFIXAFINAL = 0;
    delete Log;
    Screen->Cursor = SCursor;
   }
  return false;
}
//---------------------------------------------------------------------------
'''
        marker = "bool TPreview1::enviarWhatsGrupoBoletos(void)"
        if marker not in t:
            raise SystemExit("enviarWhatsGrupoBoletos marker missing")
        # only insert once
        if "bool TPreview1::enviarWhatsGrupoBoletosMeta(void)" not in t:
            t = t.replace(marker, meta_fns + marker)
            print("Preview Meta fn OK")
        else:
            print("Preview Meta fn already")

    write_cp1252(p, t)
    print("Preview.cpp written")


def patch_senwa() -> None:
    p = PHVCL / "SenWA.cpp"
    t = read_cp1252(p)
    old = '''    // Preferencia: Cloud API via agente WHATSPH (se CONECTADO).
    // Fallback: fluxo legado FTP + Whats.exe abaixo.
    {
     AnsiString ErroMeta;
     AnsiString CapMeta = Edit1->Text.Trim();
     if(CapMeta.IsEmpty())
      CapMeta = NomeRelatorio;
     if(enviarViaWhatsMeta(ArqRelatorio, MaskEdit1->Text.Trim(), CapMeta, ErroMeta))
      {
       AnsiString MensaLog = "WhatsMeta Cloud API OK\\r\\nRelatorio: " + NomeRelatorio + "\\r\\n";
       MensaLog += "Telefone: " + MaskEdit1->Text.Trim() + "\\r\\n";
       vg.IncluiLog(NULL,0,"99999018",MensaLog);
       ShowMensagem("Relatorio enviado via WhatsApp Meta (Cloud API).");
       Close();
       return;
      }
    }'''
    # Fix - in file the strings use real \r\n escapes as two chars backslash-r? In C++ source it's "\r\n" which is chars \, r, \, n OR actual CR LF inside quotes?
    # Looking at read earlier: MensaLog = "WhatsMeta Cloud API OK\r\nRelatorio: "
    # In the file those are backslash-r-backslash-n in the source.

    old = '''    // Preferencia: Cloud API via agente WHATSPH (se CONECTADO).
    // Fallback: fluxo legado FTP + Whats.exe abaixo.
    {
     AnsiString ErroMeta;
     AnsiString CapMeta = Edit1->Text.Trim();
     if(CapMeta.IsEmpty())
      CapMeta = NomeRelatorio;
     if(enviarViaWhatsMeta(ArqRelatorio, MaskEdit1->Text.Trim(), CapMeta, ErroMeta))
      {
       AnsiString MensaLog = "WhatsMeta Cloud API OK\r\nRelatorio: " + NomeRelatorio + "\r\n";
       MensaLog += "Telefone: " + MaskEdit1->Text.Trim() + "\r\n";
       vg.IncluiLog(NULL,0,"99999018",MensaLog);
       ShowMensagem("Relatorio enviado via WhatsApp Meta (Cloud API).");
       Close();
       return;
      }
    }'''

    new = '''    // Preferencia: Cloud API via agente WHATSPH (se CONECTADO).
    // Se Meta esta CONECTADO, nao cair no Whats.exe em silencio.
    // Fallback legado so quando Meta indisponivel/desconectado.
    {
     AnsiString ErroMeta;
     AnsiString CapMeta = Edit1->Text.Trim();
     if(CapMeta.IsEmpty())
      CapMeta = NomeRelatorio;
     AnsiString Tel11 = MaskEdit1->Text.Trim();
     TWhatsMetaClient CliChk;
     bool MetaLoaded = CliChk.LoadFromWhatsPhEnv(vg.DiretorioPrincipal);
     if(!MetaLoaded)
      MetaLoaded = CliChk.LoadFromWhatsPhEnv("C:\\PHSFTW");
     if(!MetaLoaded)
      MetaLoaded = CliChk.LoadFromWhatsPhEnv("D:\\PHSFTW");
     bool MetaConectado = MetaLoaded && CliChk.HealthOk() && CliChk.IsConnected();
     if(MetaConectado)
      {
       if(Tel11.Length() != 11)
        {
         ShowMensagem(
          "WhatsApp Meta esta CONECTADO.\\r\\n"
          "Informe telefone com 11 digitos (DDD+numero) para enviar via Cloud API.");
         return;
        }
       if(enviarViaWhatsMeta(ArqRelatorio, Tel11, CapMeta, ErroMeta))
        {
         AnsiString MensaLog = "WhatsMeta Cloud API OK\\r\\nRelatorio: " + NomeRelatorio + "\\r\\n";
         MensaLog += "Telefone: " + Tel11 + "\\r\\n";
         vg.IncluiLog(NULL,0,"99999018",MensaLog);
         ShowMensagem("Relatorio enviado via WhatsApp Meta (Cloud API).");
         Close();
         return;
        }
       ShowMensagem(
        "Falha no envio via WhatsApp Meta.\\r\\n" + ErroMeta +
        "\\r\\n\\r\\nNao sera usado Whats.exe automaticamente enquanto Meta estiver conectado.");
       return;
      }
     if(enviarViaWhatsMeta(ArqRelatorio, Tel11, CapMeta, ErroMeta))
      {
       AnsiString MensaLog = "WhatsMeta Cloud API OK\\r\\nRelatorio: " + NomeRelatorio + "\\r\\n";
       MensaLog += "Telefone: " + Tel11 + "\\r\\n";
       vg.IncluiLog(NULL,0,"99999018",MensaLog);
       ShowMensagem("Relatorio enviado via WhatsApp Meta (Cloud API).");
       Close();
       return;
      }
    }'''

    # The new string has \\r\\n which in Python becomes \r\n in output - but we need C++ source to contain backslash-r-backslash-n
    # Use raw strings carefully.

    new = r'''    // Preferencia: Cloud API via agente WHATSPH (se CONECTADO).
    // Se Meta esta CONECTADO, nao cair no Whats.exe em silencio.
    // Fallback legado so quando Meta indisponivel/desconectado.
    {
     AnsiString ErroMeta;
     AnsiString CapMeta = Edit1->Text.Trim();
     if(CapMeta.IsEmpty())
      CapMeta = NomeRelatorio;
     AnsiString Tel11 = MaskEdit1->Text.Trim();
     TWhatsMetaClient CliChk;
     bool MetaLoaded = CliChk.LoadFromWhatsPhEnv(vg.DiretorioPrincipal);
     if(!MetaLoaded)
      MetaLoaded = CliChk.LoadFromWhatsPhEnv("C:\\PHSFTW");
     if(!MetaLoaded)
      MetaLoaded = CliChk.LoadFromWhatsPhEnv("D:\\PHSFTW");
     bool MetaConectado = MetaLoaded && CliChk.HealthOk() && CliChk.IsConnected();
     if(MetaConectado)
      {
       if(Tel11.Length() != 11)
        {
         ShowMensagem(
          "WhatsApp Meta esta CONECTADO.\r\n"
          "Informe telefone com 11 digitos (DDD+numero) para enviar via Cloud API.");
         return;
        }
       if(enviarViaWhatsMeta(ArqRelatorio, Tel11, CapMeta, ErroMeta))
        {
         AnsiString MensaLog = "WhatsMeta Cloud API OK\r\nRelatorio: " + NomeRelatorio + "\r\n";
         MensaLog += "Telefone: " + Tel11 + "\r\n";
         vg.IncluiLog(NULL,0,"99999018",MensaLog);
         ShowMensagem("Relatorio enviado via WhatsApp Meta (Cloud API).");
         Close();
         return;
        }
       ShowMensagem(
        "Falha no envio via WhatsApp Meta.\r\n" + ErroMeta +
        "\r\n\r\nNao sera usado Whats.exe automaticamente enquanto Meta estiver conectado.");
       return;
      }
     if(enviarViaWhatsMeta(ArqRelatorio, Tel11, CapMeta, ErroMeta))
      {
       AnsiString MensaLog = "WhatsMeta Cloud API OK\r\nRelatorio: " + NomeRelatorio + "\r\n";
       MensaLog += "Telefone: " + Tel11 + "\r\n";
       vg.IncluiLog(NULL,0,"99999018",MensaLog);
       ShowMensagem("Relatorio enviado via WhatsApp Meta (Cloud API).");
       Close();
       return;
      }
    }'''

    if "MetaConectado" in t:
        print("SenWA skip")
        return

    old_crlf = old.replace("\n", "\r\n")
    new_crlf = new.replace("\n", "\r\n")
    if old_crlf not in t:
        idx = t.find("Preferencia: Cloud API")
        print(repr(t[idx - 20 : idx + 500]))
        raise SystemExit("SenWA block not found")
    t = t.replace(old_crlf, new_crlf)
    write_cp1252(p, t)
    print("SenWA OK")


def main() -> int:
    patch_whatsmeta_ui()
    patch_preview_h()
    patch_preview_cpp()
    patch_senwa()
    # verify
    prev = read_cp1252(PHVCL / "Preview.cpp")
    assert "enviarWhatsGrupoBoletosMeta" in prev
    assert "WhatsMetaEstaDisponivel" in prev
    assert "Meta Cloud API esta CONECTADO" in prev
    ui = read_cp1252(PHVCL / "WhatsMetaUi.cpp")
    assert "WhatsMetaEstaDisponivel" in ui
    sen = read_cp1252(PHVCL / "SenWA.cpp")
    assert "MetaConectado" in sen
    print("ALL ASSERTS OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
