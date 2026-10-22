/* Unsichtbare Same-Origin-Auslieferung für die unveränderten Vorlagen-Dateien. */
(() => {
  if (!('serviceWorker' in navigator)) return;
  window.addEventListener('load', async () => {
    try {
      const registration = await navigator.serviceWorker.register('/static/sw.js', {scope: '/'});
      const replacingVersion = !!registration.active;
      setInterval(() => registration.update().catch(() => {}), 30 * 60 * 1000);
      registration.addEventListener('updatefound', () => {
        const worker = registration.installing;
        if (!worker) return;
        worker.addEventListener('statechange', () => {
          if (worker.state === 'installed' && replacingVersion && navigator.serviceWorker.controller &&
              confirm('Neue Version der Lab Assistant App verfügbar. Jetzt laden?')) {
            window.location.reload();
          }
        });
      });
    } catch (error) {
      console.warn('[PWA] Service Worker konnte nicht registriert werden:', error);
    }
  });
  window.addEventListener('online', () => document.body.classList.remove('offline'));
  window.addEventListener('offline', () => document.body.classList.add('offline'));
})();
