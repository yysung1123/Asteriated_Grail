import asyncio
import websockets
from TestGame import TestGame

class AgrGameInstance:
    def __init__(self, players, room_id, agr_game_server):
        self._players = players
        self._room_id = room_id
        self._agr_game_server = agr_game_server
        self._game = TestGame().run()
        self._end = asyncio.Event()
        self._queues = [asyncio.Queue(maxsize=1)]\
            * self._agr_game_server._players_num_per_game
        asyncio.create_task(self.main())
        self._player_turn = -1
        self._lock = asyncio.Lock()
        
    async def main(self):
        send = None
        try:
            while True:
                msg = self._game.send(send)
                if msg is None:
                    continue
                if msg['type'] == 'broadcast':
                    await self.broadcast(msg['msg'])
                elif msg['type'] == 'send':
                    player_id, message = msg['id'], msg['msg']
                    await self.send(self._players[player_id], message)
                elif msg['type'] == 'recv':
                    async with self._lock:
                        self._player_turn = msg['id']
                    send = await self._queues[player_id].get()
        finally:
            await self.broadcast(f"Game finished\n")
            self.end()
    
    async def broadcast(self, msg):
        for player in self._players:
            await self.send(player, msg)

    async def send(self, player, msg):
        await self._agr_game_server.getPlayer(player).send(msg)

    async def msgToGame(self, player, msg):
        async with self._lock:
            print(self._player_turn, player, msg)
            if self._player_turn != -1 and self._players[self._player_turn]\
                == player:
                    await self._queues[self._player_turn].put(msg)
                    self._player_turn = -1

    def end(self):
        self._agr_game_server.removeGame(self._room_id)
        self._end.set()

    async def isEnd(self):
        return await self._end.wait()

    def playerName(self):
        return self._players


class AgrGameServer:
    def __init__(self):
        self._players_num_per_game = 2
        self._players = {}
        self._in_game = {}
        self._matching = []
        self._matching_lock = {}
        self._games = {}
        self._room_id = 0

    async def setName(self, name, agr_game_player):
        self._players[name] = agr_game_player

    async def startMatching(self, name):
        self.debug()
        if not name in self._in_game:
            self._matching.append(name)
            self._matching_lock[name] = asyncio.Lock()
            await self._matching_lock[name].acquire()
            self.matching()

    def matching(self):
        if len(self._matching) >= self._players_num_per_game:
            players = self._matching[:self._players_num_per_game]
            self.createGame(players)
            for player in players:
                self._matching_lock[player].release()
            self._matching = self._matching[self._players_num_per_game:]
            self.debug()

    def createGame(self, players):
        self._games[self._room_id] = AgrGameInstance(
            players, self._room_id, self)
        for player in players:
            self._in_game[player] = self._room_id
        self._room_id += 1

    async def matchingLock(self, player):
        await self._matching_lock[player].acquire()
        self._matching_lock.pop(player)

    def getGameInstance(self, player):
        return self._games[self._in_game[player]]

    def removeGame(self, room_id):
        agr_game_instance = self._games[room_id]
        players = agr_game_instance.playerName()
        for player in players:
            self._in_game.pop(player)
            self._players.pop(player)
        self._games.pop(room_id)
        self.debug()

    def getPlayer(self, player):
        return self._players[player]

    def debug(self):
        print(', '.join("%s: %s" % item for item in vars(self).items()))

class AgrGamePlayer:
    def __init__(self, websocket, agr_game_server):
        self._websocket = websocket
        self._name = None
        self._agr_game_server = agr_game_server
        self._agr_game_instance = None

    async def handle(self):
        await self.nameHandler()
        await self.matchingHandler()
        self._agr_game_instance = self._agr_game_server.getGameInstance(self._name)
        asyncio.create_task(self.msgToGameHandler())
        await self._agr_game_instance.isEnd()

    async def nameHandler(self):
        await self._websocket.send(f"Please type your name: ")
        self._name = await self._websocket.recv()
        await self._agr_game_server.setName(self._name, self)
        await self.send(f"{self._name}\n")

    async def matchingHandler(self):
        await self._agr_game_server.startMatching(self._name)
        await self.send(f"Waiting for matching...\n")
        return await self._agr_game_server.matchingLock(self._name)

    async def msgToGameHandler(self):
        while True:
            msg = await self._websocket.recv()
            await self._agr_game_instance.msgToGame(self._name, msg)
    
    async def send(self, msg):
        await self._websocket.send(msg)

    def name(self):
        return self._name
        

async def mainHandler(websocket, path, agr_game_server):
    await AgrGamePlayer(websocket, agr_game_server).handle()

def createGameHandler():
    agr_game_server = AgrGameServer()
    async def _mainHandler(websocket, path):
         return await mainHandler(websocket, path, agr_game_server)

    return _mainHandler

def main():
    start_server = websockets.serve(createGameHandler(), "localhost", 12345)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()

if __name__ == '__main__':
    main()