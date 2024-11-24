from typing import Dict, List, Optional, Any, Callable
import structlog
import aiohttp
import asyncio
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import socket
import ssl
from ..exceptions import HealthCheckError

logger = structlog.get_logger()

class HealthCheckType(Enum):
    """Types of health checks."""
    HTTP = "http"
    TCP = "tcp"
    SCRIPT = "script"
    GRPC = "grpc"
    TLS = "tls"
    CUSTOM = "custom"

@dataclass
class HealthCheckConfig:
    """Health check configuration."""
    type: HealthCheckType
    interval: float = 30.0  # seconds
    timeout: float = 5.0    # seconds
    retries: int = 3
    initial_delay: float = 0.0
    
    # HTTP specific
    http_path: str = "/health"
    http_method: str = "GET"
    http_headers: Dict[str, str] = None
    expected_status: int = 200
    
    # TCP specific
    tcp_send: bytes = None
    tcp_expect: bytes = None
    
    # Script specific
    script_path: str = None
    script_args: List[str] = None
    
    # TLS specific
    verify_cert: bool = True
    check_expiry: bool = True
    min_cert_days: int = 30
    
    # Custom check
    custom_check: Callable = None

class HealthChecker:
    """Customizable health check implementation."""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.checks: Dict[str, HealthCheckConfig] = {}
        self.logger = logger.bind(component="health_checker")
    
    def add_check(self, name: str, config: HealthCheckConfig) -> None:
        """Add a health check."""
        self.checks[name] = config
    
    async def run_checks(self) -> Dict[str, bool]:
        """Run all configured health checks."""
        results = {}
        
        for name, config in self.checks.items():
            try:
                if config.type == HealthCheckType.HTTP:
                    results[name] = await self._http_check(config)
                elif config.type == HealthCheckType.TCP:
                    results[name] = await self._tcp_check(config)
                elif config.type == HealthCheckType.SCRIPT:
                    results[name] = await self._script_check(config)
                elif config.type == HealthCheckType.GRPC:
                    results[name] = await self._grpc_check(config)
                elif config.type == HealthCheckType.TLS:
                    results[name] = await self._tls_check(config)
                elif config.type == HealthCheckType.CUSTOM:
                    results[name] = await self._custom_check(config)
            except Exception as e:
                self.logger.error("health_check_failed",
                                service=self.service_name,
                                check=name,
                                error=str(e))
                results[name] = False
        
        return results
    
    async def _http_check(self, config: HealthCheckConfig) -> bool:
        """Run HTTP health check."""
        async with aiohttp.ClientSession() as session:
            for attempt in range(config.retries):
                try:
                    async with session.request(
                        method=config.http_method,
                        url=config.http_path,
                        headers=config.http_headers,
                        timeout=config.timeout
                    ) as response:
                        return response.status == config.expected_status
                except Exception as e:
                    if attempt == config.retries - 1:
                        raise HealthCheckError(f"HTTP check failed: {str(e)}")
                    await asyncio.sleep(1)
    
    async def _tcp_check(self, config: HealthCheckConfig) -> bool:
        """Run TCP health check."""
        for attempt in range(config.retries):
            try:
                reader, writer = await asyncio.open_connection(
                    self.service_name,
                    config.port,
                    ssl=config.verify_cert
                )
                
                if config.tcp_send:
                    writer.write(config.tcp_send)
                    await writer.drain()
                
                if config.tcp_expect:
                    data = await asyncio.wait_for(
                        reader.read(len(config.tcp_expect)),
                        timeout=config.timeout
                    )
                    if data != config.tcp_expect:
                        return False
                
                writer.close()
                await writer.wait_closed()
                return True
                
            except Exception as e:
                if attempt == config.retries - 1:
                    raise HealthCheckError(f"TCP check failed: {str(e)}")
                await asyncio.sleep(1)
    
    async def _script_check(self, config: HealthCheckConfig) -> bool:
        """Run script-based health check."""
        try:
            process = await asyncio.create_subprocess_exec(
                config.script_path,
                *config.script_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=config.timeout
            )
            
            return process.returncode == 0
            
        except Exception as e:
            raise HealthCheckError(f"Script check failed: {str(e)}")
    
    async def _grpc_check(self, config: HealthCheckConfig) -> bool:
        """Run gRPC health check."""
        # Implementation depends on gRPC health checking protocol
        raise NotImplementedError("gRPC health check not implemented")
    
    async def _tls_check(self, config: HealthCheckConfig) -> bool:
        """Run TLS certificate health check."""
        try:
            context = ssl.create_default_context()
            with socket.create_connection(
                (self.service_name, config.port),
                timeout=config.timeout
            ) as sock:
                with context.wrap_socket(
                    sock,
                    server_hostname=self.service_name
                ) as ssock:
                    cert = ssock.getpeercert()
                    
                    if config.check_expiry:
                        not_after = datetime.strptime(
                            cert["notAfter"],
                            "%b %d %H:%M:%S %Y %Z"
                        )
                        days_remaining = (not_after - datetime.utcnow()).days
                        if days_remaining < config.min_cert_days:
                            return False
                    
                    return True
                    
        except Exception as e:
            raise HealthCheckError(f"TLS check failed: {str(e)}")
    
    async def _custom_check(self, config: HealthCheckConfig) -> bool:
        """Run custom health check."""
        if not config.custom_check:
            raise HealthCheckError("No custom check function provided")
            
        try:
            return await config.custom_check()
        except Exception as e:
            raise HealthCheckError(f"Custom check failed: {str(e)}") 