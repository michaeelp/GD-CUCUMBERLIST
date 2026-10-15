export const PLAYERS = ['thiaguinhio','michaeelp','nzrv'] as const;
export type Player = typeof PLAYERS[number];
export const PLAYER_META: Record<Player,{color:string;accountId:string|null;gdName:string|null}> = {
  thiaguinhio:{color:'#baff35',accountId:'18823987',gdName:'thiaguinhio'},
  michaeelp:{color:'#62e8ff',accountId:'24854395',gdName:'michaeelp'},
  nzrv:{color:'#e4a0ff',accountId:'13334739',gdName:'Nzrvv'}
};
export const FIREBASE_CONFIG = {
  apiKey:'AIzaSyBfw2hIsXKxU3z7d11pa2uPVFPfRQcyQe4',
  authDomain:'gd-cucumberlist.firebaseapp.com',
  databaseURL:'https://gd-cucumberlist-default-rtdb.firebaseio.com',
  projectId:'gd-cucumberlist',
  storageBucket:'gd-cucumberlist.firebasestorage.app',
  messagingSenderId:'243319547284',
  appId:'1:243319547284:web:d6100b0f2177b3ebab5b81'
};
export const SHEET_URL = 'https://docs.google.com/spreadsheets/d/1qKlWKpDkOpU1ZF6V6xGfutDY2NvcA8MNPnsv6GBkKPQ/gviz/tq?tqx=out:json&gid=0';
export const FORMS=['cube','ship','ball','ufo','wave','robot','spider','swing','jetpack'] as const;
