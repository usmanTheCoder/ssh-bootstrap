import os
import subprocess
import sys
import shutil
from pathlib import Path

# A tiny 1x1 transparent PNG payload in base64
TINY_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06"
    b"\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00"
    b"\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)

MANIFEST_XML = """<?xml version="1.0" encoding="utf-8"?>
<Package
  xmlns="http://schemas.microsoft.com/appx/manifest/foundation/windows10"
  xmlns:uap="http://schemas.microsoft.com/appx/manifest/uap/windows10"
  xmlns:rescap="http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities"
  IgnorableNamespaces="uap rescap">

  <Identity
    Name="SSHConfigurationManager"
    Publisher="CN=UsmanUmair"
    Version="1.0.0.0"
    ProcessorArchitecture="x64" />

  <Properties>
    <DisplayName>SSH Configuration Manager</DisplayName>
    <PublisherDisplayName>Usman &amp; Umair</PublisherDisplayName>
    <Logo>Assets\\StoreLogo.png</Logo>
  </Properties>

  <Resources>
    <Resource Language="en-us"/>
  </Resources>

  <Dependencies>
    <TargetDeviceFamily Name="Windows.Desktop" MinVersion="10.0.17763.0" MaxVersionTested="10.0.19041.0" />
  </Dependencies>

  <Capabilities>
    <rescap:Capability Name="runFullTrust" />
  </Capabilities>

  <Applications>
    <Application Id="SSHManager"
      Executable="SSH_Configuration_Manager.exe"
      EntryPoint="Windows.FullTrustApplication">
      <uap:VisualElements
        DisplayName="SSH Configuration Manager"
        Description="Manage your SSH and Jump Hosts easily."
        BackgroundColor="transparent"
        Square150x150Logo="Assets\\Square150x150Logo.png"
        Square44x44Logo="Assets\\Square44x44Logo.png">
        <uap:DefaultTile Wide310x150Logo="Assets\\Wide310x150Logo.png" />
      </uap:VisualElements>
    </Application>
  </Applications>
</Package>
"""

def generate_assets(msix_stage: Path):
    assets_dir = msix_stage / "Assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    pngs = ["StoreLogo.png", "Square150x150Logo.png", "Square44x44Logo.png", "Wide310x150Logo.png"]
    for p in pngs:
        (assets_dir / p).write_bytes(TINY_PNG)

def find_windows_sdk_tool(tool_name: str) -> str:
    """Finds a tool like makeappx.exe or signtool.exe in the Windows Kits folder."""
    base_dir = Path(r"C:\Program Files (x86)\Windows Kits\10\bin")
    if not base_dir.exists():
        return None
        
    # Find the latest SDK version folder
    versions = [d for d in base_dir.iterdir() if d.is_dir() and d.name.startswith("10.0.")]
    if not versions:
        return None
        
    versions.sort(key=lambda d: d.name, reverse=True)
    for v in versions:
        tool_path = v / "x64" / tool_name
        if tool_path.exists():
            return str(tool_path)
    return None

def main():
    print("=" * 60)
    print("SSH Configuration Manager - MSIX Builder")
    print("=" * 60)

    exe_path = Path("dist/SSH_Configuration_Manager.exe")
    if not exe_path.exists():
        print("Error: Executable not found. Run 'python scripts/build_executable.py' first.")
        sys.exit(1)

    # 1. Setup Staging Directory
    msix_stage = Path("dist/msix_stage")
    if msix_stage.exists():
        shutil.rmtree(msix_stage)
    msix_stage.mkdir(parents=True, exist_ok=True)

    # 2. Copy Executable
    print(f"Copying {exe_path.name} to staging area...")
    shutil.copy(exe_path, msix_stage / exe_path.name)

    # 3. Create Manifest and Assets
    print("Generating AppxManifest.xml and icon assets...")
    (msix_stage / "AppxManifest.xml").write_text(MANIFEST_XML, encoding="utf-8")
    generate_assets(msix_stage)

    # 4. Find MakeAppx.exe
    makeappx = find_windows_sdk_tool("makeappx.exe")
    signtool = find_windows_sdk_tool("signtool.exe")
    
    msix_out = Path("dist/SSH_Configuration_Manager.msix")
    if msix_out.exists():
        msix_out.unlink()

    if makeappx:
        print(f"Found makeappx.exe: {makeappx}")
        print("Building MSIX package...")
        try:
            subprocess.run([makeappx, "pack", "/d", str(msix_stage.resolve()), "/p", str(msix_out.resolve())], check=True)
            print(f"\nSuccessfully built MSIX: {msix_out.resolve()}")
            
            if signtool:
                print("\n" + "=" * 60)
                print("Generating Self-Signed Certificate and Signing MSIX...")
                cert_pfx = Path("dist/cert.pfx").resolve()
                cert_cer = Path("dist/cert.cer").resolve()
                
                ps_script = f'''
$ErrorActionPreference = "Stop"
if (-not (Test-Path "{cert_pfx}")) {{
    $cert = New-SelfSignedCertificate -Type Custom -Subject "CN=UsmanUmair" -KeyUsage DigitalSignature -FriendlyName "SSHManager Dev Cert" -CertStoreLocation "Cert:\\CurrentUser\\My" -TextExtension @("2.5.29.37={{text}}1.3.6.1.5.5.7.3.3", "2.5.29.19={{text}}")
    $pwd = ConvertTo-SecureString -String "secret" -Force -AsPlainText
    Export-PfxCertificate -cert $cert -FilePath "{cert_pfx}" -Password $pwd | Out-Null
    Export-Certificate -Cert $cert -FilePath "{cert_cer}" | Out-Null
    Import-Certificate -FilePath "{cert_cer}" -CertStoreLocation Cert:\\CurrentUser\\TrustedPeople | Out-Null
    Write-Host "Generated and trusted new certificate."
}} else {{
    Write-Host "Using existing certificate."
}}
'''
                ps_script_path = Path("dist/gen_cert.ps1")
                ps_script_path.write_text(ps_script, encoding="utf-8")
                
                try:
                    subprocess.run(["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", str(ps_script_path.resolve())], check=True)
                    print(f"Signing the MSIX package...")
                    subprocess.run([signtool, "sign", "/fd", "SHA256", "/a", "/f", str(cert_pfx), "/p", "secret", str(msix_out.resolve())], check=True)
                    print("\n" + "=" * 60)
                    print(f"SUCCESS: MSIX is fully signed and ready to install!")
                    print("You can now double-click it to install:")
                    print(f"{msix_out.resolve()}")
                    print("=" * 60)
                except subprocess.CalledProcessError:
                    print("Error: Certificate generation or signing failed.")
            else:
                print("\nIMPORTANT: signtool.exe was not found. Your MSIX is built but unsigned.")
                
        except subprocess.CalledProcessError:
            print("Failed to build MSIX package.")
    else:
        print("\nNotice: 'makeappx.exe' was not found. Please install the Windows 10/11 SDK.")
        print(f"The MSIX package layout is ready at: {msix_stage.resolve()}")
        print("You can build it manually once you have the SDK tools.")

if __name__ == "__main__":
    main()
