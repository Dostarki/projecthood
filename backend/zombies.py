import math
import random
from world import move, wall_distance


def update_zombies(game,living,dt,now):
    for zid,z in list(game.zombies.items()):
        if z['hp']<=0: game.zombies.pop(zid,None); continue
        if living and min(math.hypot(p['x']-z['x'],p['z']-z['z']) for p in living)>125:
            game.zombies.pop(zid,None); continue
        candidates=[p for p in living if not p['awaiting_input'] and p['hp']>0 and math.hypot(p['x']-z['x'],p['z']-z['z'])<=5 and wall_distance(z['x'],z['z'],p['x'],p['z'])>.98]
        if candidates:
            target=min(candidates,key=lambda p:(p['x']-z['x'])**2+(p['z']-z['z'])**2)
            dx,dz=target['x']-z['x'],target['z']-z['z'];distance=math.hypot(dx,dz)
            z['mode']='attack';z['angle']=math.atan2(dx,dz)
            if distance>1.25: move(z,dx/max(distance,1)*2.5*dt,dz/max(distance,1)*2.5*dt)
            elif now-z['last_attack']>.95 and now>target['protected_until']:
                target['hp']=max(0,target['hp']-12);z['last_attack']=now
                if target['hp']==0:
                    target['killer']='Enfekte';target['died_at']=now;game.persist(target)
        else:
            # Losing the five-metre proximity immediately ends pursuit.
            if z.get('mode')=='attack' or now>z.get('wander_until',0):
                z['mode']='wander' if random.random()>.32 else 'idle'
                z['angle']=random.uniform(0,math.tau);z['wander_until']=now+random.uniform(2.5,6)
            if z['mode']=='wander':
                before=(z['x'],z['z'])
                move(z,math.sin(z['angle'])*.55*dt,math.cos(z['angle'])*.55*dt)
                if math.hypot(z['x']-before[0],z['z']-before[1])<.001:
                    z['angle']+=1.4;z['wander_until']=now+1.5