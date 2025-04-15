;-----------------------------------------------------------
; Script d'installation pour GDJ
; (Téléchargement dynamique de GDJ.exe via PowerShell)
;-----------------------------------------------------------

#define VersionFile "..\data\version.txt"
#define MyVersion ReadIni(SourcePath + VersionFile, "Version", "value", "1.0.0")
; Vous pouvez ajuster la lecture si votre version.txt est formaté différemment.

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
Source: "..\data\config_data.json"; DestDir: "{app}\data"; Flags: recursesubdirs createallsubdirs
Source: "..\data\profile.json"; DestDir: "{app}\data"; Flags: recursesubdirs createallsubdirs
Source: "..\data\version.txt"; DestDir: "{app}\data"; Flags: recursesubdirs createallsubdirs; Attribs: readonly

[Icons]
; Crée un raccourci dans le menu Démarrer qui lancera GDJ.exe (lorsque l'utilisateur le lancera manuellement)
Name: "{group}\GDJ"; Filename: "{app}\GDJ.exe"

; La section [Run] est retirée afin que l'installateur n'exécute pas automatiquement GDJ.exe.
; Cela vous permet de contrôler le lancement de la version installée (par votre système de mise à jour, par exemple).

[Code]
var
  GDJURL: String; // URL de téléchargement de GDJ.exe

function InitializeSetup(): Boolean;
var
  ver: String;
begin
  // Récupère la version définie dans [Setup] qui est lue depuis data\version.txt
  ver := ExpandConstant('{appversion}');
  // Construit l'URL dynamiquement en fonction de la version.
  // Exemple pour AppVersion "1.0.14":
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

  // Prépare la commande PowerShell pour télécharger GDJ.exe
  Cmd := 'powershell.exe';
  Params := '-nologo -command "try { Invoke-WebRequest -Uri ''' + GDJURL + ''' -OutFile ''' + TempFile + ''' } catch { exit 1 }"';

  if Exec(Cmd, Params, '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
  begin
    if ResultCode = 0 then
    begin
      // Supprime l'ancienne version de GDJ.exe si elle existe.
      if FileExists(ExpandConstant('{app}\GDJ.exe')) then
      begin
        if not DeleteFile(ExpandConstant('{app}\GDJ.exe')) then
        begin
          MsgBox('Échec de la suppression de l''ancienne version de GDJ.exe.', mbError, MB_OK);
          Result := False;
          Exit;
        end;
      end;
      // Copie le fichier téléchargé dans le répertoire d'installation
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
  // Lors de l'étape d'installation, télécharger GDJ.exe.
  if CurStep = ssInstall then
  begin
    if not DownloadGDJExe() then
      Abort();
  end;
end;
