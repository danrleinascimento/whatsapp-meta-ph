# -*- coding: utf-8 -*-
"""Reaplica LastWarning + body_name + resumo Aceitos pela Meta (CP1252)."""
from __future__ import annotations

from pathlib import Path


def read(p: Path) -> str:
    return p.read_bytes().decode("cp1252").replace("\r\n", "\n").replace("\r", "\n")


def write(p: Path, t: str) -> None:
    p.write_bytes(t.replace("\n", "\r\n").encode("cp1252"))


def must(t: str, old: str, new: str, label: str) -> str:
    if old not in t:
        raise SystemExit(f"MISSING [{label}]: {old[:120]!r}")
    return t.replace(old, new, 1)


def main() -> int:
    h_path = Path(r"C:\CBuilder5\Projects\Lib\phvcl\WhatsMetaClient.h")
    c_path = Path(r"C:\CBuilder5\Projects\Lib\phvcl\WhatsMetaClient.cpp")
    p_path = Path(r"C:\CBuilder5\Projects\Lib\phvcl\Preview.cpp")
    s_path = Path(r"C:\CBuilder5\Projects\Lib\phvcl\SenWA.cpp")

    h = read(h_path)
    if "LastWarning" not in h:
        h = must(
            h,
            "  AnsiString LastError;\n",
            "  AnsiString LastError;\n  AnsiString LastWarning;\n",
            "h LastWarning",
        )
    if "BodyName" not in h:
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
            "h SendDocument sig",
        )
    write(h_path, h)
    print("WhatsMetaClient.h OK")

    c = read(c_path)
    if "LastWarning = \"\";" not in c.split("TWhatsMetaClient::TWhatsMetaClient()")[1][:250]:
        c = must(
            c,
            """TWhatsMetaClient::TWhatsMetaClient()
{
  BaseUrl = "http://127.0.0.1:8765";
  ApiKey = "";
  InstallationId = "";
  HubBaseUrl = "https://whatsapp-meta-ph-wzewk.ondigitalocean.app";
  TimeoutMs = 120000;
  LastError = "";
}""",
            """TWhatsMetaClient::TWhatsMetaClient()
{
  BaseUrl = "http://127.0.0.1:8765";
  ApiKey = "";
  InstallationId = "";
  HubBaseUrl = "https://whatsapp-meta-ph-wzewk.ondigitalocean.app";
  TimeoutMs = 120000;
  LastError = "";
  LastWarning = "";
}""",
            "cpp ctor",
        )
    # LoadFromWhatsPhEnv clear
    if 'bool TWhatsMetaClient::LoadFromWhatsPhEnv(AnsiString PhsftwRoot)\n{\n  LastError = "";\n  LastWarning = "";' not in c:
        c = must(
            c,
            'bool TWhatsMetaClient::LoadFromWhatsPhEnv(AnsiString PhsftwRoot)\n{\n  LastError = "";\n',
            'bool TWhatsMetaClient::LoadFromWhatsPhEnv(AnsiString PhsftwRoot)\n{\n  LastError = "";\n  LastWarning = "";\n',
            "cpp LoadFrom clear",
        )

    # Full SendDocument — keep existing LastError accents from file by reading exact slice
    start = c.find("bool TWhatsMetaClient::SendDocument(")
    end = c.find("bool TWhatsMetaClient::CreatePanelTicket(", start)
    if start < 0 or end < 0:
        raise SystemExit("SendDocument/CreatePanelTicket markers missing")
    old_fn = c[start:end]
    if "BodyName" in old_fn and "LastWarning" in old_fn and "body_name" in old_fn:
        print("cpp SendDocument already patched")
    else:
        new_fn = """bool TWhatsMetaClient::SendDocument(
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
}
//---------------------------------------------------------------------------
"""
        c = c[:start] + new_fn + c[end:]
        print("cpp SendDocument patched")
    write(c_path, c)
    print("WhatsMetaClient.cpp OK")

    p = read(p_path)
    if "AVISO Meta" not in p:
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
             "', numero " + ToPhone);
            if(PR->EventoWhatsOk)
             PR->EventoWhatsOk(PR, Codigo);
           }""",
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
             Log->Add("AVISO Meta: " + Cli.LastWarning);
            if(PR->EventoWhatsOk)
             PR->EventoWhatsOk(PR, Codigo);
           }""",
            "preview call",
        )
    if "Aceitos pela Meta" not in p:
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
    write(p_path, p)
    print("Preview.cpp OK")

    s = read(s_path)
    if 'vg.DiretorioSecundario,\n       ""))' not in s and 'vg.DiretorioSecundario,\n       ""))' not in s:
        # exact 7-arg call
        old = """  if(Cli.SendDocument(
       ToPhone,
       ArqPdf,
       Caption,
       vg.NomeUsuario,
       vg.DiretorioPrincipal,
       vg.DiretorioSecundario))
   return true;"""
        new = """  if(Cli.SendDocument(
       ToPhone,
       ArqPdf,
       Caption,
       vg.NomeUsuario,
       vg.DiretorioPrincipal,
       vg.DiretorioSecundario,
       ""))
   return true;"""
        if old not in s:
            raise SystemExit("MISSING SenWA SendDocument call")
        s = s.replace(old, new, 1)
        write(s_path, s)
        print("SenWA.cpp OK")
    else:
        print("SenWA already OK")

    # Final verify
    checks = {
        h_path: ["LastWarning", "BodyName"],
        c_path: ["LastWarning", "body_name", "JsonStringValue(R, \"warning\")"],
        p_path: ["AVISO Meta", "Aceitos pela Meta", "Acompanhar envios"],
        s_path: ['DiretorioSecundario,\n       "")'],
    }
    for path, keys in checks.items():
        text = read(path)
        for k in keys:
            if k not in text:
                raise SystemExit(f"VERIFY FAIL {path.name}: missing {k!r}")
            print("VERIFY", path.name, k, "OK")
    print("ALL REAPPLIED OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
