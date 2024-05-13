from managers.io import IoManager

class SocketManager():
    _sio = IoManager()

    def __new__(cls):
        return cls._sio

    @_sio.event
    async def connect(sid, data):
        print(f"client connected: {sid}")

    @_sio.event
    async def disconnect(sid):
        print(f"client disconnected: {sid}")