# Hexapod Gait Trajectories

This document explains the trajectory calculations used in the hexapod's gait generation system.

## Overview

The hexapod uses two types of trajectories for leg movement:
1. Swing Trajectory - For legs in the air
2. Stance Trajectory - For legs on the ground

## Trajectory Types

### Swing Trajectory

The swing trajectory is used when a leg is moving through the air (not in contact with the ground). It creates a smooth, arc-like movement that:
- Lifts the leg to clear obstacles
- Moves it forward to the next position
- Lowers it gently to the ground

#### Implementation
```python
def calculate_swing_trajectory(self, start_pos, end_pos, progress):
    # Smooth acceleration/deceleration
    eased_progress = self.ease_in_out_quad(progress)
    
    # Linear movement in X and Y
    x = start_pos[0] + eased_progress * (end_pos[0] - start_pos[0])
    y = start_pos[1] + eased_progress * (end_pos[1] - start_pos[1])
    
    # Parabolic height profile
    if progress < 1.0:
        height_factor = 4 * eased_progress * (1 - eased_progress)
        z = start_pos[2] + height_factor * self.swing_height
    else:
        z = end_pos[2]
```

#### Height Profile
```
Height
  ^
  |    * (peak)
  |   / \
  |  /   \
  | /     \
  |/       \
  |         * (target)
  +----------------> Progress
```

### Stance Trajectory

The stance trajectory is used when a leg is in contact with the ground. It creates a straight-line movement that:
- Maintains stability
- Provides predictable ground contact
- Enables smooth weight transfer

#### Implementation
```python
def calculate_stance_trajectory(self, start_pos, end_pos, progress):
    # Smooth acceleration/deceleration
    eased_progress = self.ease_in_out_quad(progress)
    
    # Linear interpolation for all coordinates
    x = start_pos[0] + eased_progress * (end_pos[0] - start_pos[0])
    y = start_pos[1] + eased_progress * (end_pos[1] - start_pos[1])
    z = start_pos[2] + eased_progress * (end_pos[2] - start_pos[2])
```

#### Height Profile
```
Height
  ^
  |    *
  |   /
  |  /
  | /
  |/
  |         *
  +----------------> Progress
```

## Easing Function

Both trajectories use an easing function to create smooth acceleration and deceleration:

```python
def ease_in_out_quad(self, t: float) -> float:
    """Quadratic easing function for smooth acceleration and deceleration."""
    return 2 * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 2) / 2
```

This creates a movement profile that:
- Starts slow (acceleration)
- Moves faster in the middle
- Ends slow (deceleration)

## Key Differences

| Feature | Swing Trajectory | Stance Trajectory |
|---------|-----------------|------------------|
| Purpose | Air movement | Ground movement |
| Path | Arc-like | Straight line |
| Height | Parabolic | Linear |
| Use case | Stepping | Weight bearing |

## Parameters

Both trajectories can be configured with:
- `swing_distance`: How far forward the leg moves during swing
- `swing_height`: Maximum height of the swing arc
- `stance_distance`: How far back the leg moves during stance
- `transition_steps`: Number of steps for smooth movement

## Testing

You can test the trajectories using the `test_leg_trajectory.py` script:
```bash
python src/scripts/test_leg_trajectory.py
```

This will demonstrate:
1. Linear movement (direct, straight lines)
2. Curved movement (smooth, parabolic paths)

## Best Practices

1. **Swing Phase**:
   - Use higher swing height for rough terrain
   - Adjust swing distance based on desired speed
   - Ensure smooth transitions at start and end

2. **Stance Phase**:
   - Keep movements small for stability
   - Maintain consistent ground contact
   - Coordinate with other legs for balance

## Future Improvements

Potential enhancements to consider:
1. Dynamic height adjustment based on terrain
2. Variable swing distances for turning
3. Adaptive transition speeds
4. More sophisticated easing functions
5. Support for different gait patterns 