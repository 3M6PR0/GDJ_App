;-----------------------------------------------------------
; Script d'installation pour GDJ
; (GDJ.exe est maintenant inclus directement)
;-----------------------------------------------------------

#define MyAppName "GDJ"
#define VersionFile "..\data\version.txt"
#define MyVersion ReadIni(SourcePath + VersionFile, "Version", "value", "1.0.0")
; Vous pouvez ajuster la lecture si votre version.txt est formaté différemment.

[Setup]
AppName={#MyAppName}
AppVersion={#MyVersion}
DefaultDirName={localappdata}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputBaseFilename=GDJ_Installer
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest

; Supprimer l'ANCIEN dossier updater complet AVANT d'installer le nouveau
[InstallDelete]
Type: dirifempty; Name: "{app}\updater"
; La ligne ci-dessus supprime le dossier s'il est vide après suppression des fichiers
; Pour forcer la suppression même s'il reste des fichiers inconnus:
Type: filesandordirs; Name: "{app}\updater"

[Files]
; Inclure GDJ.exe directement
Source: "GDJ.exe"; DestDir: "{app}"; Flags: ignoreversion

; Inclure le contenu COMPLET du nouveau dossier de l'aide à la mise à jour
; Le flag createallsubdirs recréera le dossier {app}\updater
Source: "updater\*"; DestDir: "{app}\updater"; Flags: ignoreversion recursesubdirs createallsubdirs

; Inclure les fichiers de données
; recursesubdirs est requis si createallsubdirs est utilisé
Source: "..\data\config_data.json"; DestDir: "{app}\data"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\data\profile.json"; DestDir: "{app}\data"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\data\version.txt"; DestDir: "{app}\data"; Flags: ignoreversion recursesubdirs createallsubdirs

; Inclure les notes de version
Source: "..\RELEASE_NOTES.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Crée un raccourci dans le menu Démarrer
Name: "{group}\{#MyAppName}"; Filename: "{app}\GDJ.exe"

; Lancer l'application après installation
[Run]
Filename: "{app}\GDJ.exe"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

; La section [Code] est supprimée car GDJ.exe est maintenant inclus directement.
