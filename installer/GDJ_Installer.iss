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

[Files]
; Inclure GDJ.exe directement depuis le dossier où le script .iss se trouve
; (create_release.py l'aura copié ici)
Source: "GDJ.exe"; DestDir: "{app}"; Flags: ignoreversion
; Inclure le contenu du dossier de l'aide à la mise à jour (compilé en one-folder)
Source: "updater\*"; DestDir: "{app}\updater"; Flags: ignoreversion recursesubdirs createallsubdirs
; Inclure le dossier resources (icônes, styles)
Source: "..\resources\*"; DestDir: "{app}\resources"; Flags: ignoreversion recursesubdirs createallsubdirs
; Inclure les fichiers de données
Source: "..\data\config_data.json"; DestDir: "{app}\data"; Flags: recursesubdirs createallsubdirs
Source: "..\data\version.txt"; DestDir: "{app}\data"; Flags: recursesubdirs createallsubdirs
; Inclure les notes de version
Source: "..\RELEASE_NOTES.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Crée un raccourci dans le menu Démarrer qui lancera GDJ.exe
Name: "{group}\{#MyAppName}"; Filename: "{app}\GDJ.exe"

[Registry]
; Association de l'extension .rdj avec GDJ.exe pour l'UTILISATEUR ACTUEL
Root: HKCU; Subkey: "Software\Classes\.rdj"; ValueType: string; ValueName: ""; ValueData: "Jacmar.RDJFile"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\Jacmar.RDJFile"; ValueType: string; ValueName: ""; ValueData: "Rapport de Dépense Jacmar"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\Jacmar.RDJFile\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\GDJ.exe,0"
Root: HKCU; Subkey: "Software\Classes\Jacmar.RDJFile\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\GDJ.exe"" ""%1"""

; Ajout de la section Run pour lancer l'application après installation
[Run]
Filename: "{app}\GDJ.exe"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

; La section [Code] est supprimée car GDJ.exe est maintenant inclus directement.
