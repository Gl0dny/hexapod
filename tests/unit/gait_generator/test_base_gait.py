"""
Unit tests for base gait system.
"""

import pytest
import math
import logging
from unittest.mock import Mock, patch, MagicMock
from hexapod.gait_generator.base_gait import BaseGait, GaitPhase, GaitState
from hexapod.utils import Vector2D, Vector3D


class TestGaitPhase:
    """Test cases for GaitPhase enum."""

    def test_gait_phase_values(self):
        """Test GaitPhase enum values."""
        assert GaitPhase.TRIPOD_A is not None
        assert GaitPhase.TRIPOD_B is not None
        assert GaitPhase.WAVE_1 is not None
        assert GaitPhase.WAVE_2 is not None
        assert GaitPhase.WAVE_3 is not None
        assert GaitPhase.WAVE_4 is not None
        assert GaitPhase.WAVE_5 is not None
        assert GaitPhase.WAVE_6 is not None

    def test_gait_phase_enumeration(self):
        """Test that all gait phases can be enumerated."""
        phases = list(GaitPhase)
        assert len(phases) == 8
        assert GaitPhase.TRIPOD_A in phases
        assert GaitPhase.TRIPOD_B in phases
        assert GaitPhase.WAVE_1 in phases
        assert GaitPhase.WAVE_2 in phases
        assert GaitPhase.WAVE_3 in phases
        assert GaitPhase.WAVE_4 in phases
        assert GaitPhase.WAVE_5 in phases
        assert GaitPhase.WAVE_6 in phases


class TestGaitState:
    """Test cases for GaitState dataclass."""

    def test_gait_state_creation(self):
        """Test GaitState creation with valid parameters."""
        state = GaitState(
            phase=GaitPhase.TRIPOD_A,
            swing_legs=[0, 2, 4],
            stance_legs=[1, 3, 5],
            dwell_time=0.5,
        )

        assert state.phase == GaitPhase.TRIPOD_A
        assert state.swing_legs == [0, 2, 4]
        assert state.stance_legs == [1, 3, 5]
        assert state.dwell_time == 0.5

    def test_gait_state_empty_legs(self):
        """Test GaitState creation with empty leg lists."""
        state = GaitState(
            phase=GaitPhase.WAVE_1, swing_legs=[], stance_legs=[], dwell_time=1.0
        )

        assert state.swing_legs == []
        assert state.stance_legs == []
        assert state.dwell_time == 1.0


class TestBaseGaitLegPath:
    """Test cases for BaseGait.LegPath class."""

    def test_leg_path_creation(self):
        """Test LegPath creation."""
        waypoints = [Vector3D(0, 0, 0), Vector3D(10, 10, 10)]
        path = BaseGait.LegPath(waypoints)

        assert path.waypoints == waypoints
        assert path.current_waypoint_index == 0

    def test_leg_path_creation_empty(self):
        """Test LegPath creation with empty waypoints."""
        path = BaseGait.LegPath([])

        assert path.waypoints == []
        assert path.current_waypoint_index == 0

    def test_add_waypoint(self):
        """Test adding waypoints to LegPath."""
        path = BaseGait.LegPath([])
        waypoint = Vector3D(5, 5, 5)

        path.add_waypoint(waypoint)

        assert len(path.waypoints) == 1
        assert path.waypoints[0] == waypoint

    def test_get_current_target_with_waypoints(self):
        """Test getting current target when waypoints exist."""
        waypoints = [Vector3D(0, 0, 0), Vector3D(10, 10, 10), Vector3D(20, 20, 20)]
        path = BaseGait.LegPath(waypoints)

        assert path.get_current_target() == Vector3D(0, 0, 0)

        path.current_waypoint_index = 1
        assert path.get_current_target() == Vector3D(10, 10, 10)

    def test_get_current_target_empty(self):
        """Test getting current target when no waypoints exist."""
        path = BaseGait.LegPath([])

        assert path.get_current_target() == Vector3D(0, 0, 0)

    def test_advance_to_next_waypoint_success(self):
        """Test advancing to next waypoint when more waypoints exist."""
        waypoints = [Vector3D(0, 0, 0), Vector3D(10, 10, 10), Vector3D(20, 20, 20)]
        path = BaseGait.LegPath(waypoints)

        assert path.current_waypoint_index == 0
        assert path.advance_to_next_waypoint() is True
        assert path.current_waypoint_index == 1
        assert path.advance_to_next_waypoint() is True
        assert path.current_waypoint_index == 2

    def test_advance_to_next_waypoint_end(self):
        """Test advancing to next waypoint when at the end."""
        waypoints = [Vector3D(0, 0, 0), Vector3D(10, 10, 10)]
        path = BaseGait.LegPath(waypoints)
        path.current_waypoint_index = 1

        assert path.advance_to_next_waypoint() is False
        assert path.current_waypoint_index == 1  # Should not change

    def test_reset(self):
        """Test resetting LegPath to start."""
        waypoints = [Vector3D(0, 0, 0), Vector3D(10, 10, 10), Vector3D(20, 20, 20)]
        path = BaseGait.LegPath(waypoints)
        path.current_waypoint_index = 2

        path.reset()

        assert path.current_waypoint_index == 0


class TestBaseGait:
    """Test cases for BaseGait class."""

    @pytest.fixture
    def mock_hexapod(self):
        """Mock hexapod for testing."""
        hexapod = MagicMock()
        hexapod.current_leg_positions = [
            [0, 0, 0],
            [10, 10, 0],
            [20, 20, 0],
            [30, 30, 0],
            [40, 40, 0],
            [50, 50, 0],
        ]
        return hexapod

    @pytest.fixture
    def concrete_gait(self, mock_hexapod):
        """Create a concrete implementation of BaseGait for testing."""

        class ConcreteGait(BaseGait):
            def _setup_gait_graph(self):
                self.gait_graph[GaitPhase.TRIPOD_A] = [GaitPhase.TRIPOD_B]
                self.gait_graph[GaitPhase.TRIPOD_B] = [GaitPhase.TRIPOD_A]

            def get_state(self, phase: GaitPhase) -> GaitState:
                if phase == GaitPhase.TRIPOD_A:
                    return GaitState(
                        phase=phase,
                        swing_legs=[0, 2, 4],
                        stance_legs=[1, 3, 5],
                        dwell_time=self.dwell_time,
                    )
                else:
                    return GaitState(
                        phase=phase,
                        swing_legs=[1, 3, 5],
                        stance_legs=[0, 2, 4],
                        dwell_time=self.dwell_time,
                    )

        return ConcreteGait(mock_hexapod)

    def test_init_default_parameters(self, mock_hexapod):
        """Test BaseGait initialization with default parameters."""
        gait = ConcreteGait(mock_hexapod)

        assert gait.hexapod == mock_hexapod
        assert gait.step_radius == 30.0
        assert gait.leg_lift_distance == 10.0
        assert gait.stance_height == 0.0
        assert gait.dwell_time == 0.5
        assert gait.use_full_circle_stance is False
        assert gait.direction_input == Vector2D(0, 0)
        assert gait.rotation_input == 0.0
        assert len(gait.leg_mount_angles) == 6
        assert gait.leg_mount_angles == [0, 60, 120, 180, 240, 300]
        assert len(gait.leg_paths) == 6
        assert all(isinstance(path, BaseGait.LegPath) for path in gait.leg_paths)

    def test_init_custom_parameters(self, mock_hexapod):
        """Test BaseGait initialization with custom parameters."""
        gait = ConcreteGait(
            mock_hexapod,
            step_radius=50.0,
            leg_lift_distance=20.0,
            stance_height=5.0,
            dwell_time=1.0,
            use_full_circle_stance=True,
        )

        assert gait.step_radius == 50.0
        assert gait.leg_lift_distance == 20.0
        assert gait.stance_height == 5.0
        assert gait.dwell_time == 1.0
        assert gait.use_full_circle_stance is True

    def test_direction_map(self, concrete_gait):
        """Test direction mapping constants."""
        direction_map = concrete_gait.DIRECTION_MAP

        # Test cardinal directions
        assert direction_map["forward"] == (0.0, 1.0)
        assert direction_map["backward"] == (0.0, -1.0)
        assert direction_map["right"] == (1.0, 0.0)
        assert direction_map["left"] == (-1.0, 0.0)

        # Test diagonal directions
        assert direction_map["forward right"] == (0.707, 0.707)
        assert direction_map["forward left"] == (-0.707, 0.707)
        assert direction_map["backward right"] == (0.707, -0.707)
        assert direction_map["backward left"] == (-0.707, -0.707)

        # Test neutral
        assert direction_map["neutral"] == (0.0, 0.0)

    def test_project_point_to_circle_zero_direction(self, concrete_gait):
        """Test circle projection with zero direction vector."""
        point = Vector2D(10, 10)
        direction = Vector2D(0, 0)

        result = concrete_gait.project_point_to_circle(50.0, point, direction)

        assert result == point  # Should return original point

    def test_project_point_to_circle_origin_point(self, concrete_gait):
        """Test circle projection from origin."""
        point = Vector2D(0, 0)
        direction = Vector2D(1, 0)

        result = concrete_gait.project_point_to_circle(50.0, point, direction)

        expected = direction.normalized() * 50.0
        assert result.x == pytest.approx(expected.x, abs=1e-6)
        assert result.y == pytest.approx(expected.y, abs=1e-6)

    def test_project_point_to_circle_collinear(self, concrete_gait):
        """Test circle projection with collinear point and direction."""
        point = Vector2D(10, 0)
        direction = Vector2D(1, 0)

        result = concrete_gait.project_point_to_circle(50.0, point, direction)

        expected = direction.normalized() * 50.0
        assert result.x == pytest.approx(expected.x, abs=1e-6)
        assert result.y == pytest.approx(expected.y, abs=1e-6)

    def test_project_point_to_circle_large_direction(self, concrete_gait):
        """Test circle projection with direction larger than radius."""
        point = Vector2D(10, 10)
        direction = Vector2D(100, 0)  # Larger than radius

        result = concrete_gait.project_point_to_circle(50.0, point, direction)

        # Should be clamped to boundary
        assert result.magnitude() <= 50.0

    def test_project_point_to_circle_normal_case(self, concrete_gait):
        """Test circle projection with normal case."""
        point = Vector2D(10, 10)
        direction = Vector2D(1, 1)

        result = concrete_gait.project_point_to_circle(50.0, point, direction)

        # Result should be on circle boundary
        assert abs(result.magnitude() - 50.0) < 1e-6

    def test_calculate_leg_target_no_movement_swing(self, concrete_gait):
        """Test leg target calculation with no movement input for swing leg."""
        concrete_gait.direction_input = Vector2D(0, 0)
        concrete_gait.rotation_input = 0.0

        result = concrete_gait.calculate_leg_target(0, True)

        # Should return current position with stance height
        assert result.z == -concrete_gait.stance_height

    def test_calculate_leg_target_no_movement_stance(self, concrete_gait):
        """Test leg target calculation with no movement input for stance leg."""
        concrete_gait.direction_input = Vector2D(0, 0)
        concrete_gait.rotation_input = 0.0

        result = concrete_gait.calculate_leg_target(0, False)

        # Should return current position with stance height
        current_pos = Vector3D(*concrete_gait.hexapod.current_leg_positions[0])
        current_pos.z = -concrete_gait.stance_height
        assert result == current_pos

    def test_calculate_leg_target_rotation_swing(self, concrete_gait):
        """Test leg target calculation for rotation movement with swing leg."""
        concrete_gait.direction_input = Vector2D(0, 0)
        concrete_gait.rotation_input = 0.5

        result = concrete_gait.calculate_leg_target(0, True)

        # Should have movement in rotation direction
        assert result.z == -concrete_gait.stance_height

    def test_calculate_leg_target_translation_swing(self, concrete_gait):
        """Test leg target calculation for translation movement with swing leg."""
        concrete_gait.direction_input = Vector2D(1, 0)  # Forward
        concrete_gait.rotation_input = 0.0

        result = concrete_gait.calculate_leg_target(0, True)

        # Should have movement in projected direction
        assert result.z == -concrete_gait.stance_height

    def test_calculate_leg_path_swing_marching_in_place(self, concrete_gait):
        """Test leg path calculation for swing leg marching in place."""
        concrete_gait.direction_input = Vector2D(0, 0)
        concrete_gait.rotation_input = 0.0

        target = Vector3D(0, 0, -concrete_gait.stance_height)
        concrete_gait.calculate_leg_path(0, target, True)

        path = concrete_gait.leg_paths[0]
        assert len(path.waypoints) == 3  # Start, lift, lower
        assert path.waypoints[0].z == 0  # Start at current height
        assert path.waypoints[1].z == concrete_gait.leg_lift_distance  # Lift up
        assert path.waypoints[2].z == -concrete_gait.stance_height  # Lower to target

    def test_calculate_leg_path_swing_with_movement(self, concrete_gait):
        """Test leg path calculation for swing leg with movement."""
        concrete_gait.direction_input = Vector2D(1, 0)  # Forward
        concrete_gait.rotation_input = 0.0

        target = Vector3D(30, 0, -concrete_gait.stance_height)
        concrete_gait.calculate_leg_path(0, target, True)

        path = concrete_gait.leg_paths[0]
        assert len(path.waypoints) == 3  # Start, lift+move, lower
        assert path.waypoints[0].z == 0  # Start at current height
        assert (
            path.waypoints[1].z == target.z + concrete_gait.leg_lift_distance
        )  # Lift and move
        assert path.waypoints[2] == target  # Final target

    def test_calculate_leg_path_stance(self, concrete_gait):
        """Test leg path calculation for stance leg."""
        target = Vector3D(30, 0, -concrete_gait.stance_height)
        concrete_gait.calculate_leg_path(0, target, False)

        path = concrete_gait.leg_paths[0]
        assert len(path.waypoints) == 2  # Start, target
        assert path.waypoints[0].z == 0  # Start at current height
        assert path.waypoints[1] == target  # Final target

    def test_set_direction_string(self, concrete_gait):
        """Test setting direction using string."""
        concrete_gait.set_direction("forward", 0.5)

        assert concrete_gait.direction_input == Vector2D(0.0, 1.0)
        assert concrete_gait.rotation_input == 0.5

    def test_set_direction_tuple(self, concrete_gait):
        """Test setting direction using tuple."""
        concrete_gait.set_direction((0.5, 0.5), -0.3)

        assert concrete_gait.direction_input == Vector2D(0.5, 0.5)
        assert concrete_gait.rotation_input == -0.3

    def test_set_direction_invalid_string(self, concrete_gait):
        """Test setting direction with invalid string."""
        with pytest.raises(ValueError, match="Unknown direction"):
            concrete_gait.set_direction("invalid", 0.0)

    def test_set_direction_invalid_type(self, concrete_gait):
        """Test setting direction with invalid type."""
        with pytest.raises(TypeError, match="Direction must be string or tuple"):
            concrete_gait.set_direction(123, 0.0)

    def test_set_direction_all_strings(self, concrete_gait):
        """Test all valid direction strings."""
        directions = [
            "forward",
            "backward",
            "left",
            "right",
            "forward right",
            "forward left",
            "backward right",
            "backward left",
            "neutral",
        ]

        for direction in directions:
            concrete_gait.set_direction(direction, 0.0)
            assert concrete_gait.direction_input is not None
            assert concrete_gait.rotation_input == 0.0

    def test_project_point_to_circle_collinear_warning(self, concrete_gait, caplog):
        """Test project_point_to_circle with collinear point and direction (triggers warning)."""
        point = Vector2D(10, 0)
        direction = Vector2D(1, 0)  # Same direction as point

        with caplog.at_level(logging.WARNING):
            result = concrete_gait.project_point_to_circle(50.0, point, direction)

        # Should return normalized direction * radius
        expected = direction.normalized() * 50.0
        assert result.x == pytest.approx(expected.x, abs=1e-6)
        assert result.y == pytest.approx(expected.y, abs=1e-6)

    def test_project_point_to_circle_collinear_180_degrees(self, concrete_gait, caplog):
        """Test project_point_to_circle with point and direction at 180 degrees (triggers warning)."""
        point = Vector2D(10, 0)
        direction = Vector2D(-1, 0)  # Opposite direction

        with caplog.at_level(logging.WARNING):
            result = concrete_gait.project_point_to_circle(50.0, point, direction)

        # Should return normalized direction * radius
        expected = direction.normalized() * 50.0
        assert result.x == pytest.approx(expected.x, abs=1e-6)
        assert result.y == pytest.approx(expected.y, abs=1e-6)

    def test_calculate_leg_target_rotation_counterclockwise(self, concrete_gait):
        """Test leg target calculation for counterclockwise rotation."""
        concrete_gait.direction_input = Vector2D(0, 0)
        concrete_gait.rotation_input = -0.5  # Counterclockwise

        result = concrete_gait.calculate_leg_target(0, True)

        # Should have movement in counterclockwise direction
        assert result.z == -concrete_gait.stance_height

    def test_calculate_leg_target_rotation_stance_full_circle(self, concrete_gait):
        """Test leg target calculation for rotation with stance leg and full circle."""
        concrete_gait.use_full_circle_stance = True
        concrete_gait.direction_input = Vector2D(0, 0)
        concrete_gait.rotation_input = 0.5

        result = concrete_gait.calculate_leg_target(0, False)

        # Should have movement in rotation direction
        assert result.z == -concrete_gait.stance_height

    def test_calculate_leg_target_rotation_stance_half_circle(self, concrete_gait):
        """Test leg target calculation for rotation with stance leg and half circle."""
        concrete_gait.use_full_circle_stance = False
        concrete_gait.direction_input = Vector2D(0, 0)
        concrete_gait.rotation_input = 0.5

        result = concrete_gait.calculate_leg_target(0, False)

        # Should move back to center
        assert result.z == -concrete_gait.stance_height

    def test_calculate_leg_target_translation_stance_full_circle(self, concrete_gait):
        """Test leg target calculation for translation with stance leg and full circle."""
        concrete_gait.use_full_circle_stance = True
        concrete_gait.direction_input = Vector2D(1, 0)  # Forward
        concrete_gait.rotation_input = 0.0

        result = concrete_gait.calculate_leg_target(0, False)

        # Should have movement in projected direction
        assert result.z == -concrete_gait.stance_height

    def test_calculate_leg_target_translation_stance_half_circle(self, concrete_gait):
        """Test leg target calculation for translation with stance leg and half circle."""
        concrete_gait.use_full_circle_stance = False
        concrete_gait.direction_input = Vector2D(1, 0)  # Forward
        concrete_gait.rotation_input = 0.0

        result = concrete_gait.calculate_leg_target(0, False)

        # Should move back to center
        assert result.z == -concrete_gait.stance_height

    def test_calculate_leg_target_translation_swing_with_movement(self, concrete_gait):
        """Test leg target calculation for translation with swing leg and movement."""
        concrete_gait.direction_input = Vector2D(1, 0)  # Forward
        concrete_gait.rotation_input = 0.0

        result = concrete_gait.calculate_leg_target(0, True)

        # Should have movement in projected direction
        assert result.z == -concrete_gait.stance_height

    def test_calculate_leg_target_translation_stance_full_circle_with_movement(
        self, concrete_gait
    ):
        """Test leg target calculation for translation with stance leg, full circle, and movement."""
        concrete_gait.use_full_circle_stance = True
        concrete_gait.direction_input = Vector2D(1, 0)  # Forward
        concrete_gait.rotation_input = 0.0

        result = concrete_gait.calculate_leg_target(0, False)

        # Should have movement in projected direction
        assert result.z == -concrete_gait.stance_height

    def test_calculate_leg_target_translation_stance_half_circle_with_movement(
        self, concrete_gait
    ):
        """Test leg target calculation for translation with stance leg, half circle, and movement."""
        concrete_gait.use_full_circle_stance = False
        concrete_gait.direction_input = Vector2D(1, 0)  # Forward
        concrete_gait.rotation_input = 0.0

        result = concrete_gait.calculate_leg_target(0, False)

        # Should move back to center
        assert result.z == -concrete_gait.stance_height

    def test_calculate_leg_target_no_movement_swing_stay_position(self, concrete_gait):
        """Test leg target calculation with no movement for swing leg."""
        concrete_gait.direction_input = Vector2D(0, 0)
        concrete_gait.rotation_input = 0.0

        result = concrete_gait.calculate_leg_target(0, True)

        # Should stay at current position
        assert result.x == 0.0
        assert result.y == 0.0
        assert result.z == -concrete_gait.stance_height

    def test_calculate_leg_target_no_movement_stance_stay_position(self, concrete_gait):
        """Test leg target calculation with no movement for stance leg."""
        concrete_gait.direction_input = Vector2D(0, 0)
        concrete_gait.rotation_input = 0.0

        result = concrete_gait.calculate_leg_target(0, False)

        # Should stay at current position
        current_pos = Vector3D(*concrete_gait.hexapod.current_leg_positions[0])
        current_pos.z = -concrete_gait.stance_height
        assert result == current_pos

    def test_calculate_leg_target_no_movement_translation_swing(self, concrete_gait):
        """Test leg target calculation with no movement for translation swing leg."""
        concrete_gait.direction_input = Vector2D(0, 0)  # No direction input
        concrete_gait.rotation_input = 0.0

        result = concrete_gait.calculate_leg_target(0, True)

        # Should stay at current position
        assert result.x == 0.0
        assert result.y == 0.0
        assert result.z == -concrete_gait.stance_height

    def test_calculate_leg_target_no_movement_translation_stance(self, concrete_gait):
        """Test leg target calculation with no movement for translation stance leg."""
        concrete_gait.direction_input = Vector2D(0, 0)  # No direction input
        concrete_gait.rotation_input = 0.0

        result = concrete_gait.calculate_leg_target(0, False)

        # Should stay at current position
        current_pos = Vector3D(*concrete_gait.hexapod.current_leg_positions[0])
        current_pos.z = -concrete_gait.stance_height
        assert result == current_pos


# Create concrete implementation for testing
class ConcreteGait(BaseGait):
    """Concrete implementation of BaseGait for testing."""

    def _setup_gait_graph(self):
        self.gait_graph[GaitPhase.TRIPOD_A] = [GaitPhase.TRIPOD_B]
        self.gait_graph[GaitPhase.TRIPOD_B] = [GaitPhase.TRIPOD_A]

    def get_state(self, phase: GaitPhase) -> GaitState:
        if phase == GaitPhase.TRIPOD_A:
            return GaitState(
                phase=phase,
                swing_legs=[0, 2, 4],
                stance_legs=[1, 3, 5],
                dwell_time=self.dwell_time,
            )
        else:
            return GaitState(
                phase=phase,
                swing_legs=[1, 3, 5],
                stance_legs=[0, 2, 4],
                dwell_time=self.dwell_time,
            )
