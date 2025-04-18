; Inno Setup script minimal juste pour générer unins***.exe/dat
; Ne contient que les informations de base pour la désinstallation.

[Setup]
; --- Informations de base (DOIVENT correspondre à InstallWorker dans GDJ_Installation_UI.py) ---
AppName=GDJ                       ; Correspond à self.app_name
AppVersion=1.0.0                  ; Placeholder, la vraie version vient du registre écrit par Python
AppPublisher=3M6PR0               ; Correspond à self.publisher
AppId={{GDJApp}}                  ; ID unique, DOIT correspondre à self.app_id
DefaultDirName={localappdata}\GDJ ; Inutilisé ici mais requis par Inno Setup
PrivilegesRequired=lowest

; --- Désactivation de toutes les pages (inutiles pour la génération du stub) ---
DisableWelcomePage=yes
DisableProgramGroupPage=yes
DisableReadyPage=yes
DisableFinishedPage=yes
DisableDirPage=yes

; --- Comportement Désinstalleur ---
UninstallDisplayIcon={app}\GDJ.exe      ; Icône affichée (chemin relatif au InstallLocation écrit par Python)
UninstallDisplayName=GDJ                ; Nom affiché dans Ajout/Suppression (idem AppName)
CreateUninstallRegKey=yes

; --- Options diverses ---
;WizardStyle=modern                      ; Style visuel (peu d'impact ici)
;ShowTasksTree=no                        ; Pas d'arbre de tâches
;Compression=none                        ; Pas besoin de compresser quoi que ce soit
;SolidCompression=no
;OutputBaseFilename=unins000_stub        ; Nom temporaire du setup.exe généré (on ne l'utilisera pas)

; --- Sections VIDES (Non nécessaires car Python gère tout) ---
    [Files]
    Source: "dummy.txt"; DestDir: "{app}"; Flags: external dontcopy

[Icons]

[Registry]
Root: HKCU; Subkey: "Software\GDJ_Stub_Test"; ValueType: string; ValueName: "StubGenerated"; ValueData: "Yes"; Flags: uninsdeletekey

[Run]

[UninstallRun]

[UninstallDelete]
; Normalement, unins000.exe utilise le journal créé par l'installeur.
; Si Python ne crée pas de journal compatible (ce qui est probable),
; il faudra peut-être lister explicitement les fichiers/dossiers ici
; pour une désinstallation propre. Mais pour la *génération* du stub, ce n'est pas requis.
; Exemple potentiel si nécessaire plus tard :
; Type: filesandordirs; Name: "{app}"