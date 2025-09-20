"""
Unit tests for wave gait implementation.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from hexapod.gait_generator.wave_gait import WaveGait
from hexapod.gait_generator.base_gait import GaitPhase, GaitState


class TestWaveGait:
    """Test cases for WaveGait class."""
    
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
    def wave_gait(self, mock_hexapod):
        """Create WaveGait instance for testing."""
        return WaveGait(mock_hexapod)
    
    def test_init_default_parameters(self, mock_hexapod):
        """Test WaveGait initialization with default parameters."""
        gait = WaveGait(mock_hexapod)
        
        assert gait.hexapod == mock_hexapod
        assert gait.step_radius == 30.0
        assert gait.leg_lift_distance == 10.0
        assert gait.stance_height == 0.0
        assert gait.dwell_time == 0.5
        assert gait.use_full_circle_stance is False
    
    def test_init_custom_parameters(self, mock_hexapod):
        """Test WaveGait initialization with custom parameters."""
        gait = WaveGait(
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
    
    def test_setup_gait_graph(self, wave_gait):
        """Test gait graph setup for wave gait."""
        # Test that all wave phases are in the gait graph
        wave_phases = [
            GaitPhase.WAVE_1, GaitPhase.WAVE_2, GaitPhase.WAVE_3,
            GaitPhase.WAVE_4, GaitPhase.WAVE_5, GaitPhase.WAVE_6
        ]
        
        for phase in wave_phases:
            assert phase in wave_gait.gait_graph
        
        # Test transitions form a cycle
        assert wave_gait.gait_graph[GaitPhase.WAVE_1] == [GaitPhase.WAVE_2]
        assert wave_gait.gait_graph[GaitPhase.WAVE_2] == [GaitPhase.WAVE_3]
        assert wave_gait.gait_graph[GaitPhase.WAVE_3] == [GaitPhase.WAVE_4]
        assert wave_gait.gait_graph[GaitPhase.WAVE_4] == [GaitPhase.WAVE_5]
        assert wave_gait.gait_graph[GaitPhase.WAVE_5] == [GaitPhase.WAVE_6]
        assert wave_gait.gait_graph[GaitPhase.WAVE_6] == [GaitPhase.WAVE_1]
    
    def test_get_state_wave_1(self, wave_gait):
        """Test getting state for WAVE_1 phase."""
        state = wave_gait.get_state(GaitPhase.WAVE_1)
        
        assert isinstance(state, GaitState)
        assert state.phase == GaitPhase.WAVE_1
        assert state.swing_legs == [0]  # Only leg 0 swings
        assert state.stance_legs == [1, 2, 3, 4, 5]  # All other legs stance
        assert state.dwell_time == wave_gait.dwell_time
    
    def test_get_state_wave_2(self, wave_gait):
        """Test getting state for WAVE_2 phase."""
        state = wave_gait.get_state(GaitPhase.WAVE_2)
        
        assert isinstance(state, GaitState)
        assert state.phase == GaitPhase.WAVE_2
        assert state.swing_legs == [1]  # Only leg 1 swings
        assert state.stance_legs == [0, 2, 3, 4, 5]  # All other legs stance
        assert state.dwell_time == wave_gait.dwell_time
    
    def test_get_state_wave_3(self, wave_gait):
        """Test getting state for WAVE_3 phase."""
        state = wave_gait.get_state(GaitPhase.WAVE_3)
        
        assert isinstance(state, GaitState)
        assert state.phase == GaitPhase.WAVE_3
        assert state.swing_legs == [2]  # Only leg 2 swings
        assert state.stance_legs == [0, 1, 3, 4, 5]  # All other legs stance
        assert state.dwell_time == wave_gait.dwell_time
    
    def test_get_state_wave_4(self, wave_gait):
        """Test getting state for WAVE_4 phase."""
        state = wave_gait.get_state(GaitPhase.WAVE_4)
        
        assert isinstance(state, GaitState)
        assert state.phase == GaitPhase.WAVE_4
        assert state.swing_legs == [3]  # Only leg 3 swings
        assert state.stance_legs == [0, 1, 2, 4, 5]  # All other legs stance
        assert state.dwell_time == wave_gait.dwell_time
    
    def test_get_state_wave_5(self, wave_gait):
        """Test getting state for WAVE_5 phase."""
        state = wave_gait.get_state(GaitPhase.WAVE_5)
        
        assert isinstance(state, GaitState)
        assert state.phase == GaitPhase.WAVE_5
        assert state.swing_legs == [4]  # Only leg 4 swings
        assert state.stance_legs == [0, 1, 2, 3, 5]  # All other legs stance
        assert state.dwell_time == wave_gait.dwell_time
    
    def test_get_state_wave_6(self, wave_gait):
        """Test getting state for WAVE_6 phase."""
        state = wave_gait.get_state(GaitPhase.WAVE_6)
        
        assert isinstance(state, GaitState)
        assert state.phase == GaitPhase.WAVE_6
        assert state.swing_legs == [5]  # Only leg 5 swings
        assert state.stance_legs == [0, 1, 2, 3, 4]  # All other legs stance
        assert state.dwell_time == wave_gait.dwell_time
    
    def test_one_leg_swings_per_phase(self, wave_gait):
        """Test that exactly one leg swings in each phase."""
        wave_phases = [
            GaitPhase.WAVE_1, GaitPhase.WAVE_2, GaitPhase.WAVE_3,
            GaitPhase.WAVE_4, GaitPhase.WAVE_5, GaitPhase.WAVE_6
        ]
        
        for phase in wave_phases:
            state = wave_gait.get_state(phase)
            assert len(state.swing_legs) == 1
            assert len(state.stance_legs) == 5
    
    def test_all_legs_swing_once_per_cycle(self, wave_gait):
        """Test that all legs swing exactly once per complete cycle."""
        wave_phases = [
            GaitPhase.WAVE_1, GaitPhase.WAVE_2, GaitPhase.WAVE_3,
            GaitPhase.WAVE_4, GaitPhase.WAVE_5, GaitPhase.WAVE_6
        ]
        
        all_swing_legs = []
        for phase in wave_phases:
            state = wave_gait.get_state(phase)
            all_swing_legs.extend(state.swing_legs)
        
        # All legs 0-5 should appear exactly once
        assert sorted(all_swing_legs) == [0, 1, 2, 3, 4, 5]
    
    def test_leg_swing_sequence(self, wave_gait):
        """Test that legs swing in the correct sequence."""
        wave_phases = [
            GaitPhase.WAVE_1, GaitPhase.WAVE_2, GaitPhase.WAVE_3,
            GaitPhase.WAVE_4, GaitPhase.WAVE_5, GaitPhase.WAVE_6
        ]
        
        swing_sequence = []
        for phase in wave_phases:
            state = wave_gait.get_state(phase)
            swing_sequence.append(state.swing_legs[0])
        
        # Should be sequential: 0, 1, 2, 3, 4, 5
        assert swing_sequence == [0, 1, 2, 3, 4, 5]
    
    def test_all_legs_covered_in_each_phase(self, wave_gait):
        """Test that all 6 legs are covered in each phase."""
        wave_phases = [
            GaitPhase.WAVE_1, GaitPhase.WAVE_2, GaitPhase.WAVE_3,
            GaitPhase.WAVE_4, GaitPhase.WAVE_5, GaitPhase.WAVE_6
        ]
        
        for phase in wave_phases:
            state = wave_gait.get_state(phase)
            
            all_legs = set(state.swing_legs + state.stance_legs)
            assert all_legs == {0, 1, 2, 3, 4, 5}
    
    def test_dwell_time_consistency(self, wave_gait):
        """Test that dwell time is consistent across all phases."""
        wave_phases = [
            GaitPhase.WAVE_1, GaitPhase.WAVE_2, GaitPhase.WAVE_3,
            GaitPhase.WAVE_4, GaitPhase.WAVE_5, GaitPhase.WAVE_6
        ]
        
        for phase in wave_phases:
            state = wave_gait.get_state(phase)
            assert state.dwell_time == wave_gait.dwell_time
    
    def test_inheritance_from_base_gait(self, wave_gait):
        """Test that WaveGait properly inherits from BaseGait."""
        from hexapod.gait_generator.base_gait import BaseGait
        
        assert isinstance(wave_gait, BaseGait)
        assert hasattr(wave_gait, 'step_radius')
        assert hasattr(wave_gait, 'leg_lift_distance')
        assert hasattr(wave_gait, 'stance_height')
        assert hasattr(wave_gait, 'dwell_time')
        assert hasattr(wave_gait, 'use_full_circle_stance')
        assert hasattr(wave_gait, 'direction_input')
        assert hasattr(wave_gait, 'rotation_input')
        assert hasattr(wave_gait, 'leg_mount_angles')
        assert hasattr(wave_gait, 'leg_paths')
    
    def test_gait_graph_completeness(self, wave_gait):
        """Test that gait graph is complete and valid."""
        # All wave phases should have transitions
        assert len(wave_gait.gait_graph) == 6
        
        # Each phase should have exactly one next phase
        for phase, next_phases in wave_gait.gait_graph.items():
            assert len(next_phases) == 1
            assert next_phases[0] in wave_gait.gait_graph
    
    def test_phase_cycle(self, wave_gait):
        """Test that phases form a proper cycle."""
        # Start with WAVE_1
        current_phase = GaitPhase.WAVE_1
        
        # Follow the cycle through all 6 phases
        expected_sequence = [
            GaitPhase.WAVE_1, GaitPhase.WAVE_2, GaitPhase.WAVE_3,
            GaitPhase.WAVE_4, GaitPhase.WAVE_5, GaitPhase.WAVE_6
        ]
        
        for expected_phase in expected_sequence:
            assert current_phase == expected_phase
            current_phase = wave_gait.gait_graph[current_phase][0]
        
        # Should be back to WAVE_1
        assert current_phase == GaitPhase.WAVE_1
    
    def test_state_phase_consistency(self, wave_gait):
        """Test that state phase matches the requested phase."""
        wave_phases = [
            GaitPhase.WAVE_1, GaitPhase.WAVE_2, GaitPhase.WAVE_3,
            GaitPhase.WAVE_4, GaitPhase.WAVE_5, GaitPhase.WAVE_6
        ]
        
        for phase in wave_phases:
            state = wave_gait.get_state(phase)
            assert state.phase == phase
    
    def test_swing_stance_legs_disjoint(self, wave_gait):
        """Test that swing and stance legs are disjoint in each phase."""
        wave_phases = [
            GaitPhase.WAVE_1, GaitPhase.WAVE_2, GaitPhase.WAVE_3,
            GaitPhase.WAVE_4, GaitPhase.WAVE_5, GaitPhase.WAVE_6
        ]
        
        for phase in wave_phases:
            state = wave_gait.get_state(phase)
            
            swing_set = set(state.swing_legs)
            stance_set = set(state.stance_legs)
            
            # Should be disjoint
            assert swing_set.isdisjoint(stance_set)
    
    def test_leg_indices_valid(self, wave_gait):
        """Test that all leg indices are valid (0-5)."""
        wave_phases = [
            GaitPhase.WAVE_1, GaitPhase.WAVE_2, GaitPhase.WAVE_3,
            GaitPhase.WAVE_4, GaitPhase.WAVE_5, GaitPhase.WAVE_6
        ]
        
        for phase in wave_phases:
            state = wave_gait.get_state(phase)
            
            for leg in state.swing_legs + state.stance_legs:
                assert 0 <= leg <= 5
    
    def test_sequential_leg_swing(self, wave_gait):
        """Test that legs swing in sequential order around the hexapod."""
        # This tests the specific wave gait pattern where legs swing
        # in order around the hexapod body
        wave_phases = [
            GaitPhase.WAVE_1, GaitPhase.WAVE_2, GaitPhase.WAVE_3,
            GaitPhase.WAVE_4, GaitPhase.WAVE_5, GaitPhase.WAVE_6
        ]
        
        swing_legs = []
        for phase in wave_phases:
            state = wave_gait.get_state(phase)
            swing_legs.append(state.swing_legs[0])
        
        # Should be sequential: 0, 1, 2, 3, 4, 5
        assert swing_legs == [0, 1, 2, 3, 4, 5]
    
    def test_maximum_stability(self, wave_gait):
        """Test that wave gait maintains maximum stability (5 legs always in stance)."""
        wave_phases = [
            GaitPhase.WAVE_1, GaitPhase.WAVE_2, GaitPhase.WAVE_3,
            GaitPhase.WAVE_4, GaitPhase.WAVE_5, GaitPhase.WAVE_6
        ]
        
        for phase in wave_phases:
            state = wave_gait.get_state(phase)
            
            # Should always have 5 legs in stance for maximum stability
            assert len(state.stance_legs) == 5
            assert len(state.swing_legs) == 1