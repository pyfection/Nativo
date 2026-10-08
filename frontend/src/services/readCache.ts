import { withStore, openDb } from './localDb';

/**
 * Last copy of each API read (by full URL), so pages opened before still
 * work offline. The API client saves every successful GET and falls back to
 * the copy when the network is down (api.ts). Holds the signed-in user's own
 * data, so it is wiped when the session ends.
 */

const MAX_AGE_MS = 30 * 24 * 60 * 60 * 1000;

interface ReadEntry {
  key: string;
  data: unknown;
  savedAt: number;
}

export async function saveRead(key: string, data: unknown): Promise<void> {
  try {
    await withStore('reads', 'readwrite', (store) =>
      store.put({ key, data, savedAt: Date.now() } satisfies ReadEntry),
    );
  } catch {
    // Not keeping an offline copy is harmless.
  }
}

/** The saved copy, or undefined when there is none (or it's too old). */
export async function loadRead(key: string): Promise<{ data: unknown } | undefined> {
  try {
    const entry = await withStore<ReadEntry | undefined>('reads', 'readonly', (store) =>
      store.get(key),
    );
    if (entry && Date.now() - entry.savedAt < MAX_AGE_MS) return { data: entry.data };
  } catch {
    // IndexedDB unavailable: no offline copy.
  }
  return undefined;
}

export async function clearReads(): Promise<void> {
  try {
    await withStore('reads', 'readwrite', (store) => store.clear());
  } catch {
    // Nothing stored.
  }
}

/** Drop copies too old to serve, so the store doesn't grow forever. */
async function prune() {
  const db = await openDb();
  const tx = db.transaction('reads', 'readwrite');
  const cursorRequest = tx.objectStore('reads').openCursor();
  cursorRequest.onsuccess = () => {
    const cursor = cursorRequest.result;
    if (!cursor) return;
    if (Date.now() - (cursor.value as ReadEntry).savedAt >= MAX_AGE_MS) cursor.delete();
    cursor.continue();
  };
}

if (typeof indexedDB !== 'undefined') prune().catch(() => {});
