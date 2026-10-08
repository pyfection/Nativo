import ReactMarkdown from 'react-markdown';

import policy from '../content/privacy.md?raw';
import './Privacy.css';

/**
 * Privacy policy. Public (the app stores link to it), English only for now.
 * Edit src/content/privacy.md.
 */
export default function Privacy() {
  return (
    <article className="privacy-page">
      <ReactMarkdown>{policy}</ReactMarkdown>
    </article>
  );
}
