;-----------------------------------------------------------
; Script d'installation pour GDJ
; (Téléchargement dynamique de GDJ.exe via PowerShell)
;-----------------------------------------------------------
#define MyVersion Trim(GetFileContents("..\data\version.txt"))

[Setup]
AppName=GDJ
AppVersion={#MyVersion}
DefaultDirName={localappdata}\GDJ
DefaultGroupName=GDJ
OutputBaseFilename=GDJ_Installer
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest

[Files]
; Inclure par exemple les fichiers du dossier data (si nécessaire)
Source: "..\data\*.*"; DestDir: "{app}\data"; Flags: recursesubdirs createallsubdirs

[Icons]
; Création du raccourci dans le menu Démarrer qui lancera GDJ.exe
Name: "{group}\GDJ"; Filename: "{app}\GDJ.exe"

[Run]
; Lancement de GDJ.exe après l'installation.
Filename: "{app}\GDJ.exe"; Description: "Lancer GDJ"; Flags: nowait postinstall skipifsilent

[Code]
var
  GDJURL: String;

function InitializeSetup(): Boolean;
var
  ver: String;
begin
  // Récupère la version automatiquement depuis MyVersion, insérée dans AppVersion
  ver := ExpandConstant('{appversion}');
  // Construit l'URL dynamiquement : par exemple,
  // https://github.com/3M6PR0/GDJ_App/releases/download/v1.0.14/GDJ.exe
  GDJURL := 'https://github.com/3M6PR0/GDJ_App/releases/download/v' + ver + '/GDJ.exe';
  Result := True;
end;

function DownloadGDJExe(): Boolean;
var
  TempFile: String;
  Cmd, Params: String;
  ResultCode: Integer;
begin
  TempFile := ExpandConstant('{tmp}\GDJ.exe');

  // Prépare la commande PowerShell pour télécharger GDJ.exe.
  // La commande utilise Invoke-WebRequest pour télécharger le fichier dans TempFile.
  Cmd := 'powershell.exe';
  Params := '-nologo -command "try { Invoke-WebRequest -Uri ''' + GDJURL + ''' -OutFile ''' + TempFile + ''' } catch { exit 1 }"';

  if Exec(Cmd, Params, '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
  begin
    if ResultCode = 0 then
    begin
      // Supprime l'ancienne version si elle existe
      if FileExists(ExpandConstant('{app}\GDJ.exe')) then
      begin
        if not DeleteFile(ExpandConstant('{app}\GDJ.exe')) then
        begin
          MsgBox('Échec de la suppression de l''ancienne version de GDJ.exe.', mbError, MB_OK);
          Result := False;
          Exit;
        end;
      end;

      // Copie le fichier téléchargé vers le répertoire d'installation
      if not FileCopy(TempFile, ExpandConstant('{app}\GDJ.exe'), False) then
      begin
        MsgBox('Échec de la copie de GDJ.exe dans le dossier d''installation.', mbError, MB_OK);
        Result := False;
        Exit;
      end;
      Result := True;
    end
    else
    begin
      MsgBox('Erreur lors du téléchargement de GDJ.exe depuis ' + GDJURL, mbError, MB_OK);
      Result := False;
    end;
  end
  else
  begin
    MsgBox('Impossible d''exécuter PowerShell pour télécharger GDJ.exe.', mbError, MB_OK);
    Result := False;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then
  begin
    if not DownloadGDJExe() then
      Abort();
  end;
end;
