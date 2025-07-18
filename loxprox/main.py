import asyncio
import argparse
import logging
import signal
import sys
from typing import Optional
from .config import load_config
from .inputs.parser import InputParser
from .handler_manager import HandlerManager
from .output_manager import OutputManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LoxproxServer:
    """Main server class for loxprox with modular architecture."""
    
    def __init__(self, config_path: str):
        """Initialize the server with configuration.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = load_config(config_path)
        self.parser = InputParser()
        self.handler_manager = HandlerManager()
        self.output_manager = OutputManager(self.config)
        self.servers = []
        self.running = True
        
    async def start(self) -> None:
        """Start the UDP servers."""
        udp_config = self.config['inputs']['udp']
        server_ip = udp_config['ip']
        ports = udp_config['ports']
        
        logger.info(f"Starting UDP servers on {server_ip}:{ports}")
        
        loop = asyncio.get_event_loop()
        
        for port in ports:
            server = await loop.create_datagram_endpoint(
                lambda: UDPProtocol(self),
                local_addr=(server_ip, port)
            )
            self.servers.append(server)
            logger.info(f"UDP server listening on {server_ip}:{port}")
            
    async def stop(self) -> None:
        """Stop all servers and clean up."""
        self.running = False
        
        for transport, protocol in self.servers:
            transport.close()
            
        self.output_manager.shutdown()
        logger.info("Server stopped")
        
    def process_packet(self, data: bytes, addr: tuple) -> None:
        """Process a received UDP packet.
        
        Args:
            data: Raw packet data
            addr: Source address
        """
        try:
            # Decode packet
            packet_str = data.decode('utf-8')
            logger.info(f"Received from {addr}: {packet_str}")
            
            # Parse packet
            parsed_data = self.parser.parse_packet(packet_str)
            if not parsed_data:
                logger.warning(f"Failed to parse packet: {packet_str}")
                return
                
            # Process through handler
            processed_data = self.handler_manager.process_data(parsed_data)
            if not processed_data:
                logger.warning(f"Handler failed to process data")
                return
                
            # Route to outputs
            results = self.output_manager.route_data(processed_data)
            
            # Log results
            success_count = sum(1 for success in results.values() if success)
            total_count = len(results)
            
            if success_count < total_count:
                logger.warning(f"Sent to {success_count}/{total_count} outputs")
            else:
                logger.debug(f"Successfully sent to all {total_count} outputs")
                
        except Exception as e:
            logger.error(f"Error processing packet from {addr}: {e}")


class UDPProtocol(asyncio.DatagramProtocol):
    """UDP protocol handler."""
    
    def __init__(self, server: LoxproxServer):
        """Initialize protocol with server reference.
        
        Args:
            server: LoxproxServer instance
        """
        self.server = server
        self.transport = None
        
    def connection_made(self, transport):
        """Called when connection is established."""
        self.transport = transport
        
    def datagram_received(self, data, addr):
        """Called when datagram is received."""
        # Process packet
        self.server.process_packet(data, addr)
        
        # Echo back (for compatibility)
        if self.transport:
            self.transport.sendto(data, addr)


async def async_main(config_path: str) -> None:
    """Async main function.
    
    Args:
        config_path: Path to configuration file
    """
    server = LoxproxServer(config_path)
    
    # Set up signal handlers
    def signal_handler(sig, frame):
        logger.info("Received interrupt signal, shutting down...")
        asyncio.create_task(server.stop())
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start server
    await server.start()
    
    # Keep running until stopped
    try:
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        pass
    
    await server.stop()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="loxprox UDP server (modular version)")
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
        sys.exit(1)
        
    try:
        asyncio.run(async_main(args.config_file))
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()