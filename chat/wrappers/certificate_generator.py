import ipaddress
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID

# -------------------------
# Default certificate directory
# -------------------------
BASE_DIR = Path(__file__).parent.resolve()
DEFAULT_CERT_DIR = BASE_DIR / "certificate"
DEFAULT_CERT_DIR.mkdir(parents=True, exist_ok=True)

CA_KEY = DEFAULT_CERT_DIR / "ca.key"
CA_CERT = DEFAULT_CERT_DIR / "ca.crt"


# -------------------------
# Helpers
# -------------------------
def save_key(key, path):
    path = Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(
            key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )


def save_cert(cert, path):
    path = Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))


def load_key(path):
    path = Path(path).resolve()
    with open(path, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)


def load_cert(path):
    path = Path(path).resolve()
    with open(path, "rb") as f:
        return x509.load_pem_x509_certificate(f.read())


def generate_ca(cert_dir: Path = DEFAULT_CERT_DIR):
    cert_dir.mkdir(parents=True, exist_ok=True)
    ca_key_path = cert_dir / "ca.key"
    ca_cert_path = cert_dir / "ca.crt"

    if ca_key_path.exists() or ca_cert_path.exists():
        print("CA already exists, skipping generation")
        return ca_key_path, ca_cert_path

    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "QUIC Dev CA"),
        x509.NameAttribute(NameOID.COMMON_NAME, "QUIC Root CA"),
    ])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=3650))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(ca_key, hashes.SHA256())
    )

    save_key(ca_key, ca_key_path)
    save_cert(cert, ca_cert_path)
    print("CA created:")
    print("  Key:", ca_key_path)
    print("  Cert:", ca_cert_path)

    return ca_key_path, ca_cert_path


def generate_client_cert(save_dir: Path = DEFAULT_CERT_DIR, client_name: str = None):
    save_dir = Path(save_dir).resolve()
    save_dir.mkdir(parents=True, exist_ok=True)

    if not CA_KEY.exists() or not CA_CERT.exists():
        raise Exception("CA not found. Run generate_ca() first")

    ca_key = load_key(CA_KEY)
    ca_cert = load_cert(CA_CERT)

    client_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    client_name = client_name or f"client-{uuid.uuid4()}"
    client_cert = (
        x509.CertificateBuilder()
        .subject_name(
            x509.Name([
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "QUIC Client Org"),
                x509.NameAttribute(NameOID.COMMON_NAME, str(client_name)),
            ])
        )
        .issuer_name(ca_cert.subject)
        .public_key(client_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=825))
        .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CLIENT_AUTH]), critical=False)
        .sign(ca_key, hashes.SHA256())
    )

    key_path = save_dir / "client.key"
    cert_path = save_dir / "client.crt"

    save_key(client_key, key_path)
    save_cert(client_cert, cert_path)

    print(f"Client certificate created: {client_name}")
    print("  Key:", key_path)
    print("  Cert:", cert_path)

    return key_path, cert_path


def generate_server_cert(ip: str, save_dir: Path = DEFAULT_CERT_DIR, server_name="server"):
    save_dir = Path(save_dir).resolve()
    save_dir.mkdir(parents=True, exist_ok=True)

    if not CA_KEY.exists() or not CA_CERT.exists():
        raise Exception("CA not found. Run generate_ca() first")

    ca_key = load_key(CA_KEY)
    ca_cert = load_cert(CA_CERT)

    # Validate and convert the single IP
    ip_obj = ipaddress.ip_address(ip)
    san = x509.SubjectAlternativeName([x509.IPAddress(ip_obj)])

    server_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    server_cert = (
        x509.CertificateBuilder()
        .subject_name(
            x509.Name([
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "QUIC Server"),
                x509.NameAttribute(NameOID.COMMON_NAME, server_name),
            ])
        )
        .issuer_name(ca_cert.subject)
        .public_key(server_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=825))
        .add_extension(san, critical=False)
        .sign(ca_key, hashes.SHA256())
    )

    key_path = save_dir / f"server.key"
    cert_path = save_dir / f"server.crt"

    save_key(server_key, key_path)
    save_cert(server_cert, cert_path)

    print(f"Server certificate created for IP: {ip}")
    print("  Key:", key_path)
    print("  Cert:", cert_path)

    return key_path, cert_path
