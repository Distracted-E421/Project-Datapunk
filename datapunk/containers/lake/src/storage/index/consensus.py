from typing import Dict, Any, List, Optional, Union, Set, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import logging
from pathlib import Path
from enum import Enum
import asyncio
import random
import aiohttp
import hashlib
import threading
from collections import defaultdict

from .distributed import DistributedManager, Node, NodeState
from .monitor import IndexMonitor

logger = logging.getLogger(__name__)

class NodeRole(Enum):
    """Raft node roles."""
    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    LEADER = "leader"

class LogEntryType(Enum):
    """Log entry types."""
    CONFIG = "config"
    INDEX = "index"
    SHARD = "shard"
    MEMBERSHIP = "membership"

@dataclass
class LogEntry:
    """Raft log entry."""
    term: int
    index: int
    entry_type: LogEntryType
    command: Dict[str, Any]
    timestamp: datetime

@dataclass
class ConsensusState:
    """Raft node state."""
    current_term: int
    voted_for: Optional[str]
    log: List[LogEntry]
    commit_index: int
    last_applied: int
    role: NodeRole
    leader_id: Optional[str]
    last_heartbeat: datetime

class RaftConsensus:
    """Implements Raft consensus protocol."""
    
    def __init__(
        self,
        distributed: DistributedManager,
        monitor: IndexMonitor,
        config_path: Optional[Union[str, Path]] = None,
        node_id: Optional[str] = None
    ):
        self.distributed = distributed
        self.monitor = monitor
        self.config_path = Path(config_path) if config_path else None
        self.node_id = node_id or distributed.node_id
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize state
        self.state = ConsensusState(
            current_term=0,
            voted_for=None,
            log=[],
            commit_index=-1,
            last_applied=-1,
            role=NodeRole.FOLLOWER,
            leader_id=None,
            last_heartbeat=datetime.now()
        )
        
        # Initialize volatile state
        self.next_index: Dict[str, int] = {}
        self.match_index: Dict[str, int] = {}
        
        # Initialize election timer
        self.election_timeout = self._random_timeout()
        self.last_election_check = datetime.now()
        
        # Start consensus tasks
        self._start_consensus_tasks()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load consensus configuration."""
        if not self.config_path or not self.config_path.exists():
            return {
                "consensus": {
                    "heartbeat_interval_ms": 100,
                    "election_timeout_min_ms": 150,
                    "election_timeout_max_ms": 300,
                    "max_entries_per_request": 100,
                    "snapshot_threshold": 1000
                },
                "recovery": {
                    "max_log_gaps": 100,
                    "catch_up_rounds": 5,
                    "max_snapshot_size_mb": 100
                }
            }
            
        with open(self.config_path, 'r') as f:
            return json.load(f)
            
    def _random_timeout(self) -> float:
        """Generate random election timeout."""
        min_ms = self.config["consensus"]["election_timeout_min_ms"]
        max_ms = self.config["consensus"]["election_timeout_max_ms"]
        return random.uniform(min_ms, max_ms) / 1000  # Convert to seconds
        
    def _start_consensus_tasks(self):
        """Start consensus background tasks."""
        asyncio.create_task(self._election_task())
        if self.state.role == NodeRole.LEADER:
            asyncio.create_task(self._heartbeat_task())
            
    async def _election_task(self):
        """Monitor election timeout and initiate election if needed."""
        while True:
            try:
                now = datetime.now()
                elapsed = (now - self.last_election_check).total_seconds()
                
                if (
                    self.state.role != NodeRole.LEADER and
                    elapsed > self.election_timeout
                ):
                    await self._start_election()
                    
                self.last_election_check = now
                await asyncio.sleep(0.05)  # 50ms check interval
                
            except Exception as e:
                logger.error(f"Election task error: {str(e)}")
                
    async def _start_election(self):
        """Start leader election."""
        # Increment term and become candidate
        self.state.current_term += 1
        self.state.role = NodeRole.CANDIDATE
        self.state.voted_for = self.node_id
        self.state.leader_id = None
        
        # Reset election timeout
        self.election_timeout = self._random_timeout()
        
        # Request votes from all nodes
        votes = 1  # Vote for self
        term = self.state.current_term
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for node_id, node in self.distributed.nodes.items():
                if node_id == self.node_id:
                    continue
                    
                if node.state != NodeState.ACTIVE:
                    continue
                    
                tasks.append(
                    self._request_vote(session, node, term)
                )
                
            # Wait for votes
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            for response in responses:
                if isinstance(response, Exception):
                    continue
                    
                if response.get("vote_granted"):
                    votes += 1
                elif response.get("term", 0) > term:
                    # Found higher term, revert to follower
                    self._become_follower(response["term"])
                    return
                    
        # Check if we won the election
        if (
            votes > len(self.distributed.nodes) / 2 and
            self.state.role == NodeRole.CANDIDATE
        ):
            self._become_leader()
            
    async def _request_vote(
        self,
        session: aiohttp.ClientSession,
        node: Node,
        term: int
    ) -> Dict[str, Any]:
        """Request vote from a node."""
        try:
            url = f"http://{node.host}:{node.port}/request_vote"
            async with session.post(
                url,
                json={
                    "term": term,
                    "candidate_id": self.node_id,
                    "last_log_index": len(self.state.log) - 1,
                    "last_log_term": (
                        self.state.log[-1].term
                        if self.state.log
                        else 0
                    )
                }
            ) as response:
                if response.status == 200:
                    return await response.json()
                return {"vote_granted": False}
        except Exception as e:
            logger.error(f"Vote request failed: {str(e)}")
            return {"vote_granted": False}
            
    def _become_follower(self, term: int):
        """Convert to follower state."""
        self.state.role = NodeRole.FOLLOWER
        self.state.current_term = term
        self.state.voted_for = None
        self.election_timeout = self._random_timeout()
        
    def _become_leader(self):
        """Convert to leader state."""
        self.state.role = NodeRole.LEADER
        self.state.leader_id = self.node_id
        
        # Initialize leader state
        for node_id in self.distributed.nodes:
            if node_id != self.node_id:
                self.next_index[node_id] = len(self.state.log)
                self.match_index[node_id] = -1
                
        # Start sending heartbeats
        asyncio.create_task(self._heartbeat_task())
        
    async def _heartbeat_task(self):
        """Send heartbeats to followers."""
        while self.state.role == NodeRole.LEADER:
            try:
                await self._send_append_entries()
                await asyncio.sleep(
                    self.config["consensus"]["heartbeat_interval_ms"] / 1000
                )
            except Exception as e:
                logger.error(f"Heartbeat task error: {str(e)}")
                
    async def _send_append_entries(self):
        """Send AppendEntries RPCs to all followers."""
        async with aiohttp.ClientSession() as session:
            tasks = []
            for node_id, node in self.distributed.nodes.items():
                if node_id == self.node_id:
                    continue
                    
                if node.state != NodeState.ACTIVE:
                    continue
                    
                next_idx = self.next_index.get(node_id, 0)
                prev_idx = next_idx - 1
                prev_term = (
                    self.state.log[prev_idx].term
                    if prev_idx >= 0 and self.state.log
                    else 0
                )
                
                entries = self.state.log[next_idx:next_idx + 
                    self.config["consensus"]["max_entries_per_request"]]
                
                tasks.append(
                    self._send_append_entries_to_node(
                        session,
                        node,
                        prev_idx,
                        prev_term,
                        entries
                    )
                )
                
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process responses
            for node_id, response in zip(
                [n for n in self.distributed.nodes if n != self.node_id],
                responses
            ):
                if isinstance(response, Exception):
                    continue
                    
                if response.get("term", 0) > self.state.current_term:
                    self._become_follower(response["term"])
                    return
                    
                if response.get("success"):
                    # Update follower progress
                    self.match_index[node_id] = (
                        self.next_index[node_id] +
                        len(response.get("entries", []))
                    )
                    self.next_index[node_id] = self.match_index[node_id] + 1
                else:
                    # Decrement next_index and retry
                    self.next_index[node_id] = max(0, self.next_index[node_id] - 1)
                    
    async def _send_append_entries_to_node(
        self,
        session: aiohttp.ClientSession,
        node: Node,
        prev_log_index: int,
        prev_log_term: int,
        entries: List[LogEntry]
    ) -> Dict[str, Any]:
        """Send AppendEntries RPC to a single node."""
        try:
            url = f"http://{node.host}:{node.port}/append_entries"
            async with session.post(
                url,
                json={
                    "term": self.state.current_term,
                    "leader_id": self.node_id,
                    "prev_log_index": prev_log_index,
                    "prev_log_term": prev_log_term,
                    "entries": [
                        {
                            "term": e.term,
                            "index": e.index,
                            "type": e.entry_type.value,
                            "command": e.command,
                            "timestamp": e.timestamp.isoformat()
                        }
                        for e in entries
                    ],
                    "leader_commit": self.state.commit_index
                }
            ) as response:
                if response.status == 200:
                    return await response.json()
                return {"success": False}
        except Exception as e:
            logger.error(f"AppendEntries failed: {str(e)}")
            return {"success": False}
            
    async def append_entry(
        self,
        entry_type: LogEntryType,
        command: Dict[str, Any]
    ) -> bool:
        """Append new entry to log."""
        if self.state.role != NodeRole.LEADER:
            return False
            
        # Create log entry
        entry = LogEntry(
            term=self.state.current_term,
            index=len(self.state.log),
            entry_type=entry_type,
            command=command,
            timestamp=datetime.now()
        )
        
        # Append to log
        self.state.log.append(entry)
        
        # Wait for replication
        success = await self._wait_for_replication(entry.index)
        
        if success:
            # Apply entry
            await self._apply_log_entry(entry)
            
        return success
        
    async def _wait_for_replication(self, index: int) -> bool:
        """Wait for log entry to be replicated to majority."""
        timeout = self.config["consensus"]["heartbeat_interval_ms"] / 1000 * 10
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < timeout:
            # Count nodes that have replicated this entry
            replicated = 1  # Leader has it
            for node_id in self.distributed.nodes:
                if node_id != self.node_id:
                    if self.match_index.get(node_id, -1) >= index:
                        replicated += 1
                        
            # Check if we have majority
            if replicated > len(self.distributed.nodes) / 2:
                return True
                
            await asyncio.sleep(0.05)
            
        return False
        
    async def _apply_log_entry(self, entry: LogEntry):
        """Apply committed log entry."""
        if entry.entry_type == LogEntryType.CONFIG:
            # Apply configuration change
            pass
        elif entry.entry_type == LogEntryType.INDEX:
            # Apply index operation
            if entry.command["operation"] == "create":
                await self.distributed.manager.create_index(
                    entry.command["name"],
                    entry.command["type"]
                )
            elif entry.command["operation"] == "delete":
                await self.distributed.manager.delete_index(
                    entry.command["name"]
                )
        elif entry.entry_type == LogEntryType.SHARD:
            # Apply shard operation
            pass
        elif entry.entry_type == LogEntryType.MEMBERSHIP:
            # Apply membership change
            pass 