import pytest
from loxprox.inputs.parser import InputParser


class TestInputParser:
    """Test the input parser module."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = InputParser()
        
    def test_parse_legacy_rgb_packet(self):
        """Test parsing legacy RGB light packet."""
        packet = "2025-07-18 12:03:06;udplight;ph9.100050025"
        result = self.parser.parse_packet(packet)
        
        assert result is not None
        assert result['device_type'] == 'ph'
        assert result['device_id'] == '9'
        assert result['timestamp'] == '2025-07-18 12:03:06'
        assert result['source'] == 'udplight'
        assert result['value']['mode'] == 'rgb'
        assert result['value']['r'] == 63  # 25 * 255 / 100
        assert result['value']['g'] == 127  # 50 * 255 / 100
        assert result['value']['b'] == 255  # 100 * 255 / 100
        
    def test_parse_legacy_cct_packet(self):
        """Test parsing legacy CCT light packet."""
        packet = "2025-07-18 12:03:06;udplight;ph9.201003000"
        result = self.parser.parse_packet(packet)
        
        assert result is not None
        assert result['device_type'] == 'ph'
        assert result['device_id'] == '9'
        assert result['value']['mode'] == 'cct'
        assert result['value']['brightness'] == 100
        assert result['value']['kelvin'] == 3000
        
    def test_parse_power_meter_packet(self):
        """Test parsing power meter packet."""
        packet = "2025-07-18 12:03:06;udplight;pm1.123456789"
        result = self.parser.parse_packet(packet)
        
        assert result is not None
        assert result['device_type'] == 'pm'
        assert result['device_id'] == '1'
        assert result['value']['raw_value'] == 123456789
        
    def test_parse_invalid_packet_format(self):
        """Test parsing invalid packet formats."""
        # Not enough parts
        assert self.parser.parse_packet("invalid") is None
        assert self.parser.parse_packet("2025-07-18;only-two") is None
        
        # Invalid device format
        assert self.parser.parse_packet("2025-07-18 12:03:06;udplight;invalid.123") is None
        assert self.parser.parse_packet("2025-07-18 12:03:06;udplight;123.456") is None
        
        # Invalid payload
        assert self.parser.parse_packet("2025-07-18 12:03:06;udplight;ph9.notanumber") is None
        
    def test_parse_json_packet(self):
        """Test parsing future JSON format."""
        packet = '2025-07-18 12:03:06;udplight;{"type":"ph","id":9,"value":{"mode":"rgb","r":255,"g":0,"b":0}}'
        result = self.parser.parse_packet(packet)
        
        assert result is not None
        assert result['device_type'] == 'ph'
        assert result['device_id'] == '9'
        assert result['value']['mode'] == 'rgb'
        assert result['value']['r'] == 255
        assert result['value']['g'] == 0
        assert result['value']['b'] == 0
        
    def test_device_pattern_matching(self):
        """Test device pattern regex."""
        # Valid patterns
        assert self.parser.device_pattern.match('ph9') is not None
        assert self.parser.device_pattern.match('pm123') is not None
        assert self.parser.device_pattern.match('xx0') is not None
        
        # Invalid patterns
        assert self.parser.device_pattern.match('PH9') is None  # uppercase
        assert self.parser.device_pattern.match('ph') is None  # no number
        assert self.parser.device_pattern.match('9ph') is None  # wrong order
        assert self.parser.device_pattern.match('ph9a') is None  # extra chars