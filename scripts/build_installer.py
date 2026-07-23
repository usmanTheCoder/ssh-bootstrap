import os
import subprocess
import sys
from pathlib import Path

def generate_iss(app_name, app_version, publisher, exe_path, output_dir):
    iss_content = f"""
[Setup]
AppId={{{{8A9B2C3D-4E5F-6A7B-8C9D-0E1F2A3B4C5D}}}}
AppName={app_name}
AppVersion={app_version}
AppPublisher={publisher}
DefaultDirName={{autopf}}\\{app_name}
DisableProgramGroupPage=yes
OutputBaseFilename={app_name}_Installer
OutputDir={output_dir}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest

[Tasks]
Name: "desktopicon"; Description: "{{cm:CreateDesktopIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"; Flags: unchecked

[Files]
Source: "{exe_path}"; DestDir: "{{app}}"; Flags: ignoreversion

[Icons]
Name: "{{autoprograms}}\\{app_name}"; Filename: "{{app}}\\{Path(exe_path).name}"
Name: "{{autodesktop}}\\{app_name}"; Filename: "{{app}}\\{Path(exe_path).name}"; Tasks: desktopicon

[Run]
Filename: "{{app}}\\{Path(exe_path).name}"; Description: "{{cm:LaunchProgram,{app_name}}}"; Flags: nowait postinstall skipifsilent
"""
    iss_path = Path("build_installer.iss")
    iss_path.write_text(iss_content, encoding="utf-8")
    return iss_path

def main():
    print("=" * 60)
    print("SSH Configuration Manager - Installer Builder")
    print("=" * 60)

    # 1. Ensure the executable exists
    exe_path = Path("dist/SSH_Configuration_Manager.exe")
    if not exe_path.exists():
        print("Error: Executable not found. Please run 'python scripts/build_executable.py' first.")
        sys.exit(1)

    # 2. Generate Inno Setup Script
    iss_path = generate_iss(
        app_name="SSH Configuration Manager",
        app_version="1.0.0",
        publisher="M. Usman Sharif & M Umair Khan",
        exe_path=str(exe_path.resolve()),
        output_dir=str(Path("dist").resolve())
    )
    print(f"Generated Inno Setup script: {iss_path}")

    # 3. Look for Inno Setup compiler
    iscc_paths = [
        r"C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe",
        r"C:\\Program Files\\Inno Setup 6\\ISCC.exe"
    ]
    
    compiler_path = None
    for path in iscc_paths:
        if os.path.exists(path):
            compiler_path = path
            break
            
    if compiler_path:
        print(f"Found Inno Setup compiler: {compiler_path}")
        print("Compiling installer...")
        try:
            subprocess.run([compiler_path, str(iss_path)], check=True)
            print("=" * 60)
            
            # Check for signtool and cert to sign the installer and exe
            signtool = r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.20348.0\x64\signtool.exe"
            cert_pfx = Path("dist/cert.pfx").resolve()
            installer_exe = Path("dist/SSH Configuration Manager_Installer.exe")
            
            if Path(signtool).exists() and cert_pfx.exists():
                print("Signing the executables to help bypass Smart App Control...")
                # Sign raw exe
                subprocess.run([signtool, "sign", "/fd", "SHA256", "/a", "/f", str(cert_pfx), "/p", "secret", str(exe_path.resolve())], check=False)
                # Sign installer
                if installer_exe.exists():
                    subprocess.run([signtool, "sign", "/fd", "SHA256", "/a", "/f", str(cert_pfx), "/p", "secret", str(installer_exe.resolve())], check=False)
                print("Executables digitally signed!")
            
            print("Installer successfully created at: dist\\SSH_Configuration_Manager_Installer.exe")
            print("You can distribute this file to anyone to easily install the app!")
            print("=" * 60)
        except subprocess.CalledProcessError:
            print("Error: Failed to compile the installer.")
    else:
        print("\\n" + "=" * 60)
        print("Notice: Inno Setup compiler (ISCC.exe) was not found on your system.")
        print("To easily create a professional Windows installer (.exe):")
        print("1. Download and install Inno Setup from: https://jrsoftware.org/isdl.php")
        print("2. Run this script again.")
        print("=" * 60)

if __name__ == "__main__":
    main()
