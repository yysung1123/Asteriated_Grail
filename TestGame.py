class TestGame:
    def broadcast(self, msg):
        yield {'type': 'broadcast', 'msg': msg}
    
    def send(self, player_id, msg):
        yield {'type': 'send', 'id': player_id, 'msg': msg}

    def recv_request(self, player_id):
        yield {'type': 'recv', 'id': player_id}

    def recv_get(self):
        return (yield None)

    def run(self):
        yield from self.broadcast(f"Game started\n")
        player_id = 0
        for _ in range(2):
            yield from self.send(player_id, f"your turn\n")
            yield from self.recv_request(player_id)
            num = yield from self.recv_get()
            yield from self.broadcast(f"{num}\n")
            player_id = 1 - player_id
        