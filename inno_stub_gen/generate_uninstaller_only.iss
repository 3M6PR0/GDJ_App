    ; generate_uninstaller_only.iss - Tentative la plus minimale

    [Setup]
    AppName=GDJ_Stub_Final_Try
    AppVersion=1.0
    AppId={{AUTO}}
    DefaultDirName={tmp}\Dummy

    [Files]
    Source: "dummy.txt"; DestDir: "{app}"; Flags: external