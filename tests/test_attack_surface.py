"""Tests for the MITRE ATT&CK action space module."""

from stratagem.environment.attack_surface import (
    TECHNIQUE_BY_ID,
    TECHNIQUE_CATALOG,
    AccessLevel,
    Tactic,
    Technique,
    get_applicable_techniques,
    techniques_by_tactic,
)
from stratagem.environment.network import NodeAttributes, NodeType, OS, Service


class TestTechniqueCatalog:
    def test_catalog_not_empty(self):
        assert len(TECHNIQUE_CATALOG) > 0

    def test_all_ids_unique(self):
        ids = [t.id for t in TECHNIQUE_CATALOG]
        assert len(ids) == len(set(ids))

    def test_index_matches_catalog(self):
        for tech in TECHNIQUE_CATALOG:
            assert TECHNIQUE_BY_ID[tech.id] is tech

    def test_success_rates_in_range(self):
        for tech in TECHNIQUE_CATALOG:
            assert 0.0 < tech.base_success_rate <= 1.0, f"{tech.id} has invalid success rate"

    def test_noise_in_range(self):
        for tech in TECHNIQUE_CATALOG:
            assert 0.0 <= tech.noise <= 1.0, f"{tech.id} has invalid noise"


class TestApplicability:
    def test_linux_server_gets_ssh_techniques(self):
        node = NodeAttributes(NodeType.SERVER, OS.LINUX, [Service.SSH, Service.HTTP], 5.0)
        techniques = get_applicable_techniques(node, AccessLevel.USER)
        ids = {t.id for t in techniques}
        assert "T1021.004" in ids  # SSH lateral movement
        assert "T1059.004" in ids  # Unix shell

    def test_windows_workstation_gets_rdp_techniques(self):
        node = NodeAttributes(NodeType.WORKSTATION, OS.WINDOWS, [Service.SMB, Service.RDP], 2.0)
        techniques = get_applicable_techniques(node, AccessLevel.USER)
        ids = {t.id for t in techniques}
        assert "T1021.001" in ids  # RDP
        assert "T1059.001" in ids  # PowerShell

    def test_no_access_limits_techniques(self):
        node = NodeAttributes(NodeType.SERVER, OS.LINUX, [Service.HTTP, Service.SSH], 5.0)
        no_access = get_applicable_techniques(node, AccessLevel.NONE)
        user_access = get_applicable_techniques(node, AccessLevel.USER)
        assert len(no_access) < len(user_access)

    def test_root_unlocks_more_techniques(self):
        node = NodeAttributes(NodeType.SERVER, OS.LINUX, [Service.SSH, Service.HTTP], 5.0)
        user = get_applicable_techniques(node, AccessLevel.USER)
        root = get_applicable_techniques(node, AccessLevel.ROOT)
        assert len(root) >= len(user)

    def test_os_filtering(self):
        linux_node = NodeAttributes(NodeType.SERVER, OS.LINUX, [Service.SSH], 5.0)
        techniques = get_applicable_techniques(linux_node, AccessLevel.USER)
        for tech in techniques:
            if tech.supported_os:
                assert OS.LINUX in tech.supported_os


class TestTacticGrouping:
    def test_lateral_movement_techniques_exist(self):
        lat = techniques_by_tactic(Tactic.LATERAL_MOVEMENT)
        assert len(lat) >= 2

    def test_initial_access_techniques_exist(self):
        ia = techniques_by_tactic(Tactic.INITIAL_ACCESS)
        assert len(ia) >= 1
