import socketio

class IoManager:
    _sio = None

    def __new__(cls):
        if cls._sio is None:
            cls._sio = socketio.AsyncServer(cors_allowed_origins='*',async_mode='asgi')

        return cls._sio






