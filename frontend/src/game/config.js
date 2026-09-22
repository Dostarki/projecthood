export const WEAPONS = [
  {id:'ak47',name:'AK-47',type:'TAARRUZ TÜFEĞİ',tag:'KLASİK GÜÇ',damage:35,speed:71,range:72,mag:30,rate:.10,kind:'bullet'},
  {id:'ak117',name:'AK-117',type:'TAARRUZ TÜFEĞİ',tag:'YÜKSEK ATIŞ HIZI',damage:26,speed:95,range:62,mag:35,rate:.075,kind:'bullet'},
  {id:'ak107',name:'AK-107',type:'TAARRUZ TÜFEĞİ',tag:'DENGELİ GERİ TEPME',damage:30,speed:87,range:82,mag:30,rate:.09,kind:'bullet'},
  {id:'shotgun',name:'AA-12',type:'OTOMATİK AV TÜFEĞİ',tag:'YAKIN MESAFE',damage:126,speed:26,range:25,mag:8,rate:.30,kind:'bullet'},
  {id:'m4',name:'M4A1',type:'TAARRUZ TÜFEĞİ',tag:'HASSAS ATIŞ',damage:28,speed:90,range:85,mag:30,rate:.085,kind:'bullet'},
  {id:'rocket',name:'RPG-7',type:'ROKETATAR',tag:'PATLAYICI BAŞLIK',damage:220,speed:9,range:110,mag:1,rate:1.1,kind:'rocket'},
  {id:'minigun',name:'M134',type:'MINIGUN',tag:'KESİNTİSİZ ATEŞ',damage:16,speed:100,range:75,mag:150,rate:.05,kind:'bullet'},
  {id:'flamethrower',name:'ALEV-21',type:'ALEV PÜSKÜRTÜCÜ',tag:'YAKIN MESAFE ALEVİ',damage:9,speed:71,range:9,mag:100,rate:.10,kind:'flame'},
  {id:'lava',name:'LAV-6',type:'LAV FIRLATICI',tag:'YERDE KALAN ATEŞ',damage:45,speed:15,range:40,mag:6,rate:.65,kind:'lava'},
];
export const WEAPON_MAP = Object.fromEntries(WEAPONS.map(w=>[w.id,w]));