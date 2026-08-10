const CACHE='agrow-field-v3-camera'; const CORE=['/','/manifest.webmanifest','/assets/app.js','/assets/style.css','/assets/icons/icon-192.png','/assets/icons/icon-512.png'];
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(CORE))));
self.addEventListener('fetch',e=>{ if(e.request.method!=='GET') return; e.respondWith(fetch(e.request).then(r=>{const x=r.clone(); caches.open(CACHE).then(c=>c.put(e.request,x)); return r}).catch(()=>caches.match(e.request).then(r=>r||caches.match('/')))) });
