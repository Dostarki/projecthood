import asyncio
import logging
import math
import random
import time
import uuid
from world import WEAPONS, free, move, interior_at
from combat import shoot, update_projectiles
from zombies import update_zombies


class Game:
    def __init__(self, save_score):
        self.players, self.zombies = {}, {}
        self.events, self.drops = [], []
        self.projectiles, self.fires = [], []
        self.save_score = save_score
        self.counter = 0
        self.tasks = set()

    def persist(self, player):
        task = asyncio.create_task(self.save_score(dict(player)))
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)

    def add_player(self, session, ws):
        player = {'id': uuid.uuid4().hex[:12], 'name': session['name'], 'weapon': session['weapon'], 'ws': ws, 'lock': asyncio.Lock()}
        self.reset(player)
        self.players[player['id']] = player
        self.spawn_zombies(player, 12)
        return player

    def reset(self, p):
        now = time.monotonic()
        # Distribute newcomers across safe road intersections, keeping early players nearby.
        slot = len(self.players) // 8
        x = (slot % 5)*80 + random.uniform(-4, 4)
        z = (slot // 5)*80 + random.uniform(-4, 4)
        p.update(x=x, z=z, angle=0, hp=100, ammo=WEAPONS[p['weapon']]['mag'], reserve=WEAPONS[p['weapon']]['reserve'], aim_distance=20, vx=0, vz=0,
                 score=0, kills=0, pvp=0, stamina=100, reload_until=0, last_shot=0, killer='',
                 protected_until=now+12, awaiting_input=True, input_time=now, born=now, died_at=0, last_spawn=now, trigger=False,
                 controls={'x': 0, 'z': 0, 'fire': False, 'sprint': False})

    def respawn(self, p):
        old_id = p['id']
        p['id'] = uuid.uuid4().hex[:12]
        self.players.pop(old_id, None)
        self.reset(p)
        # Respawn away from the swarm that killed the player, not inside it.
        for ox, oz in [(0, 0), (80, 0), (-80, 0), (0, 80), (0, -80), (80, 80)]:
            x, z = p['x']+ox, p['z']+oz
            if free(x, z) and all(math.hypot(e['x']-x, e['z']-z) > 18 for e in self.zombies.values()):
                p['x'], p['z'] = x, z
                break
        self.players[p['id']] = p
        self.spawn_zombies(p, 8)

    def spawn_zombies(self, p, count):
        if len(self.zombies) >= 600:
            return
        for _ in range(count):
            angle, radius = random.uniform(0, 6.28), random.uniform(16, 42)
            x, z = p['x']+math.sin(angle)*radius, p['z']+math.cos(angle)*radius
            if free(x, z):
                self.counter += 1
                zid = f'z{self.counter}'
                self.zombies[zid] = {'id': zid, 'x': x, 'z': z, 'angle': 0, 'hp': 100,
                                     'zombie': True, 'variant': self.counter % 5, 'speed': .55, 'last_attack': 0, 'mode':'wander','wander_until':0}

    def set_input(self, p, data):
        try:
            x, z, angle = float(data.get('x', 0)), float(data.get('z', 0)), float(data.get('angle', 0))
            if not all(math.isfinite(v) for v in (x, z, angle)):
                return
        except (TypeError, ValueError, OverflowError):
            return
        length = max(1, math.hypot(x, z))
        p['controls'] = {'x': x/length, 'z': z/length, 'fire': data.get('fire') is True, 'sprint': data.get('sprint') is True}
        p['angle'] = angle % math.tau
        if data.get('fire_pressed') is True and data.get('fire') is True:p['trigger']=True
        try:
            distance=float(data.get('aim_distance',20))
            if math.isfinite(distance): p['aim_distance']=max(3,min(110,distance))
        except (ValueError,TypeError): pass
        p['input_time'] = time.monotonic()
        if p['awaiting_input'] and (abs(x)+abs(z) > .05 or data.get('fire') is True):
            p['awaiting_input'] = False
            p['born'] = p['input_time']
            p['protected_until'] = p['input_time']+12
            p['last_spawn'] = p['input_time']
        # Taking an offensive action cancels protection: no invulnerable firing.
        if data.get('fire') is True:
            p['protected_until'] = 0
        w = WEAPONS[p['weapon']]
        if data.get('reload') and not p['reload_until'] and p['ammo'] < w['mag'] and p['reserve'] > 0:
            p['reload_until'] = p['input_time']+w['reload']

    async def send(self, player, data):
        try:
            async with player['lock']:
                await asyncio.wait_for(player['ws'].send_json(data), .3)
        except Exception:
            with __import__('contextlib').suppress(Exception):
                await player['ws'].close()

    def update(self, dt, now):
        living = [p for p in self.players.values() if p['hp'] > 0]
        for p in living:
            if p['awaiting_input']:
                p['protected_until'] = now+12
            c = p['controls'] if now-p['input_time'] < .4 else {'x': 0, 'z': 0, 'fire': False, 'sprint': False}
            running = c['sprint'] and p['stamina'] > 1 and (abs(c['x'])+abs(c['z']) > 0)
            speed = 10 if running else 6
            p['vx'],p['vz']=c['x']*speed,c['z']*speed
            p['stamina'] = max(0, min(100, p['stamina']+(-22 if running else 13)*dt))
            move(p, c['x']*speed*dt, c['z']*speed*dt)
            if p['reload_until'] and now >= p['reload_until']:
                amount = min(WEAPONS[p['weapon']]['mag']-p['ammo'], p['reserve'])
                p['ammo'] += amount
                p['reserve'] -= amount
                p['reload_until'] = 0
            if c['fire'] or p['trigger']:
                shoot(self, p, now)
                p['trigger']=False
            if not p['awaiting_input'] and now-p['last_spawn'] > 35:
                nearby = sum((z['x']-p['x'])**2+(z['z']-p['z'])**2 < 3600 for z in self.zombies.values())
                if nearby < 14:
                    self.spawn_zombies(p, 4)
                p['last_spawn'] = now
            # Roadside resupply stations replenish ammo/health once per minute per player.
            sx, sz = round((p['x']-11)/80)*80+11, round(p['z']/80)*80
            if math.hypot(p['x']-sx, p['z']-sz) < 2.6 and now-p.get('supplied', -1000) > 60:
                w=WEAPONS[p['weapon']]
                p['reserve'] = min(w['reserve']*2, p['reserve']+w['mag']*3)
                p['hp'] = min(100, p['hp']+30)
                p['supplied'] = now
                self.events.append({'type': 'supply', 'owner': p['id']})
        update_zombies(self,living,dt,now)
        update_projectiles(self,dt,now)
        for drop in list(self.drops):
            picked = next((p for p in living if math.hypot(p['x']-drop['x'], p['z']-drop['z']) < 2), None)
            if picked:
                w=WEAPONS[picked['weapon']]
                picked['reserve'] = min(w['reserve']*2, picked['reserve']+w['mag'])
                picked['hp'] = min(100, picked['hp']+12)
                self.events.append({'type': 'supply', 'owner': picked['id']})
            if picked or drop['expires'] < now:
                self.drops.remove(drop)

    def snapshot(self, p, now):
        def close(e):
            return (e['x']-p['x'])**2+(e['z']-p['z'])**2 < 85**2
        def compact(e, fields):
            return {k: round(e[k], 2) if isinstance(e[k], float) else e[k] for k in fields}
        me = compact(p, ['id', 'name', 'weapon', 'x', 'z', 'angle', 'hp', 'ammo', 'reserve', 'score', 'kills', 'pvp', 'stamina', 'killer','vx','vz'])
        me['interior']=interior_at(p['x'],p['z'])
        me.update(reloading=max(0, p['reload_until']-now), protected=max(0, p['protected_until']-now), awaiting_input=p['awaiting_input'], survived=0 if p['awaiting_input'] else int((p['died_at'] or now)-p['born']))
        return {'type': 'state', 'me': me, 'online': len(self.players),
                'players': [compact(e, ['id', 'name', 'weapon', 'x', 'z', 'angle', 'hp']) for e in self.players.values() if e['id'] != p['id'] and close(e)],
                'zombies': [compact(e, ['id', 'x', 'z', 'angle', 'hp', 'variant','mode']) for e in self.zombies.values() if close(e)],
                'projectiles': [compact(e,['id','kind','owner','x','z','dx','dz','remaining','total']) for e in self.projectiles if close(e)],
                'fires': [{**compact(e,['id','x','z','r']), 'ttl':round(e['until']-now,2)} for e in self.fires if close(e)],
                'drops': [{k: e[k] for k in ('id', 'x', 'z')} for e in self.drops if close(e)],
                'events': [e for e in self.events if 'x' not in e or close(e)],
                'leaders': sorted([compact(e, ['id', 'name', 'score', 'kills', 'pvp']) for e in self.players.values()], key=lambda e: -e['score'])[:10]}

    async def run(self):
        previous = time.monotonic()
        while True:
            now = time.monotonic()
            dt, previous = min(now-previous, .1), now
            try:
                self.events = []
                self.update(dt, now)
                await asyncio.gather(*(self.send(p, self.snapshot(p, now)) for p in list(self.players.values())))
                if not self.players:
                    self.zombies.clear()
                    self.drops.clear()
                    self.projectiles.clear()
                    self.fires.clear()
            except Exception:
                logging.exception('World tick failed')
            await asyncio.sleep(max(.001, .05-(time.monotonic()-now)))