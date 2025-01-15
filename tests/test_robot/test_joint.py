import pytest

from robot import Joint

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

class TestJoint:
    def test_set_angle_within_limits(self, joint_fixture):
        joint_fixture.set_angle(0)
        joint_fixture.controller.set_speed.assert_called_with(joint_fixture.channel, Joint.DEFAULT_SPEED)
        joint_fixture.controller.set_acceleration.assert_called_with(joint_fixture.channel, Joint.DEFAULT_ACCEL)
        joint_fixture.controller.set_target.assert_called()

    def test_set_angle_below_min(self, joint_fixture):
        with pytest.raises(ValueError) as excinfo:
            joint_fixture.set_angle(-50)
        assert "out of bounds" in str(excinfo.value)

    def test_set_angle_above_max(self, joint_fixture):
        with pytest.raises(ValueError) as excinfo:
            joint_fixture.set_angle(50)
        assert "out of bounds" in str(excinfo.value)

    def test_angle_to_servo_target(self, joint_fixture):
        target = joint_fixture.angle_to_servo_target(0)
        expected = int(joint_fixture.servo_min + (joint_fixture.servo_max - joint_fixture.servo_min) * ((0 - joint_fixture.angle_min) / (joint_fixture.angle_max - joint_fixture.angle_min)))
        assert target == expected
