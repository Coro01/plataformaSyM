// control_horas/static/sw.js

// Este es un Service Worker básico. 
// Para funcionalidad avanzada (caché, offline), se necesitaría lógica adicional.

self.addEventListener('fetch', function(event) {
    // Si estás sirviendo todos los archivos en línea,
    // simplemente omite la lógica de caché por ahora.
    // Esto asegura que la PWA se registre sin errores de Service Worker.
});

self.addEventListener('install', function(event) {
    // El Service Worker se ha instalado.
    console.log('[Service Worker] Instalado.');
});

self.addEventListener('activate', function(event) {
    // El Service Worker se ha activado.
    console.log('[Service Worker] Activado.');
});