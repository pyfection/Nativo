import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import authService, { ApiToken, CreatedApiToken } from '../services/authService';
import { API_URL } from '../services/api';
import './ApiTokens.css';

const MCP_URL = `${API_URL.replace(/\/$/, '')}/mcp`;

function CopyButton({ value }: { value: string }) {
  const { t } = useTranslation();
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard blocked (e.g. insecure origin) — the value is still selectable.
    }
  };

  return (
    <button type="button" className="api-tokens-copy" onClick={copy}>
      {copied ? t('api_tokens.copied') : t('api_tokens.copy')}
    </button>
  );
}

export default function ApiTokens() {
  const { t, i18n } = useTranslation();
  const [tokens, setTokens] = useState<ApiToken[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [name, setName] = useState('');
  const [creating, setCreating] = useState(false);
  const [created, setCreated] = useState<CreatedApiToken | null>(null);

  useEffect(() => {
    authService
      .listApiTokens()
      .then(setTokens)
      .catch(() => setError(t('api_tokens.load_failed')))
      .finally(() => setLoading(false));
  }, [t]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setCreating(true);
    try {
      const token = await authService.createApiToken(name.trim());
      setCreated(token);
      setTokens((prev) => [token, ...prev]);
      setName('');
    } catch (err: any) {
      setError(err.response?.data?.detail || t('api_tokens.create_failed'));
    } finally {
      setCreating(false);
    }
  };

  const handleRevoke = async (token: ApiToken) => {
    if (!window.confirm(t('api_tokens.revoke_confirm', { name: token.name }))) return;
    setError('');
    try {
      await authService.revokeApiToken(token.id);
      setTokens((prev) => prev.filter((tk) => tk.id !== token.id));
      if (created?.id === token.id) setCreated(null);
    } catch {
      setError(t('api_tokens.revoke_failed'));
    }
  };

  const formatDate = (iso: string) =>
    new Date(iso.endsWith('Z') ? iso : `${iso}Z`).toLocaleDateString(i18n.language, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });

  const secret = created?.token ?? '<token>';
  const claudeCodeCommand = `claude mcp add --transport http nativo ${MCP_URL} --header "Authorization: Bearer ${secret}"`;

  return (
    <div className="api-tokens-page">
      <header className="api-tokens-header">
        <h1>{t('api_tokens.title')}</h1>
        <p className="api-tokens-subtitle">{t('api_tokens.subtitle')}</p>
      </header>

      {error && <div className="error-message">{error}</div>}

      <section className="api-tokens-section">
        <h2 className="api-tokens-section-title">{t('api_tokens.connect_heading')}</h2>
        <p className="api-tokens-hint">{t('api_tokens.connect_hint')}</p>
        <div className="api-tokens-code-row">
          <code className="api-tokens-code">{MCP_URL}</code>
          <CopyButton value={MCP_URL} />
        </div>
        <p className="api-tokens-hint">{t('api_tokens.claude_code_hint')}</p>
        <div className="api-tokens-code-row">
          <code className="api-tokens-code">{claudeCodeCommand}</code>
          <CopyButton value={claudeCodeCommand} />
        </div>
      </section>

      <section className="api-tokens-section">
        <h2 className="api-tokens-section-title">{t('api_tokens.create_heading')}</h2>
        <form className="api-tokens-form" onSubmit={handleCreate}>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder={t('api_tokens.name_placeholder')}
            aria-label={t('api_tokens.name_label')}
            maxLength={100}
            required
          />
          <button type="submit" className="api-tokens-create" disabled={creating || !name.trim()}>
            {creating ? t('api_tokens.creating') : t('api_tokens.create')}
          </button>
        </form>

        {created && (
          <div className="api-tokens-created" role="status">
            <p>{t('api_tokens.created_notice')}</p>
            <div className="api-tokens-code-row">
              <code className="api-tokens-code">{created.token}</code>
              <CopyButton value={created.token} />
            </div>
          </div>
        )}
      </section>

      <section className="api-tokens-section">
        <h2 className="api-tokens-section-title">{t('api_tokens.list_heading')}</h2>
        {loading && <div className="loading-state">{t('api_tokens.loading')}</div>}
        {!loading && tokens.length === 0 && (
          <p className="api-tokens-empty">{t('api_tokens.empty')}</p>
        )}
        <ul className="api-tokens-list">
          {tokens.map((token) => (
            <li key={token.id} className="api-tokens-item">
              <div className="api-tokens-item-main">
                <span className="api-tokens-item-name">{token.name}</span>
                <code className="api-tokens-item-prefix">{token.token_prefix}…</code>
              </div>
              <div className="api-tokens-item-meta">
                {t('api_tokens.created_on', { date: formatDate(token.created_at) })}
                {' · '}
                {token.last_used_at
                  ? t('api_tokens.last_used', { date: formatDate(token.last_used_at) })
                  : t('api_tokens.never_used')}
              </div>
              <button
                type="button"
                className="api-tokens-revoke"
                onClick={() => handleRevoke(token)}
              >
                {t('api_tokens.revoke')}
              </button>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
