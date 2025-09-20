# Hexapod Test Suite

This directory contains the comprehensive test suite for the hexapod voice control system.

## Test Structure

```
tests/
├── conftest.py                    # Shared fixtures and configuration
├── unit/                          # Unit tests
│   ├── test_maestro_uart.py      # Maestro UART communication tests
│   ├── test_hexapod.py           # Hexapod robot logic tests
│   ├── test_gait_generator.py    # Gait algorithm tests
│   ├── test_voice_control.py     # Voice recognition tests
│   ├── test_odas_processor.py    # ODAS audio processing tests
│   └── test_lights.py            # LED system tests
├── integration/                   # Integration tests
│   ├── test_robot_movement.py    # Full movement system tests
│   └── test_voice_commands.py    # Voice command integration tests
├── fixtures/                      # Test data and mock objects
│   ├── mock_audio_data.py        # Audio test data generators
│   └── test_configs.py           # Test configuration data
└── reports/                       # Test reports (generated)
    ├── html/                      # HTML coverage reports
    ├── xml/                       # XML coverage reports
    └── json/                      # JSON coverage reports
```

## Running Tests

### Prerequisites
```bash
# Install development dependencies
pip install -e ".[dev]"
```

### Basic Test Commands
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=hexapod

# Run specific test file
pytest tests/unit/test_maestro_uart.py

# Run with verbose output
pytest -v

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run tests with specific markers
pytest -m "not hardware"  # Skip hardware-dependent tests
pytest -m "slow"          # Run only slow tests
```

### Coverage Reports
```bash
# Generate HTML coverage report
pytest --cov=hexapod --cov-report=html

# Generate XML coverage report (for CI/CD)
pytest --cov=hexapod --cov-report=xml

# Generate JSON coverage report
pytest --cov=hexapod --cov-report=json
```

## Test Categories

### Unit Tests
- **Hardware Abstraction**: Mock hardware interfaces (Maestro, GPIO, I2C)
- **Mathematical Functions**: Test kinematics, gait calculations
- **Data Processing**: Test audio processing, ODAS algorithms
- **Error Handling**: Test failure scenarios and recovery

### Integration Tests
- **End-to-End Workflows**: Complete command-to-action flows
- **System Interactions**: Component communication and coordination
- **Performance**: Real-time constraints and timing

### Test Markers
- `@pytest.mark.hardware`: Tests requiring physical hardware
- `@pytest.mark.slow`: Tests that take longer to run
- `@pytest.mark.integration`: Integration tests

## Fixtures

The test suite includes comprehensive fixtures for:
- **Hardware Mocking**: Serial, GPIO, I2C, Audio interfaces
- **Test Data**: Sample audio, IMU, ODAS data
- **Configuration**: Test-specific configurations
- **Mock Objects**: Picovoice, ODAS, Maestro mocks

## Writing Tests

### Test Naming Convention
- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`

### Example Test Structure
```python
def test_function_name_valid_input(self, fixture_name):
    """Test description of what this test validates."""
    # Arrange
    input_data = fixture_name
    
    # Act
    result = function_under_test(input_data)
    
    # Assert
    assert result == expected_value
```

### Mocking Hardware
```python
def test_hardware_function(self, mock_serial):
    """Test hardware function with mocked serial connection."""
    mock_serial.write.return_value = 10
    result = hardware_function(mock_serial)
    assert result == expected_value
```

## Continuous Integration

The test suite is configured for CI/CD with:
- Coverage reporting
- XML output for CI systems
- Hardware test exclusion
- Performance monitoring

## Debugging Tests

### Verbose Output
```bash
pytest -v -s  # Verbose with print statements
```

### Debug Specific Test
```bash
pytest tests/unit/test_maestro_uart.py::TestMaestroUART::test_connect_success -v -s
```

### Coverage Debugging
```bash
pytest --cov=hexapod --cov-report=html --cov-report=term-missing
```

## Best Practices

1. **Isolation**: Each test should be independent
2. **Mocking**: Mock external dependencies and hardware
3. **Data**: Use fixtures for consistent test data
4. **Assertions**: Clear, specific assertions
5. **Documentation**: Descriptive test names and docstrings
6. **Coverage**: Aim for high test coverage
7. **Performance**: Keep tests fast and efficient
