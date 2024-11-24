from dataclasses import dataclass
from typing import Optional, Dict
import ssl
import os
from pathlib import Path
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from datetime import datetime, timedelta

@dataclass
class CertificateConfig:
    """Configuration for certificate generation"""
    common_name: str
    organization: str
    country: str = "US"
    state: str = "CA"
    locality: str = "San Francisco"
    valid_days: int = 365
    key_size: int = 2048
    
@dataclass
class MTLSConfig:
    """Configuration for mutual TLS"""
    certificate: bytes  # Server/Client certificate
    private_key: bytes  # Server/Client private key
    ca_cert: bytes     # Certificate Authority certificate
    verify_peer: bool = True
    allowed_sans: Optional[list[str]] = None  # Subject Alternative Names
    verify_depth: int = 3
    crl_check: bool = True
    
    @classmethod
    def from_files(
        cls,
        cert_path: str,
        key_path: str,
        ca_path: str,
        key_password: Optional[str] = None
    ) -> "MTLSConfig":
        """Create MTLS config from certificate files"""
        try:
            with open(cert_path, 'rb') as f:
                cert = f.read()
            with open(key_path, 'rb') as f:
                key = f.read()
            with open(ca_path, 'rb') as f:
                ca = f.read()
                
            # Validate certificates and key
            cls._validate_certificate_chain(cert, ca)
            cls._validate_private_key(key, cert, key_password)
            
            return cls(
                certificate=cert,
                private_key=key,
                ca_cert=ca
            )
        except Exception as e:
            raise ValueError(f"Failed to load MTLS certificates: {str(e)}")

    @staticmethod
    def generate_self_signed(
        config: CertificateConfig,
        output_dir: str
    ) -> "MTLSConfig":
        """Generate self-signed certificates for development/testing"""
        # Generate CA key and certificate
        ca_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=config.key_size
        )
        
        ca_name = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, f"CA-{config.common_name}"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, config.organization),
            x509.NameAttribute(NameOID.COUNTRY_NAME, config.country),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, config.state),
            x509.NameAttribute(NameOID.LOCALITY_NAME, config.locality),
        ])
        
        ca_cert = (
            x509.CertificateBuilder()
            .subject_name(ca_name)
            .issuer_name(ca_name)
            .public_key(ca_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.utcnow())
            .not_valid_after(datetime.utcnow() + timedelta(days=config.valid_days))
            .add_extension(
                x509.BasicConstraints(ca=True, path_length=None),
                critical=True
            )
            .sign(ca_key, hashes.SHA256())
        )
        
        # Generate server key and certificate
        server_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=config.key_size
        )
        
        server_name = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, config.common_name),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, config.organization),
            x509.NameAttribute(NameOID.COUNTRY_NAME, config.country),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, config.state),
            x509.NameAttribute(NameOID.LOCALITY_NAME, config.locality),
        ])
        
        server_cert = (
            x509.CertificateBuilder()
            .subject_name(server_name)
            .issuer_name(ca_name)
            .public_key(server_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.utcnow())
            .not_valid_after(datetime.utcnow() + timedelta(days=config.valid_days))
            .add_extension(
                x509.BasicConstraints(ca=False, path_length=None),
                critical=True
            )
            .sign(ca_key, hashes.SHA256())
        )
        
        # Save certificates and keys
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        with open(output_path / "ca.crt", "wb") as f:
            f.write(ca_cert.public_bytes(serialization.Encoding.PEM))
            
        with open(output_path / "server.crt", "wb") as f:
            f.write(server_cert.public_bytes(serialization.Encoding.PEM))
            
        with open(output_path / "server.key", "wb") as f:
            f.write(server_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
            
        return cls(
            certificate=server_cert.public_bytes(serialization.Encoding.PEM),
            private_key=server_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ),
            ca_cert=ca_cert.public_bytes(serialization.Encoding.PEM)
        )

    @staticmethod
    def _validate_certificate_chain(cert: bytes, ca_cert: bytes) -> None:
        """Validate certificate chain"""
        try:
            cert_obj = x509.load_pem_x509_certificate(cert)
            ca_obj = x509.load_pem_x509_certificate(ca_cert)
            
            # Basic validation
            if cert_obj.issuer != ca_obj.subject:
                raise ValueError("Certificate not issued by provided CA")
                
            # Verify dates
            now = datetime.utcnow()
            if now < cert_obj.not_valid_before or now > cert_obj.not_valid_after:
                raise ValueError("Certificate has expired or is not yet valid")
                
        except Exception as e:
            raise ValueError(f"Certificate validation failed: {str(e)}")

    @staticmethod
    def _validate_private_key(
        key: bytes,
        cert: bytes,
        password: Optional[str] = None
    ) -> None:
        """Validate private key matches certificate"""
        try:
            cert_obj = x509.load_pem_x509_certificate(cert)
            key_obj = serialization.load_pem_private_key(
                key,
                password=password.encode() if password else None
            )
            
            # Verify key matches certificate
            cert_public_key = cert_obj.public_key().public_numbers()
            key_public_key = key_obj.public_key().public_numbers()
            
            if cert_public_key != key_public_key:
                raise ValueError("Private key does not match certificate")
                
        except Exception as e:
            raise ValueError(f"Private key validation failed: {str(e)}") 