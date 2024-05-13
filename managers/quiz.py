import json
import asyncio
from managers.sockets import SocketManager
from config import REDIS_CONFIG

import aioredis

sio = SocketManager()

redis_data = dict()

pub = aioredis.Redis(**REDIS_CONFIG)

sub = aioredis.Redis(**REDIS_CONFIG)

pubsub = sub.pubsub()


class QuizManager:

    def __init__(self):
        asyncio.create_task(self.subscribe())

    def init_handlers(self):

        @sio.event
        async def join_room(sid, user:dict):
            user["sid"] = sid
            await pub.publish("JOIN_ROOM", json.dumps(user))

        @sio.event
        async def leave_room(sid, user:dict):
            user["sid"] = sid
            await pub.publish("LEAVE_ROOM", json.dumps(user))

        @sio.event
        async def chat(sid, data):
            data["sid"] = sid
            await pub.publish("CHAT", json.dumps(data))

    @staticmethod
    async def sub_chat(data:dict):
        sid = data["sid"]
        room = data['room']
        print(f"Received message from : {sid}, message: {str(data)}")
        await sio.emit("chat", data, room=room)

    @staticmethod
    async def sub_join_room(user:dict):
        join_user = True
        quiz_type = None

        sid = user["sid"]
        room = user["room"]
        
        if room not in redis_data:
            redis_data[room] = dict()

        room_users = redis_data[room]
        number_of_users = len(room_users.keys())
        
        if number_of_users < 2:
            redis_data[room][user["name"]] = user
        elif number_of_users == 2:
            if user["name"] in room_users:
                redis_data[room][user["name"]] = user
            else:
                join_user = False
        else:
            join_user = False

        if join_user:
            try:
                await sio.enter_room(sid, room)
                print(f'Socket {sid} joined room {room}')
                updated_room = redis_data[room]
                event_data = {"users": redis_data[room]}
                if len(updated_room.keys()) == 1:
                    quiz_type = "lobby"
                    event_name = "user_joined"
                elif len(updated_room.keys()) == 2:
                    quiz_type = "question"
                    event_data["question"] = {}
                    event_name = "quiz_start"
                join_data = {"type": quiz_type, "user": user["name"], "data": event_data}
                await sio.emit(event_name, join_data, room=room)
            except ValueError:
                print("Ignored activity from other server")
        else:
            await sio.emit("quiz_error", {"error": "Room is in use"}, room=sid)

        print(quiz_type) 
        print(redis_data)

    
    @staticmethod
    async def sub_leave_room(user:dict):
        name = user["name"]
        room = user["room"]
        sid = user["sid"]
        await sio.leave_room(sid, room)
        print(f'Socket {sid} left room {room}')
        if redis_data.get(room):
            if redis_data[room].get(name):
                del redis_data[room][name]

            updated_users = redis_data[room]
        
            if len(updated_users) == 1:
                await sio.emit("user_left", {"type": "lobby", "user": name, "data": updated_users}, room=room)
        print(redis_data)


    async def subscribe(self):
        print("SUBSCRIBING") 
        await pubsub.subscribe("JOIN_ROOM")
        await pubsub.subscribe("LEAVE_ROOM")
        await pubsub.subscribe("CHAT")
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True)
            if message is not None:
                print(message)
                if message["channel"] == "JOIN_ROOM":
                    await QuizManager.sub_join_room(json.loads(message["data"]))
                elif message["channel"] == "LEAVE_ROOM":
                    await QuizManager.sub_leave_room(json.loads(message["data"]))
                elif message["channel"] == "CHAT":
                    await QuizManager.sub_chat(json.loads(message["data"]))