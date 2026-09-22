/* Network/input cadence runs independently of GPU work on the UI thread. */
let socket, pulse, heartbeat, publish, controls = { type: 'input', x: 0, z: 0, angle: 0, fire: false };
let latest, events = [], lastInput = 0;
const stop = () => { clearInterval(pulse); clearInterval(heartbeat); clearInterval(publish); };

self.onmessage = ({ data }) => {
  if (data.type === 'connect') {
    socket = new WebSocket(data.url);
    socket.onopen = () => {
      self.postMessage({ type: 'open' });
      pulse = setInterval(() => {
        if (socket.readyState !== 1) return;
        if (Date.now()-lastInput > 2500) controls = { ...controls, x: 0, z: 0, fire: false, reload: false };
        socket.send(JSON.stringify(controls)); controls.reload = false;
      }, 50);
      const ping = () => { if (socket.readyState === 1) socket.send(JSON.stringify({ type: 'ping', time: Date.now() })); };
      ping(); heartbeat = setInterval(ping, 2000);
      publish = setInterval(() => {
        if (latest) { self.postMessage({ type: 'state', ...latest, events }); latest = null; events = []; }
      }, 100);
    };
    socket.onmessage = e => {
      const m = JSON.parse(e.data);
      if (m.type === 'state') { latest = m; events.push(...m.events); if (events.length > 100) events = events.slice(-100); }
      else if (m.type === 'pong') self.postMessage({ type: 'ping', value: Date.now()-m.time });
      else self.postMessage(m);
    };
    socket.onclose = () => { stop(); self.postMessage({ type: 'close' }); };
    socket.onerror = () => self.postMessage({ type: 'error' });
  } else if (data.type === 'input') {
    const press=data.fire&&!controls.fire;
    controls = { ...data, reload: data.reload || controls.reload || false }; lastInput = Date.now();
    if(press&&socket?.readyState===1)socket.send(JSON.stringify({...controls,fire_pressed:true}));
  } else if (data.type === 'respawn') {
    if (socket?.readyState === 1) socket.send(JSON.stringify({ type: 'respawn' }));
  } else if (data.type === 'disconnect') {
    stop(); socket?.close();
  }
};