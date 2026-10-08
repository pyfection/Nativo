import { useSyncExternalStore } from 'react';
import axios, { AxiosRequestConfig } from 'axios';
import api from './api';
import { withStore } from './localDb';

/**
 * Offline outbox. A write that opts in (`outbox` on its request config) and
 * fails because there is no network is saved in IndexedDB instead, and the
 * request rejects with `QueuedOffline` so the page can say "saved, will be
 * sent later". Saved writes are replayed in order, as the user who made them,
 * when the browser is back online. The token is added at send time, so a
 * token that expired while offline just means "log in again", not lost work.
 *
 * Opt in only for writes whose page handles `QueuedOffline`.
 */

declare module 'axios' {
  interface AxiosRequestConfig {
    /** Save this write for later if the network is down. `label` names it
     *  in the offline banner; `key` lets a page recognise its own pending
     *  items (Quick Contribute hides cards that are already answered). */
    outbox?: { label: string; key?: string };
  }
}

export type OutboxConfig = Pick<AxiosRequestConfig, 'outbox'>;

export class QueuedOffline extends Error {
  constructor() {
    super('Saved offline; will be sent when back online');
    this.name = 'QueuedOffline';
  }
}

interface OutboxItem {
  id?: number;
  userId: string;
  label: string;
  key?: string;
  method: string;
  url: string;
  params?: unknown;
  /** JSON body as sent, or FormData entries (Blobs survive IndexedDB). */
  body?: string;
  form?: [string, FormDataEntryValue][];
  createdAt: number;
}

export interface OutboxFailure {
  label: string;
  detail: string;
}

interface OutboxState {
  online: boolean;
  pending: number;
  pendingKeys: ReadonlySet<string>;
  sending: boolean;
  failures: OutboxFailure[];
}

const RETRY_MS = 60_000;

let userId: string | null = null;
let flushing = false;
let state: OutboxState = {
  online: typeof navigator === 'undefined' ? true : navigator.onLine,
  pending: 0,
  pendingKeys: new Set(),
  sending: false,
  failures: [],
};
const listeners = new Set<() => void>();

function setState(patch: Partial<OutboxState>) {
  state = { ...state, ...patch };
  listeners.forEach((listener) => listener());
}

/** No response at all: offline, DNS, server unreachable. */
export function isNetworkError(error: unknown): boolean {
  return axios.isAxiosError(error) && !error.response && error.code !== 'ERR_CANCELED';
}

async function myItems(): Promise<OutboxItem[]> {
  if (!userId) return [];
  const all = await withStore<OutboxItem[]>('outbox', 'readonly', (store) => store.getAll());
  return all.filter((item) => item.userId === userId).sort((a, b) => a.id! - b.id!);
}

async function refresh() {
  try {
    const items = await myItems();
    setState({
      pending: items.length,
      pendingKeys: new Set(items.flatMap((item) => (item.key ? [item.key] : []))),
    });
  } catch {
    // IndexedDB unavailable (private mode on some browsers): nothing queued.
  }
}

// ---------- Queue + replay ----------

/** Save a failed request. Resolves false when it can't be saved. */
export async function enqueue(config: AxiosRequestConfig): Promise<boolean> {
  if (!userId || !config.outbox || !config.url) return false;
  const item: OutboxItem = {
    userId,
    label: config.outbox.label,
    key: config.outbox.key,
    method: (config.method ?? 'post').toLowerCase(),
    url: config.url,
    params: config.params,
    createdAt: Date.now(),
  };
  if (config.data instanceof FormData) item.form = Array.from(config.data.entries());
  else if (typeof config.data === 'string') item.body = config.data;
  try {
    await withStore('outbox', 'readwrite', (store) => store.add(item));
  } catch {
    return false;
  }
  await refresh();
  return true;
}

function bodyOf(item: OutboxItem) {
  if (!item.form) return item.body;
  const form = new FormData();
  item.form.forEach(([name, value]) => form.append(name, value));
  return form;
}

/** Send saved writes, oldest first. Stops at the first one that can't go
 *  yet (offline, server error, expired login) and tries again later. */
export async function flush() {
  if (flushing || !userId || !navigator.onLine) return;
  flushing = true;
  setState({ sending: true });
  try {
    for (const item of await myItems()) {
      try {
        await api.request({
          method: item.method,
          url: item.url,
          params: item.params,
          data: bodyOf(item),
          headers: item.form ? { 'Content-Type': 'multipart/form-data' } : undefined,
        });
      } catch (error) {
        const status = axios.isAxiosError(error) ? error.response?.status : undefined;
        if (status === undefined || status >= 500 || [401, 408, 429].includes(status)) break;
        // The server refused it (already done, no permission, invalid):
        // retrying won't help, so drop it and tell the user.
        const detail = axios.isAxiosError(error) ? error.response?.data?.detail : undefined;
        setState({
          failures: [
            ...state.failures,
            { label: item.label, detail: typeof detail === 'string' ? detail : `HTTP ${status}` },
          ],
        });
      }
      await withStore('outbox', 'readwrite', (store) => store.delete(item.id!));
      await refresh();
    }
  } catch {
    // IndexedDB error: leave everything for the next attempt.
  } finally {
    flushing = false;
    setState({ sending: false });
    await refresh();
  }
}

/** Items belong to the user who made them and are only sent as that user. */
export function setOutboxUser(id: string | null) {
  if (id === userId) return;
  userId = id;
  setState({ failures: [] });
  void refresh().then(flush);
}

/** Drop the current user's unsent writes (their account is gone). */
export async function discardOutbox() {
  try {
    for (const item of await myItems()) {
      await withStore('outbox', 'readwrite', (store) => store.delete(item.id!));
    }
  } catch {
    // Nothing stored.
  }
  await refresh();
}

export function dismissFailures() {
  setState({ failures: [] });
}

if (typeof window !== 'undefined') {
  window.addEventListener('online', () => {
    setState({ online: true });
    void flush();
  });
  window.addEventListener('offline', () => setState({ online: false }));
  window.setInterval(() => {
    if (state.pending > 0) void flush();
  }, RETRY_MS);
}

// ---------- React ----------

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function useOutbox(): OutboxState {
  return useSyncExternalStore(subscribe, () => state);
}

/** Keys of writes still waiting, for pages that load before React renders. */
export function pendingKeys(): ReadonlySet<string> {
  return state.pendingKeys;
}
