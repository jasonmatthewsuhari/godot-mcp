# MCP Protocol Packet Definitions
# Based on Minecraft Classic Protocol (0.30)

from enum import IntEnum
import struct

class PacketType(IntEnum):
    IDENTIFICATION = 0
    PING = 1
    LEVEL_INITIALIZE = 2
    LEVEL_DATA_CHUNK = 3
    LEVEL_FINALIZE = 4
    SET_BLOCK_CLIENT = 5
    SET_BLOCK_SERVER = 6
    ADD_PLAYER = 7
    POSITION_AND_ORIENTATION = 8
    REMOVE_PLAYER = 9
    MESSAGE = 10
    DISCONNECT_PLAYER = 11
    UPDATE_PLAYER_TYPE = 12

class MCPPacket:
    """Base MCP Packet class"""
    
    def __init__(self, packet_type):
        self.packet_type = packet_type
        self.payload = b''
    
    def serialize(self):
        """Serialize packet to bytes"""
        length = len(self.payload) + 1  # +1 for packet type byte
        return struct.pack('b', self.packet_type) + self.payload
    
    @classmethod
    def deserialize(cls, data):
        """Deserialize bytes to packet"""
        if len(data) < 1:
            raise ValueError("Packet too short")
        
        packet_type = data[0]
        payload = data[1:]
        
        # Create appropriate packet subclass
        if packet_type == PacketType.IDENTIFICATION:
            return IdentificationPacket.from_payload(payload)
        elif packet_type == PacketType.PING:
            return PingPacket.from_payload(payload)
        # Add more packet types as needed
        else:
            packet = MCPPacket(packet_type)
            packet.payload = payload
            return packet

class IdentificationPacket(MCPPacket):
    """Packet 0: Identification"""
    
    def __init__(self, protocol_version=7, server_name="Mistral MCP", server_motd="Mistral Vibe MCP Server", user_type=0):
        super().__init__(PacketType.IDENTIFICATION)
        self.protocol_version = protocol_version
        self.server_name = server_name
        self.server_motd = server_motd
        self.user_type = user_type
        self._update_payload()
    
    def _update_payload(self):
        self.payload = struct.pack('B', self.protocol_version) + \
                     self._encode_string(self.server_name) + \
                     self._encode_string(self.server_motd) + \
                     struct.pack('B', self.user_type)
    
    @classmethod
    def from_payload(cls, payload):
        if len(payload) < 3:
            raise ValueError("Identification packet too short")
        
        protocol_version = payload[0]
        rest = payload[1:]
        
        # Parse strings
        server_name, rest = cls._decode_string(rest)
        server_motd, rest = cls._decode_string(rest)
        
        if len(rest) < 1:
            raise ValueError("Identification packet missing user type")
        
        user_type = rest[0]
        
        return cls(protocol_version, server_name, server_motd, user_type)
    
    @staticmethod
    def _encode_string(s):
        return s.encode('utf-8') + b'\x00'
    
    @staticmethod
    def _decode_string(data):
        if b'\x00' not in data:
            raise ValueError("String not null-terminated")
        
        parts = data.split(b'\x00', 1)
        return parts[0].decode('utf-8'), parts[1]

class PingPacket(MCPPacket):
    """Packet 1: Ping"""
    
    def __init__(self):
        super().__init__(PacketType.PING)
        self.payload = b''