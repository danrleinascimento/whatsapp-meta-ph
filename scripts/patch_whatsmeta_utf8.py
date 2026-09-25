# -*- coding: utf-8 -*-
"""Converte o JSON do agente para UTF-8 (CP1252 do BCB5 quebrava 'Relatorio')."""
from __future__ import annotations

from pathlib import Path


def read(p: Path) -> str:
    return p.read_bytes().decode("cp1252").replace("\r\n", "\n").replace("\r", "\n")


def write(p: Path, t: str) -> None:
    p.write_bytes(t.replace("\n", "\r\n").encode("cp1252"))


def must(t: str, old: str, new: str, label: str) -> str:
    n = t.count(old)
    if n != 1:
        raise SystemExit(f"COUNT {n} [{label}]")
    return t.replace(old, new, 1)


HELPERS = r'''//---------------------------------------------------------------------------
// JSON do FastAPI e UTF-8. O BCB5 monta o texto em CP1252.
// Sem esta conversao, "Relatorio" (byte F3) faz o agente rejeitar o corpo.
static AnsiString Cp1252ToUtf8(AnsiString S)
{
  if(S.IsEmpty())
   return S;
  int Wlen = MultiByteToWideChar(1252, 0, S.c_str(), S.Length(), NULL, 0);
  if(Wlen <= 0)
   return S;
  wchar_t *W = new wchar_t[Wlen + 1];
  W[Wlen] = 0;
  if(!MultiByteToWideChar(1252, 0, S.c_str(), S.Length(), W, Wlen))
   {
    delete[] W;
    return S;
   }
  int Ulen = WideCharToMultiByte(65001, 0, W, Wlen, NULL, 0, NULL, NULL);
  if(Ulen <= 0)
   {
    delete[] W;
    return S;
   }
  char *U = new char[Ulen + 1];
  U[Ulen] = 0;
  if(!WideCharToMultiByte(65001, 0, W, Wlen, U, Ulen, NULL, NULL))
   {
    delete[] U;
    delete[] W;
    return S;
   }
  AnsiString Out;
  Out.SetLength(Ulen);
  for(int i = 0; i < Ulen; i++)
   Out[i + 1] = U[i];
  delete[] U;
  delete[] W;
  return Out;
}
//---------------------------------------------------------------------------
static AnsiString Utf8ToCp1252(AnsiString S)
{
  if(S.IsEmpty())
   return S;
  int Wlen = MultiByteToWideChar(65001, 8, S.c_str(), S.Length(), NULL, 0);
  if(Wlen <= 0)
   return S;
  wchar_t *W = new wchar_t[Wlen + 1];
  W[Wlen] = 0;
  if(!MultiByteToWideChar(65001, 8, S.c_str(), S.Length(), W, Wlen))
   {
    delete[] W;
    return S;
   }
  int Alen = WideCharToMultiByte(1252, 0, W, Wlen, NULL, 0, NULL, NULL);
  if(Alen <= 0)
   {
    delete[] W;
    return S;
   }
  char *A = new char[Alen + 1];
  A[Alen] = 0;
  if(!WideCharToMultiByte(1252, 0, W, Wlen, A, Alen, NULL, NULL))
   {
    delete[] A;
    delete[] W;
    return S;
   }
  AnsiString Out;
  Out.SetLength(Alen);
  for(int i = 0; i < Alen; i++)
   Out[i + 1] = A[i];
  delete[] A;
  delete[] W;
  return Out;
}
//---------------------------------------------------------------------------
'''


def main() -> int:
    p = Path(r"C:\CBuilder5\Projects\Lib\phvcl\WhatsMetaClient.cpp")
    t = read(p)
    if "Cp1252ToUtf8" in t:
        print("JA_APLICADO")
        return 0
    t = must(
        t,
        "//---------------------------------------------------------------------------\nAnsiString TWhatsMetaClient::HttpGet(AnsiString Path)\n",
        HELPERS + "AnsiString TWhatsMetaClient::HttpGet(AnsiString Path)\n",
        "helpers",
    )
    t = must(
        t,
        "      Body = Http->Get(BaseUrl + Path);\n",
        "      Body = Utf8ToCp1252(Http->Get(BaseUrl + Path));\n",
        "get body",
    )
    t = must(
        t,
        "  TStringStream *Req = new TStringStream(JsonBody);\n",
        "  TStringStream *Req = new TStringStream(Cp1252ToUtf8(JsonBody));\n",
        "post req",
    )
    t = must(
        t,
        "      Http->Post(BaseUrl + Path, Req, Resp);\n      Body = Resp->DataString;\n",
        "      Http->Post(BaseUrl + Path, Req, Resp);\n      Body = Utf8ToCp1252(Resp->DataString);\n",
        "post ok",
    )
    t = must(
        t,
        "      try { Body = Resp->DataString; } catch(...) {}\n",
        "      try { Body = Utf8ToCp1252(Resp->DataString); } catch(...) {}\n",
        "post err",
    )
    write(p, t)
    t2 = read(p)
    assert "Cp1252ToUtf8" in t2 and "Utf8ToCp1252" in t2
    assert t2.count("Cp1252ToUtf8(JsonBody)") == 1
    assert t2.count("Utf8ToCp1252(") == 3
    assert "\ufeff" not in t2
    print("PATCH_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
