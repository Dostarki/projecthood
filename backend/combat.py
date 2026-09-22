import math
import random
import uuid
from world import WEAPONS, wall_distance


def targets(game):
    return list(game.zombies.values())+list(game.players.values())


def hurt(game,target,amount,owner,now):
    if target['hp'] <= 0 or target.get('protected_until',0)>now: return
    target['hp'] = max(0,target['hp']-amount)
    if target['hp'] > 0: return
    zombie = target.get('zombie',False)
    if owner and owner['id'] != target['id']:
        owner['kills' if zombie else 'pvp'] += 1
        owner['score'] += 100 if zombie else 25
    game.events.append({'type':'kill','owner':owner['id'] if owner else '', 'name':owner['name'] if owner else 'Ateş', 'target':'Enfekte' if zombie else target['name'],'x':target['x'],'z':target['z'],'zombie':zombie})
    if not zombie:
        target['killer'] = owner['name'] if owner else 'Ateş'
        target['died_at'] = now
        game.persist(target)
    elif owner and owner['kills']%3 == 0:
        game.drops.append({'id':target['id'],'x':target['x'],'z':target['z'],'expires':now+90})


def explode(game,projectile,now):
    x,z = projectile['x'],projectile['z']
    owner = game.players.get(projectile['owner'])
    if projectile['kind'] == 'lava':
        game.fires.append({'id':projectile['id'],'x':x,'z':z,'r':3.8,'until':now+8,'owner':projectile['owner'],'last_damage':0})
        radius,damage = 2.8,45
    else: radius,damage = 8,220
    game.events.append({'type':'explosion','kind':projectile['kind'],'x':x,'z':z,'r':radius,'owner':projectile['owner']})
    for e in targets(game):
        distance = math.hypot(e['x']-x,e['z']-z)
        if distance < radius and wall_distance(x,z,e['x'],e['z']) > .95:
            hurt(game,e,round(damage*(1-distance/radius*.7)),owner,now)


def update_projectiles(game,dt,now):
    for projectile in list(game.projectiles):
        step = min(projectile['remaining'],projectile['speed']*dt)
        x,z = projectile['x'],projectile['z']
        nx,nz = x+projectile['dx']*step,z+projectile['dz']*step
        fraction = wall_distance(x,z,nx,nz)
        # Stop just in front of the surface so the explosion is on the visible side.
        projectile['x'],projectile['z'] = x+(nx-x)*max(0,fraction-.02),z+(nz-z)*max(0,fraction-.02)
        projectile['remaining'] -= step
        impact = fraction < 1 or projectile['remaining'] <= .01
        if projectile['kind'] == 'rocket':
            for e in targets(game):
                if e['id'] == projectile['owner'] or e['hp'] <= 0: continue
                vx,vz = e['x']-x,e['z']-z
                along = max(0,min(step,vx*projectile['dx']+vz*projectile['dz']))
                if math.hypot(vx-along*projectile['dx'],vz-along*projectile['dz'])<.9:
                    projectile['x'],projectile['z']=x+along*projectile['dx'],z+along*projectile['dz']; impact=True; break
        if impact:
            explode(game,projectile,now); game.projectiles.remove(projectile)
    for fire in list(game.fires):
        if now>=fire['until']: game.fires.remove(fire); continue
        if now-fire['last_damage'] < .35: continue
        fire['last_damage']=now
        for e in targets(game):
            if math.hypot(e['x']-fire['x'],e['z']-fire['z'])<fire['r'] and wall_distance(fire['x'],fire['z'],e['x'],e['z'])>.95:
                hurt(game,e,8,game.players.get(fire['owner']),now)


def shoot(game,p,now):
    w = WEAPONS[p['weapon']]
    if p['reload_until'] or p['ammo']<=0 or now-p['last_shot']<w['rate']-.005: return
    p['last_shot']=now; p['ammo']-=1
    dx,dz=math.sin(p['angle']),math.cos(p['angle'])
    if w['kind'] in ('rocket','lava'):
        reach = w['range'] if w['kind']=='rocket' else min(w['range'],max(3,p.get('aim_distance',20)))
        projectile={'id':uuid.uuid4().hex[:10],'kind':w['kind'],'owner':p['id'],'x':p['x'],'z':p['z'],'dx':dx,'dz':dz,'speed':45 if w['kind']=='rocket' else 24,'remaining':reach,'total':reach}
        game.projectiles.append(projectile)
        game.events.append({'type':'shot','kind':w['kind'],'weapon':p['weapon'],'owner':p['id'],'x':p['x'],'z':p['z'],'tx':p['x']+dx*reach,'tz':p['z']+dz*reach,'hit':False})
    elif w['kind']=='flame':
        reach=w['range']*wall_distance(p['x'],p['z'],p['x']+dx*w['range'],p['z']+dz*w['range'])
        game.events.append({'type':'shot','kind':'flame','weapon':p['weapon'],'owner':p['id'],'x':p['x'],'z':p['z'],'tx':p['x']+dx*reach,'tz':p['z']+dz*reach,'hit':False})
        for e in targets(game):
            if e['id']==p['id'] or e['hp']<=0: continue
            ex,ez=e['x']-p['x'],e['z']-p['z']; along=ex*dx+ez*dz
            if 0<along<reach and abs(ex*dz-ez*dx)<.7+along*.25 and wall_distance(p['x'],p['z'],e['x'],e['z'])>.95:
                hurt(game,e,w['damage'],p,now)
    else:
        for _ in range(w['pellets']):
            angle=p['angle']+random.uniform(-w['spread'],w['spread']);dx,dz=math.sin(angle),math.cos(angle)
            reach=w['range']*wall_distance(p['x'],p['z'],p['x']+dx*w['range'],p['z']+dz*w['range'])
            target,nearest=None,reach
            for e in targets(game):
                if e['id']==p['id'] or e['hp']<=0 or e.get('protected_until',0)>now: continue
                ex,ez=e['x']-p['x'],e['z']-p['z']; along=ex*dx+ez*dz
                if 0<along<nearest and abs(ex*dz-ez*dx)<.72: target,nearest=e,along
            game.events.append({'type':'shot','kind':'bullet','weapon':p['weapon'],'owner':p['id'],'x':p['x'],'z':p['z'],'tx':p['x']+dx*nearest,'tz':p['z']+dz*nearest,'hit':target is not None})
            if target: hurt(game,target,w['damage'],p,now)
    if p['ammo']==0 and p['reserve']: p['reload_until']=now+w['reload']