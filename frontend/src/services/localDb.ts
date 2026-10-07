/**
 * The app's IndexedDB database. Two stores:
 * - `outbox`: writes made offline, waiting to be sent (outbox.ts)
 * - `reads`: the last copy of each API read, for offline use (readCache.ts)
 *
 * These live in the app rather than the service worker because the iOS app
 * (WKWebView under capacitor://) can't run a service worker.
 */

const DB_NAME = 'nativo';
const VERSION = 2;
export type StoreName = 'outbox' | 'reads';

let dbPromise: Promise<IDBDatabase> | null = null;

export function openDb(): Promise<IDBDatabase> {
  dbPromise ??= new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, VERSION);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains('outbox')) {
        db.createObjectStore('outbox', { keyPath: 'id', autoIncrement: true });
      }
      if (!db.objectStoreNames.contains('reads')) {
        db.createObjectStore('reads', { keyPath: 'key' });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => {
      dbPromise = null;
      reject(request.error);
    };
  });
  return dbPromise;
}

/** Run one request in its own transaction; resolves once it's committed. */
export async function withStore<T>(
  name: StoreName,
  mode: IDBTransactionMode,
  run: (store: IDBObjectStore) => IDBRequest<T>,
): Promise<T> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(name, mode);
    const request = run(tx.objectStore(name));
    tx.oncomplete = () => resolve(request.result);
    tx.onerror = () => reject(tx.error);
    tx.onabort = () => reject(tx.error);
  });
}
