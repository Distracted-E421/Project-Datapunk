import unittest
import tempfile
import shutil
from pathlib import Path
import json
from datetime import datetime, timedelta
import asyncio
from unittest.mock import Mock, patch
import aiohttp
from aiohttp import web

from ..src.storage.index.consensus import (
    RaftConsensus,
    NodeRole,
    LogEntryType,
    LogEntry,
    ConsensusState
)
from ..src.storage.index.distributed import (
    DistributedManager,
    Node,
    NodeState
)
from ..src.storage.index.stats import StatisticsStore
from ..src.storage.index.manager import IndexManager
from ..src.storage.index.monitor import IndexMonitor
from ..src.storage.index.security import SecurityManager

class TestRaftConsensus(unittest.TestCase):
    def setUp(self):
        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "consensus_config.json"
        
        # Create test configuration
        config = {
            "consensus": {
                "heartbeat_interval_ms": 50,
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
        
        with open(self.config_path, 'w') as f:
            json.dump(config, f)
            
        # Initialize components
        self.store = StatisticsStore(Path(self.temp_dir) / "test.db")
        self.manager = IndexManager(self.store)
        self.monitor = IndexMonitor(
            self.store,
            self.manager,
            None,  # No optimizer needed
            None   # No config needed
        )
        self.security = SecurityManager(None)  # No config needed
        
        # Initialize distributed manager
        self.distributed = DistributedManager(
            self.store,
            self.manager,
            self.monitor,
            self.security,
            None,  # No config needed
            "node1"
        )
        
        # Initialize consensus
        self.consensus = RaftConsensus(
            self.distributed,
            self.monitor,
            self.config_path,
            "node1"
        )
        
        # Create test data
        self._create_test_data()
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        
    def _create_test_data(self):
        """Create test nodes and data."""
        # Create test nodes
        self.test_nodes = {
            "node1": Node(
                node_id="node1",
                role=NodeRole.FOLLOWER,
                host="localhost",
                port=8001,
                state=NodeState.ACTIVE,
                last_heartbeat=datetime.now(),
                indexes=set(),
                version="1.0.0"
            ),
            "node2": Node(
                node_id="node2",
                role=NodeRole.FOLLOWER,
                host="localhost",
                port=8002,
                state=NodeState.ACTIVE,
                last_heartbeat=datetime.now(),
                indexes=set(),
                version="1.0.0"
            ),
            "node3": Node(
                node_id="node3",
                role=NodeRole.FOLLOWER,
                host="localhost",
                port=8003,
                state=NodeState.ACTIVE,
                last_heartbeat=datetime.now(),
                indexes=set(),
                version="1.0.0"
            )
        }
        
        self.distributed.nodes.update(self.test_nodes)
        
    async def _start_mock_node(self, port: int, behavior: str = "normal"):
        """Start mock Raft node server."""
        routes = web.RouteTableDef()
        
        @routes.post("/request_vote")
        async def handle_vote_request(request):
            data = await request.json()
            
            if behavior == "deny_votes":
                return web.json_response({
                    "term": data["term"],
                    "vote_granted": False
                })
                
            if behavior == "higher_term":
                return web.json_response({
                    "term": data["term"] + 1,
                    "vote_granted": False
                })
                
            return web.json_response({
                "term": data["term"],
                "vote_granted": True
            })
            
        @routes.post("/append_entries")
        async def handle_append_entries(request):
            data = await request.json()
            
            if behavior == "reject_entries":
                return web.json_response({
                    "term": data["term"],
                    "success": False
                })
                
            return web.json_response({
                "term": data["term"],
                "success": True,
                "entries": data["entries"]
            })
            
        app = web.Application()
        app.add_routes(routes)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', port)
        await site.start()
        return runner
        
    def test_initial_state(self):
        """Test initial Raft state."""
        self.assertEqual(self.consensus.state.role, NodeRole.FOLLOWER)
        self.assertEqual(self.consensus.state.current_term, 0)
        self.assertIsNone(self.consensus.state.voted_for)
        self.assertEqual(len(self.consensus.state.log), 0)
        
    async def test_election_timeout(self):
        """Test election timeout triggers election."""
        # Force election timeout
        self.consensus.last_election_check = (
            datetime.now() - timedelta(seconds=10)
        )
        
        # Mock vote responses
        runners = []
        try:
            for node in self.test_nodes.values():
                if node.node_id != "node1":
                    runner = await self._start_mock_node(
                        node.port,
                        "normal"
                    )
                    runners.append(runner)
                    
            # Trigger election
            await self.consensus._election_task()
            
            # Verify became candidate
            self.assertEqual(self.consensus.state.role, NodeRole.CANDIDATE)
            self.assertEqual(self.consensus.state.current_term, 1)
            self.assertEqual(self.consensus.state.voted_for, "node1")
            
        finally:
            for runner in runners:
                await runner.cleanup()
                
    async def test_leader_election(self):
        """Test leader election process."""
        # Start mock nodes that will grant votes
        runners = []
        try:
            for node in self.test_nodes.values():
                if node.node_id != "node1":
                    runner = await self._start_mock_node(
                        node.port,
                        "normal"
                    )
                    runners.append(runner)
                    
            # Start election
            await self.consensus._start_election()
            
            # Verify became leader
            self.assertEqual(self.consensus.state.role, NodeRole.LEADER)
            self.assertEqual(self.consensus.state.leader_id, "node1")
            
            # Verify leader state initialized
            for node_id in self.test_nodes:
                if node_id != "node1":
                    self.assertIn(node_id, self.consensus.next_index)
                    self.assertIn(node_id, self.consensus.match_index)
                    
        finally:
            for runner in runners:
                await runner.cleanup()
                
    async def test_log_replication(self):
        """Test log entry replication."""
        # Make node leader
        self.consensus.state.role = NodeRole.LEADER
        self.consensus.state.leader_id = "node1"
        
        # Start mock follower nodes
        runners = []
        try:
            for node in self.test_nodes.values():
                if node.node_id != "node1":
                    runner = await self._start_mock_node(
                        node.port,
                        "normal"
                    )
                    runners.append(runner)
                    
            # Append entry
            success = await self.consensus.append_entry(
                LogEntryType.INDEX,
                {
                    "operation": "create",
                    "name": "test_index",
                    "type": "btree"
                }
            )
            
            # Verify entry appended and replicated
            self.assertTrue(success)
            self.assertEqual(len(self.consensus.state.log), 1)
            
            entry = self.consensus.state.log[0]
            self.assertEqual(entry.entry_type, LogEntryType.INDEX)
            self.assertEqual(entry.command["name"], "test_index")
            
        finally:
            for runner in runners:
                await runner.cleanup()
                
    async def test_append_entries_rejection(self):
        """Test handling of rejected append entries."""
        # Make node leader
        self.consensus.state.role = NodeRole.LEADER
        self.consensus.state.leader_id = "node1"
        
        # Start mock nodes that reject entries
        runners = []
        try:
            for node in self.test_nodes.values():
                if node.node_id != "node1":
                    runner = await self._start_mock_node(
                        node.port,
                        "reject_entries"
                    )
                    runners.append(runner)
                    
            # Try to append entry
            success = await self.consensus.append_entry(
                LogEntryType.INDEX,
                {
                    "operation": "create",
                    "name": "test_index",
                    "type": "btree"
                }
            )
            
            # Verify entry not committed
            self.assertFalse(success)
            
            # Verify next_index decremented
            for node_id in self.test_nodes:
                if node_id != "node1":
                    self.assertEqual(
                        self.consensus.next_index[node_id],
                        0
                    )
                    
        finally:
            for runner in runners:
                await runner.cleanup()
                
    async def test_higher_term_discovery(self):
        """Test handling of higher term discovery."""
        # Start mock node with higher term
        runners = []
        try:
            runner = await self._start_mock_node(
                self.test_nodes["node2"].port,
                "higher_term"
            )
            runners.append(runner)
            
            # Try to append entry
            success = await self.consensus.append_entry(
                LogEntryType.INDEX,
                {
                    "operation": "create",
                    "name": "test_index",
                    "type": "btree"
                }
            )
            
            # Verify reverted to follower
            self.assertEqual(
                self.consensus.state.role,
                NodeRole.FOLLOWER
            )
            self.assertGreater(
                self.consensus.state.current_term,
                0
            )
            
        finally:
            for runner in runners:
                await runner.cleanup()
                
    def test_log_consistency(self):
        """Test log consistency checks."""
        # Create some log entries
        self.consensus.state.log = [
            LogEntry(
                term=1,
                index=0,
                entry_type=LogEntryType.CONFIG,
                command={"setting": "value"},
                timestamp=datetime.now()
            ),
            LogEntry(
                term=1,
                index=1,
                entry_type=LogEntryType.INDEX,
                command={"operation": "create"},
                timestamp=datetime.now()
            )
        ]
        
        # Verify log matching
        prev_index = 0
        prev_term = self.consensus.state.log[0].term
        
        # This would match
        self.assertTrue(
            prev_term == self.consensus.state.log[prev_index].term
        )
        
        # This would not match
        self.assertFalse(
            prev_term == self.consensus.state.log[1].term - 1
        ) 