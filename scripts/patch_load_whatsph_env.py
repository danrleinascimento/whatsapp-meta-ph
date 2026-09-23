# -*- coding: utf-8 -*-
"""Rewrite TWhatsMetaClient::LoadFromWhatsPhEnv with robust path search (CP1252)."""
from pathlib import Path

CLIENT_CPP = Path(r"C:\CBuilder5\Projects\Lib\phvcl\WhatsMetaClient.cpp")

NEW_FN = r"""bool TWhatsMetaClient::LoadFromWhatsPhEnv(AnsiString PhsftwRoot)
{
  LastError = "";
  TStringList *Cands = new TStringList();
  try
   {
    AnsiString H = PhsftwRoot.Trim();
    if(!H.IsEmpty())
     {
      if(H[H.Length()] != '\\')
       H += "\\";
      Cands->Add(H + "WHATSPH\\.env");
      Cands->Add(H + ".env");

      AnsiString Walk = H;
      for(int w = 0; w < 12; w++)
       {
        AnsiString NoSlash = Walk;
        if(NoSlash.Length() > 0 && NoSlash[NoSlash.Length()] == '\\')
         NoSlash = NoSlash.SubString(1, NoSlash.Length() - 1);
        AnsiString Parent = ExtractFilePath(NoSlash);
        if(Parent.IsEmpty() || Parent == Walk)
         break;
        if(Parent[Parent.Length()] != '\\')
         Parent += "\\";
        AnsiString Cand = Parent + "WHATSPH\\.env";
        if(Cands->IndexOf(Cand) < 0)
         Cands->Add(Cand);
        Walk = Parent;
       }
     }

    if(Cands->IndexOf("C:\\PHSFTW\\WHATSPH\\.env") < 0)
     Cands->Add("C:\\PHSFTW\\WHATSPH\\.env");
    if(Cands->IndexOf("D:\\PHSFTW\\WHATSPH\\.env") < 0)
     Cands->Add("D:\\PHSFTW\\WHATSPH\\.env");

    for(int c = 0; c < Cands->Count; c++)
     {
      AnsiString EnvPath = Cands->Strings[c];
      if(!FileExists(EnvPath))
       continue;

      TStringList *L = new TStringList();
      try
       {
        L->LoadFromFile(EnvPath);
        ApiKey = "";
        InstallationId = "";
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
          V = TrimLineKeyValue(L->Strings[i], "HUB_BASE_URL");
          if(V != "")
           {
            while(V.Length() > 0 && V[V.Length()] == '/')
             V = V.SubString(1, V.Length() - 1);
            HubBaseUrl = V;
           }
         }
       }
      __finally
       {
        delete L;
       }

      if(ApiKey.IsEmpty())
       {
        LastError = "PH_API_KEY ausente em: " + EnvPath;
        continue;
       }
      LastError = "";
      return true;
     }
   }
  __finally
   {
    delete Cands;
   }
  if(LastError.IsEmpty())
   LastError = "WHATSPH\\.env nao encontrado (C:\\PHSFTW ou D:\\PHSFTW)";
  return false;
}
"""


def main() -> int:
    t = CLIENT_CPP.read_text(encoding="cp1252")
    old_start = t.find("bool TWhatsMetaClient::LoadFromWhatsPhEnv(AnsiString PhsftwRoot)")
    if old_start < 0:
        raise SystemExit("LoadFromWhatsPhEnv not found")
    je = t.find("AnsiString TWhatsMetaClient::JsonEscape")
    if je < 0:
        raise SystemExit("JsonEscape not found")
    sep = t.rfind("//---------------------------------------------------------------------------", old_start, je)
    if sep < 0:
        raise SystemExit("separator before JsonEscape not found")
    t2 = t[:old_start] + NEW_FN + t[sep:]
    CLIENT_CPP.write_text(t2, encoding="cp1252", newline="\r\n")
    assert "HubBaseUrl" in t2
    assert "D:\\PHSFTW\\WHATSPH\\.env" in t2
    print("OK rewritten", CLIENT_CPP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
