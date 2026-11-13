-- micro:bit Arcade Ranking: baza wyników i API w Supabase (PostgreSQL).
--
-- API to wbudowane REST API Supabase (PostgREST):
--   POST /rest/v1/rpc/add_score   {"pid": -1234567890, "score": 7}   zapis wyniku
--   GET  /rest/v1/ranking         najlepszy wynik każdego gracza
--   GET  /rest/v1/scores          wszystkie wyniki
-- Publiczny klucz (anon / publishable) pozwala tylko zapisać wynik przez add_score i czytać dane.

-- Gracze. PID to numer seryjny micro:bita (control.deviceSerialNumber(), liczba 32-bitowa ze znakiem).
create table public.players (
    pid        bigint primary key,
    nick       text check (char_length(nick) between 1 and 20),
    created_at timestamptz not null default now()
);

comment on table public.players is 'Gracze. PID to numer seryjny micro:bita, nick wpisuje się ręcznie w panelu Supabase.';

-- Wyniki: kolumny jak na tablicy (ID, PID, SCORE, TS).
-- Snake na planszy 5x5 startuje z dwoma polami, więc da się zjeść najwyżej 23 punkty.
create table public.scores (
    id    uuid primary key default gen_random_uuid(),
    pid   bigint not null references public.players (pid) on delete cascade,
    score integer not null check (score between 0 and 23),
    ts    timestamptz not null default now()
);

comment on table public.scores is 'Wyniki gier. Godzinę (ts) wpisuje baza, bo Arduino nie ma zegara.';

create index scores_pid_score_idx on public.scores (pid, score desc, ts);

-- Zabezpieczenia: wszyscy mogą czytać, nikt z publicznym kluczem nie może pisać wprost do tabel.
alter table public.players enable row level security;
alter table public.scores enable row level security;

create policy "Każdy może czytać graczy"
    on public.players for select
    to anon, authenticated
    using (true);

create policy "Każdy może czytać wyniki"
    on public.scores for select
    to anon, authenticated
    using (true);

revoke all on public.players, public.scores from anon, authenticated;
grant select on public.players, public.scores to anon, authenticated;

-- Zapis wyniku (odpowiednik AddScore z tablicy). Zakłada gracza, jeśli jeszcze go nie ma.
-- Działa z uprawnieniami właściciela (security definer), więc omija blokadę zapisu do tabel.
create function public.add_score(pid bigint, score integer)
returns public.scores
language plpgsql
security definer
set search_path = ''
as $$
#variable_conflict use_column
declare
    new_score public.scores;
begin
    if add_score.score is null or add_score.score < 0 or add_score.score > 23 then
        raise exception 'Nieprawidłowy wynik: % (dozwolone 0–23)', add_score.score
            using errcode = '22023';
    end if;

    insert into public.players (pid)
    values (add_score.pid)
    on conflict (pid) do nothing;

    insert into public.scores (pid, score)
    values (add_score.pid, add_score.score)
    returning * into new_score;

    return new_score;
end;
$$;

comment on function public.add_score(bigint, integer) is 'Zapisuje wynik gracza. Wywołanie: POST /rest/v1/rpc/add_score {"pid": ..., "score": ...}';

revoke execute on function public.add_score(bigint, integer) from public, anon, authenticated;
grant execute on function public.add_score(bigint, integer) to anon, authenticated;

-- Ranking: najlepszy wynik każdego gracza. Przy remisie wyżej jest ten, kto zdobył wynik wcześniej.
create view public.ranking
with (security_invoker = true)
as
select
    rank() over (order by best.score desc, best.ts) as rank,
    best.pid,
    p.nick,
    best.score,
    best.ts
from (
    select distinct on (s.pid) s.pid, s.score, s.ts
    from public.scores s
    order by s.pid, s.score desc, s.ts
) as best
join public.players p on p.pid = best.pid;

comment on view public.ranking is 'Ranking: najlepszy wynik każdego gracza. Top 10: GET /rest/v1/ranking?order=rank&limit=10';

revoke all on public.ranking from anon, authenticated;
grant select on public.ranking to anon, authenticated;
