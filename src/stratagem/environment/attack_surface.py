"""MITRE ATT&CK technique action space for the attacker agent."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from stratagem.environment.network import NodeAttributes, OS, Service


class Tactic(str, Enum):
    INITIAL_ACCESS = "initial-access"
    EXECUTION = "execution"
    PERSISTENCE = "persistence"
    PRIVILEGE_ESCALATION = "privilege-escalation"
    CREDENTIAL_ACCESS = "credential-access"
    DISCOVERY = "discovery"
    LATERAL_MOVEMENT = "lateral-movement"
    COLLECTION = "collection"
    EXFILTRATION = "exfiltration"


class AccessLevel(str, Enum):
    NONE = "none"  # No access to the node.
    USER = "user"  # Unprivileged shell.
    ROOT = "root"  # Privileged / admin access.


@dataclass(frozen=True)
class Technique:
    id: str
    name: str
    tactic: Tactic
    base_success_rate: float  # 0-1, probability of success before modifiers.
    noise: float  # 0-1, detection signal strength (higher = easier to detect).
    required_access: AccessLevel  # Minimum access needed on source node.
    grants_access: AccessLevel  # Access level gained on target if successful.
    required_services: frozenset[Service]  # Target must run at least one of these.
    supported_os: frozenset[OS] | None  # None = OS-agnostic.

    def applicable_to(self, node: NodeAttributes) -> bool:
        """Check if this technique can target a node given its attributes."""
        if self.supported_os and node.os not in self.supported_os:
            return False
        if not self.required_services:
            return True
        return bool(self.required_services & set(node.services))


# ---------------------------------------------------------------------------
# Curated technique catalog
# ---------------------------------------------------------------------------
# Each entry is derived from real ATT&CK technique IDs but parameterized for
# the simulation. Success rates and noise levels are tuned for game balance.

TECHNIQUE_CATALOG: list[Technique] = [
    # -- Initial Access --
    Technique(
        id="T1190",
        name="Exploit Public-Facing Application",
        tactic=Tactic.INITIAL_ACCESS,
        base_success_rate=0.35,
        noise=0.4,
        required_access=AccessLevel.NONE,
        grants_access=AccessLevel.USER,
        required_services=frozenset({Service.HTTP, Service.HTTPS}),
        supported_os=None,
    ),
    Technique(
        id="T1133",
        name="External Remote Services",
        tactic=Tactic.INITIAL_ACCESS,
        base_success_rate=0.30,
        noise=0.3,
        required_access=AccessLevel.NONE,
        grants_access=AccessLevel.USER,
        required_services=frozenset({Service.SSH, Service.RDP}),
        supported_os=None,
    ),
    # -- Execution --
    Technique(
        id="T1059.004",
        name="Unix Shell Command Execution",
        tactic=Tactic.EXECUTION,
        base_success_rate=0.80,
        noise=0.2,
        required_access=AccessLevel.USER,
        grants_access=AccessLevel.USER,
        required_services=frozenset({Service.SSH}),
        supported_os=frozenset({OS.LINUX}),
    ),
    Technique(
        id="T1059.001",
        name="PowerShell Execution",
        tactic=Tactic.EXECUTION,
        base_success_rate=0.80,
        noise=0.3,
        required_access=AccessLevel.USER,
        grants_access=AccessLevel.USER,
        required_services=frozenset({Service.SMB, Service.RDP}),
        supported_os=frozenset({OS.WINDOWS}),
    ),
    # -- Privilege Escalation --
    Technique(
        id="T1068",
        name="Exploitation for Privilege Escalation",
        tactic=Tactic.PRIVILEGE_ESCALATION,
        base_success_rate=0.25,
        noise=0.5,
        required_access=AccessLevel.USER,
        grants_access=AccessLevel.ROOT,
        required_services=frozenset(),
        supported_os=None,
    ),
    Technique(
        id="T1078",
        name="Valid Accounts",
        tactic=Tactic.PRIVILEGE_ESCALATION,
        base_success_rate=0.40,
        noise=0.1,
        required_access=AccessLevel.USER,
        grants_access=AccessLevel.ROOT,
        required_services=frozenset(),
        supported_os=None,
    ),
    # -- Credential Access --
    Technique(
        id="T1110",
        name="Brute Force",
        tactic=Tactic.CREDENTIAL_ACCESS,
        base_success_rate=0.20,
        noise=0.7,
        required_access=AccessLevel.NONE,
        grants_access=AccessLevel.USER,
        required_services=frozenset({Service.SSH, Service.RDP, Service.FTP}),
        supported_os=None,
    ),
    Technique(
        id="T1003",
        name="OS Credential Dumping",
        tactic=Tactic.CREDENTIAL_ACCESS,
        base_success_rate=0.55,
        noise=0.4,
        required_access=AccessLevel.ROOT,
        grants_access=AccessLevel.ROOT,
        required_services=frozenset(),
        supported_os=None,
    ),
    Technique(
        id="T1552",
        name="Unsecured Credentials",
        tactic=Tactic.CREDENTIAL_ACCESS,
        base_success_rate=0.45,
        noise=0.15,
        required_access=AccessLevel.USER,
        grants_access=AccessLevel.USER,
        required_services=frozenset(),
        supported_os=None,
    ),
    # -- Discovery --
    Technique(
        id="T1046",
        name="Network Service Discovery",
        tactic=Tactic.DISCOVERY,
        base_success_rate=0.90,
        noise=0.35,
        required_access=AccessLevel.USER,
        grants_access=AccessLevel.USER,
        required_services=frozenset(),
        supported_os=None,
    ),
    Technique(
        id="T1083",
        name="File and Directory Discovery",
        tactic=Tactic.DISCOVERY,
        base_success_rate=0.95,
        noise=0.1,
        required_access=AccessLevel.USER,
        grants_access=AccessLevel.USER,
        required_services=frozenset(),
        supported_os=None,
    ),
    # -- Lateral Movement --
    Technique(
        id="T1021.001",
        name="Remote Desktop Protocol",
        tactic=Tactic.LATERAL_MOVEMENT,
        base_success_rate=0.50,
        noise=0.3,
        required_access=AccessLevel.USER,
        grants_access=AccessLevel.USER,
        required_services=frozenset({Service.RDP}),
        supported_os=frozenset({OS.WINDOWS}),
    ),
    Technique(
        id="T1021.004",
        name="SSH Lateral Movement",
        tactic=Tactic.LATERAL_MOVEMENT,
        base_success_rate=0.55,
        noise=0.2,
        required_access=AccessLevel.USER,
        grants_access=AccessLevel.USER,
        required_services=frozenset({Service.SSH}),
        supported_os=frozenset({OS.LINUX}),
    ),
    Technique(
        id="T1021.002",
        name="SMB/Windows Admin Shares",
        tactic=Tactic.LATERAL_MOVEMENT,
        base_success_rate=0.45,
        noise=0.35,
        required_access=AccessLevel.ROOT,
        grants_access=AccessLevel.USER,
        required_services=frozenset({Service.SMB}),
        supported_os=frozenset({OS.WINDOWS}),
    ),
    Technique(
        id="T1210",
        name="Exploitation of Remote Services",
        tactic=Tactic.LATERAL_MOVEMENT,
        base_success_rate=0.30,
        noise=0.5,
        required_access=AccessLevel.USER,
        grants_access=AccessLevel.USER,
        required_services=frozenset({Service.HTTP, Service.HTTPS, Service.MYSQL, Service.POSTGRESQL}),
        supported_os=None,
    ),
    # -- Collection --
    Technique(
        id="T1005",
        name="Data from Local System",
        tactic=Tactic.COLLECTION,
        base_success_rate=0.85,
        noise=0.15,
        required_access=AccessLevel.USER,
        grants_access=AccessLevel.USER,
        required_services=frozenset(),
        supported_os=None,
    ),
    Technique(
        id="T1039",
        name="Data from Network Shared Drive",
        tactic=Tactic.COLLECTION,
        base_success_rate=0.75,
        noise=0.2,
        required_access=AccessLevel.USER,
        grants_access=AccessLevel.USER,
        required_services=frozenset({Service.SMB, Service.FTP}),
        supported_os=None,
    ),
    # -- Exfiltration --
    Technique(
        id="T1041",
        name="Exfiltration Over C2 Channel",
        tactic=Tactic.EXFILTRATION,
        base_success_rate=0.70,
        noise=0.45,
        required_access=AccessLevel.USER,
        grants_access=AccessLevel.USER,
        required_services=frozenset(),
        supported_os=None,
    ),
    Technique(
        id="T1048",
        name="Exfiltration Over Alternative Protocol",
        tactic=Tactic.EXFILTRATION,
        base_success_rate=0.60,
        noise=0.25,
        required_access=AccessLevel.USER,
        grants_access=AccessLevel.USER,
        required_services=frozenset({Service.DNS, Service.FTP}),
        supported_os=None,
    ),
]

# Index for fast lookup.
TECHNIQUE_BY_ID: dict[str, Technique] = {t.id: t for t in TECHNIQUE_CATALOG}


def get_applicable_techniques(
    node: NodeAttributes,
    attacker_access: AccessLevel,
) -> list[Technique]:
    """Return techniques the attacker can use against a node given current access."""
    access_order = [AccessLevel.NONE, AccessLevel.USER, AccessLevel.ROOT]
    attacker_rank = access_order.index(attacker_access)

    results = []
    for tech in TECHNIQUE_CATALOG:
        required_rank = access_order.index(tech.required_access)
        if required_rank > attacker_rank:
            continue
        if not tech.applicable_to(node):
            continue
        results.append(tech)
    return results


def techniques_by_tactic(tactic: Tactic) -> list[Technique]:
    """Return all techniques for a given tactic."""
    return [t for t in TECHNIQUE_CATALOG if t.tactic == tactic]
