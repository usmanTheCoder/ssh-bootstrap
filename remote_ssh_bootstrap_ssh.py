import os
import subprocess
import paramiko
import getpass
import socket
from pathlib import Path

def generate_ssh_key():
    ssh_dir = Path.home() / ".ssh"
    private_key = ssh_dir / "id_rsa"
    public_key = ssh_dir / "id_rsa.pub"

    if private_key.exists() and public_key.exists():
        print("[✔] SSH key already exists.")
        return public_key

    print("[+] Generating SSH key...")
    ssh_dir.mkdir(mode=0o700, exist_ok=True)
    subprocess.run(["ssh-keygen", "-t", "rsa", "-b", "2048", "-f", str(private_key), "-N", ""], check=True)
    print("[✔] SSH key generated.")
    return public_key

def upload_ssh_key(ip, username, password, public_key_path, max_retries=3):
    from paramiko.ssh_exception import AuthenticationException
    import getpass

    ssh_dir = ".ssh"
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    for attempt in range(1, max_retries + 1):
        print(f"[+] Connecting to {ip} as {username} (Attempt {attempt}/{max_retries})...")
        try:
            client.connect(ip, username=username, password=password, timeout=10)
            break  # If successful, exit retry loop
        except AuthenticationException:
            print("[✖] Authentication failed: incorrect username or password.")
            if attempt < max_retries:
                username = input("Enter remote server username: ").strip()
                password = getpass.getpass("Enter remote server password: ")
            else:
                print("[✖] Max authentication attempts exceeded.")
                return False
        except socket.timeout as e:
            print(f"[✖] Connection timeout: {e}")
            return False

    commands = [
        f"mkdir -p ~/{ssh_dir} && chmod 700 ~/{ssh_dir}",
        f"echo '{Path(public_key_path).read_text().strip()}' >> ~/{ssh_dir}/authorized_keys",
        f"chmod 600 ~/{ssh_dir}/authorized_keys"
    ]

    for cmd in commands:
        stdin, stdout, stderr = client.exec_command(cmd)
        err = stderr.read().decode()
        if err:
            print(f"[!] Error running command `{cmd}`:\n{err}")
            client.close()
            return False

    print("[✔] Public key added successfully.")
    client.close()
    return True

def test_ssh_connection(ip, username):
    print("[+] Testing SSH connection (should NOT prompt for password)...")
    try:
        subprocess.run([
            "ssh",
            "-o", "StrictHostKeyChecking=no",   # Skip prompt about unknown hosts
            "-o", "BatchMode=yes",              # Fail immediately if password would be required
            "-o", "ConnectTimeout=3",           # Optional: speed up timeout
            f"{username}@{ip}",
            "echo 'Connected via SSH without password.'"
        ], check=True)
        print("[✔] Passwordless SSH works.")
    except subprocess.CalledProcessError:
        print("[✖] Passwordless SSH failed or prompted for password.")

def main():
    ip = input("Enter remote server IP: ").strip()
    username = input("Enter remote server username: ").strip()
    password = getpass.getpass("Enter remote server password: ")

    public_key_path = generate_ssh_key()
    success = upload_ssh_key(ip, username, password, public_key_path)

    if success:
        test_ssh_connection(ip, username)

if __name__ == "__main__":
    main()
