import {FIREBASE_CONFIG} from './config';
import {assetUrl} from './catalog-client';
let promise:Promise<any>|null=null;
export function getFirebase():Promise<any>{
  if(promise)return promise;
  promise=(async()=>{
    for(const name of ['app','database','auth']){
      await new Promise<void>((resolve,reject)=>{const script=document.createElement('script');script.src=assetUrl(`assets/vendor/firebase-${name}-compat.js`);script.onload=()=>resolve();script.onerror=()=>reject(Error('No se pudo cargar Firebase.'));window.document.head.appendChild(script);});
    }
    const fb=(window as any).firebase;
    if(!fb.apps.length)fb.initializeApp(FIREBASE_CONFIG);
    await fb.auth().setPersistence(fb.auth.Auth.Persistence.SESSION);
    return fb;
  })().catch(e=>{promise=null;throw e;});
  return promise;
}
