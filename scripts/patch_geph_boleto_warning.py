# -*- coding: utf-8 -*-
"""GEPH/PHVCL: warning Meta 24h + body_name no SendDocument (CP1252)."""
from pathlib import Path

CLIENT_H = Path(r"C:\CBuilder5\Projects\Lib\phvcl\WhatsMetaClient.h")
CLIENT_CPP = Path(r"C:\CBuilder5\Projects\Lib\phvcl\WhatsMetaClient.cpp")
PREVIEW = Path(r"C:\CBuilder5\Projects\Lib\phvcl\Preview.cpp")


def rw(p: Path) -> str:
    return p.read_bytes().decode("cp1252").replace("\r\n", "\n").replace("\r", "\n")


def ww(p: Path, t: str) -> None:
    p.write_bytes(t.replace("\n", "\r\n").encode("cp1252"))


def must(t: str, old: str, new: str, label: str) -> str:
    if old not in t:
        raise SystemExit(f"MISSING {label}: {old[:90]!r}")
    return t.replace(old, new)


def main() -> int:
    h = rw(CLIENT_H)
    h = must(
        h,
        "  AnsiString LastError;\n",
        "  AnsiString LastError;\n  AnsiString LastWarning;\n",
        "h LastWarning",
    )
    h = must(
        h,
        """  bool SendDocument(
    AnsiString ToPhone,
    AnsiString FilePath,
    AnsiString Caption,
    AnsiString UsuarioGeph,
    AnsiString DiretorioPrincipal,
    AnsiString DiretorioSecundario
  );""",
        """  bool SendDocument(
    AnsiString ToPhone,
    AnsiString FilePath,
    AnsiString Caption,
    AnsiString UsuarioGeph,
    AnsiString DiretorioPrincipal,
    AnsiString DiretorioSecundario,
    AnsiString BodyName
  );""",
        "h SendDocument",
    )
    ww(CLIENT_H, h)
    print("h OK")

    c = rw(CLIENT_CPP)
    # ctor clear LastWarning
    if "LastWarning" not in c:
        c = must(
            c,
            "  LastError = \"\";\n",
            "  LastError = \"\";\n  LastWarning = \"\";\n",
            "cpp ctor",
        )
    c = must(
        c,
        """bool TWhatsMetaClient::SendDocument(
  AnsiString ToPhone,
  AnsiString FilePath,
  AnsiString Caption,
  AnsiString UsuarioGeph,
  AnsiString DiretorioPrincipal,
  AnsiString DiretorioSecundario
)
{
  AnsiString Json = "{";
  Json += "\\"to\\":\\"" + JsonEscape(ToPhone) + "\\",";
  Json += "\\"file_path\\":\\"" + JsonEscape(FilePath) + "\\",";
  Json += "\\"caption\\":\\"" + JsonEscape(Caption) + "\\",";
  Json += "\\"usuario_geph\\":\\"" + JsonEscape(UsuarioGeph) + "\\",";
  Json += "\\"sistema_origem\\":\\"GEPH\\",";
  Json += "\\"diretorio_principal\\":\\"" + JsonEscape(DiretorioPrincipal) + "\\",";
  Json += "\\"diretorio_secundario\\":\\"" + JsonEscape(DiretorioSecundario) + "\\"";
  Json += "}";

  AnsiString R = HttpPostJson("/v1/whatsapp/send-document", Json);
  if(R.IsEmpty())
   {
    if(LastError.IsEmpty())
     LastError = "O serviço de envio WhatsApp não respondeu.";
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
}""",
        """bool TWhatsMetaClient::SendDocument(
  AnsiString ToPhone,
  AnsiString FilePath,
  AnsiString Caption,
  AnsiString UsuarioGeph,
  AnsiString DiretorioPrincipal,
  AnsiString DiretorioSecundario,
  AnsiString BodyName
)
{
  LastWarning = "";
  AnsiString Json = "{";
  Json += "\\"to\\":\\"" + JsonEscape(ToPhone) + "\\",";
  Json += "\\"file_path\\":\\"" + JsonEscape(FilePath) + "\\",";
  Json += "\\"caption\\":\\"" + JsonEscape(Caption) + "\\",";
  Json += "\\"usuario_geph\\":\\"" + JsonEscape(UsuarioGeph) + "\\",";
  Json += "\\"sistema_origem\\":\\"GEPH\\",";
  Json += "\\"diretorio_principal\\":\\"" + JsonEscape(DiretorioPrincipal) + "\\",";
  Json += "\\"diretorio_secundario\\":\\"" + JsonEscape(DiretorioSecundario) + "\\",";
  Json += "\\"body_name\\":\\"" + JsonEscape(BodyName) + "\\"";
  Json += "}";

  AnsiString R = HttpPostJson("/v1/whatsapp/send-document", Json);
  if(R.IsEmpty())
   {
    if(LastError.IsEmpty())
     LastError = "O serviço de envio WhatsApp não respondeu.";
    return false;
   }
  if(JsonBoolTrue(R, "ok"))
   {
    LastWarning = JsonStringValue(R, "warning");
    return true;
   }
  AnsiString Detail = JsonStringValue(R, "detail");
  if(Detail.IsEmpty())
   Detail = JsonStringValue(R, "error");
  if(Detail.IsEmpty())
   Detail = R.SubString(1, 300);
  LastError = Detail;
  return false;
}""",
        "cpp SendDocument",
    )
    ww(CLIENT_CPP, c)
    print("cpp OK")

    p = rw(PREVIEW)
    p = must(
        p,
        """          if(Cli.SendDocument(
               ToPhone,
               FileName,
               Cap,
               vg.NomeUsuario,
               vg.DiretorioPrincipal,
               vg.DiretorioSecundario))
           {
            Ok++;
            Log->Add("OK boleto " + Codigo + " '" + Nome +
             "', numero " + ToPhone);""",
        """          if(Cli.SendDocument(
               ToPhone,
               FileName,
               Cap,
               vg.NomeUsuario,
               vg.DiretorioPrincipal,
               vg.DiretorioSecundario,
               Nome))
           {
            Ok++;
            Log->Add("OK boleto " + Codigo + " '" + Nome +
             "', numero " + ToPhone);
            if(!Cli.LastWarning.IsEmpty())
             Log->Add("AVISO Meta: " + Cli.LastWarning);""",
        "preview SendDocument",
    )
    p = must(
        p,
        """    ShowMensagem("Envio WhatsApp em grupo finalizado.\\r\\nEnviados com sucesso: " + IntToStr(Ok) +
     "\\r\\nCom falha: " + IntToStr(Erro) + "\\r\\nIgnorados: " + IntToStr(Pulados));""",
        """    ShowMensagem("Envio WhatsApp em grupo finalizado.\\r\\n"
     "Aceitos pela Meta: " + IntToStr(Ok) +
     "\\r\\nCom falha: " + IntToStr(Erro) +
     "\\r\\nIgnorados: " + IntToStr(Pulados) +
     "\\r\\n\\r\\nConfira no celular e em Acompanhar envios "
     "(Aceito pela Meta ainda nao e entrega no WhatsApp).");""",
        "preview summary",
    )
    ww(PREVIEW, p)
    print("preview OK")

    # SenWA call sites - 4-arg SendDocument needs BodyName ""
    sen = Path(r"C:\CBuilder5\Projects\Lib\phvcl\SenWA.cpp")
    s = rw(sen)
    old_sen = """  if(Cli.SendDocument(
       ToPhone,
       ArqPdf,
       Caption,
       vg.NomeUsuario,
       vg.DiretorioPrincipal,
       vg.DiretorioSecundario))
   return true;"""
    new_sen = """  if(Cli.SendDocument(
       ToPhone,
       ArqPdf,
       Caption,
       vg.NomeUsuario,
       vg.DiretorioPrincipal,
       vg.DiretorioSecundario,
       ""))
   return true;"""
    if old_sen in s:
        s = s.replace(old_sen, new_sen)
        ww(sen, s)
        print("SenWA OK")
    else:
        print("SenWA WARN — conferir assinatura manualmente")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
