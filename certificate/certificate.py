"""

A certificate (specifically an X.509 certificate) is a digital document that:

Proves the identity of a server (or client)
Contains a public key
Is digitally signed by a trusted authority

Think of it like a passport for your server.

///////

When one server connects to another over QUIC:

The server presents its certificate
The client verifies it
They establish an encrypted connection using TLS 1.3

Without a certificate, encrypted QUIC connections cannot be established.

///////

An X.509 certificate contains:

Public key
Domain name (CN / SAN)
Issuer (who signed it)
Expiration date
Digital signature

The private key is stored separately and must remain secret.

//////

SERVER:
Generate cert once → store on disk → load on startup

research about "Let's Encrypt" for generating goof certs

"""
