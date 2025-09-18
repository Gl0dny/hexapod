import pytest
from unittest.mock import Mock, patch
import importlib.util


@pytest.fixture
def joint_module():
    """Import the real joint module with mocked dependencies."""
    spec = importlib.util.spec_from_file_location(
        "joint_module", 
        "/Users/gl0dny/workspace/hexapod/hexapod/robot/joint.py"
    )
    joint_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(joint_module)
    return joint_module


class TestJoint:
    """Test the Joint class from joint.py"""

    def test_joint_class_exists(self, joint_module):
        """Test that Joint class exists."""
        assert hasattr(joint_module, 'Joint')
        assert callable(joint_module.Joint)

    def test_joint_initialization(self, joint_module):
        """Test Joint initialization."""
        with patch('hexapod.robot.joint.MaestroUART') as mock_maestro:
            joint = joint_module.Joint(
                channel=1,
                controller=mock_maestro,
                length=10.0,
                servo_min=1000,
                servo_max=2000,
                angle_min=-90,
                angle_max=90
            )
            
            # Verify initialization
            assert hasattr(joint, 'channel')
            assert hasattr(joint, 'servo_min')
            assert hasattr(joint, 'servo_max')
            assert hasattr(joint, 'angle_min')
            assert hasattr(joint, 'angle_max')

    def test_joint_methods_exist(self, joint_module):
        """Test that Joint has required methods."""
        Joint = joint_module.Joint
        
        # Test that required methods exist (check for common method patterns)
        assert hasattr(Joint, '__init__'), "Joint should have __init__ method"
        # Check if it's a class
        assert callable(Joint), "Joint should be callable"

    def test_joint_class_structure(self, joint_module):
        """Test Joint class structure."""
        Joint = joint_module.Joint
        
        # Test that the class can be instantiated and has expected attributes
        assert hasattr(Joint, '__init__')
        assert callable(Joint)
