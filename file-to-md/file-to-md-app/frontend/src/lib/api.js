const API_BASE = '/api';

export async function convertFile(file) {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE}/convert/file`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Error desconocido' }));
    throw new Error(err.detail || `Error ${res.status}`);
  }

  return res.json();
}

export async function convertUrl(url) {
  const res = await fetch(`${API_BASE}/convert/url`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Error desconocido' }));
    throw new Error(err.detail || `Error ${res.status}`);
  }

  return res.json();
}

export async function convertHtml(html) {
  const res = await fetch(`${API_BASE}/convert/html`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ html }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Error desconocido' }));
    throw new Error(err.detail || `Error ${res.status}`);
  }

  return res.json();
}
