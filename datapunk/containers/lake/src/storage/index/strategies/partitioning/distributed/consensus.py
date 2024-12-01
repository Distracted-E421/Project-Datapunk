from typing import Dict, Any, List, Optional, Set
import asyncio
import random
import time
import logging
from datetime import datetime, timedelta
from .network import NetworkManager, NetworkMessage, MessageTypes
from .node import PartitionNode

class ConsensusState:
    """Represents the state of a consensus node"""
    
    FOLLOWER = 'follower'
    CANDIDATE = 'candidate'
    LEADER = 'leader'
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.current_term = 0
        self.voted_for: Optional[str] = None
        self.role = self.FOLLOWER
        self.leader_id: Optional[str] = None
        self.last_heartbeat = datetime.now()
        self.votes_received: Set[str] = set()
        self.log: List[Dict[str, Any]] = []
        self.commit_index = -1
        self.last_applied = -1
        self.next_index: Dict[str, int] = {}
        self.match_index: Dict[str, int] = {}
        
class ConsensusManager:
    """Implements Raft consensus protocol"""
    
    def __init__(self, node: PartitionNode,
                 network: NetworkManager):
        self.node = node
        self.network = network
        self.state = ConsensusState(node.node_id)
        self.logger = logging.getLogger(__name__)
        self._stop = False
        self._election_timer = None
        self._heartbeat_timer = None
        
        # Register message handlers
        self._register_handlers()
        
        # Configuration
        self.election_timeout = random.uniform(150, 300)  # milliseconds
        self.heartbeat_interval = 50  # milliseconds
        
    async def start(self):
        """Start consensus manager"""
        self._stop = False
        await self._start_election_timer()
        
    async def stop(self):
        """Stop consensus manager"""
        self._stop = True
        if self._election_timer:
            self._election_timer.cancel()
        if self._heartbeat_timer:
            self._heartbeat_timer.cancel()
            
    async def append_entry(self, entry: Dict[str, Any]) -> bool:
        """Append entry to log"""
        if self.state.role != ConsensusState.LEADER:
            return False
            
        # Add entry to log
        entry['term'] = self.state.current_term
        self.state.log.append(entry)
        log_index = len(self.state.log) - 1
        
        # Replicate to followers
        success = await self._replicate_log(log_index)
        
        if success:
            # Update commit index
            await self._update_commit_index()
            return True
            
        return False
        
    def _register_handlers(self):
        """Register message handlers"""
        self.network.register_handler(
            MessageTypes.PREPARE,
            self._handle_vote_request
        )
        self.network.register_handler(
            MessageTypes.PROMISE,
            self._handle_vote_response
        )
        self.network.register_handler(
            MessageTypes.ACCEPT,
            self._handle_append_entries
        )
        self.network.register_handler(
            MessageTypes.ACCEPTED,
            self._handle_append_response
        )
        
    async def _start_election_timer(self):
        """Start election timeout timer"""
        while not self._stop:
            timeout = random.uniform(
                self.election_timeout,
                self.election_timeout * 2
            )
            try:
                await asyncio.sleep(timeout / 1000)  # Convert to seconds
                
                if (self.state.role != ConsensusState.LEADER and
                    (datetime.now() - self.state.last_heartbeat).total_seconds() * 1000 
                    >= self.election_timeout):
                    await self._start_election()
            except asyncio.CancelledError:
                break
                
    async def _start_election(self):
        """Start leader election"""
        self.state.current_term += 1
        self.state.role = ConsensusState.CANDIDATE
        self.state.voted_for = self.node.node_id
        self.state.votes_received = {self.node.node_id}
        self.state.leader_id = None
        
        # Request votes from all nodes
        request = {
            'term': self.state.current_term,
            'last_log_index': len(self.state.log) - 1,
            'last_log_term': self.state.log[-1]['term'] if self.state.log else 0
        }
        
        results = await self.network.broadcast(
            MessageTypes.PREPARE,
            request,
            self._get_other_nodes()
        )
        
        # Process results
        if len(self.state.votes_received) > len(self._get_all_nodes()) / 2:
            await self._become_leader()
            
    async def _become_leader(self):
        """Transition to leader state"""
        if self.state.role == ConsensusState.CANDIDATE:
            self.state.role = ConsensusState.LEADER
            self.state.leader_id = self.node.node_id
            
            # Initialize leader state
            for node_id in self._get_other_nodes():
                self.state.next_index[node_id] = len(self.state.log)
                self.state.match_index[node_id] = -1
                
            # Start heartbeat timer
            await self._start_heartbeat_timer()
            
    async def _start_heartbeat_timer(self):
        """Start heartbeat timer"""
        while not self._stop and self.state.role == ConsensusState.LEADER:
            try:
                await self._send_heartbeat()
                await asyncio.sleep(self.heartbeat_interval / 1000)
            except asyncio.CancelledError:
                break
                
    async def _send_heartbeat(self):
        """Send heartbeat to all followers"""
        if self.state.role != ConsensusState.LEADER:
            return
            
        for node_id in self._get_other_nodes():
            next_index = self.state.next_index[node_id]
            prev_log_index = next_index - 1
            prev_log_term = (self.state.log[prev_log_index]['term'] 
                           if prev_log_index >= 0 else 0)
                           
            entries = self.state.log[next_index:]
            
            request = {
                'term': self.state.current_term,
                'prev_log_index': prev_log_index,
                'prev_log_term': prev_log_term,
                'entries': entries,
                'leader_commit': self.state.commit_index
            }
            
            await self.network.send_message(NetworkMessage(
                MessageTypes.ACCEPT,
                self.node.node_id,
                node_id,
                request
            ))
            
    async def _handle_vote_request(self, message: NetworkMessage):
        """Handle vote request"""
        request = message.payload
        term = request['term']
        
        if term < self.state.current_term:
            response = {
                'term': self.state.current_term,
                'vote_granted': False
            }
        elif (self.state.voted_for is None or 
              self.state.voted_for == message.source):
            # Check if candidate's log is up-to-date
            last_log_index = len(self.state.log) - 1
            last_log_term = (self.state.log[last_log_index]['term'] 
                           if self.state.log else 0)
                           
            if (request['last_log_term'] > last_log_term or
                (request['last_log_term'] == last_log_term and
                 request['last_log_index'] >= last_log_index)):
                self.state.voted_for = message.source
                response = {
                    'term': term,
                    'vote_granted': True
                }
            else:
                response = {
                    'term': term,
                    'vote_granted': False
                }
        else:
            response = {
                'term': term,
                'vote_granted': False
            }
            
        await self.network.send_message(NetworkMessage(
            MessageTypes.PROMISE,
            self.node.node_id,
            message.source,
            response
        ))
        
    async def _handle_vote_response(self, message: NetworkMessage):
        """Handle vote response"""
        response = message.payload
        
        if (self.state.role == ConsensusState.CANDIDATE and
            response['term'] == self.state.current_term and
            response['vote_granted']):
            self.state.votes_received.add(message.source)
            
            if len(self.state.votes_received) > len(self._get_all_nodes()) / 2:
                await self._become_leader()
                
    async def _handle_append_entries(self, message: NetworkMessage):
        """Handle append entries request"""
        request = message.payload
        term = request['term']
        
        success = False
        if term < self.state.current_term:
            response = {
                'term': self.state.current_term,
                'success': False
            }
        else:
            if term > self.state.current_term:
                self.state.current_term = term
                self.state.voted_for = None
                
            self.state.role = ConsensusState.FOLLOWER
            self.state.leader_id = message.source
            self.state.last_heartbeat = datetime.now()
            
            # Check previous log entry
            prev_log_index = request['prev_log_index']
            if (prev_log_index >= len(self.state.log) or
                (prev_log_index >= 0 and
                 self.state.log[prev_log_index]['term'] != request['prev_log_term'])):
                response = {
                    'term': self.state.current_term,
                    'success': False
                }
            else:
                # Append new entries
                if request['entries']:
                    self.state.log = self.state.log[:prev_log_index + 1]
                    self.state.log.extend(request['entries'])
                    
                # Update commit index
                if request['leader_commit'] > self.state.commit_index:
                    self.state.commit_index = min(
                        request['leader_commit'],
                        len(self.state.log) - 1
                    )
                    
                success = True
                response = {
                    'term': self.state.current_term,
                    'success': True
                }
                
        await self.network.send_message(NetworkMessage(
            MessageTypes.ACCEPTED,
            self.node.node_id,
            message.source,
            response
        ))
        
    async def _handle_append_response(self, message: NetworkMessage):
        """Handle append entries response"""
        if self.state.role != ConsensusState.LEADER:
            return
            
        response = message.payload
        if response['term'] > self.state.current_term:
            self.state.current_term = response['term']
            self.state.role = ConsensusState.FOLLOWER
            self.state.voted_for = None
            return
            
        if response['success']:
            self.state.match_index[message.source] = self.state.next_index[message.source] - 1
            self.state.next_index[message.source] = self.state.match_index[message.source] + 1
            
            # Update commit index
            await self._update_commit_index()
        else:
            # Decrement next index and retry
            self.state.next_index[message.source] = max(
                0,
                self.state.next_index[message.source] - 1
            )
            
    async def _replicate_log(self, log_index: int) -> bool:
        """Replicate log entry to followers"""
        if self.state.role != ConsensusState.LEADER:
            return False
            
        success_count = 1  # Count self
        for node_id in self._get_other_nodes():
            next_index = self.state.next_index[node_id]
            prev_log_index = next_index - 1
            prev_log_term = (self.state.log[prev_log_index]['term']
                           if prev_log_index >= 0 else 0)
                           
            entries = self.state.log[next_index:log_index + 1]
            
            request = {
                'term': self.state.current_term,
                'prev_log_index': prev_log_index,
                'prev_log_term': prev_log_term,
                'entries': entries,
                'leader_commit': self.state.commit_index
            }
            
            response = await self.network.send_message(NetworkMessage(
                MessageTypes.ACCEPT,
                self.node.node_id,
                node_id,
                request
            ))
            
            if response:
                success_count += 1
                
        return success_count > len(self._get_all_nodes()) / 2
        
    async def _update_commit_index(self):
        """Update commit index based on match indices"""
        if self.state.role != ConsensusState.LEADER:
            return
            
        for n in range(len(self.state.log) - 1, self.state.commit_index, -1):
            if self.state.log[n]['term'] == self.state.current_term:
                match_count = 1  # Count self
                for node_id in self._get_other_nodes():
                    if self.state.match_index[node_id] >= n:
                        match_count += 1
                        
                if match_count > len(self._get_all_nodes()) / 2:
                    self.state.commit_index = n
                    break
                    
    def _get_other_nodes(self) -> List[str]:
        """Get list of other nodes"""
        # This would typically come from configuration
        return []
        
    def _get_all_nodes(self) -> List[str]:
        """Get list of all nodes"""
        return [self.node.node_id] + self._get_other_nodes() 