import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { bakeMeshes } from './batching';
import { createWeapon } from './weapons';
export { createWeapon } from './weapons';

const materials = new Map();
export const material = (color, roughness = .85) => {
  const key = `${color}-${roughness}`;
  if (!materials.has(key)) materials.set(key, roughness < .6 ? new THREE.MeshStandardMaterial({ color, roughness, metalness: .55 }) : new THREE.MeshLambertMaterial({ color }));
  return materials.get(key);
};
export function box(group, x, y, z, w, h, d, color, roughness) {
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), typeof color === 'object' ? color : material(color, roughness));
  mesh.position.set(x, y, z); mesh.castShadow = true; mesh.receiveShadow = true; group.add(mesh); return mesh;
}
export function cylinder(group, x, y, z, radius, height, color, sides = 8) {
  const mesh = new THREE.Mesh(new THREE.CylinderGeometry(radius, radius, height, sides), material(color));
  mesh.position.set(x, y, z); mesh.castShadow = true; group.add(mesh); return mesh;
}

function rounded(group, x,y,z,w,h,d,color,radius=.04) {
  const m=new THREE.Mesh(new RoundedBoxGeometry(w,h,d,2,radius), material(color)); m.position.set(x,y,z); m.castShadow=true; m.receiveShadow=true; group.add(m); return m;
}
function limb(group,x,y,z,radius,length,color,scaleZ=1) {
  const m=new THREE.Mesh(new THREE.CapsuleGeometry(radius,Math.max(.01,length-radius*2),4,10),material(color));m.position.set(x,y,z);m.scale.z=scaleZ;m.castShadow=true;group.add(m);return m;
}
function mergeBody(group) {
  const meshes=group.children.filter(c=>c.isMesh&&!c.material.transparent),baked=bakeMeshes(meshes);
  meshes.forEach(m=>{group.remove(m);m.geometry.dispose();});baked.forEach(m=>group.add(m));
}

export function createHuman(zombie = false, variant = 0, weaponType = 'ak47') {
  const g = new THREE.Group();
  const shirt = zombie ? ['#647753', '#6c493f', '#687c7d', '#807859', '#394e55'][variant % 5] : '#687761';
  const skin = zombie ? '#9b9e7b' : '#cba883';
  const pants = zombie ? '#40463f' : '#303a35';
  const legs = [],knees=[];
  for (const side of [-1, 1]) {
    const pivot = new THREE.Group(); pivot.position.set(side*.17, .93, 0); g.add(pivot);
    limb(pivot, 0, -.20, 0, .145, .44, pants,.95);
    const knee=new THREE.Group();knee.position.y=-.39;pivot.add(knee);knees.push(knee);
    limb(knee, 0, -.16, 0, .12, .40, pants,1.1);
    rounded(knee, 0, -.40, .06, .28, .21, .44, '#212820', .07); legs.push(pivot);
  }
  limb(g, 0, 1.26, 0, .34, .77, shirt, .65);
  rounded(g,0,.90,0,.57,.24,.37,pants,.09);
  if (!zombie) {
    rounded(g, 0, 1.25, .21, .57, .53, .13, '#3a483d', .05);
    for (const x of [-.19, 0, .19]) rounded(g, x, 1.2, .31, .15, .22, .09, '#4a594a', .015);
    rounded(g, 0, 1.24, -.26, .45, .6, .26, '#414a36', .08);
    box(g, 0, .88, 0, .67, .095, .44, '#282d26');
  } else {
    box(g, -.1, 1.32, .205, .19, .26, .009, '#663b30');
  }
  const head = new THREE.Mesh(new THREE.SphereGeometry(.24, 16, 12), material(skin));
  head.scale.set(.86, 1.18, .95); head.position.y = 1.95; head.castShadow = true; g.add(head);
  limb(g, 0, 1.69, 0, .085, .18, skin);
  rounded(g,0,1.94,.218,.065,.09,.065,skin,.021);
  for(const side of [-1,1]){
    limb(g,side*.211,1.965,0,.042,.10,skin,.5);
    rounded(g,side*.088,2.014,.208,.058,.024,.018,'#282d26',.006);
  }
  if (!zombie) {
    const helmet = new THREE.Mesh(new THREE.SphereGeometry(.27, 20, 12, 0, Math.PI*2, 0, Math.PI*.59), material('#3b4738'));
    helmet.position.set(0, 2, -.015); g.add(helmet);
    box(g, 0, 2.0, .21, .36, .085, .07, '#232d2b');
  } else {
    const hair=new THREE.Mesh(new THREE.SphereGeometry(.242,14,8,0,Math.PI*2,0,Math.PI*.45),material('#43453a'));hair.position.set(0,2.02,-.025);g.add(hair);
    for (const x of [-.09, .09]) box(g, x, 1.98, .213, .046, .035, .015, '#d5bb68');
  }
  const arms = [];
  for (const side of [-1, 1]) {
    const arm = new THREE.Group(); arm.position.set(side*.43, 1.49, .03); arm.rotation.x = zombie ? -1.15 : -1.2; g.add(arm);
    limb(arm,0,-.18,0,.115,.36,shirt,1.05);
    limb(arm,0,-.395,0,.085,.22,skin,1.04);
    rounded(arm,0,-.51,.017,.15,.13,.19,skin,.045); arms.push(arm);
  }
  if (!zombie) {
    const gun = createWeapon(weaponType); gun.position.set(.24, 1.35, .55); gun.scale.setScalar(.88); g.add(gun); g.userData.gun = gun;
    arms[0].rotation.z = -.3; arms[1].rotation.z = .16;
  }
  const shadow = new THREE.Mesh(new THREE.CircleGeometry(.7, 20), new THREE.MeshBasicMaterial({ color: '#0c140b', transparent: true, opacity: .3, depthWrite: false }));
  shadow.rotation.x = -Math.PI/2; shadow.position.y = .025; g.add(shadow);
  g.userData.legs = legs;g.userData.knees=knees; g.userData.arms = arms; g.userData.zombie = zombie;g.userData.phase=0;g.userData.blend=0;g.userData.gunRest=new THREE.Vector3(.24,1.35,.55);
  mergeBody(g); legs.forEach(mergeBody);knees.forEach(mergeBody); arms.forEach(mergeBody);
  return g;
}

export function animateHuman(g,time,moving,running=false,dt=1/60,direction=0){
  const u=g.userData,zombie=u.zombie;u.blend+=(Number(moving)-u.blend)*(1-Math.exp(-dt*16));
  u.phase+=dt*(zombie?5:running?14.5:10.5);const amplitude=(zombie?.35:running?.82:.52)*u.blend;
  u.legs.forEach((leg,i)=>{const phase=u.phase+i*Math.PI,wave=Math.sin(phase);leg.rotation.x=wave*amplitude;leg.rotation.y=Math.sin(direction)*.5*u.blend;leg.rotation.z=Math.sin(direction)*wave*.18*u.blend;u.knees[i].rotation.x=-Math.max(0,-wave)*(running?1.1:.64)*u.blend;});
  g.position.y=(1-Math.cos(u.phase*2))*(running?.025:.013)*u.blend;g.rotation.x=(zombie?.045:running?.085:.015)*u.blend;
  if(zombie)u.arms.forEach((arm,i)=>{arm.rotation.x=-1.05+Math.sin(u.phase+i*Math.PI)*.14*u.blend;});
  if(u.gun){const recoil=u.recoil||0;u.recoil=recoil*Math.exp(-dt*22);u.gun.position.copy(u.gunRest);u.gun.position.z-=recoil*.085;u.gun.position.y+=Math.sin(u.phase*2)*.01*u.blend;u.gun.rotation.x=-recoil*.085+(running?.08:0);}
}