"""
ASGI config for sbw_site project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""
import json
import os
from datetime import datetime

import socketio
from django.core.asgi import get_asgi_application
from asgiref.sync import sync_to_async

from dateutil import parser

from socket_app.models import LocationData

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

# Initialize Django ASGI application
django_asgi_app = get_asgi_application()

# Create Socket.IO server
sio = socketio.AsyncServer(async_mode='asgi')
app = socketio.ASGIApp(sio, django_asgi_app)


# Define Socket.IO event handlers
@sio.event
async def connect(sid, environ):
    print(f"Client 🟢 [{sid}] connected")
    await sio.emit('message', {'data': 'Connected to server'}, to=sid)

@sio.event
async def disconnect(sid):
    print(f"Client 🔴 [{sid}] disconnected")

@sio.event
async def update_location(sid, data_list):
    print(f"📥 Bulk message from {sid}: {data_list}")

    # If it's not a list, return early with error
    if not isinstance(data_list, list):
        await sio.emit('update_location', {
            'status': 'error',
            'message': 'Expected a list of data objects',
            'timestamp': datetime.now().isoformat()
        }, to=sid)
        return

    now = datetime.now()
    location_objects = []

    try:
        for data in data_list:
            raw_date = data.get('date')
            raw_time = data.get('time')

            # Default to current time
            now = datetime.now()

            # Parse date
            try:
                parsed_date = parser.parse(raw_date).date() if raw_date else now.date()
            except Exception as e:
                parsed_date = now.date()  # fallback
                await sio.emit('update_location', {
                    'status': 'error',
                    'message': 'Parse date error',
                    'timestamp': datetime.now().isoformat()
                }, to=sid)
                print(f"⚠️ Date parsing error: {e}")
                return

            # Parse time
            try:
                parsed_time = parser.parse(raw_time).time() if raw_time else now.time()
            except Exception as e:
                parsed_time = now.time()  # fallback
                await sio.emit('update_location', {
                    'status': 'error',
                    'message': 'Parse date error',
                    'timestamp': datetime.now().isoformat()
                }, to=sid)
                print(f"⚠️ Time parsing error: {e}")
                return

            location_objects.append(LocationData(
                user_id=data.get('user'),
                socket_id=sid,
                latitude=data.get('lat'),
                longitude=data.get('long'),
                timestamp=now,
                date=parsed_date,
                time = parsed_time
            ))

        # ⚡ Perform bulk insert (efficient single query)
        await sync_to_async(LocationData.objects.bulk_create, thread_sensitive=True)(location_objects)

        print(f"✅ Inserted {len(location_objects)} location records to DB")

        # Emit success response back to the sender

        await sio.emit('update_location', {
            'status': 'success',
            'message': f'{len(location_objects)} location records saved successfully',
            'timestamp': now.isoformat()
        }, to=sid)


        # 🔊 Broadcast data to all clients except sender
        await sio.emit('message', {'data': data_list}, skip_sid=sid)

    except Exception as e:
        print(f"❌ Error in bulk insert: {e}")
        await sio.emit('update_location', {
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }, to=sid)

# Bellow Commented Working Code For 1 Record At A Time.
'''
@sio.event
async def update_location(sid, data):
    print(f"Message from {sid}: {data}")

    try:
        # Wrap the ORM operation in sync_to_async
        await sync_to_async(LocationData.objects.create)(
            user_id=data.get('user'),
            socket_id=sid,
            latitude=data.get('lat'),
            longitude=data.get('long'),
            timestamp=datetime.now(),
            date=datetime.now().date(),
            time=datetime.now().time()
        )
        print("✅ Data saved to database!")

        # Emit a success confirmation back to the client
        await sio.emit('update_location', {
            'status': 'success',
            'message': 'Location data saved successfully',
            'timestamp': datetime.now().isoformat()
        }, to=sid)

    except Exception as e:
        print(f"❌ Error saving data: {e}")

        # Emit an error message back to the client
        await sio.emit('update_location', {
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }, to=sid)

    # Broadcast the message (unchanged)
    await sio.emit('message', {'data': data}, skip_sid=sid)
'''

# Export the ASGI application
application = app
