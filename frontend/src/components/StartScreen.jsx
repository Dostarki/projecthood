import { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { Button } from './ui/button';
import './StartScreen.css';

const fragment = `
  precision highp float;
  uniform float uTime; uniform vec2 uResolution;
  varying vec2 vUv;
  float hash(vec2 p) { return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453); }
  float noise(vec2 p) { vec2 i=floor(p), f=fract(p); f=f*f*(3.-2.*f); return mix(mix(hash(i),hash(i+vec2(1.,0.)),f.x),mix(hash(i+vec2(0.,1.)),hash(i+vec2(1.)),f.x),f.y); }
  float fbm(vec2 p) { float f=0., a=.5; for(int i=0;i<5;i++){ f+=a*noise(p); p=mat2(.8,-.6,.6,.8)*p*2.02; a*=.51; } return f; }
  void main(){
    vec2 uv=vUv; vec2 p=(uv-.5)*vec2(uResolution.x/uResolution.y,1.)*2.8;
    float t=uTime*.07;
    vec2 q=vec2(fbm(p+vec2(t,.2)),fbm(p+vec2(4.8,1.3)-t*.6));
    vec2 r=vec2(fbm(p+2.5*q+vec2(1.7,9.2)+t*.7),fbm(p+2.8*q+vec2(8.3,2.8)-t*.4));
    float f=fbm(p+3.5*r); float silk=pow(.5+.5*sin(p.x*2.4+p.y*1.4+f*7.+t),3.);
    vec3 c=mix(vec3(.018,.045,.031),vec3(.13,.25,.17),smoothstep(.15,.85,f));
    c=mix(c,vec3(.28,.39,.25),silk*.52);
    float streak=pow(clamp(1.-abs(f-.52)*5.,0.,1.),8.);
    c+=streak*vec3(.032,.067,.041);
    float vignette=smoothstep(1.35,.12,length((uv-.5)*vec2(1.2,1.)));
    c*=.6+.4*vignette;
    c+=(hash(gl_FragCoord.xy+floor(uTime*12.))-.5)*.014;
    gl_FragColor=vec4(c,1.);
  }
`;

export const StartScreen = ({ onStart }) => {
  const host = useRef(null);
  useEffect(() => {
    let renderer, frame;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: false, powerPreference: 'low-power', preserveDrawingBuffer: true });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1)); renderer.domElement.setAttribute('data-testid', 'start-background-canvas'); renderer.domElement.setAttribute('aria-hidden', 'true'); host.current.appendChild(renderer.domElement);
      const uniforms = { uTime: { value: 0 }, uResolution: { value: new THREE.Vector2() } };
      const scene = new THREE.Scene(), camera = new THREE.Camera();
      const geometry = new THREE.PlaneGeometry(2, 2), material = new THREE.ShaderMaterial({ uniforms, vertexShader: 'varying vec2 vUv; void main(){vUv=uv;gl_Position=vec4(position,1.);}', fragmentShader: fragment });
      scene.add(new THREE.Mesh(geometry, material));
      const resize = () => { const w = host.current.clientWidth, h = host.current.clientHeight; renderer.setSize(w, h); uniforms.uResolution.value.set(w,h); }; resize();
      const observer = new ResizeObserver(resize); observer.observe(host.current);
      const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      const started = performance.now(); let previous = 0;
      const tick = now => { if (now-previous > 32) { uniforms.uTime.value = reduced ? 0 : (now-started)/1000; renderer.render(scene,camera); previous=now; } frame=requestAnimationFrame(tick); }; frame=requestAnimationFrame(tick);
      return () => { cancelAnimationFrame(frame); observer.disconnect(); geometry.dispose(); material.dispose(); renderer.dispose(); renderer.forceContextLoss(); renderer.domElement.remove(); };
    } catch (e) { renderer?.dispose(); }
  }, []);
  return <section className="start-screen" data-testid="start-screen"><div className="start-atmosphere" ref={host} /><Button className="intro-start-button" data-testid="start-game-button" onClick={onStart}>START GAME</Button></section>;
};