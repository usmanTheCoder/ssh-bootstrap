
[Setup]
AppId={{8A9B2C3D-4E5F-6A7B-8C9D-0E1F2A3B4C5D}}
AppName=SSH Configuration Manager
AppVersion=1.0.0
AppPublisher=M. Usman Sharif & M Umair Khan
DefaultDirName={autopf}\SSH Configuration Manager
DisableProgramGroupPage=yes
OutputBaseFilename=SSH Configuration Manager_Installer
OutputDir=C:\Users\umair\Documents\GitHub\ssh-app (Usman)\ssh-bootstrap\dist
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "C:\Users\umair\Documents\GitHub\ssh-app (Usman)\ssh-bootstrap\dist\SSH_Configuration_Manager.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\SSH Configuration Manager"; Filename: "{app}\SSH_Configuration_Manager.exe"
Name: "{autodesktop}\SSH Configuration Manager"; Filename: "{app}\SSH_Configuration_Manager.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\SSH_Configuration_Manager.exe"; Description: "{cm:LaunchProgram,SSH Configuration Manager}"; Flags: nowait postinstall skipifsilent
