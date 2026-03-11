# Godot API for MCP Server Integration
# This GDScript file provides an interface to the MCP server from Godot

class_name GodotMCPAPI
extends Node

# Server connection settings
var server_host: String = "localhost"
var server_port: int = 25565
var connected: bool = false

# TCP Client
var tcp_client: TCP_Server = null
var stream_peer: StreamPeerTCP = null

# Callbacks
signal server_connected()
signal server_disconnected()
signal message_received(player_id: int, message: String)
signal block_updated(x: int, y: int, z: int, block_type: int)
signal player_joined(player_id: int, username: String)
signal player_left(player_id: int, username: String)

# Scene management
signal scene_created(scene_path: String)
signal node_added(scene_path: String, node_type: String, node_name: String)
signal screenshot_captured(image_path: String)

func _ready():
    print("Godot MCP API initialized")
    tcp_client = TCP_Server.new()

func connect_to_server(host: String = "localhost", port: int = 25565):
    """Connect to MCP server"""
    server_host = host
    server_port = port
    
    var err = tcp_client.connect_to_host(server_host, server_port)
    if err == OK:
        connected = true
        stream_peer = tcp_client.get_stream_peer()
        emit_signal("server_connected")
        print("Connected to MCP server at ", host, ":", port)
        
        # Start receiving data
        _start_receiving()
    else:
        print("Failed to connect to MCP server: ", err)

func disconnect_from_server():
    """Disconnect from MCP server"""
    if connected:
        if stream_peer:
            stream_peer.disconnect_from_host()
        if tcp_client:
            tcp_client.stop()
        connected = false
        emit_signal("server_disconnected")
        print("Disconnected from MCP server")

func _start_receiving():
    """Start receiving data from server"""
    if not connected or not stream_peer:
        return
    
    # Set up polling
    set_process(true)

func _process(delta: float) -> void:
    """Process incoming data"""
    if not connected or not stream_peer:
        set_process(false)
        return
    
    if stream_peer.get_available_bytes() > 0:
        var data = stream_peer.get_data(stream_peer.get_available_bytes())
        _handle_incoming_data(data)

func _handle_incoming_data(data: PoolByteArray):
    """Handle incoming data from server"""
    var offset = 0
    
    while offset < data.size():
        # Read packet type
        if offset + 1 > data.size():
            break
        
        var packet_type = data[offset]
        
        # Parse packet based on type
        match packet_type:
            0:  # Identification
                offset = _parse_identification_packet(data, offset)
            1:  # Ping
                offset = _parse_ping_packet(data, offset)
            5:  # Set Block
                offset = _parse_set_block_packet(data, offset)
            8:  # Position and Orientation
                offset = _parse_position_packet(data, offset)
            10: # Message
                offset = _parse_message_packet(data, offset)
            11: # Disconnect
                offset = _parse_disconnect_packet(data, offset)
            _:
                print("Unknown packet type: ", packet_type)
                offset = data.size()  # Skip rest

func _parse_identification_packet(data: PoolByteArray, offset: int) -> int:
    """Parse identification packet"""
    # Skip protocol version (1 byte)
    offset += 1
    
    # Read server name (null-terminated string)
    var server_name = _read_string(data, offset)
    offset += server_name.length() + 1
    
    # Read MOTD (null-terminated string)
    var motd = _read_string(data, offset)
    offset += motd.length() + 1
    
    # Skip user type (1 byte)
    offset += 1
    
    print("Server identification - Name: ", server_name, ", MOTD: ", motd)
    return offset

func _parse_ping_packet(data: PoolByteArray, offset: int) -> int:
    """Parse ping packet"""
    # Ping packet has no payload
    print("Received ping from server")
    return offset + 1

func _parse_set_block_packet(data: PoolByteArray, offset: int) -> int:
    """Parse set block packet"""
    if offset + 7 > data.size():
        print("Invalid set block packet")
        return data.size()
    
    # Read coordinates (3 shorts = 6 bytes)
    var x = _read_short(data, offset)
    var y = _read_short(data, offset + 2)
    var z = _read_short(data, offset + 4)
    
    # Read block type (1 byte)
    var block_type = data[offset + 6]
    
    emit_signal("block_updated", x, y, z, block_type)
    print("Block updated at (", x, ", ", y, ", ", z, ") to type ", block_type)
    
    return offset + 7

func _parse_position_packet(data: PoolByteArray, offset: int) -> int:
    """Parse position and orientation packet"""
    if offset + 7 > data.size():
        print("Invalid position packet")
        return data.size()
    
    var player_id = data[offset]
    var x = _read_short(data, offset + 1)
    var y = _read_short(data, offset + 3)
    var z = _read_short(data, offset + 5)
    
    print("Player ", player_id, " position: (", x, ", ", y, ", ", z, ")")
    return offset + 7

func _parse_message_packet(data: PoolByteArray, offset: int) -> int:
    """Parse message packet"""
    if offset + 1 > data.size():
        print("Invalid message packet")
        return data.size()
    
    var player_id = data[offset]
    var message = _read_string(data, offset + 1)
    
    emit_signal("message_received", player_id, message)
    print("Message from player ", player_id, ": ", message)
    
    return offset + 1 + message.length() + 1

func _parse_disconnect_packet(data: PoolByteArray, offset: int) -> int:
    """Parse disconnect packet"""
    if offset + 1 > data.size():
        print("Invalid disconnect packet")
        return data.size()
    
    var player_id = data[offset]
    var reason = _read_string(data, offset + 1)
    
    print("Player ", player_id, " disconnected: ", reason)
    emit_signal("player_left", player_id, "Unknown")
    
    return offset + 1 + reason.length() + 1

# Helper functions
func _read_string(data: PoolByteArray, offset: int) -> String:
    """Read null-terminated string from data"""
    var end = offset
    while end < data.size() and data[end] != 0:
        end += 1
    
    if end >= data.size():
        return ""
    
    var bytes = []
    for i in range(offset, end):
        bytes.append(data[i])
    
    return String.from_utf8(bytes)

func _read_short(data: PoolByteArray, offset: int) -> int:
    """Read 16-bit signed short from data"""
    if offset + 2 > data.size():
        return 0
    
    var value = (data[offset] << 8) | data[offset + 1]
    if value > 32767:
        value -= 65536
    return value

# Scene Management Functions
func create_scene(project_path: String, scene_name: String, root_node_type: String = "Node2D") -> String:
    """Create a new scene in a Godot project"""
    var http = HTTPRequest.new()
    add_child(http)
    http.connect("request_completed", self, "_on_scene_created")
    
    var url = "http://" + server_host + ":" + str(server_port) + "/create_scene"
    var headers = ["Content-Type: application/json"]
    var body = JSON.print({
        "project_path": project_path,
        "scene_name": scene_name,
        "root_node_type": root_node_type
    })
    
    http.request(url, headers, true, HTTPClient.METHOD_POST, body)
    return ""

func _on_scene_created(result: int, response_code: int, headers: PoolStringArray, body: PoolByteArray):
    """Handle scene creation response"""
    if response_code == 200:
        var response = JSON.parse(body.get_string_from_utf8()).result
        emit_signal("scene_created", response.scene_path)
        print("Scene created: ", response.scene_path)
    else:
        print("Failed to create scene: ", response_code)

func add_node_to_scene(scene_path: String, node_type: String, node_name: String, parent_path: String = "") -> bool:
    """Add a node to an existing scene"""
    var http = HTTPRequest.new()
    add_child(http)
    http.connect("request_completed", self, "_on_node_added")
    
    var url = "http://" + server_host + ":" + str(server_port) + "/add_node"
    var headers = ["Content-Type: application/json"]
    var body = JSON.print({
        "scene_path": scene_path,
        "node_type": node_type,
        "node_name": node_name,
        "parent_path": parent_path
    })
    
    http.request(url, headers, true, HTTPClient.METHOD_POST, body)
    return false

func _on_node_added(result: int, response_code: int, headers: PoolStringArray, body: PoolByteArray):
    """Handle node addition response"""
    if response_code == 200:
        var response = JSON.parse(body.get_string_from_utf8()).result
        emit_signal("node_added", response.scene_path, response.node_type, response.node_name)
        print("Node added to scene")
    else:
        print("Failed to add node: ", response_code)

func capture_screenshot(project_path: String, output_path: String, width: int = 1920, height: int = 1080) -> String:
    """Capture screenshot from running Godot project"""
    var http = HTTPRequest.new()
    add_child(http)
    http.connect("request_completed", self, "_on_screenshot_captured")
    
    var url = "http://" + server_host + ":" + str(server_port) + "/capture_screenshot"
    var headers = ["Content-Type: application/json"]
    var body = JSON.print({
        "project_path": project_path,
        "output_path": output_path,
        "width": width,
        "height": height
    })
    
    http.request(url, headers, true, HTTPClient.METHOD_POST, body)
    return ""

func _on_screenshot_captured(result: int, response_code: int, headers: PoolStringArray, body: PoolByteArray):
    """Handle screenshot capture response"""
    if response_code == 200:
        var response = JSON.parse(body.get_string_from_utf8()).result
        emit_signal("screenshot_captured", response.image_path)
        print("Screenshot captured: ", response.image_path)
    else:
        print("Failed to capture screenshot: ", response_code)

# Server Control Functions
func send_chat_message(message: String):
    """Send a chat message to the server"""
    if not connected or not stream_peer:
        return
    
    # Create message packet: type 10, player_id 0, message
    var packet = PoolByteArray()
    packet.append(10)  # Packet type
    packet.append(0)   # Player ID (0 for this client)
    packet.append_array(message.to_utf8())
    packet.append(0)   # Null terminator
    
    stream_peer.put_data(packet)
    print("Sent message: ", message)

func set_block(x: int, y: int, z: int, block_type: int):
    """Set a block in the world"""
    if not connected or not stream_peer:
        return
    
    # Create set block packet: type 5, x, y, z, block_type
    var packet = PoolByteArray()
    packet.append(5)  # Packet type
    
    # Add coordinates as shorts
    packet.append(_int_to_byte(x >> 8))
    packet.append(_int_to_byte(x & 0xFF))
    packet.append(_int_to_byte(y >> 8))
    packet.append(_int_to_byte(y & 0xFF))
    packet.append(_int_to_byte(z >> 8))
    packet.append(_int_to_byte(z & 0xFF))
    
    packet.append(block_type)
    
    stream_peer.put_data(packet)
    print("Set block at (", x, ", ", y, ", ", z, ") to type ", block_type)

func update_position(x: int, y: int, z: int):
    """Update player position"""
    if not connected or not stream_peer:
        return
    
    # Create position packet: type 8, player_id, x, y, z
    var packet = PoolByteArray()
    packet.append(8)  # Packet type
    packet.append(0)  # Player ID
    
    # Add coordinates as shorts
    packet.append(_int_to_byte(x >> 8))
    packet.append(_int_to_byte(x & 0xFF))
    packet.append(_int_to_byte(y >> 8))
    packet.append(_int_to_byte(y & 0xFF))
    packet.append(_int_to_byte(z >> 8))
    packet.append(_int_to_byte(z & 0xFF))
    
    stream_peer.put_data(packet)
    print("Updated position to (", x, ", ", y, ", ", z, ")")

# Helper function
func _int_to_byte(value: int) -> int:
    """Convert int to byte (0-255)"""
    return value & 0xFF