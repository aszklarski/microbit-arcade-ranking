// Test API Supabase dla micro:bit Arcade Ranking (Node 18+).
//
// Bash:       SUPABASE_URL=https://xxxx.supabase.co SUPABASE_KEY=sb_publishable_... node supabase/test-api.mjs
// PowerShell: $env:SUPABASE_URL="https://xxxx.supabase.co"; $env:SUPABASE_KEY="sb_publishable_..."; node supabase/test-api.mjs
//
// Test zapisuje jeden wynik graczowi o PID 1. Usuniesz go w SQL Editor:
//   delete from public.players where pid = 1;

const url = process.env.SUPABASE_URL?.replace(/\/+$/, '');
const key = process.env.SUPABASE_KEY;
if (!url || !key) {
    console.error('Ustaw zmienne SUPABASE_URL i SUPABASE_KEY (publiczny klucz projektu).');
    process.exit(2);
}

const headers = { apikey: key, 'Content-Type': 'application/json' };
if (!key.startsWith('sb_')) headers.Authorization = `Bearer ${key}`;  // stary klucz anon (JWT)

const TEST_PID = 1;
let failures = 0;
const check = (ok, msg) => {
    console.log(ok ? 'OK  ' : 'BŁĄD', msg);
    if (!ok) failures++;
};

async function call(method, path, body) {
    const res = await fetch(`${url}/rest/v1/${path}`, {
        method,
        headers,
        body: body === undefined ? undefined : JSON.stringify(body),
    });
    const text = await res.text();
    let data = text;
    try { data = JSON.parse(text); } catch { /* odpowiedź nie jest JSON-em */ }
    return { status: res.status, data };
}

const saved = await call('POST', 'rpc/add_score', { pid: TEST_PID, score: 5 });
check(saved.status === 200 && saved.data?.score === 5 && saved.data?.id,
      `zapis wyniku: POST rpc/add_score → ${saved.status} ${JSON.stringify(saved.data)}`);

const ranking = await call('GET', 'ranking?order=rank&limit=10');
check(ranking.status === 200 && Array.isArray(ranking.data),
      `ranking Top 10: GET ranking → ${ranking.status}, ${Array.isArray(ranking.data) ? ranking.data.length : 0} wierszy`);
if (Array.isArray(ranking.data)) console.table(ranking.data);

const mine = await call('GET', `scores?pid=eq.${TEST_PID}&order=ts.desc`);
check(mine.status === 200 && Array.isArray(mine.data) && mine.data.some(r => r.id === saved.data?.id),
      `lista wyników: GET scores → ${mine.status}, zapisany wynik jest na liście`);

const invalid = await call('POST', 'rpc/add_score', { pid: TEST_PID, score: 99 });
check(invalid.status === 400, `wynik 99 odrzucony → ${invalid.status} ${invalid.data?.message ?? ''}`);

for (const [method, path, body, label] of [
    ['POST', 'scores', { pid: TEST_PID, score: 23 }, 'bezpośredni zapis do scores'],
    ['PATCH', `scores?pid=eq.${TEST_PID}`, { score: 23 }, 'zmiana wyniku'],
    ['DELETE', `scores?pid=eq.${TEST_PID}`, undefined, 'usunięcie wyników'],
    ['PATCH', `players?pid=eq.${TEST_PID}`, { nick: 'haker' }, 'zmiana nicku'],
]) {
    const res = await call(method, path, body);
    check(res.status === 401 || res.status === 403, `${label} zablokowany → ${res.status}`);
}

console.log(failures === 0 ? '\nAPI działa i jest zabezpieczone.' : `\nNieudane testy: ${failures}`);
process.exit(failures === 0 ? 0 : 1);
