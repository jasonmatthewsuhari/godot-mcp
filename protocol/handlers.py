# MCP Packet Handlers

from .packets import *
import logging

class PacketHandler:
    """Base packet handler class"""
    
    def __init__(self, server):
        self.server = server
        self.logger = logging.getLogger(f"MCP.{self.__class__.__name__}")
    
    def handle(self, packet, client):
        """Handle a packet"""
        raise NotImplementedError("Subclasses must implement handle method")

class IdentificationHandler(PacketHandler):
    """Handle Identification packets (Packet 0)"""
    
    def handle(self, packet, client):
        if not isinstance(packet, IdentificationPacket):
            self.logger.warning(f"Expected IdentificationPacket, got {type(packet)}")
            return
        
        self.logger.info(f"Client identification: protocol={packet.protocol_version}, "
                       f"name='{packet.server_name}', motd='{packet.server_motd}', "
                       f"user_type={packet.user_type}")
        
        # Send server identification back
        server_id = IdentificationPacket(
            protocol_version=7,
            server_name=self.server.config.server_name,
            server_motd=self.server.config.motd,
            user_type=1  # Server
        )
        
        client.send_packet(server_id)
        
        # Add client to server
        self.server.add_client(client, packet.server_name)

class PingHandler(PacketHandler):
    """Handle Ping packets (Packet 1)"""
    
    def handle(self, packet, client):
        if not isinstance(packet, PingPacket):
            self.logger.warning(f"Expected PingPacket, got {type(packet)}")
            return
        
        self.logger.debug(f"Received ping from {client}")
        # Just respond with empty ping packet
        client.send_packet(PingPacket())

class SetBlockHandler(PacketHandler):
    """Handle Set Block packets (Packet 5)"""
    
    def handle(self, packet, client):
        # Parse block position and type from raw payload
        if len(packet.payload) != 7:
            self.logger.warning(f"Invalid SetBlock packet length: {len(packet.payload)}")
            return
        
        # Parse: short x, short y, short z, byte block_type
        try:
            x = int.from_bytes(packet.payload[0:2], 'big', signed=True)
            y = int.from_bytes(packet.payload[2:4], 'big', signed=True)
            z = int.from_bytes(packet.payload[4:6], 'big', signed=True)
            block_type = packet.payload[6]
            
            self.logger.info(f"Block set at ({x}, {y}, {z}) to type {block_type}")
            
            # Update world
            self.server.world.set_block(x, y, z, block_type)
            
            # Broadcast to all clients
            self.server.broadcast_packet(packet, exclude_client=client)
            
        except Exception as e:
            self.logger.error(f"Error handling SetBlock packet: {e}")

class PositionOrientationHandler(PacketHandler):
    """Handle Position and Orientation packets (Packet 8)"""
    
    def handle(self, packet, client):
        if len(packet.payload) != 7:
            self.logger.warning(f"Invalid PositionOrientation packet length: {len(packet.payload)}")
            return
        
        try:
            # Parse: byte player_id, short x, short y, short z, byte yaw, byte pitch
            player_id = packet.payload[0]
            x = int.from_bytes(packet.payload[1:3], 'big', signed=True)
            y = int.from_bytes(packet.payload[3:5], 'big', signed=True)
            z = int.from_bytes(packet.payload[5:7], 'big', signed=True)
            
            # Note: Original MCP has yaw and pitch, but payload is only 7 bytes
            # So we'll assume basic position for now
            
            self.logger.debug(f"Player {player_id} position: ({x}, {y}, {z})")
            
            # Update client position
            if client.player_id == player_id:
                client.position = (x, y, z)
            
            # Broadcast to other clients
            self.server.broadcast_packet(packet, exclude_client=client)
            
        except Exception as e:
            self.logger.error(f"Error handling PositionOrientation packet: {e}")

class MessageHandler(PacketHandler):
    """Handle Message packets (Packet 10)"""
    
    def handle(self, packet, client):
        if len(packet.payload) < 2:
            self.logger.warning(f"Invalid Message packet length: {len(packet.payload)}")
            return
        
        try:
            # Parse: byte player_id, string message
            player_id = packet.payload[0]
            message = packet.payload[1:].decode('utf-8').rstrip('\x00')
            
            self.logger.info(f"Message from player {player_id}: {message}")
            
            # Broadcast chat message to all clients
            self.server.broadcast_chat_message(player_id, message)
            
        except Exception as e:
            self.logger.error(f"Error handling Message packet: {e}")