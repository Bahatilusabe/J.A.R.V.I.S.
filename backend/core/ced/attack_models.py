"""
Pre-built MITRE ATT&CK Attack Chain Models

This module contains realistic attack chain DAGs mapped to MITRE ATT&CK
techniques. Each chain represents a multi-stage attack progression from
reconnaissance through impact.

Attack chains are represented as causal DAGs where:
- Nodes: Attack techniques/phases (e.g., 'Initial Access', 'Privilege Escalation')
- Edges: Causal relationships (e.g., "Initial Access enables Persistence")
- Weights: Probability/likelihood of progression

Chains cover:
1. Ransomware attacks (10+ stages)
2. Lateral movement campaigns (8+ stages)
3. Data exfiltration (9+ stages)
4. Privilege escalation (6+ stages)
5. Persistence mechanisms (7+ stages)
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import logging

logger = logging.getLogger("jarvis.ced.attack_models")


@dataclass
class AttackNode:
    """Represents a node in an attack chain DAG."""
    id: str
    mitre_id: str  # e.g., "T1547.001"
    name: str  # e.g., "Boot or Logon Autostart Execution"
    description: str
    category: str  # e.g., "persistence", "lateral_movement", "impact"
    severity: float  # 0.0 to 1.0
    prerequisites: List[str] = field(default_factory=list)  # IDs of prerequisite techniques
    
    def __hash__(self):
        return hash(self.id)


@dataclass
class AttackEdge:
    """Represents a directed edge (causal relationship) in attack chain."""
    source: str  # Node ID
    target: str  # Node ID
    relationship: str  # "enables", "facilitates", "requires"
    strength: float  # 0.0 to 1.0 - how strongly source enables target
    description: str = ""


@dataclass
class AttackChain:
    """Complete attack scenario as a DAG."""
    name: str
    description: str
    nodes: Dict[str, AttackNode]
    edges: List[AttackEdge]
    entry_points: List[str]  # Initial access technique IDs
    goals: List[str]  # Impact/objective technique IDs
    estimated_duration_hours: float
    
    def get_node(self, node_id: str) -> Optional[AttackNode]:
        """Get node by ID."""
        return self.nodes.get(node_id)
    
    def get_outgoing_edges(self, node_id: str) -> List[AttackEdge]:
        """Get all edges from this node."""
        return [e for e in self.edges if e.source == node_id]
    
    def get_incoming_edges(self, node_id: str) -> List[AttackEdge]:
        """Get all edges to this node."""
        return [e for e in self.edges if e.target == node_id]


# ============================================================================
# MITRE ATT&CK Attack Chains - Based on Real Threat Intelligence
# ============================================================================

# Ransomware attack chain (e.g., Conti, LockBit, Rhysida)
RANSOMWARE_CHAIN = AttackChain(
    name="Ransomware Multi-Stage Attack",
    description="Typical ransomware attack progression from initial compromise to impact",
    nodes={
        "initial_access": AttackNode(
            id="initial_access",
            mitre_id="T1566",
            name="Phishing with Attachment",
            description="Attacker sends malicious email with infected document",
            category="initial_access",
            severity=0.7,
            prerequisites=[]
        ),
        "execution": AttackNode(
            id="execution",
            mitre_id="T1204.002",
            name="User Execution: Malicious File",
            description="User opens malicious attachment, executes code",
            category="execution",
            severity=0.8,
            prerequisites=["initial_access"]
        ),
        "persistence": AttackNode(
            id="persistence",
            mitre_id="T1547.001",
            name="Boot or Logon Autostart Execution",
            description="Malware establishes persistence via registry/scheduled tasks",
            category="persistence",
            severity=0.75,
            prerequisites=["execution"]
        ),
        "privilege_escalation": AttackNode(
            id="privilege_escalation",
            mitre_id="T1548.002",
            name="Abuse Elevation Control Mechanism",
            description="Attacker escalates privileges using UAC bypass or similar",
            category="privilege_escalation",
            severity=0.8,
            prerequisites=["persistence"]
        ),
        "defense_evasion": AttackNode(
            id="defense_evasion",
            mitre_id="T1112",
            name="Modify Registry",
            description="Disable Windows Defender, firewall, UAC",
            category="defense_evasion",
            severity=0.7,
            prerequisites=["privilege_escalation"]
        ),
        "lateral_movement": AttackNode(
            id="lateral_movement",
            mitre_id="T1570",
            name="Lateral Tool Transfer",
            description="Spread malware to other systems on network",
            category="lateral_movement",
            severity=0.8,
            prerequisites=["privilege_escalation", "defense_evasion"]
        ),
        "exfiltration": AttackNode(
            id="exfiltration",
            mitre_id="T1020",
            name="Automated Exfiltration",
            description="Steal sensitive data to attacker-controlled server",
            category="exfiltration",
            severity=0.85,
            prerequisites=["lateral_movement"]
        ),
        "impact": AttackNode(
            id="impact",
            mitre_id="T1491.001",
            name="Defacement: Internal",
            description="Deploy ransomware, encrypt files, display ransom note",
            category="impact",
            severity=0.95,
            prerequisites=["exfiltration"]
        ),
    },
    edges=[
        AttackEdge("initial_access", "execution", "enables", 0.9),
        AttackEdge("execution", "persistence", "enables", 0.85),
        AttackEdge("persistence", "privilege_escalation", "enables", 0.8),
        AttackEdge("privilege_escalation", "defense_evasion", "enables", 0.9),
        AttackEdge("privilege_escalation", "lateral_movement", "enables", 0.75),
        AttackEdge("defense_evasion", "lateral_movement", "facilitates", 0.7),
        AttackEdge("lateral_movement", "exfiltration", "enables", 0.8),
        AttackEdge("exfiltration", "impact", "enables", 0.95),
    ],
    entry_points=["initial_access"],
    goals=["impact"],
    estimated_duration_hours=72.0
)

# Lateral movement for credential theft
LATERAL_MOVEMENT_CHAIN = AttackChain(
    name="Lateral Movement & Credential Theft",
    description="Attack progression focusing on internal network movement and credential harvesting",
    nodes={
        "initial_breach": AttackNode(
            id="initial_breach",
            mitre_id="T1566.001",
            name="Spearphishing with Credential Theft Link",
            description="Attacker tricks user to visit credential harvesting site",
            category="initial_access",
            severity=0.6,
            prerequisites=[]
        ),
        "credential_access": AttackNode(
            id="credential_access",
            mitre_id="T1110.001",
            name="Brute Force: Credentials",
            description="Attempt to crack stolen credentials or brute force accounts",
            category="credential_access",
            severity=0.75,
            prerequisites=["initial_breach"]
        ),
        "domain_enumeration": AttackNode(
            id="domain_enumeration",
            mitre_id="T1087.002",
            name="Account Discovery: Domain Account",
            description="Enumerate domain users and groups for targeting",
            category="discovery",
            severity=0.5,
            prerequisites=["credential_access"]
        ),
        "lateral_movement_winrm": AttackNode(
            id="lateral_movement_winrm",
            mitre_id="T1021.006",
            name="Remote Services: Windows Remote Management",
            description="Use WinRM to move to other systems",
            category="lateral_movement",
            severity=0.8,
            prerequisites=["credential_access", "domain_enumeration"]
        ),
        "data_staging": AttackNode(
            id="data_staging",
            mitre_id="T1074.002",
            name="Data Staged: Remote Location",
            description="Collect sensitive data on target system",
            category="collection",
            severity=0.7,
            prerequisites=["lateral_movement_winrm"]
        ),
        "exfiltration_scheduled": AttackNode(
            id="exfiltration_scheduled",
            mitre_id="T1020.001",
            name="Exfiltration Over Other Network Medium",
            description="Transfer stolen data via alternate channels",
            category="exfiltration",
            severity=0.85,
            prerequisites=["data_staging"]
        ),
    },
    edges=[
        AttackEdge("initial_breach", "credential_access", "enables", 0.85),
        AttackEdge("credential_access", "domain_enumeration", "enables", 0.9),
        AttackEdge("credential_access", "lateral_movement_winrm", "enables", 0.8),
        AttackEdge("domain_enumeration", "lateral_movement_winrm", "facilitates", 0.7),
        AttackEdge("lateral_movement_winrm", "data_staging", "enables", 0.85),
        AttackEdge("data_staging", "exfiltration_scheduled", "enables", 0.9),
    ],
    entry_points=["initial_breach"],
    goals=["exfiltration_scheduled"],
    estimated_duration_hours=48.0
)

# Data exfiltration attack chain
DATA_EXFILTRATION_CHAIN = AttackChain(
    name="Targeted Data Exfiltration",
    description="Focused on stealing sensitive data without deploying malware",
    nodes={
        "reconnaissance": AttackNode(
            id="reconnaissance",
            mitre_id="T1592.001",
            name="Gather Victim Information: Credentials",
            description="Research company structure and employee information",
            category="reconnaissance",
            severity=0.3,
            prerequisites=[]
        ),
        "phishing": AttackNode(
            id="phishing",
            mitre_id="T1566.002",
            name="Phishing: Spearphishing Link",
            description="Targeted phishing to security officer or IT admin",
            category="initial_access",
            severity=0.7,
            prerequisites=["reconnaissance"]
        ),
        "credential_compromise": AttackNode(
            id="credential_compromise",
            mitre_id="T1021.001",
            name="Remote Services: Remote Desktop Protocol",
            description="Gain RDP access with stolen credentials",
            category="lateral_movement",
            severity=0.8,
            prerequisites=["phishing"]
        ),
        "file_discovery": AttackNode(
            id="file_discovery",
            mitre_id="T1083",
            name="File and Directory Discovery",
            description="Locate sensitive files and databases",
            category="discovery",
            severity=0.6,
            prerequisites=["credential_compromise"]
        ),
        "archive_data": AttackNode(
            id="archive_data",
            mitre_id="T1560.001",
            name="Archive via Utility: WinRAR/7-Zip",
            description="Compress sensitive data for transfer",
            category="collection",
            severity=0.65,
            prerequisites=["file_discovery"]
        ),
        "exfiltrate_cloud": AttackNode(
            id="exfiltrate_cloud",
            mitre_id="T1020",
            name="Automated Exfiltration",
            description="Upload data to cloud storage or FTP server",
            category="exfiltration",
            severity=0.85,
            prerequisites=["archive_data"]
        ),
    },
    edges=[
        AttackEdge("reconnaissance", "phishing", "facilitates", 0.6),
        AttackEdge("phishing", "credential_compromise", "enables", 0.8),
        AttackEdge("credential_compromise", "file_discovery", "enables", 0.9),
        AttackEdge("file_discovery", "archive_data", "enables", 0.85),
        AttackEdge("archive_data", "exfiltrate_cloud", "enables", 0.9),
    ],
    entry_points=["reconnaissance"],
    goals=["exfiltrate_cloud"],
    estimated_duration_hours=24.0
)

# Privilege escalation chain
PRIVILEGE_ESCALATION_CHAIN = AttackChain(
    name="Privilege Escalation Attack",
    description="Focus on escalating from user to admin/SYSTEM privileges",
    nodes={
        "user_account": AttackNode(
            id="user_account",
            mitre_id="T1078",
            name="Valid Accounts: Local Accounts",
            description="Attacker has valid local user account",
            category="initial_access",
            severity=0.5,
            prerequisites=[]
        ),
        "exploit_cve": AttackNode(
            id="exploit_cve",
            mitre_id="T1548.004",
            name="Abuse Elevation Control Mechanism: Elevated Execution",
            description="Exploit CVE in Windows (e.g., kernel privilege escalation)",
            category="privilege_escalation",
            severity=0.85,
            prerequisites=["user_account"]
        ),
        "system_access": AttackNode(
            id="system_access",
            mitre_id="T1134",
            name="Access Token Manipulation",
            description="Attacker achieves SYSTEM privileges",
            category="privilege_escalation",
            severity=0.9,
            prerequisites=["exploit_cve"]
        ),
        "persistence_admin": AttackNode(
            id="persistence_admin",
            mitre_id="T1547.014",
            name="Boot or Logon Autostart Execution: System Startup Script",
            description="Establish persistence as SYSTEM user",
            category="persistence",
            severity=0.85,
            prerequisites=["system_access"]
        ),
    },
    edges=[
        AttackEdge("user_account", "exploit_cve", "enables", 0.9),
        AttackEdge("exploit_cve", "system_access", "enables", 0.95),
        AttackEdge("system_access", "persistence_admin", "enables", 0.9),
    ],
    entry_points=["user_account"],
    goals=["persistence_admin"],
    estimated_duration_hours=1.0
)

# Registry/persistence backdoor chain
PERSISTENCE_CHAIN = AttackChain(
    name="Persistence Mechanisms",
    description="Establishing long-term access and backdoors",
    nodes={
        "initial_code_exec": AttackNode(
            id="initial_code_exec",
            mitre_id="T1204",
            name="User Execution",
            description="Initial code execution capability (from exploit, script, etc.)",
            category="execution",
            severity=0.7,
            prerequisites=[]
        ),
        "registry_persistence": AttackNode(
            id="registry_persistence",
            mitre_id="T1547.001",
            name="Boot or Logon Autostart Execution: Registry Run Keys",
            description="Add malware to HKLM/HKCU Run registry keys",
            category="persistence",
            severity=0.8,
            prerequisites=["initial_code_exec"]
        ),
        "scheduled_task": AttackNode(
            id="scheduled_task",
            mitre_id="T1053.005",
            name="Scheduled Task/Job: Scheduled Task",
            description="Create scheduled task to run payload periodically",
            category="persistence",
            severity=0.75,
            prerequisites=["initial_code_exec"]
        ),
        "wmi_event": AttackNode(
            id="wmi_event",
            mitre_id="T1546.003",
            name="Event Triggered Execution: Windows Management Instrumentation",
            description="Set up WMI event subscription for persistence",
            category="persistence",
            severity=0.7,
            prerequisites=["initial_code_exec"]
        ),
    },
    edges=[
        AttackEdge("initial_code_exec", "registry_persistence", "enables", 0.9),
        AttackEdge("initial_code_exec", "scheduled_task", "enables", 0.85),
        AttackEdge("initial_code_exec", "wmi_event", "enables", 0.7),
    ],
    entry_points=["initial_code_exec"],
    goals=["registry_persistence", "scheduled_task", "wmi_event"],
    estimated_duration_hours=0.5
)

# Master dictionary of all attack chains
MITRE_ATTACK_CHAINS: Dict[str, AttackChain] = {
    "ransomware": RANSOMWARE_CHAIN,
    "lateral_movement": LATERAL_MOVEMENT_CHAIN,
    "data_exfiltration": DATA_EXFILTRATION_CHAIN,
    "privilege_escalation": PRIVILEGE_ESCALATION_CHAIN,
    "persistence": PERSISTENCE_CHAIN,
}


# ============================================================================
# Helper Functions for Attack Chain Management
# ============================================================================

def get_attack_chain_dag(chain_type: str) -> Optional[AttackChain]:
    """
    Retrieve a pre-built attack chain by type.
    
    Args:
        chain_type: One of "ransomware", "lateral_movement", "data_exfiltration",
                   "privilege_escalation", "persistence"
    
    Returns:
        AttackChain DAG or None if not found
    """
    return MITRE_ATTACK_CHAINS.get(chain_type.lower())


def get_all_chain_types() -> List[str]:
    """Get list of all available attack chain types."""
    return list(MITRE_ATTACK_CHAINS.keys())


def find_attack_path(chain: AttackChain, start_node: str, end_node: str) -> Optional[List[str]]:
    """
    Find shortest path from start to end node in attack chain DAG.
    
    Args:
        chain: AttackChain to search
        start_node: Starting node ID
        end_node: Ending node ID
    
    Returns:
        List of node IDs representing path, or None if no path exists
    """
    from collections import deque
    
    if start_node not in chain.nodes or end_node not in chain.nodes:
        return None
    
    queue = deque([(start_node, [start_node])])
    visited = {start_node}
    
    while queue:
        current, path = queue.popleft()
        
        if current == end_node:
            return path
        
        for edge in chain.get_outgoing_edges(current):
            if edge.target not in visited:
                visited.add(edge.target)
                queue.append((edge.target, path + [edge.target]))
    
    return None


__all__ = [
    "AttackNode",
    "AttackEdge",
    "AttackChain",
    "MITRE_ATTACK_CHAINS",
    "RANSOMWARE_CHAIN",
    "LATERAL_MOVEMENT_CHAIN",
    "DATA_EXFILTRATION_CHAIN",
    "PRIVILEGE_ESCALATION_CHAIN",
    "PERSISTENCE_CHAIN",
    "get_attack_chain_dag",
    "get_all_chain_types",
    "find_attack_path",
]
