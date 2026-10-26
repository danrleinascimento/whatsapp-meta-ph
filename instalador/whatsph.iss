; Instalador e atualizador do WHATSPH (servico Windows PHWhatsMeta).
; O cliente escolhe a pasta PHSFTW que já existe; o destino é {essa pasta}\SERVICOS\WHATSPH.
; Parar o serviço, trocar o whatsph.exe, criar o .env (só se faltar), criar o banco
; (se faltar) e as tabelas, registrar, iniciar e conferir a saúde é feito pelo
; preparar_ambiente_whatsph.ps1, que o instalador executa depois de extrair os arquivos.
; Gerar: scripts\build_instalador.ps1 (passa /DMyAppVersion=<versão do whatsph.exe>).

#ifndef MyAppVersion
  #error Informe a versao: use scripts\build_instalador.ps1 (ISCC /DMyAppVersion=x.y.z)
#endif

#define MyAppName "WHATSPH"

[Setup]
AppId={{D58CC4E4-35BD-40EA-8687-5E5C805BFFD9}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher=PH Softwares
VersionInfoVersion={#MyAppVersion}
VersionInfoDescription=Instalador do WHATSPH (serviço PHWhatsMeta)
SetupIconFile=..\ph.ico
; Sem pasta {app}: o destino vem da página "Pasta PHSFTW" (evita criar C:\PHSFTW quando o PHSFTW é em outra unidade).
CreateAppDir=no
DisableProgramGroupPage=yes
OutputDir=saida
OutputBaseFilename=instalarWHATSPH
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=admin
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
Uninstallable=no
CloseApplications=no
RestartApplications=no
ShowLanguageDialog=no

[Languages]
Name: "ptbr"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Files]
Source: "..\dist\whatsph.exe"; DestDir: "{tmp}"; Flags: ignoreversion
Source: "..\scripts\preparar_ambiente_whatsph.ps1"; DestDir: "{tmp}"; Flags: ignoreversion
Source: "..\scripts\preparar_ambiente_whatsph.ps1"; DestDir: "{code:PastaWhatsPh}"; Flags: ignoreversion

[Code]
const
  NomeServico = 'PHWhatsMeta';
  ChaveServico = 'SYSTEM\CurrentControlSet\Services\PHWhatsMeta';

var
  Pagina: TInputDirWizardPage;
  ServicoExiste: Boolean;
  RaizServico: String;
  CaminhoServico: String;
  ResultadoOk: Boolean;
  ResultadoTexto: String;

{ Pasta PHSFTW do serviço já registrado (ImagePath ...\PHSFTW\SERVICOS\WHATSPH\whatsph.exe). }
function PhsftwDoServico(var Raiz: String): Boolean;
var
  Caminho, Pasta: String;
  Fim: Integer;
begin
  Result := False;
  Raiz := '';
  if not RegQueryStringValue(HKLM, ChaveServico, 'ImagePath', CaminhoServico) then
    Exit;
  Caminho := Trim(CaminhoServico);
  if (Length(Caminho) > 0) and (Caminho[1] = '"') then
  begin
    Delete(Caminho, 1, 1);
    Fim := Pos('"', Caminho);
    if Fim > 0 then
      Caminho := Copy(Caminho, 1, Fim - 1);
  end;
  Pasta := ExtractFileDir(Caminho);
  if CompareText(ExtractFileName(Pasta), 'WHATSPH') <> 0 then
    Exit;
  Pasta := ExtractFileDir(Pasta);
  if CompareText(ExtractFileName(Pasta), 'SERVICOS') <> 0 then
    Exit;
  Raiz := RemoveBackslashUnlessRoot(ExtractFileDir(Pasta));
  Result := Raiz <> '';
end;

function RaizEscolhida: String;
begin
  Result := RemoveBackslashUnlessRoot(Trim(Pagina.Values[0]));
end;

function PastaWhatsPh(Param: String): String;
begin
  Result := AddBackslash(RaizEscolhida) + 'SERVICOS\WHATSPH';
end;

procedure InitializeWizard;
var
  Explicacao: String;
begin
  ServicoExiste := RegKeyExists(HKLM, ChaveServico);
  if ServicoExiste and PhsftwDoServico(RaizServico) then
    Explicacao := 'O serviço ' + NomeServico + ' já está instalado nesta pasta e será atualizado. ' +
      'O arquivo .env (configuração) é mantido.'
  else if ServicoExiste then
    Explicacao := 'Atenção: o serviço ' + NomeServico + ' está registrado com outro programa e precisa ser removido antes.'
  else
    Explicacao := 'O instalador cria a pasta SERVICOS\WHATSPH dentro dela, cria o banco de dados whatsapp_ph ' +
      '(se não existir) e as tabelas, instala o serviço ' + NomeServico + ' e o inicia.';
  Pagina := CreateInputDirPage(wpWelcome,
    'Pasta PHSFTW',
    'Escolha a pasta PHSFTW que já existe (onde está o GEPH).',
    Explicacao,
    False, '');
  Pagina.Add('Pasta PHSFTW');
  if RaizServico <> '' then
    Pagina.Values[0] := RaizServico
  else
    Pagina.Values[0] := ExpandConstant('{sd}\PHSFTW');
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  Raiz: String;
begin
  Result := True;
  if CurPageID = Pagina.ID then
  begin
    Raiz := RaizEscolhida;
    if ServicoExiste and (RaizServico = '') then
    begin
      MsgBox('O serviço ' + NomeServico + ' está registrado com outro programa:' + #13#10 + CaminhoServico + #13#10#13#10 +
        'Remova o serviço antigo antes (como Administrador: sc delete ' + NomeServico + ') e rode o instalador de novo.',
        mbError, MB_OK);
      Result := False;
    end
    else if not DirExists(Raiz) then
    begin
      MsgBox('A pasta PHSFTW informada não existe. Escolha a pasta que já está no computador.', mbError, MB_OK);
      Result := False;
    end
    else if CompareText(ExtractFileName(Raiz), 'PHSFTW') <> 0 then
    begin
      MsgBox('A pasta escolhida precisa se chamar PHSFTW (ex.: C:\PHSFTW).', mbError, MB_OK);
      Result := False;
    end
    else if ServicoExiste and (RaizServico <> '') and (CompareText(RaizServico, Raiz) <> 0) then
    begin
      MsgBox('O serviço ' + NomeServico + ' já está instalado em ' + AddBackslash(RaizServico) +
        'SERVICOS\WHATSPH.' + #13#10 + 'Para atualizar, escolha a pasta ' + RaizServico + '.',
        mbError, MB_OK);
      Result := False;
    end;
  end;
end;

function UpdateReadyMemo(Space, NewLine, MemoUserInfoInfo, MemoDirInfo, MemoTypeInfo,
  MemoComponentsInfo, MemoGroupInfo, MemoTasksInfo: String): String;
var
  Acao: String;
begin
  if ServicoExiste then
    Acao := 'atualizar (o .env é mantido)'
  else
    Acao := 'instalar e iniciar';
  Result := 'Pasta do WHATSPH:' + NewLine + Space + PastaWhatsPh('') + NewLine + NewLine +
    'Banco de dados (PostgreSQL):' + NewLine + Space + 'criar se não existir e criar/atualizar as tabelas' + NewLine + NewLine +
    'Serviço do Windows ' + NomeServico + ':' + NewLine + Space + Acao;
end;

function OemToCharBuff(lpszSrc: AnsiString; lpszDst: AnsiString; cchDstLength: Cardinal): Boolean;
  external 'OemToCharBuffA@user32.dll stdcall';

{ A saída redirecionada do PowerShell vem na página OEM (850); a tela do instalador usa ANSI (1252). }
function OemParaAnsi(const Texto: AnsiString): AnsiString;
begin
  Result := Texto;
  if Length(Texto) = 0 then
    Exit;
  Result := StringOfChar(' ', Length(Texto));
  if not OemToCharBuff(Texto, Result, Length(Texto)) then
    Result := Texto;
end;

{ Valor de texto de um campo do JSON de uma linha gerado pelo ConvertTo-Json -Compress. }
function CampoJson(const Texto, Campo: String): String;
var
  I, Codigo: Integer;
  Resto: String;
begin
  Result := '';
  I := Pos('"' + Campo + '":"', Texto);
  if I = 0 then
    Exit;
  Resto := Copy(Texto, I + Length(Campo) + 4, Length(Texto));
  I := 1;
  while I <= Length(Resto) do
  begin
    if Resto[I] = '"' then
      Break;
    if (Resto[I] = '\') and (I < Length(Resto)) then
    begin
      if (Resto[I + 1] = 'u') and (I + 5 <= Length(Resto)) then
      begin
        Codigo := StrToIntDef('$' + Copy(Resto, I + 2, 4), 63);
        if Codigo > 255 then
          Codigo := 63;
        Result := Result + Chr(Codigo);
        I := I + 6;
      end
      else
      begin
        Result := Result + Resto[I + 1];
        I := I + 2;
      end;
    end
    else
    begin
      Result := Result + Resto[I];
      I := I + 1;
    end;
  end;
end;

procedure ExecutarPreparacao;
var
  PowerShell, Comando, ArquivoResultado, ArquivoSaida, Pasta, Mensagem: String;
  Texto, Saida: AnsiString;
  Codigo: Integer;
begin
  Pasta := PastaWhatsPh('');
  ArquivoResultado := ExpandConstant('{tmp}\resultado_whatsph.json');
  ArquivoSaida := ExpandConstant('{tmp}\saida_whatsph.txt');
  DeleteFile(ArquivoResultado);
  DeleteFile(ArquivoSaida);
  PowerShell := ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe');
  Comando := '"' + PowerShell + '" -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' +
    ExpandConstant('{tmp}\preparar_ambiente_whatsph.ps1') + '"' +
    ' -ExecutavelOrigem "' + ExpandConstant('{tmp}\whatsph.exe') + '"' +
    ' -Diretorio "' + Pasta + '"' +
    ' -ArquivoResultado "' + ArquivoResultado + '"';

  WizardForm.StatusLabel.Caption := 'Parando o serviço ' + NomeServico + ', trocando o whatsph.exe e iniciando de novo...';
  WizardForm.FilenameLabel.Caption := Pasta;
  Log('Executando: ' + Comando);

  ResultadoOk := False;
  { cmd /S /C "..." tira só as aspas de fora; a saída do PowerShell vai para ArquivoSaida (erro antes do script rodar). }
  if not Exec(ExpandConstant('{cmd}'), '/S /C "' + Comando + ' > "' + ArquivoSaida + '" 2>&1"',
    ExpandConstant('{tmp}'), SW_HIDE, ewWaitUntilTerminated, Codigo) then
  begin
    ResultadoTexto := 'Não foi possível executar o PowerShell (' + SysErrorMessage(Codigo) + ').';
    Log(ResultadoTexto);
    Exit;
  end;

  Texto := '';
  if not LoadStringFromFile(ArquivoResultado, Texto) then
    Texto := '';
  Saida := '';
  if LoadStringFromFile(ArquivoSaida, Saida) then
    Saida := OemParaAnsi(Saida)
  else
    Saida := '';
  Log('Código de saída: ' + IntToStr(Codigo) + '; resultado: ' + Texto);
  Log('Saída do PowerShell: ' + Saida);

  Mensagem := CampoJson(Texto, 'mensagem');
  if (Codigo = 0) and (Pos('WHATSPH_AMBIENTE_PRONTO', Texto) > 0) then
  begin
    ResultadoOk := True;
    ResultadoTexto := Mensagem;
    if Pos('"configuracao":"gerada"', Texto) > 0 then
      ResultadoTexto := ResultadoTexto + #13#10#13#10 +
        'Foi criado um .env novo em ' + Pasta + '.';
    if Pos('"banco_criado":true', Texto) > 0 then
      ResultadoTexto := ResultadoTexto + #13#10#13#10 + 'Banco de dados criado agora e tabelas criadas.'
    else
      ResultadoTexto := ResultadoTexto + #13#10#13#10 + 'Banco de dados já existia; tabelas conferidas e atualizadas.';
    if (Pos('"db_ok":true', Texto) = 0) then
      ResultadoTexto := ResultadoTexto + #13#10#13#10 +
        'Atenção: o serviço subiu, mas não conectou no banco de dados. Confira o PostgreSQL (serviço postgresPH) ' +
        'e o DATABASE_URL em ' + Pasta + '\.env; depois, como Administrador, rode na pasta: whatsph.exe restart-service';
  end
  else
  begin
    if Mensagem = '' then
    begin
      Saida := Trim(Saida);
      if Length(Saida) > 800 then
        Saida := '...' + Copy(Saida, Length(Saida) - 799, 800);
      Mensagem := 'O PowerShell terminou com código ' + IntToStr(Codigo) + ' sem resultado do script.';
      if Saida <> '' then
        Mensagem := Mensagem + #13#10#13#10 + Saida;
    end;
    ResultadoTexto := Mensagem;
    if Pos('"servico_religado":true', Texto) > 0 then
      ResultadoTexto := ResultadoTexto + #13#10#13#10 + 'O serviço ' + NomeServico + ' foi religado na versão que estava registrada.';
    ResultadoTexto := ResultadoTexto + #13#10#13#10 + 'Logs: ' + Pasta + '\logs';
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    ExecutarPreparacao;
    if not ResultadoOk then
      SuppressibleMsgBox('O WHATSPH não foi instalado/atualizado.' + #13#10#13#10 + ResultadoTexto,
        mbCriticalError, MB_OK, IDOK);
  end;
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if (CurPageID = wpFinished) and (ResultadoTexto <> '') then
  begin
    if ResultadoOk then
      WizardForm.FinishedHeadingLabel.Caption := 'WHATSPH pronto'
    else
      WizardForm.FinishedHeadingLabel.Caption := 'WHATSPH com falha';
    WizardForm.FinishedLabel.Caption := ResultadoTexto;
    WizardForm.AdjustLabelHeight(WizardForm.FinishedLabel);
  end;
end;
