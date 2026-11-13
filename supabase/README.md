# Baza danych i API w Supabase

Baza wyników i ranking działają w Supabase (PostgreSQL). API to wbudowane REST API Supabase,
więc nie trzeba pisać ani utrzymywać osobnego serwera. Całą bazę tworzy jeden plik SQL:
[migrations/20261113120000_ranking.sql](migrations/20261113120000_ranking.sql).

## Baza

| Tabela | Kolumny | Opis |
|---|---|---|
| `players` | `pid`, `nick`, `created_at` | Gracze. `pid` to numer seryjny micro:bita, `nick` wpisuje się ręcznie. |
| `scores` | `id`, `pid`, `score`, `ts` | Wyniki gier, kolumny jak na tablicy. `ts` wpisuje baza. |
| `ranking` (widok) | `rank`, `pid`, `nick`, `score`, `ts` | Najlepszy wynik każdego gracza, posortowany. |

Snake na planszy 5×5 daje najwyżej 23 punkty, więc baza przyjmuje wyniki od 0 do 23.
Przy remisie wyżej w rankingu jest ten, kto zdobył wynik wcześniej.

## Uruchomienie

1. Załóż darmowy projekt na [supabase.com](https://supabase.com) (region w Europie, np. Frankfurt).
2. Otwórz **SQL Editor**, wklej całą zawartość pliku migracji i kliknij **Run**.
3. Skopiuj adres projektu (Project URL, `https://<projekt>.supabase.co`) i klucz publiczny
   (Publishable key `sb_publishable_…` albo stary klucz `anon`). Oba są w ustawieniach projektu,
   w sekcji API Keys, i pod przyciskiem **Connect**.
4. Sprawdź API:

   ```bash
   SUPABASE_URL=https://<projekt>.supabase.co SUPABASE_KEY=sb_publishable_... node supabase/test-api.mjs
   ```

   Test zapisuje jeden wynik graczowi o PID 1. Usuniesz go w SQL Editor:
   `delete from public.players where pid = 1;`

Klucz publiczny może trafić do Arduino i na stronę WWW. Klucza tajnego (`sb_secret_…` albo `service_role`)
nie wpisuj nigdzie poza panelem Supabase, bo omija wszystkie zabezpieczenia.

## API

Każde żądanie musi mieć nagłówek `apikey: <klucz publiczny>`.
Stary klucz `anon` wymaga dodatkowo nagłówka `Authorization: Bearer <klucz>`.

### Zapis wyniku (bramka wyników, Arduino)

Odpowiednik `AddScore` z tablicy. Gracz zakłada się sam przy pierwszym wyniku.

```bash
curl -X POST "https://<projekt>.supabase.co/rest/v1/rpc/add_score" \
  -H "apikey: <klucz publiczny>" \
  -H "Content-Type: application/json" \
  -d '{"pid": -1234567890, "score": 7}'
```

Odpowiedź `200`:

```json
{"id": "8f91a89c-b698-4d4b-a8de-5729e5d2e470", "pid": -1234567890, "score": 7, "ts": "2026-11-13T17:41:10.529Z"}
```

Wynik spoza zakresu 0–23 daje odpowiedź `400`.

micro:bit wysyła po grze wiersz `WYNIK;-1234567890;7`. Arduino dzieli go po średnikach i wysyła
`{"pid": <druga część>, "score": <trzecia część>}`. Supabase działa tylko po HTTPS, więc Arduino
potrzebuje klienta TLS (na ESP32/ESP8266 `WiFiClientSecure`, na Arduino UNO R4 WiFi `WiFiSSLClient`).

### Ranking Top 10 (wyświetlacz, strona WWW)

```bash
curl "https://<projekt>.supabase.co/rest/v1/ranking?order=rank&limit=10" \
  -H "apikey: <klucz publiczny>"
```

Odpowiedź `200`:

```json
[
  {"rank": 1, "pid": -1234567890, "nick": "Adrian", "score": 12, "ts": "2026-11-13T17:41:10.612Z"},
  {"rank": 2, "pid": 42, "nick": null, "score": 12, "ts": "2026-11-13T17:41:10.640Z"}
]
```

Wyświetlacz może pobrać mniej danych: `ranking?select=rank,nick,pid,score&order=rank&limit=10`.

Na stronie WWW:

```js
const res = await fetch(`${SUPABASE_URL}/rest/v1/ranking?order=rank&limit=10`, {
  headers: { apikey: SUPABASE_KEY },
});
const ranking = await res.json();
```

### Wszystkie wyniki

Odpowiednik `GET List<GS>` z tablicy:

```bash
curl "https://<projekt>.supabase.co/rest/v1/scores?order=ts.desc" -H "apikey: <klucz publiczny>"
```

Filtrowanie po graczu: `scores?pid=eq.-1234567890&order=ts.desc`.

## Zabezpieczenia

Klucz publiczny pozwala tylko na:

- zapis wyniku przez `rpc/add_score` (z kontrolą zakresu wyniku),
- odczyt `ranking`, `scores` i `players`.

Bezpośrednie dodawanie, zmiana i usuwanie wierszy w tabelach są zablokowane (`401`/`403`).
Wyniki i nicki poprawia się w panelu Supabase (Table Editor albo SQL Editor), np.:

```sql
update public.players set nick = 'Ala' where pid = -1234567890;
```

Kto zna klucz publiczny, może wysłać wymyślony wynik. W projekcie szkolnym to akceptujemy.
