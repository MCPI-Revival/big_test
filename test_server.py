from rak_net.server import server
from rak_net.protocol.frame import frame
import pi_protocol
from pi_world.world import world

rak_server: object = server(".".join(["0"] * 4), 19132)
rak_server.name: str = "MCCPP;Demo;Dedicated Server"
   
class interface:
    def __init__(self):
        self.players = {}
        self.eid = 0
        
    def send_packet(self, data, connection):
        packet = frame()
        packet.reliability = 0
        packet.body = data
        connection.add_to_queue(packet)
        
    def broadcast_packet(self, data, blacklist = []):
        for player in self.players.values():
            if player["connection"].address.token not in blacklist:
                self.send_packet(data, player["connection"])
                  
    def send_chunk(self, x, z, data, connection):
        new_packet = pi_protocol.encode_packet({
            "id": 158,
            "x": x,
            "z": z,
            "data": data
        })
        self.send_packet(new_packet, connection)
                
    def init_players(self, connection):
        for player in self.players.values():
            if player["connected"]:
                    new_packet = pi_protocol.encode_packet({
                        "id": 137,
                        "clientId": 28347893264,
                        "username": player["username"],
                        "entityId": player["eid"],
                        "x": player["x"] + 128,
                        "y": player["y"] + 64,
                        "z": player["z"] + 128,
                        "pitch": 0,
                        "yaw": 0,
                        "item": 0,
                        "meta": 0,
                        "metadata": []
                    })
                    if player["connection"].address.token != connection.address.token:
                        self.send_packet(new_packet, connection)
                    else:
                        self.broadcast_packet(new_packet, [player["connection"].address.token])
        
    def send_message(self, message, connection):
        new_packet = pi_protocol.encode_packet({
            "id": 133,
            "message": message
        })
        self.send_packet(new_packet, connection)
        
    def broadcast_message(self, message, blacklist = []):
        new_packet = pi_protocol.encode_packet({
            "id": 133,
            "message": message
        })
        self.broadcast_packet(new_packet, blacklist)

    def on_frame(self, packet: object, connection: object) -> None:
        pid = packet.body[0]
        if pid == 0x82:
            packet = pi_protocol.decode_packet(packet.body)
            self.players[connection.address.token]["username"] = packet["username"]
            self.players[connection.address.token]["eid"] = self.eid
            self.eid += 1
            new_packet = pi_protocol.encode_packet({
                "id": 131,
                "status": 0
            })
            self.send_packet(new_packet, connection)
            new_packet = pi_protocol.encode_packet({
                "id": 135,
                "seed": 0,
                "generator": 0,
                "gamemode": 1,
                "entityId": self.players[connection.address.token]["eid"],
                "x": 0 + 128,
                "y": 9 + 64,
                "z": 0 + 128
            })
            self.players[connection.address.token]["x"] = 0
            self.players[connection.address.token]["y"] = 9
            self.players[connection.address.token]["z"] = 0
            self.players[connection.address.token]["pitch"] = 0
            self.players[connection.address.token]["yaw"] = 0
            self.send_packet(new_packet, connection)
        elif pid == 0x84:
            self.players[connection.address.token]["connected"] = True
            self.init_players(connection)
            message = f"""{self.players[connection.address.token]["username"]} joined the game."""
            self.broadcast_message(message)
            print(message)
        elif pid == 148:
            new_packet = pi_protocol.decode_packet(packet.body)
            self.players[connection.address.token]["x"] = new_packet["x"] - 128
            self.players[connection.address.token]["y"] = new_packet["y"] - 64
            self.players[connection.address.token]["z"] = new_packet["z"] - 128
            self.players[connection.address.token]["pitch"] = new_packet["pitch"]
            self.players[connection.address.token]["yaw"] = new_packet["yaw"]
            self.broadcast_packet(packet.body)
        elif pid == 157:
            new_packet = pi_protocol.decode_packet(packet.body)
            #chunk_data = self.map.get_chunk(new_packet["x"], new_packet["z"]).network_serialize()
            #self.send_chunk(new_packet["x"], new_packet["z"], chunk_data)
            
    def on_disconnect(self, connection: object) -> None:
        print(f"{connection.address.token} has disconnected.")
        
    def on_new_incoming_connection(self, connection: object) -> None:
        print(f"{connection.address.token} connected.")
        self.players[connection.address.token] = {}
        self.players[connection.address.token]["connection"] = connection
        self.players[connection.address.token]["connected"] = False
        
rak_server.interface: object = interface()
    
while True:
    rak_server.handle()
