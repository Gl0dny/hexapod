"""
Unit tests for tripod gait implementation.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from hexapod.gait_generator.tripod_gait import TripodGait
from hexapod.gait_generator.base_gait import GaitPhase, GaitState


class TestTripodGait:
    """Test cases for TripodGait class."""
    
    @pytest.fixture
    def mock_hexapod(self):
        """Mock hexapod for testing."""
        hexapod = MagicMock()
        hexapod.current_leg_positions = [
            [0, 0, 0], [10, 10, 0], [20, 20, 0],
            [30, 30, 0], [40, 40, 0], [50, 50, 0]
        ]
        return hexapod
    
    @pytest.fixture
    def tripod_gait(self, mock_hexapod):
        """Create TripodGait instance for testing."""
        return TripodGait(mock_hexapod)
    
    def test_init_default_parameters(self, mock_hexapod):
        """Test TripodGait initialization with default parameters."""
        gait = TripodGait(mock_hexapod)
        
        assert gait.hexapod == mock_hexapod
        assert gait.step_radius == 30.0
        assert gait.leg_lift_distance == 20.0
        assert gait.stance_height == 0.0
        assert gait.dwell_time == 0.5
        assert gait.use_full_circle_stance is False
    
    def test_init_custom_parameters(self, mock_hexapod):
        """Test TripodGait initialization with custom parameters."""
        gait = TripodGait(
            mock_hexapod,
            step_radius=50.0,
            leg_lift_distance=25.0,
            stance_height=5.0,
            dwell_time=1.0,
            use_full_circle_stance=True
        )
        
        assert gait.step_radius == 50.0
        assert gait.leg_lift_distance == 25.0
        assert gait.stance_height == 5.0
        assert gait.dwell_time == 1.0
        assert gait.use_full_circle_stance is True
    
    def test_setup_gait_graph(self, tripod_gait):
        """Test gait graph setup for tripod gait."""
        # Test that the gait graph is properly set up
        assert GaitPhase.TRIPOD_A in tripod_gait.gait_graph
        assert GaitPhase.TRIPOD_B in tripod_gait.gait_graph
        
        # Test transitions
        assert tripod_gait.gait_graph[GaitPhase.TRIPOD_A] == [GaitPhase.TRIPOD_B]
        assert tripod_gait.gait_graph[GaitPhase.TRIPOD_B] == [GaitPhase.TRIPOD_A]
    
    def test_get_state_tripod_a(self, tripod_gait):
        """Test getting state for TRIPOD_A phase."""
        state = tripod_gait.get_state(GaitPhase.TRIPOD_A)
        
        assert isinstance(state, GaitState)
        assert state.phase == GaitPhase.TRIPOD_A
        assert state.swing_legs == [0, 2, 4]  # Right, Left Front, Left Back
        assert state.stance_legs == [1, 3, 5]  # Right Front, Left, Right Back
        assert state.dwell_time == tripod_gait.dwell_time
    
    def test_get_state_tripod_b(self, tripod_gait):
        """Test getting state for TRIPOD_B phase."""
        state = tripod_gait.get_state(GaitPhase.TRIPOD_B)
        
        assert isinstance(state, GaitState)
        assert state.phase == GaitPhase.TRIPOD_B
        assert state.swing_legs == [1, 3, 5]  # Right Front, Left, Right Back
        assert state.stance_legs == [0, 2, 4]  # Right, Left Front, Left Back
        assert state.dwell_time == tripod_gait.dwell_time
    
    def test_leg_groups_alternate(self, tripod_gait):
        """Test that leg groups alternate correctly between phases."""
        state_a = tripod_gait.get_state(GaitPhase.TRIPOD_A)
        state_b = tripod_gait.get_state(GaitPhase.TRIPOD_B)
        
        # Swing legs in A should be stance legs in B
        assert state_a.swing_legs == state_b.stance_legs
        # Stance legs in A should be swing legs in B
        assert state_a.stance_legs == state_b.swing_legs
    
    def test_all_legs_covered(self, tripod_gait):
        """Test that all 6 legs are covered in both phases."""
        state_a = tripod_gait.get_state(GaitPhase.TRIPOD_A)
        state_b = tripod_gait.get_state(GaitPhase.TRIPOD_B)
        
        # All legs should be in either swing or stance in each phase
        all_legs_a = set(state_a.swing_legs + state_a.stance_legs)
        all_legs_b = set(state_b.swing_legs + state_b.stance_legs)
        
        assert all_legs_a == {0, 1, 2, 3, 4, 5}
        assert all_legs_b == {0, 1, 2, 3, 4, 5}
    
    def test_three_legs_per_group(self, tripod_gait):
        """Test that each group has exactly 3 legs."""
        state_a = tripod_gait.get_state(GaitPhase.TRIPOD_A)
        state_b = tripod_gait.get_state(GaitPhase.TRIPOD_B)
        
        assert len(state_a.swing_legs) == 3
        assert len(state_a.stance_legs) == 3
        assert len(state_b.swing_legs) == 3
        assert len(state_b.stance_legs) == 3
    
    def test_leg_group_consistency(self, tripod_gait):
        """Test that leg groups are consistent with hexapod layout."""
        state_a = tripod_gait.get_state(GaitPhase.TRIPOD_A)
        
        # Group A: Legs 0, 2, 4 (Right, Left Front, Left Back)
        # These should be evenly spaced around the hexagon
        expected_group_a = [0, 2, 4]
        assert state_a.swing_legs == expected_group_a
        
        # Group B: Legs 1, 3, 5 (Right Front, Left, Right Back)
        expected_group_b = [1, 3, 5]
        assert state_a.stance_legs == expected_group_b
    
    def test_dwell_time_consistency(self, tripod_gait):
        """Test that dwell time is consistent across phases."""
        state_a = tripod_gait.get_state(GaitPhase.TRIPOD_A)
        state_b = tripod_gait.get_state(GaitPhase.TRIPOD_B)
        
        assert state_a.dwell_time == state_b.dwell_time
        assert state_a.dwell_time == tripod_gait.dwell_time
    
    def test_inheritance_from_base_gait(self, tripod_gait):
        """Test that TripodGait properly inherits from BaseGait."""
        from hexapod.gait_generator.base_gait import BaseGait
        
        assert isinstance(tripod_gait, BaseGait)
        assert hasattr(tripod_gait, 'step_radius')
        assert hasattr(tripod_gait, 'leg_lift_distance')
        assert hasattr(tripod_gait, 'stance_height')
        assert hasattr(tripod_gait, 'dwell_time')
        assert hasattr(tripod_gait, 'use_full_circle_stance')
        assert hasattr(tripod_gait, 'direction_input')
        assert hasattr(tripod_gait, 'rotation_input')
        assert hasattr(tripod_gait, 'leg_mount_angles')
        assert hasattr(tripod_gait, 'leg_paths')
    
    def test_gait_graph_completeness(self, tripod_gait):
        """Test that gait graph is complete and valid."""
        # All phases should have transitions
        assert len(tripod_gait.gait_graph) == 2
        
        # Each phase should have exactly one next phase
        for phase, next_phases in tripod_gait.gait_graph.items():
            assert len(next_phases) == 1
            assert next_phases[0] in tripod_gait.gait_graph
    
    def test_phase_cycle(self, tripod_gait):
        """Test that phases form a proper cycle."""
        # Start with TRIPOD_A
        current_phase = GaitPhase.TRIPOD_A
        
        # Follow the cycle
        next_phase = tripod_gait.gait_graph[current_phase][0]
        assert next_phase == GaitPhase.TRIPOD_B
        
        # Continue the cycle
        next_phase = tripod_gait.gait_graph[next_phase][0]
        assert next_phase == GaitPhase.TRIPOD_A
    
    def test_state_phase_consistency(self, tripod_gait):
        """Test that state phase matches the requested phase."""
        for phase in [GaitPhase.TRIPOD_A, GaitPhase.TRIPOD_B]:
            state = tripod_gait.get_state(phase)
            assert state.phase == phase
    
    def test_swing_stance_legs_disjoint(self, tripod_gait):
        """Test that swing and stance legs are disjoint in each phase."""
        for phase in [GaitPhase.TRIPOD_A, GaitPhase.TRIPOD_B]:
            state = tripod_gait.get_state(phase)
            
            swing_set = set(state.swing_legs)
            stance_set = set(state.stance_legs)
            
            # Should be disjoint
            assert swing_set.isdisjoint(stance_set)
    
    def test_leg_indices_valid(self, tripod_gait):
        """Test that all leg indices are valid (0-5)."""
        for phase in [GaitPhase.TRIPOD_A, GaitPhase.TRIPOD_B]:
            state = tripod_gait.get_state(phase)
            
            for leg in state.swing_legs + state.stance_legs:
                assert 0 <= leg <= 5
