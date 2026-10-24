// Every call goes to the local Python server. X-Ui is the CSRF guard it requires on POST.
async function post(path, body) {
  const res = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Ui': '1' },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
  return data;
}

// Streams one scan as Server-Sent Events. onEvent(kind, payload) fires per GMGN source,
// per agent step, and once more with the final result ('done') or a failure ('error').
export async function scan(chain, address, onEvent, signal) {
  const res = await fetch('/api/research/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Ui': '1' },
    body: JSON.stringify({ chain, address }),
    signal,
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error || `HTTP ${res.status}`);
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let end = buffer.indexOf('\n\n');
    while (end !== -1) {
      const frame = buffer.slice(0, end);
      buffer = buffer.slice(end + 2);
      let kind = 'message';
      let data = '';
      for (const line of frame.split('\n')) {
        if (line.startsWith('event: ')) kind = line.slice(7);
        else if (line.startsWith('data: ')) data += line.slice(6);
      }
      if (data) onEvent(kind, JSON.parse(data));
      end = buffer.indexOf('\n\n');
    }
  }
}

export const holderReport = (chain, address) => post('/api/holders', { chain, address, lang: 'en' });
