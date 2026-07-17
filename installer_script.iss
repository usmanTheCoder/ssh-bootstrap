; SSH Configuration Manager Installer Script
; Inno Setup Script

#define MyAppName "SSH Configuration Manager"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "M. Usman Sharif & M. Umair Khan"
#define MyAppURL "https://github.com/usmanTheCoder/ssh-bootstrap"
#define MyAppExeName "SSH_Configuration_Manager.exe"
#define MyAppDebugExeName "SSH_Configuration_Manager_Debug.exe"

[Setup]
; Basic Application Info
AppId={{8F9A2C3D-1E4B-5A6C-7D8E-9F0A1B2C3D4E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Installation Directories
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

; Output Configuration
OutputDir=installer
OutputBaseFilename=SSH_Configuration_Manager_Setup_v{#MyAppVersion}
SetupIconFile=
Compression=lzma
SolidCompression=yes
WizardStyle=modern

; Privileges
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; Uninstall
UninstallDisplayIcon={app}\{#MyAppExeName}

; Licensing and Information
LicenseFile=LICENSE
InfoBeforeFile=QUICKSTART.md
InfoAfterFile=

; Visual
WizardImageFile=
WizardSmallImageFile=

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Main executable
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\{#MyAppDebugExeName}"; DestDir: "{app}"; Flags: ignoreversion

; Documentation
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "QUICKSTART.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion

; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
; Start Menu shortcuts
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{#MyAppName} (Debug)"; Filename: "{app}\{#MyAppDebugExeName}"
Name: "{group}\Quick Start Guide"; Filename: "{app}\QUICKSTART.md"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

; Desktop shortcut (optional)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

; Quick Launch shortcut (optional, for older Windows)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
; Option to run after installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Registry]
; Add to Windows "Apps & Features"
Root: HKCU; Subkey: "Software\{#MyAppPublisher}\{#MyAppName}"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\{#MyAppPublisher}\{#MyAppName}"; ValueType: string; ValueName: "Version"; ValueData: "{#MyAppVersion}"
Root: HKCU; Subkey: "Software\{#MyAppPublisher}\{#MyAppName}"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"

[Code]
// Custom code to check prerequisites
function InitializeSetup(): Boolean;
var
  MsgBoxResult: Integer;
begin
  Result := True;

  // Show welcome message with requirements
  MsgBoxResult := MsgBox(
    'Welcome to SSH Configuration Manager Setup!' + #13#10#13#10 +
    'Requirements:' + #13#10 +
    '- Windows 10 or later' + #13#10 +
    '- OpenSSH Client (usually pre-installed)' + #13#10 +
    '- Git (for the optional Git Synchronization feature)' + #13#10 +
    '- Visual C++ Redistributable (recommended)' + #13#10#13#10 +
    'If you encounter issues, install VC++ Redistributable from:' + #13#10 +
    'https://aka.ms/vs/17/release/vc_redist.x64.exe' + #13#10#13#10 +
    'Continue with installation?',
    mbInformation, MB_YESNO
  );

  if MsgBoxResult = IDNO then
    Result := False;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Post-installation tasks
    MsgBox(
      'Installation complete!' + #13#10#13#10 +
      'Quick Start:' + #13#10 +
      '1. Launch SSH Configuration Manager' + #13#10 +
      '2. Use the Dashboard to add a Server/VM or import an existing SSH config' + #13#10 +
      '3. Manage Jump Hosts, SSH Keys, and Git Synchronization from the sidebar' + #13#10 +
      '4. Every change you make is applied to ~/.ssh/config automatically' + #13#10#13#10 +
      'For help, see QUICKSTART.md in the installation folder.',
      mbInformation, MB_OK
    );
  end;
end;

function InitializeUninstall(): Boolean;
var
  MsgBoxResult: Integer;
begin
  Result := True;

  MsgBoxResult := MsgBox(
    'This will remove SSH Configuration Manager from your computer.' + #13#10#13#10 +
    'Note: your SSH keys and ~/.ssh/config will NOT be deleted.' + #13#10 +
    'They are stored in: C:\Users\YourName\.ssh\' + #13#10#13#10 +
    'Continue with uninstallation?',
    mbConfirmation, MB_YESNO
  );

  if MsgBoxResult = IDNO then
    Result := False;
end;
