import pytest
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/')))
from robot.joint import Joint

@pytest.fixture
def joint_fixture(mocker):
    mock_controller = mocker.Mock()
    return Joint(
        controller=mock_controller,
        length=10.0,
        channel=1,
        angle_min=-45.0,
        angle_max=45.0
    )

def test_set_angle_within_limits(joint_fixture):
    joint_fixture.set_angle(0)
    joint_fixture.controller.set_speed.assert_called_with(joint_fixture.channel, Joint.DEFAULT_SPEED)
    joint_fixture.controller.set_acceleration.assert_called_with(joint_fixture.channel, Joint.DEFAULT_ACCEL)
    joint_fixture.controller.set_target.assert_called()

def test_set_angle_below_min(joint_fixture):
    with pytest.raises(ValueError) as excinfo:
        joint_fixture.set_angle(-50)
    assert "out of limits" in str(excinfo.value)

def test_set_angle_above_max(joint_fixture):
    with pytest.raises(ValueError) as excinfo:
        joint_fixture.set_angle(50)
    assert "out of limits" in str(excinfo.value)

def test_angle_to_servo_target(joint_fixture):
    target = joint_fixture.angle_to_servo_target(0)
    expected = int(joint_fixture.servo_min + (joint_fixture.servo_max - joint_fixture.servo_min) * ((0 - joint_fixture.angle_min) / (joint_fixture.angle_max - joint_fixture.angle_min)))
    assert target == expected
