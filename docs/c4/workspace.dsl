/*
 * Model C4 systemu micro:bit Arcade Ranking (Structurizr DSL).
 * Na podstawie architektury narysowanej na tablicy podczas zajęć.
 *
 * Podgląd: wklej ten plik do edytora Structurizr DSL albo uruchom Structurizr Lite:
 *   docker run -it --rm -p 8080:8080 -v ${PWD}/docs/c4:/usr/local/structurizr structurizr/lite
 */
workspace "micro:bit Arcade Ranking" "Gra zręcznościowa na micro:bit z rankingiem online." {

    !identifiers hierarchical

    model {
        gracz = person "Gracz" "Gra na micro:bicie i sprawdza ranking w przeglądarce oraz na wyświetlaczu."

        arcade = softwareSystem "micro:bit Arcade Ranking" "Zapisuje identyfikator gracza i wynik w bazie online oraz pokazuje ranking na stronie WWW i na fizycznym wyświetlaczu." {

            gra = container "Gra" "Gra zręcznościowa. Po rozgrywce wysyła identyfikator gracza (PID) i wynik (SCORE)." "micro:bit, MakeCode"

            bramka = container "Bramka wyników" "Odbiera dane z micro:bita, zamienia bity na obiekt wyniku i wysyła go do Web API." "Arduino + Wi-Fi, C++" {
                odbiornik = component "Odbiornik danych" "Odbiera surowe bajty wysłane przez micro:bita." "C++, Serial / radio"
                konwerter = component "Konwerter bit → klasa" "Zamienia odebrane bity na obiekt wyniku: ID (GUID), SCORE (INT), TIMESTAMP (DATETIME)." "C++"
                klientHttp = component "Klient HTTP" "Zamienia obiekt na JSON i wysyła go do Web API." "C++, Wi-Fi, HTTPClient"
            }

            webApi = container "Web API" "CRUD wyników. GameController: POST AddScore zapisuje wynik, GET zwraca listę wyników." "C#, ASP.NET Core" {
                gameController = component "GameController" "POST AddScore(GUID, INT, DT) zapisuje wynik. GET zwraca List<GameScore> jako JSON." "Kontroler ASP.NET Core"
                repozytorium = component "Repozytorium wyników" "Zapis i odczyt wyników w bazie danych (operacje CRUD)." "C#, Entity Framework Core"
            }

            baza = container "Baza danych" "Tabela wyników z kolumnami ID, PID, SCORE, TS." "Relacyjna baza SQL" {
                tags "Database"
            }

            wyswietlacz = container "Wyświetlacz rankingu" "Pobiera ranking z Web API i pokazuje Top 10 na wyświetlaczu." "Arduino + OLED/LCD, C++"

            www = container "Strona WWW z rankingiem" "Pobiera wyniki przez fetch() i wyświetla ranking online." "JavaScript, przeglądarka"
        }

        # Relacje ludzi z systemem
        gracz -> arcade.gra "Gra w grę"
        gracz -> arcade.www "Sprawdza ranking" "HTTPS"
        gracz -> arcade.wyswietlacz "Ogląda Top 10"

        # Zapis wyniku
        arcade.gra -> arcade.bramka.odbiornik "Przesyła PID i wynik" "radio / UART"
        arcade.bramka.odbiornik -> arcade.bramka.konwerter "Przekazuje bajty"
        arcade.bramka.konwerter -> arcade.bramka.klientHttp "Przekazuje obiekt wyniku"
        arcade.bramka.klientHttp -> arcade.webApi.gameController "Wysyła wynik: POST AddScore(GUID, INT, DT)" "HTTP, JSON"
        arcade.webApi.gameController -> arcade.webApi.repozytorium "Zapisuje i pobiera wyniki"
        arcade.webApi.repozytorium -> arcade.baza "Zapisuje i odczytuje wyniki" "SQL"

        # Odczyt rankingu
        arcade.www -> arcade.webApi.gameController "Pobiera listę wyników: fetch() → GET" "HTTP, JSON"
        arcade.wyswietlacz -> arcade.webApi.gameController "Pobiera Top 10: GET" "HTTP, JSON"
    }

    views {
        systemContext arcade "C1-Kontekst" "Kto korzysta z systemu i z czym system się łączy." {
            include *
            autoLayout tb
        }

        container arcade "C2-Kontenery" "Z jakich uruchamialnych części składa się system." {
            include *
            autoLayout tb
        }

        component arcade.webApi "C3-WebAPI" "Komponenty kontenera Web API." {
            include *
            autoLayout tb
        }

        component arcade.bramka "C3-Bramka" "Komponenty bramki wyników (Arduino)." {
            include *
            autoLayout lr
        }

        dynamic arcade "Dynamiczny" "Zapis wyniku i odczyt rankingu." {
            gracz -> arcade.gra "Gra i kończy rozgrywkę"
            arcade.gra -> arcade.bramka "Wysyła PID i wynik"
            arcade.bramka -> arcade.webApi "POST AddScore(GUID, INT, DT)"
            arcade.webApi -> arcade.baza "Zapisuje wynik (INSERT)"
            gracz -> arcade.www "Otwiera ranking"
            arcade.www -> arcade.webApi "fetch(): GET listy wyników"
            arcade.wyswietlacz -> arcade.webApi "Cyklicznie: GET Top 10"
            arcade.webApi -> arcade.baza "Odczytuje wyniki (SELECT … ORDER BY SCORE DESC)"
            autoLayout tb
        }

        styles {
            element "Person" {
                shape Person
                background #08427b
                color #ffffff
            }
            element "Software System" {
                background #1168bd
                color #ffffff
            }
            element "Container" {
                background #438dd5
                color #ffffff
            }
            element "Component" {
                background #85bbf0
                color #000000
            }
            element "Database" {
                shape Cylinder
            }
        }
    }
}
