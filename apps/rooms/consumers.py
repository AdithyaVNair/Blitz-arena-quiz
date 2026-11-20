import asyncio
import time
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Room, RoomPlayer
from . import services


class RoomConsumer(AsyncJsonWebsocketConsumer):
    # Class-level dictionary to track active question start timestamps and timer tasks per room
    room_timers = {}
    room_start_times = {}

    async def connect(self):
        self.code = self.scope['url_route']['kwargs']['code'].upper()
        self.room_group_name = f'room_{self.code}'
        self.user = self.scope.get('user')

        if not self.user or not self.user.is_authenticated:
            await self.close()
            return

        # Check room exists in DB
        room = await self.get_room()
        if not room:
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Add or get player
        await self.add_player()

        # Send state on connect / reconnect
        await self.send_current_state()

        # Check duel auto-start
        if room.mode == 'duel' and room.status == 'lobby':
            player_count = await self.get_player_count()
            if player_count >= 2:
                # In a duel, auto-start as soon as both players are connected
                asyncio.create_task(self.start_game_flow())

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive_json(self, content):
        msg_type = content.get('type')
        room = await self.get_room()
        if not room:
            return

        if msg_type == 'start':
            # Start is host only
            if room.host_id == self.user.id and room.status == 'lobby':
                asyncio.create_task(self.start_game_flow())

        elif msg_type == 'answer':
            if room.status != 'live':
                return
            option_id = content.get('option_id')
            start_time = self.room_start_times.get(self.code, time.time())
            time_taken_ms = max(0, int((time.time() - start_time) * 1000))
            
            question_id = await self.get_current_question_id()
            if question_id:
                await self.save_player_answer(question_id, option_id, time_taken_ms)

    # Broadcast Handlers
    async def broadcast_message(self, event):
        await self.send_json(event['payload'])

    # State Sync
    async def send_current_state(self):
        room = await self.get_room()
        if not room:
            return

        if room.status == 'lobby':
            players = await self.get_players_data()
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'broadcast_message',
                    'payload': {
                        'type': 'lobby_state',
                        'players': players,
                        'is_host': (room.host_id == self.user.id),
                    }
                }
            )
        elif room.status == 'live':
            # Reconnect during question
            payload = await self.get_question_data()
            if payload:
                await self.send_json({
                    'type': 'question',
                    **payload
                })
        elif room.status == 'finished':
            scores = await self.get_finished_data()
            await self.send_json({
                'type': 'finished',
                **scores
            })

    # Game Loop
    async def start_game_flow(self):
        # Cancel any existing task
        if self.code in self.room_timers:
            self.room_timers[self.code].cancel()

        await self.set_room_status('live', 0)
        await self.run_question_round()

    async def run_question_round(self):
        q_payload = await self.get_question_data()
        if not q_payload:
            # Quiz finished
            await self.set_room_status('finished')
            finished_payload = await self.get_finished_data()
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'broadcast_message',
                    'payload': {
                        'type': 'finished',
                        **finished_payload
                    }
                }
            )
            return

        # Record start time on server
        self.room_start_times[self.code] = time.time()
        time_limit = q_payload['time_limit']

        # Broadcast question to all players
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'broadcast_message',
                'payload': {
                    'type': 'question',
                    **q_payload
                }
            }
        )

        # Server timer owns the countdown
        await asyncio.sleep(time_limit)

        # Reveal answer and scores
        reveal_payload = await self.get_reveal_data()
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'broadcast_message',
                'payload': {
                    'type': 'reveal',
                    **reveal_payload
                }
            }
        )

        # 4 seconds reveal pause so players can see scores and answer
        await asyncio.sleep(4)

        # Advance question
        has_more = await self.advance_room()
        if has_more:
            await self.run_question_round()
        else:
            finished_payload = await self.get_finished_data()
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'broadcast_message',
                    'payload': {
                        'type': 'finished',
                        **finished_payload
                    }
                }
            )

    # Database Helpers
    @database_sync_to_async
    def get_room(self):
        return Room.objects.filter(code=self.code).first()

    @database_sync_to_async
    def add_player(self):
        room = Room.objects.filter(code=self.code).first()
        if room:
            RoomPlayer.objects.get_or_create(room=room, user=self.user)

    @database_sync_to_async
    def get_player_count(self):
        return RoomPlayer.objects.filter(room__code=self.code).count()

    @database_sync_to_async
    def get_players_data(self):
        room = Room.objects.filter(code=self.code).first()
        if not room:
            return []
        return [
            {'name': p.user.username, 'avatar': p.user.avatar}
            for p in room.players.select_related('user').all()
        ]

    @database_sync_to_async
    def set_room_status(self, status, index=None):
        room = Room.objects.filter(code=self.code).first()
        if room:
            room.status = status
            if index is not None:
                room.current_index = index
                room.save(update_fields=['status', 'current_index'])
            else:
                room.save(update_fields=['status'])

    @database_sync_to_async
    def get_current_question_id(self):
        room = Room.objects.filter(code=self.code).first()
        q = services.get_current_question(room) if room else None
        return q.id if q else None

    @database_sync_to_async
    def get_question_data(self):
        room = Room.objects.filter(code=self.code).first()
        return services.get_question_payload(room) if room else None

    @database_sync_to_async
    def get_reveal_data(self):
        room = Room.objects.filter(code=self.code).first()
        return services.get_reveal_payload(room) if room else {'correct_option_id': None, 'scores': []}

    @database_sync_to_async
    def get_finished_data(self):
        room = Room.objects.filter(code=self.code).first()
        return services.get_finished_payload(room) if room else {'scores': []}

    @database_sync_to_async
    def advance_room(self):
        room = Room.objects.filter(code=self.code).first()
        return services.advance_question(room) if room else False

    @database_sync_to_async
    def save_player_answer(self, q_id, opt_id, time_ms):
        room = Room.objects.filter(code=self.code).first()
        if room:
            services.record_answer(room, self.user, q_id, opt_id, time_ms)
