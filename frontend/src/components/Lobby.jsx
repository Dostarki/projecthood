import { useMemo, useState } from 'react';
import { ArrowRight, Check, ChevronRight, Crosshair, ShieldAlert, UserRound, LoaderCircle } from 'lucide-react';
import { Button } from './ui/button';
import { getWeaponPreviews } from '../game/weaponPreviews';
import { WEAPONS } from '../game/config';
export { WEAPONS } from '../game/config';

export const Lobby = ({ weapon, setWeapon, start, mode, ready, error }) => {
  const [name, setName] = useState(() => localStorage.getItem('deadzone-name') || 'Gezgin');
  const previews = useMemo(getWeaponPreviews, []);
  const selected = WEAPONS.find(w => w.id === weapon);
  const submit = e => { e.preventDefault(); localStorage.setItem('deadzone-name', name); start(name, weapon); };
  return <section className="lobby" data-testid="lobby-panel">
    <div className="lobby-heading"><div className="eyebrow" data-testid="game-eyebrow"><span className="red-tick" /> WESTFALL <span className="eyebrow-slash">/</span> HAZIRLIK</div><h1 className="loadout-title" data-testid="game-title">SİLAHINI SEÇ</h1></div>
    <form onSubmit={submit} className="loadout-form">
      <label className="section-label" htmlFor="nickname" data-testid="nickname-label"><span>01</span> ÇAĞRI ADIN</label>
      <div className="nickname-field"><UserRound size={16} /><input id="nickname" data-testid="nickname-input" autoComplete="nickname" minLength={2} maxLength={18} required value={name} onChange={e => setName(e.target.value)} placeholder="Çağrı adını gir" /><span className="field-status">HAZIR <i className="status-dot" /></span></div>
      <div className="section-label weapon-label" data-testid="weapon-selection-label"><span>02</span> SİLAHINI SEÇ <small>{String(WEAPONS.length).padStart(2,'0')} SİLAH MEVCUT</small></div>
      <div className="weapon-grid" role="radiogroup" aria-label="Başlangıç silahı">
        {WEAPONS.map((w, index) => <button type="button" key={w.id} role="radio" aria-checked={weapon === w.id} className={`weapon-card ${weapon === w.id ? 'selected' : ''}`} onClick={() => setWeapon(w.id)} data-testid={`weapon-card-${w.id}`}>
          <span className="weapon-card-top"><span className="weapon-name">{w.name}</span><span className="weapon-index">{weapon === w.id ? <Check size={12} strokeWidth={3} /> : `0${index+1}`}</span></span>
          <img data-testid={`weapon-preview-${w.id}`} src={previews[w.id]} alt={`${w.name} silahının 3D modeli`} draggable="false" />
          <span className="weapon-card-bottom"><span>{w.type}</span><span>{w.mag} <span className="ammo-glyph">▰</span></span></span>
        </button>)}
      </div>
      <div className="weapon-specs" data-testid="selected-weapon-stats"><div><span>HASAR</span><div className="stat-track"><i style={{ width: `${Math.min(100, selected.damage*2)}%` }} /></div><b>{selected.damage}</b></div><div><span>ATIŞ HIZI</span><div className="stat-track"><i style={{ width: `${selected.speed}%` }} /></div><b>{selected.speed}</b></div><div><span>MENZİL</span><div className="stat-track"><i style={{ width: `${selected.range}%` }} /></div><b>{selected.range}m</b></div></div>
      <div className="friendly-warning" data-testid="friendly-fire-warning"><ShieldAlert size={15} /><span>Dost ateşi açık.</span><span>Kime güvendiğine dikkat et.</span></div>
      {error && <p className="form-error" role="alert" data-testid="connection-error">{error}</p>}
      <Button className="start-button" type="submit" data-testid="join-game-button" disabled={!ready || mode === 'connecting'}><span className="start-icon">{mode === 'connecting' ? <LoaderCircle className="spin" /> : <Crosshair />}</span><span className="start-copy">{mode === 'connecting' ? 'BAĞLANILIYOR' : 'OYUNA KATIL'}<small>WESTFALL–01</small></span><ArrowRight size={22} /></Button>
      <div className="lobby-under-button" data-testid="lobby-mode"><span className="status-dot" /> HERKES TEK <span>•</span> AÇIK DÜNYA <ChevronRight size={12} /></div>
    </form>
  </section>;
};