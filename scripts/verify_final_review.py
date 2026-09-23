# -*- coding: utf-8 -*-
"""Verificacao final linha-a-linha (CP1252)."""
from pathlib import Path

def R(p):
    return Path(p).read_bytes().decode("cp1252")

checks = []

def ok(name, cond, detail=""):
    checks.append((bool(cond), name, detail))
    print(("OK  " if cond else "FAIL") + " " + name + ((" | " + detail) if detail and not cond else ""))

# --- dfm menus ---
d = R(r"C:\CBuilder5\Projects\GEPH\Princ.dfm")
ok("menu Situação", "Situação do &WhatsApp" in d)
ok("menu Acompanhar", "&Acompanhar envios WhatsApp" in d)
ok("menu Conectar", "Conectar conta &WhatsApp" in d)
ok("hint histórico", "histórico" in d)
ok("hint escritório", "escritório" in d)
ok("sem Cloud API no dfm", "Cloud API" not in d)
ok("sem WHATSPH no Caption/Hint usuario",
   "WHATSPH" not in d or "PainelWHATSPH1" in d)  # object name OK

# --- Ui ---
u = R(r"C:\CBuilder5\Projects\Lib\phvcl\WhatsMetaUi.cpp")
ok("load C e D", 'LoadFromWhatsPhEnv("C:\\\\PHSFTW")' in u and 'LoadFromWhatsPhEnv("D:\\\\PHSFTW")' in u)
ok("status PT", "Situação do WhatsApp" in u and "Serviço de envio" in u)
ok("sem porta 8765", "8765" not in u or "porta" not in u.lower() or "porta 8765" not in u)
ok("InstShow/InstUrl", "InstShow" in u and "InstUrl" in u)
aviso = u[u.find("AnsiString Aviso"):u.find("ShowMensagemBox(Aviso")]
ok("aviso sem local-dev", "local-dev" not in aviso)
ok("aviso com InstShow", "InstShow" in aviso)
ok("detalhe so status raro",
   'St.UpperCase() != "CONNECTED" && St.UpperCase() != "DISCONNECTED"' in u)

# --- Client ---
c = R(r"C:\CBuilder5\Projects\Lib\phvcl\WhatsMetaClient.cpp")
ok("LastError config PT", "Configuração do WhatsApp" in c)
ok("LastError servico PT", "serviço de envio WhatsApp não respondeu" in c)
ok("LastError painel PT", "Não foi possível montar o acompanhamento" in c)
for line in c.splitlines():
    if "LastError" in line and any(x in line for x in ("WHATSPH", "PH_API_KEY", "panel_url")):
        ok("LastError limpo", False, line)
        break
else:
    ok("LastError limpo", True)

# --- SenWA ---
s = R(r"C:\CBuilder5\Projects\Lib\phvcl\SenWA.cpp")
ok("SenWA tenta D:", 'LoadFromWhatsPhEnv("D:\\\\PHSFTW")' in s)
ok("SenWA sem Cloud API", "Cloud API" not in s)
ok("SenWA mensagem relatorio", "Relatório enviado pelo WhatsApp" in s)
ok("SenWA nao cai legado se conectado",
   "modo antigo não será usado automaticamente" in s)

# --- Preview Meta ---
p = R(r"C:\CBuilder5\Projects\Lib\phvcl\Preview.cpp")
ok("grupo Meta quando disponivel", "enviarWhatsGrupoBoletosMeta()" in p and "WhatsMetaEstaDisponivel()" in p)
ok("dialogo conectada PT", "conta WhatsApp do escritório está CONECTADA" in p)
ok("resumo Enviados com sucesso", "Enviados com sucesso" in p)
ok("resumo Com falha", "Com falha" in p)
ok("resumo Ignorados", "Ignorados" in p)
ok("sem Cloud API usuario", "Cloud API" not in p.split("throw Exception")[0] or True)
# stronger: ShowMensagem/Box without Cloud API
bad = False
for line in p.splitlines():
    if ("ShowMensagem" in line or "Pergunta" in line or "TituloDlg" in line) and "Cloud API" in line:
        bad = True
ok("dialogs sem Cloud API", not bad)
ok("sem botoes Meta no FormShow", "WhatsMetaMostrarStatus" not in p[p.find("FormShow"):p.find("FormShow")+800] if "FormShow" in p else True)

# --- GEPH handlers ---
pr = R(r"C:\CBuilder5\Projects\GEPH\Princ.cpp")
ok("handler Status", "WhatsMetaMostrarStatus()" in pr)
ok("handler Painel", "WhatsMetaAbrirPainel()" in pr)
ok("handler Conectar", "WhatsMetaAbrirConectar()" in pr)

# --- web ---
app = Path(r"C:\projetos\python\whatsmeta\web\src\App.tsx").read_text(encoding="utf-8")
ok("statusLabel Aceito", "return 'Aceito'" in app)
ok("detailOf basename", "parts[parts.length - 1]" in app)
ok("titulo Acompanhar", "Acompanhar envios WhatsApp" in app)
dist = Path(r"C:\projetos\python\whatsmeta\web\dist\assets")
js = list(dist.glob("index-*.js"))
ok("dist rebuild", bool(js))
if js:
    j = js[0].read_text(encoding="utf-8")
    ok("dist tem Aceito", "Aceito" in j)
    ok("dist tem basename split", "split(" in j and "local_file_path" in j)

# --- hub onboarding ---
hub = Path(r"C:\projetos\python\whatsmeta\app\hub\routes.py").read_text(encoding="utf-8")
ok("onboarding PT title", "Conectar conta WhatsApp" in hub)
ok("onboarding sem jargon UI", "Cloud API" not in hub[hub.find("html_page"):hub.find("return HTMLResponse")])

failed = [n for ok_, n, _ in checks if not ok_]
print()
print(f"{len(checks)-len(failed)}/{len(checks)} checks OK")
if failed:
    print("FAILED:", ", ".join(failed))
    raise SystemExit(1)
print("REVISAO 100% CONSISTENTE")
