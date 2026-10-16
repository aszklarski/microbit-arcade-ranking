# Opis zadania

Robimy grę zręcznościową na platformie Microbit. Wynik i identyfikator użytkownika ma być przesyłany online => zapisywany w bazie, ranking ma być dostępny online webowo i na fizycznym urządzeniu. Do dyspozycji mamy Microbity i Arduino. Wybór narzędzi typu bazy danych, frameworki, protokoły komunikacyjne, chmury, wirtualizacja dowolne.

# Architektura

- micro:bit + MakeCode – tutaj działa sama gra.
- Arduino z Wi-Fi + Arduino C++ – odbiera wynik z micro:bita i wysyła go do Internetu.
- UART – „kabelek do rozmowy” między micro:bitem a Arduino.
- Wi-Fi + HTTPS/REST API – sposób, w jaki Arduino wysyła wynik do Internetu.
- Supabase + PostgreSQL – miejsce w Internecie, gdzie zapamiętujemy graczy i wyniki.
- React + Vite – robimy w tym stronę WWW z rankingiem.
- OLED/LCD podłączony do Arduino – pokazuje ranking na fizycznym urządzeniu.
- Vercel – może darmowo hostować naszą stronę WWW.
