import asyncio, argparse
from .config import load_config
from .converter import convert_received_data
from phue import Bridge
from .colors import *
import re

# Global Control Object
bridge = None

# Function to initialize the bridge object
def initialize_bridge(config):
    global bridge 
    bridge = Bridge(config["hue_bridge"]["ip"], username=config["hue_bridge"]["username"])
    print(f"Connected to Philips Hue bridge at {config['hue_bridge']['ip']}")

def extract_id(s):
    match = re.search(r'ph(\d+)', s)
    if match:
        return int(match.group(1))
    else:
        return None

# Temporary converter function for rgb to xy conversion. TODO: Include and use the color conversion library.
def rgb_to_xy(r, g, b):
    X = r * 0.664511 + g * 0.154324 + b * 0.162028
    Y = r * 0.283881 + g * 0.668433 + b * 0.047685
    Z = r * 0.000088 + g * 0.072310 + b * 0.986039

    x = X / (X + Y + Z)
    y = Y / (X + Y + Z)

    return x, y

# Directly set the calculated colors to the hue lamp. TODO: Create one lamp object with XYZ parameters. Remember lamp state.
def update_color(lamp_id,lamp_type,rgb_color):
    control_id = extract_id(lamp_id)

    if lamp_type == 'RGB':
      print(f"Lamp {control_id}: Update RGB color")
      r = rgb_color[0]
      g = rgb_color[1]
      b = rgb_color[2]

      brightness = max(r, g, b)
      print(f"R:{r}, G:{g}, B:{b}, Brightness: {brightness} ({round(brightness/255*100)}%)")

      if (r+g+b) == 0:
        bridge.set_light(control_id, 'on', False)
      else:
        x, y = rgb_to_xy(r, g, b)
        bridge.set_light(control_id, 'on', True)  # Turn on the light
        bridge.set_light(control_id, {'bri': int(brightness), 'xy': [x, y]})

    elif lamp_type == 'CCT':
      print(f"Lamp {control_id}: Update CCT value")
      brightness = int(rgb_color[0] * 254 / 100)
      kelvin = int(rgb_color[1])
      print(f"CCT: {kelvin}K, Brightness: {brightness} ({round(brightness/255*100)}%)")

      #x, y = colour.temperature.CCT_to_xy_CIE_D(kelvin)
      ct = int(1000000 / kelvin)
    
      # Clamp the ct value within the accepted range for Philips Hue (153-500)
      ct = max(min(ct, 500), 153)

      #print([x,y])
      if brightness == 0:
        bridge.set_light(control_id, 'on', False)
      else:
        bridge.set_light(control_id, 'on', True)
        bridge.set_light(control_id, {'bri': brightness, 'ct': ct})

# UDP Echo server + lamp updater
class EchoServerProtocol(asyncio.DatagramProtocol):
    def __init__(self):
        super().__init__()

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        try:
            data_str = data.decode("utf-8")
            print("*----------------------------------------------------------------")
            print(f"Received from {addr}: {data_str}")
            converted_data = convert_received_data(data_str)
            if converted_data:
                print(f"Converted data: {converted_data}")
                
                # Update Philips Hue lamps
                update_color(*converted_data)
            else:
                print(f"Warning: Unsupported data format received from {addr}: {data_str}")
        except Exception as e:
            print(f"Error processing data from {addr}: {e}")

        self.transport.sendto(data, addr)

async def async_main(config):
    # Set server IP and ports
    SERVER_IP = config['udp_server']['ip']
    PORTS = config['udp_server']['ports']
    print(f"Starting UDP server on {SERVER_IP}:{PORTS}")

    loop = asyncio.get_event_loop()
    servers = []

    for port in PORTS:
        server = await loop.create_datagram_endpoint(
            lambda: EchoServerProtocol(), local_addr=(SERVER_IP, port)
        )
        servers.append(server)

    print("Servers are running... Press Ctrl+C to stop.")
    await asyncio.Event().wait()

def main():
    parser = argparse.ArgumentParser(description="loxprox UDP server")
    parser.add_argument(
        "-c",
        "--config",
        dest="config_file",
        required=True,
        help="Path to the loxprox.yml configuration file",
    )

    args = parser.parse_args()

    if not args.config_file:
        parser.print_help()
    else:
        try:
            # Load content of yaml config file into a dictionary
            config = load_config(args.config_file)
            # Initialize hue bridge controller
            initialize_bridge(config)
            # Start the UDP server
            asyncio.run(async_main(config))
        except KeyboardInterrupt:
            print("Servers stopped.")

if __name__ == "__main__":
    main()
