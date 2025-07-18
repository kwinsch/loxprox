# loxprox

A modular UDP proxy that receives data from Loxone home automation systems and routes it to multiple outputs including Philips Hue lights and monitoring systems.

## Features

- **Multiple Output Support**: Send data to Philips Hue, Telegraf/InfluxDB, and more
- **Device Type Routing**: Route different device types to different outputs
- **Extensible Architecture**: Easy to add new device types and outputs
- **Backward Compatible**: Supports existing Loxone UDP packet formats
- **Future Ready**: Prepared for JSON packet formats and new device types

## Supported Device Types

- **ph**: Philips Hue lights (RGB and CCT modes)
- **pm**: Power meters (format TBD)

## Packet Format

Loxprox receives UDP packets in the format:
```
timestamp;source;data
```

Example: `2025-07-18 12:03:06;udplight;ph9.201003000`

### Data Formats

#### RGB Lights (ph devices, values 0-100100100)
Format: `phN.BBBGGGRRR` where:
- N = device ID
- BBB = Blue (0-100)
- GGG = Green (0-100) 
- RRR = Red (0-100)

Example: `ph9.100050025` = Device 9, 100% blue, 50% green, 25% red

#### CCT Lights (ph devices, values 200002700-201006500)
Format: `phN.2BBBTTTT` where:
- N = device ID
- 2 = CCT mode prefix
- BBB = Brightness (0-100)
- TTTT = Color temperature in Kelvin (2700-6500)

Example: `ph9.201003000` = Device 9, 100% brightness, 3000K

## Configuration

### New Format (Recommended)
```yaml
inputs:
  udp:
    ip: "0.0.0.0"
    ports:
      - 52001

outputs:
  hue:
    enabled: true
    bridge_ip: "192.168.24.103"
    username: "your-hue-username"
  
  telegraf:
    enabled: true
    host: "192.168.23.87"
    port: 52002

routing:
  ph:  # Route Philips Hue devices
    outputs:
      - hue
      - telegraf
  pm:  # Route power meters
    outputs:
      - telegraf
```

### Legacy Format (Still Supported)
```yaml
udp_server:
  ip: "0.0.0.0"
  ports:
    - 52001

hue_bridge:
  ip: "192.168.24.103"
  username: "your-hue-username"
```

# Execute in place

```sh
python3 -m loxprox.main -c config/loxprox.yml
```
Make sure to install dependencies first. Pipenv is recommended. See also `requirements.txt`.

## Docker

### Server configuration
The sample configuration can be found in the directory 'config.in'. Make a local copy and adjust accordingly to be safe from future upstream changes.

```sh
cp -r config.in config
```

### Docker Compose

Rename docker-compose.yml.in to docker-compose.yml and edit the files to your liking. Especially the ports and volumes need to be adjusted to your needs.

```sh
cp docker-compose.yml.in docker-compose.yml
```

Edit the `docker-compose.yml` file to your liking and run:

```sh
docker compose up -d
```

### Logs
The server process is started with supervisord. Logs can be found in the directory 'config/log/'. Supervisor is also providing a webinterface on port 52080 in my default config. Username and password are 'loxprox:loxone'. The logs have unfurtunately a delay for some reason.

## Architecture

Loxprox uses a modular architecture:

```
UDP Packet → Input Parser → Device Handler → Output Manager → Multiple Outputs
                                                    ↓
                                            Routing Rules
```

### Components

1. **Input Parser** (`inputs/parser.py`): Parses UDP packets and extracts device data
2. **Device Handlers** (`handlers/`): Process device-specific data formats
3. **Output Manager** (`output_manager.py`): Routes data to appropriate outputs
4. **Output Modules** (`outputs/`): Send data to external systems

### Adding New Device Types

1. Create a handler in `loxprox/handlers/`
2. Register it in `HandlerManager`
3. Add routing configuration

### Adding New Outputs

1. Create an output module in `loxprox/outputs/`
2. Register it in `OutputManager`
3. Add to configuration

## Monitoring Integration

When Telegraf output is enabled, loxprox sends metrics in InfluxDB line protocol format:
- Light state changes (RGB values, brightness, color temperature)
- Power meter readings (when implemented)
- Device activity patterns

Configure your Telegraf instance to receive UDP input on the configured port.

