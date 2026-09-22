; Inno Setup — WHATSPH (rascunho N5)
; Compilar com Inno Setup 6. Ajuste SourceDir para o build do agente.

#define MyAppName "WHATSPH"
#define MyAppVersion "0.2.2"
#define MyAppPublisher "PH Softwares"

[Setup]
AppId={{A8F3C2E1-WHATSPH-PHSOFT-2026}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={code:GetPhsftw}\WHATSPH
DisableDirPage=no
PrivilegesRequired=admin
OutputBaseFilename=WHATSPH_Setup_{#MyAppVersion}
Compression=lzma
SolidCompression=yes
ArchitecturesAllowed=x86 x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Files]
; Empacotar: app Python, .venv ou embed, scripts, sql
Source: "..\dist\whatsph\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Run]
Filename: "{app}\install_service.bat"; Description: "Instalar servico PHWhatsMeta"; Flags: runhidden waituntilterminated
Filename: "{app}\apply_sql.bat"; Description: "Aplicar schema whatsapp_ph"; Flags: runhidden waituntilterminated

[Code]
function GetPhsftw(Param: String): String;
begin
  Result := 'C:\PHSFTW';
  if DirExists('D:\PHSFTW') then
    Result := 'D:\PHSFTW';
end;
