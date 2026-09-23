; Inno Setup 6 — WHATSPH (PH Softwares)
; 1) Rodar scripts\build_dist.ps1
; 2) Colocar nssm.exe em dist\whatsph\nssm\
; 3) Compilar este .iss

#define MyAppName "WHATSPH"
#define MyAppVersion "0.2.4"
#define MyAppPublisher "PH Softwares"

[Setup]
AppId={{A8F3C2E1-WHATSPH-PHSOFT-2026}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={code:GetPhsftw}\WHATSPH
DisableDirPage=no
PrivilegesRequired=admin
OutputDir=..\dist\installer
OutputBaseFilename=WHATSPH_Setup_{#MyAppVersion}
Compression=lzma
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Files]
Source: "..\dist\whatsph\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\WHATSPH Health"; Filename: "{cmd}"; Parameters: "/C start http://127.0.0.1:8765/health"; WorkingDir: "{app}"
; Nao criar atalho do painel sem ticket (403).

[Run]
Filename: "{app}\first_run.bat"; Description: "Gerar .env inicial"; Flags: runhidden waituntilterminated
Filename: "{app}\apply_sql.bat"; Description: "Aplicar schema Postgres whatsapp_ph"; Flags: runhidden waituntilterminated
Filename: "{app}\install_service.bat"; Description: "Instalar servico PHWhatsMeta"; Flags: runhidden waituntilterminated

[UninstallRun]
Filename: "{app}\nssm\nssm.exe"; Parameters: "stop PHWhatsMeta"; Flags: runhidden
Filename: "{app}\nssm\nssm.exe"; Parameters: "remove PHWhatsMeta confirm"; Flags: runhidden

[Code]
function GetPhsftw(Param: String): String;
begin
  Result := 'C:\PHSFTW';
  if DirExists('D:\PHSFTW') then
    Result := 'D:\PHSFTW';
end;
