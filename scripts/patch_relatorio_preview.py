# -*- coding: utf-8 -*-
"""Liga Preview avulso ao modelo ph_relatorio_pdf (CP1252)."""
from __future__ import annotations

from pathlib import Path


def read(p: Path) -> str:
    return p.read_bytes().decode("cp1252").replace("\r\n", "\n").replace("\r", "\n")


def write(p: Path, t: str) -> None:
    p.write_bytes(t.replace("\n", "\r\n").encode("cp1252"))


def must(t: str, old: str, new: str, label: str) -> str:
    n = t.count(old)
    if n == 0:
        raise SystemExit(f"MISSING [{label}]")
    return t.replace(old, new)


def main() -> int:
    h = Path(r"C:\CBuilder5\Projects\Lib\phvcl\WhatsMetaClient.h")
    c = Path(r"C:\CBuilder5\Projects\Lib\phvcl\WhatsMetaClient.cpp")
    p = Path(r"C:\CBuilder5\Projects\Lib\phvcl\Preview.cpp")
    s = Path(r"C:\CBuilder5\Projects\Lib\phvcl\SenWA.cpp")

    ht = read(h)
    if "AnsiString EnvioTipo" not in ht:
        ht = must(
            ht,
            """    AnsiString DiretorioSecundario,
    AnsiString BodyName
  );""",
            """    AnsiString DiretorioSecundario,
    AnsiString BodyName,
    AnsiString EnvioTipo
  );""",
            "h sig",
        )
        write(h, ht)
    print("h OK")

    ct = read(c)
    if "AnsiString EnvioTipo" not in ct:
        ct = must(
            ct,
            """  AnsiString DiretorioSecundario,
  AnsiString BodyName
)""",
            """  AnsiString DiretorioSecundario,
  AnsiString BodyName,
  AnsiString EnvioTipo
)""",
            "cpp sig",
        )
        ct = must(
            ct,
            """  LastWarning = "";
  AnsiString Json = "{";""",
            """  LastWarning = "";
  if(EnvioTipo.IsEmpty())
   EnvioTipo = "boleto";
  AnsiString Json = "{";""",
            "cpp default tipo",
        )
        ct = must(
            ct,
            'Json += "\\"body_name\\":\\"" + JsonEscape(BodyName) + "\\"";',
            'Json += "\\"body_name\\":\\"" + JsonEscape(BodyName) + "\\",";\n'
            '  Json += "\\"envio_tipo\\":\\"" + JsonEscape(EnvioTipo) + "\\"";',
            "cpp json",
        )
        write(c, ct)
    print("cpp OK")

    pt = read(p)
    if '"boleto"' not in pt[pt.find("enviarWhatsGrupoBoletosMeta"):pt.find("enviarWhatsGrupoBoletos(void)")]:
        pt = must(
            pt,
            """               vg.DiretorioSecundario,
               Nome))""",
            """               vg.DiretorioSecundario,
               Nome,
               "boleto"))""",
            "preview call",
        )
        write(p, pt)
    print("preview OK")

    st = read(s)
    st = must(
        st,
        """static bool enviarViaWhatsMeta(
  AnsiString ArqPdf,
  AnsiString Telefone11,
  AnsiString Caption,
  AnsiString &OutErro
)""",
        """static bool enviarViaWhatsMeta(
  AnsiString ArqPdf,
  AnsiString Telefone11,
  AnsiString Caption,
  AnsiString NomeRelatorio,
  AnsiString &OutErro,
  AnsiString &OutWarning
)""",
        "sen sig",
    )
    st = must(
        st,
        """  OutErro = "";
  if(Telefone11.Trim().Length() != 11)""",
        """  OutErro = "";
  OutWarning = "";
  if(Telefone11.Trim().Length() != 11)""",
        "sen clear warning",
    )
    st = must(
        st,
        """       vg.DiretorioSecundario,
       ""))
   return true;""",
        """       vg.DiretorioSecundario,
       NomeRelatorio,
       "relatorio"))
   {
    OutWarning = Cli.LastWarning;
    return true;
   }""",
        "sen send",
    )
    st = must(
        st,
        """     AnsiString ErroMeta;
     AnsiString CapMeta = Edit1->Text.Trim();
     if(CapMeta.IsEmpty())
      CapMeta = NomeRelatorio;""",
        """     AnsiString ErroMeta;
     AnsiString AvisoMeta;
     AnsiString CapMeta = "Relatório gerado no Sistema PH em anexo.";
     if(!NomeRelatorio.IsEmpty())
      CapMeta += "\\r\\n" + NomeRelatorio;""",
        "sen caption",
    )
    if st.count("enviarViaWhatsMeta(ArqRelatorio, Tel11, CapMeta, ErroMeta)") != 2:
        raise SystemExit("sen calls count != 2")
    st = st.replace(
        "enviarViaWhatsMeta(ArqRelatorio, Tel11, CapMeta, ErroMeta)",
        "enviarViaWhatsMeta(ArqRelatorio, Tel11, CapMeta, NomeRelatorio, ErroMeta, AvisoMeta)",
    )
    old_ok = 'ShowMensagem("Relatório enviado pelo WhatsApp.");'
    if st.count(old_ok) != 2:
        raise SystemExit(f"sen ok msg count {st.count(old_ok)}")
    st = st.replace(
        old_ok,
        'ShowMensagem(AvisoMeta.IsEmpty()\n'
        '          ? AnsiString("Relatório enviado pelo WhatsApp.")\n'
        '          : AnsiString("Relatório enviado pelo WhatsApp.\\r\\n\\r\\n") + AvisoMeta);',
    )
    write(s, st)
    print("senwa OK")

    # verify
    ht, ct, pt, st = read(h), read(c), read(p), read(s)
    assert "EnvioTipo" in ht and "EnvioTipo" in ct
    assert "envio_tipo" in ct
    assert '"boleto"' in pt
    assert '"relatorio"' in st
    assert "ph_relatorio" not in st  # nome fica no agente
    assert "Relatório gerado no Sistema PH em anexo." in st
    assert "AvisoMeta" in st
    print("VERIFY OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
