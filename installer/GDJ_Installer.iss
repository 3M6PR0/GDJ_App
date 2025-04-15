;-----------------------------------------------------------
; Script d'installation pour GDJ
;-----------------------------------------------------------
[Setup]
AppName=GDJ
AppVersion=1.0.12
DefaultDirName={localappdata}\GDJ
DefaultGroupName=GDJ
OutputBaseFilename=GDJ_Installer
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest

[Files]
; Fichier principal (exécutable généré par PyInstaller)
Source: "..\dist\GDJ.exe"; DestDir: "{app}"; Flags: ignoreversion
; Copie de tous les fichiers du dossier data
Source: "..\data\*.*"; DestDir: "{app}\data"; Flags: recursesubdirs createallsubdirs

; Source: "..\updater\update_helper.exe"; DestDir: "{app}\updater"; Flags: ignoreversion


[Icons]
; Création d'un raccourci dans le menu Démarrer
Name: "{group}\GDJ"; Filename: "{app}\GDJ.exe"

[Run]
; Lancement de l'application après l'installation (optionnel)
Filename: "{app}\GDJ.exe"; Description: "Lancer GDJ"; Flags: nowait postinstall skipifsilent
