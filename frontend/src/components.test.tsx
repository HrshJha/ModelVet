import { describe, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { formatBytes, shortDigest, stages } from './api';
import { Badge, Notice } from './components';

describe('local review presentation contracts', () => {
  it.each(['APPROVE', 'CONTROLS', 'BLOCK', 'INSUFFICIENT'])('labels %s without relying on color', state => {
    expect(renderToStaticMarkup(<Badge state={state} />)).toContain(state);
  });
  it('escapes hostile artifact text', () => {
    const html = renderToStaticMarkup(<Notice>{'<img src=x onerror=alert(1)>'}</Notice>);
    expect(html).not.toContain('<img');
    expect(html).toContain('&lt;img');
  });
  it('uses binary byte units and shortened identities', () => {
    expect(formatBytes(1024)).toBe('1.0 KiB');
    expect(shortDigest('sha256:' + 'a'.repeat(64))).toBe('a'.repeat(12));
    expect(stages).toHaveLength(9);
  });
});
