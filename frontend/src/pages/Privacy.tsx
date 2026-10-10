import ReactMarkdown from 'react-markdown';

import policy from '../content/privacy.md?raw';
import './Privacy.css';

/**
 * Privacy policy. Public (the app stores link to it), English only for now.
 * Edit src/content/privacy.md.
 */
// Put together at runtime so the address isn't one plain string in the
// public repo or the built JS, where spam bots harvest addresses.
const CONTACT_EMAIL = ['mat', 'pyfection.com'].join('@');

export default function Privacy() {
  return (
    <article className="privacy-page">
      <ReactMarkdown>{policy.split('{{contact_email}}').join(CONTACT_EMAIL)}</ReactMarkdown>
    </article>
  );
}
