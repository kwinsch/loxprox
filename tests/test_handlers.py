import pytest
from loxprox.handlers.lights import LightHandler
from loxprox.handlers.power import PowerHandler


class TestLightHandler:
    """Test the light handler."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.handler = LightHandler()
        
    def test_process_rgb_data(self):
        """Test processing RGB light data."""
        data = {
            'device_type': 'ph',
            'device_id': '9',
            'value': {
                'mode': 'rgb',
                'r': 255,
                'g': 128,
                'b': 0
            },
            'timestamp': '2025-07-18 12:03:06',
            'source': 'udplight'
        }
        
        result = self.handler.process(data)
        
        assert result is not None
        assert result['device_type'] == 'ph'
        assert result['device_id'] == '9'
        assert result['value']['r'] == 255
        assert result['value']['g'] == 128
        assert result['value']['b'] == 0
        
    def test_process_cct_data(self):
        """Test processing CCT light data."""
        data = {
            'device_type': 'ph',
            'device_id': '9',
            'value': {
                'mode': 'cct',
                'brightness': 75,
                'kelvin': 4000
            }
        }
        
        result = self.handler.process(data)
        
        assert result is not None
        assert result['value']['brightness'] == 75
        assert result['value']['kelvin'] == 4000
        
    def test_clamp_rgb_values(self):
        """Test RGB value clamping."""
        data = {
            'device_type': 'ph',
            'device_id': '1',
            'value': {
                'mode': 'rgb',
                'r': 300,  # Over max
                'g': -50,  # Under min
                'b': 128
            }
        }
        
        result = self.handler.process(data)
        
        assert result['value']['r'] == 255  # Clamped to max
        assert result['value']['g'] == 0    # Clamped to min
        assert result['value']['b'] == 128  # Unchanged
        
    def test_clamp_cct_values(self):
        """Test CCT value clamping."""
        data = {
            'device_type': 'ph',
            'device_id': '1',
            'value': {
                'mode': 'cct',
                'brightness': 150,  # Over max
                'kelvin': 2000      # Under min
            }
        }
        
        result = self.handler.process(data)
        
        assert result['value']['brightness'] == 100  # Clamped to max
        assert result['value']['kelvin'] == 2700     # Clamped to min
        
    def test_reject_wrong_device_type(self):
        """Test rejection of wrong device type."""
        data = {
            'device_type': 'pm',  # Wrong type
            'device_id': '1',
            'value': {}
        }
        
        result = self.handler.process(data)
        assert result is None
        
    def test_reject_unknown_mode(self):
        """Test rejection of unknown light mode."""
        data = {
            'device_type': 'ph',
            'device_id': '1',
            'value': {
                'mode': 'unknown'
            }
        }
        
        result = self.handler.process(data)
        assert result is None


class TestPowerHandler:
    """Test the power handler."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.handler = PowerHandler()
        
    def test_process_raw_power_data(self):
        """Test processing raw power data."""
        data = {
            'device_type': 'pm',
            'device_id': '1',
            'value': {
                'raw_value': 123456789
            },
            'timestamp': '2025-07-18 12:03:06',
            'source': 'udplight'
        }
        
        result = self.handler.process(data)
        
        assert result is not None
        assert result['device_type'] == 'pm'
        assert result['device_id'] == '1'
        assert result['value']['raw'] == 123456789
        
    def test_process_structured_power_data(self):
        """Test processing structured power data (future JSON format)."""
        data = {
            'device_type': 'pm',
            'device_id': '2',
            'value': {
                'power': 1234.5,
                'voltage': 230.2,
                'current': 5.36
            }
        }
        
        result = self.handler.process(data)
        
        assert result is not None
        assert result['value']['power'] == 1234.5
        assert result['value']['voltage'] == 230.2
        assert result['value']['current'] == 5.36
        
    def test_reject_wrong_device_type(self):
        """Test rejection of wrong device type."""
        data = {
            'device_type': 'ph',  # Wrong type
            'device_id': '1',
            'value': {}
        }
        
        result = self.handler.process(data)
        assert result is None