import asyncio
import contextlib
import logging
import os
import secrets
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field

from world import WORLD, WEAPONS
from engine import Game

load_dotenv(Path(__file__).parent / '.env')
client = AsyncIOMotorClient(os.environ['MONGO_URL'])
db = client[os.environ['DB_NAME']]
logging.basicConfig(level=logging.INFO)
log = logging.getLogger('deadzone')
pending = {}


async def save_score(player):
    if player['score'] <= 0:
        return
    doc = {k: player[k] for k in ('id', 'name', 'weapon', 'score', 'kills', 'pvp')}
    doc['ended_at'] = datetime.now(timezone.utc).isoformat()
    try:
        await db.scores.update_one({'id': doc['id']}, {'$set': doc}, upsert=True)
    except Exception:
        log.exception('Score persistence failed')


game = Game(save_score)


@asynccontextmanager
async def lifespan(app):
    await db.scores.create_index([('score', -1)])
    task = asyncio.create_task(game.run())
    yield
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task
    await asyncio.gather(*(save_score(p) for p in list(game.players.values())))
    client.close()


app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=os.environ['CORS_ORIGINS'].split(','), allow_methods=['*'], allow_headers=['*'])
app.add_middleware(GZipMiddleware, minimum_size=1000)


class JoinRequest(BaseModel):
    name: str = Field(min_length=2, max_length=18, pattern=r'^[\w .-]+$')
    weapon: str


class Score(BaseModel):
    id: str
    name: str
    weapon: str
    score: int
    kills: int
    pvp: int
    ended_at: str


@app.get('/api/')
async def root():
    return {'name': 'DEADZONE', 'status': 'online'}


@app.get('/api/status')
async def status():
    return {'online': len(game.players), 'capacity': 200, 'friendly_fire': True, 'map': 'Westfall', 'size': 1600, 'tick_rate': 20}


@app.get('/api/world')
async def world():
    return WORLD


@app.get('/api/weapons')
async def weapons():
    return WEAPONS


@app.get('/api/leaderboard', response_model=list[Score])
async def leaderboard():
    return await db.scores.find({}, {'_id': 0}).sort('score', -1).limit(20).to_list(20)


@app.post('/api/join')
async def join(body: JoinRequest):
    now = time.monotonic()
    for key in list(pending):
        if pending[key]['expires'] < now:
            pending.pop(key, None)
    if len(game.players) >= 200 or len(pending) >= 600:
        raise HTTPException(409, 'Sunucu dolu. Lütfen biraz sonra tekrar dene.')
    if body.weapon not in WEAPONS:
        raise HTTPException(422, 'Geçersiz silah.')
    if len(body.name.strip()) < 2:
        raise HTTPException(422, 'Çağrı adı en az 2 karakter olmalı.')
    token = secrets.token_urlsafe(24)
    pending[token] = {'name': body.name.strip(), 'weapon': body.weapon, 'expires': now + 60}
    return {'token': token}


@app.websocket('/api/ws/{token}')
async def websocket(ws: WebSocket, token: str):
    session = pending.pop(token, None)
    if not session or session['expires'] < time.monotonic() or len(game.players) >= 200:
        await ws.close(code=1008)
        return
    await ws.accept()
    player = game.add_player(session, ws)
    try:
        await ws.send_json({'type': 'welcome', 'id': player['id']})
        while True:
            data = await ws.receive_json()
            if not isinstance(data, dict):
                continue
            if data.get('type') == 'ping':
                await game.send(player, {'type': 'pong', 'time': data.get('time')})
            elif data.get('type') == 'input':
                game.set_input(player, data)
            elif data.get('type') == 'respawn' and player['hp'] <= 0:
                await save_score(player)
                game.respawn(player)
    except (WebSocketDisconnect, RuntimeError, ValueError):
        pass
    finally:
        game.players.pop(player['id'], None)
        await save_score(player)