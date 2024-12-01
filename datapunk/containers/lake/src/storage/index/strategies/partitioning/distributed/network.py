from typing import Dict, Any, List, Optional, Callable
import asyncio
import aiohttp
import json
import logging
from datetime import datetime
from .node import PartitionNode

class NetworkMessage:
    """Represents a network message between nodes"""
    
    def __init__(self, msg_type: str,
                 source: str,
                 target: str,
                 payload: Dict[str, Any]):
        self.msg_type = msg_type
        self.source = source
        self.target = target
        self.payload = payload
        self.timestamp = datetime.now()
        self.id = f"{source}_{target}_{self.timestamp.timestamp()}"
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            'id': self.id,
            'type': self.msg_type,
            'source': self.source,
            'target': self.target,
            'payload': self.payload,
            'timestamp': self.timestamp.isoformat()
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NetworkMessage':
        """Create message from dictionary"""
        msg = cls(
            data['type'],
            data['source'],
            data['target'],
            data['payload']
        )
        msg.id = data['id']
        msg.timestamp = datetime.fromisoformat(data['timestamp'])
        return msg

class NetworkManager:
    """Manages network communication between nodes"""
    
    def __init__(self, node: PartitionNode, port: int):
        self.node = node
        self.port = port
        self.handlers: Dict[str, List[Callable]] = {}
        self.connections: Dict[str, aiohttp.ClientSession] = {}
        self.logger = logging.getLogger(__name__)
        self.server = None
        self._stop = False
        
    async def start(self):
        """Start network manager"""
        # Start HTTP server
        self.server = await self._start_server()
        
        # Initialize client sessions
        await self._init_connections()
        
    async def stop(self):
        """Stop network manager"""
        self._stop = True
        
        # Close client sessions
        for session in self.connections.values():
            await session.close()
            
        # Stop server
        if self.server:
            await self.server.cleanup()
            
    async def send_message(self, message: NetworkMessage) -> bool:
        """Send message to target node"""
        try:
            session = self.connections.get(message.target)
            if not session:
                session = await self._create_connection(message.target)
                
            async with session.post(
                f"http://{message.target}:{self.port}/message",
                json=message.to_dict()
            ) as response:
                return response.status == 200
        except Exception as e:
            self.logger.error(f"Failed to send message: {str(e)}")
            return False
            
    def register_handler(self, msg_type: str,
                        handler: Callable[[NetworkMessage], None]):
        """Register message handler"""
        if msg_type not in self.handlers:
            self.handlers[msg_type] = []
        self.handlers[msg_type].append(handler)
        
    async def broadcast(self, msg_type: str,
                       payload: Dict[str, Any],
                       targets: List[str]) -> Dict[str, bool]:
        """Broadcast message to multiple nodes"""
        results = {}
        for target in targets:
            message = NetworkMessage(
                msg_type,
                self.node.node_id,
                target,
                payload
            )
            results[target] = await self.send_message(message)
        return results
        
    async def _start_server(self) -> aiohttp.web.Application:
        """Start HTTP server for receiving messages"""
        app = aiohttp.web.Application()
        app.router.add_post('/message', self._handle_message)
        app.router.add_get('/health', self._handle_health_check)
        
        runner = aiohttp.web.AppRunner(app)
        await runner.setup()
        
        site = aiohttp.web.TCPSite(runner, 'localhost', self.port)
        await site.start()
        
        return runner
        
    async def _handle_message(self, request: aiohttp.web.Request) -> aiohttp.web.Response:
        """Handle incoming message"""
        try:
            data = await request.json()
            message = NetworkMessage.from_dict(data)
            
            # Process message
            await self._process_message(message)
            
            return aiohttp.web.Response(status=200)
        except Exception as e:
            self.logger.error(f"Error handling message: {str(e)}")
            return aiohttp.web.Response(status=500)
            
    async def _handle_health_check(self, request: aiohttp.web.Request) -> aiohttp.web.Response:
        """Handle health check request"""
        return aiohttp.web.json_response({
            'status': 'healthy',
            'node_id': self.node.node_id,
            'timestamp': datetime.now().isoformat()
        })
        
    async def _process_message(self, message: NetworkMessage):
        """Process received message"""
        handlers = self.handlers.get(message.msg_type, [])
        for handler in handlers:
            try:
                await handler(message)
            except Exception as e:
                self.logger.error(f"Handler error: {str(e)}")
                
    async def _init_connections(self):
        """Initialize client sessions"""
        # This would typically load known nodes from configuration
        pass
        
    async def _create_connection(self, target: str) -> aiohttp.ClientSession:
        """Create new client session"""
        session = aiohttp.ClientSession()
        self.connections[target] = session
        return session
        
    async def check_node_health(self, target: str) -> bool:
        """Check health of target node"""
        try:
            session = self.connections.get(target)
            if not session:
                session = await self._create_connection(target)
                
            async with session.get(
                f"http://{target}:{self.port}/health"
            ) as response:
                return response.status == 200
        except Exception:
            return False
            
class MessageTypes:
    """Constants for message types"""
    
    # Cluster management
    NODE_JOIN = 'node_join'
    NODE_LEAVE = 'node_leave'
    STATE_UPDATE = 'state_update'
    
    # Partition management
    PARTITION_ASSIGN = 'partition_assign'
    PARTITION_TRANSFER = 'partition_transfer'
    PARTITION_SYNC = 'partition_sync'
    
    # Health and monitoring
    HEALTH_CHECK = 'health_check'
    HEALTH_REPORT = 'health_report'
    ALERT = 'alert'
    
    # Consensus
    PREPARE = 'prepare'
    PROMISE = 'promise'
    ACCEPT = 'accept'
    ACCEPTED = 'accepted'
    
    # Recovery
    RECOVERY_REQUEST = 'recovery_request'
    RECOVERY_RESPONSE = 'recovery_response'
    
    # Replication
    REPLICATE = 'replicate'
    REPLICATE_ACK = 'replicate_ack'
    
class NetworkMetrics:
    """Tracks network-related metrics"""
    
    def __init__(self):
        self.messages_sent = 0
        self.messages_received = 0
        self.bytes_sent = 0
        self.bytes_received = 0
        self.failed_messages = 0
        self.latencies: List[float] = []
        
    def record_send(self, message: NetworkMessage, success: bool):
        """Record sent message"""
        if success:
            self.messages_sent += 1
            self.bytes_sent += len(json.dumps(message.to_dict()))
        else:
            self.failed_messages += 1
            
    def record_receive(self, message: NetworkMessage):
        """Record received message"""
        self.messages_received += 1
        self.bytes_received += len(json.dumps(message.to_dict()))
        
    def record_latency(self, latency: float):
        """Record message latency"""
        self.latencies.append(latency)
        if len(self.latencies) > 1000:
            self.latencies = self.latencies[-1000:]
            
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return {
            'messages_sent': self.messages_sent,
            'messages_received': self.messages_received,
            'bytes_sent': self.bytes_sent,
            'bytes_received': self.bytes_received,
            'failed_messages': self.failed_messages,
            'avg_latency': sum(self.latencies) / max(1, len(self.latencies)),
            'success_rate': self.messages_sent / max(1, self.messages_sent + self.failed_messages)
        } 