import ipaddress
from datetime import datetime, timedelta
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

CERT_DIR = Path("certs")
CA_KEY = CERT_DIR / "ca.key"
CA_CERT = CERT_DIR / "ca.crt"

SERVER_KEY = CERT_DIR / "server.key"
SERVER_CERT = CERT_DIR / "server.crt"


def save_key(key, path):
    with open(path, "wb") as f:
        f.write(
            key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.TraditionalOpenSSL,
                serialization.NoEncryption(),
            )
        )


def save_cert(cert, path):
    with open(path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))


def load_key(path):
    with open(path, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)


def load_cert(path):
    with open(path, "rb") as f:
        return x509.load_pem_x509_certificate(f.read())


# -------------------------
# Generate CA (run once)
# -------------------------

def generate_ca():
    CERT_DIR.mkdir(exist_ok=True)

    if CA_KEY.exists() or CA_CERT.exists():
        raise Exception("CA already exists")

    ca_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096
    )

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
        .add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True
        )
        .sign(ca_key, hashes.SHA256())
    )

    save_key(ca_key, CA_KEY)
    save_cert(cert, CA_CERT)

    print("CA created:")
    print(CA_KEY)
    print(CA_CERT)


# -------------------------
# Regenerate server cert
# -------------------------

def regenerate_server_cert(ips):
    """
    ips: list[str]
    example:
        ["192.168.1.10", "10.0.0.5"]
    """

    if not CA_KEY.exists():
        raise Exception("CA not found. Run generate_ca() first")

    ca_key = load_key(CA_KEY)
    ca_cert = load_cert(CA_CERT)

    server_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

    san_list = []

    for ip in ips:
        san_list.append(
            x509.IPAddress(ipaddress.ip_address(ip))
        )

    san = x509.SubjectAlternativeName(san_list)

    subject = x509.Name([
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "QUIC Server"),
        x509.NameAttribute(NameOID.COMMON_NAME, ips[0]),
    ])

    server_cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(ca_cert.subject)
        .public_key(server_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=825))
        .add_extension(san, critical=False)
        .sign(ca_key, hashes.SHA256())
    )

    save_key(server_key, SERVER_KEY)
    save_cert(server_cert, SERVER_CERT)

    print("Server certificate regenerated for:")
    for ip in ips:
        print("  ", ip)

    print(SERVER_KEY)
    print(SERVER_CERT)


# -------------------------
# Example usage
# -------------------------

if __name__ == "__main__":
    # run once
    # generate_ca()

    regenerate_server_cert([
        "192.168.68.108"
    ])
