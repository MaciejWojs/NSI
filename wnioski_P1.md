# Sprawozdanie — zajęcia projektowe nr 1

**Pomiar niezawodności testowego oprogramowania (blok P1)**  
**Wariant SUT:** Zespół C  
**Repozytorium:** https://github.com/MaciejWojs/NSI.git

## 1. Zespół i repozytorium

Zespół pracuje przez cały semestr na jednym, wspólnym systemie testowanym. Kod, dokumentacja SUT i materiał z zajęć są w repozytorium Git:

https://github.com/MaciejWojs/NSI.git

Wariant przypisany zespołowi to plik `zespol_C.py`. Na tym repozytorium będą dokładane kolejne etapy projektu (testy strukturalne, funkcjonalne, analiza statyczna, modele wzrostu niezawodności). Dzisiejszy pomiar jest punktem odniesienia do tych porównań.

## 2. Odebrany system testowany

Od prowadzącego odebrano wariant C systemu zarządzania kontem bankowym, opisany w załączniku A do zajęć i w `sut_dokumentacja.pdf`.

System składa się z trzech elementów. `BankSystem` trzyma konta i udostępnia operacje. `Konto` trzyma numer, właściciela, saldo (`Decimal`), historię i status (`aktywne` albo `zablokowane`). `ZewnetrznyProcesor` symuluje izbę rozliczeniową dla przelewów poza system i z założenia bywa niedostępny (domyślnie około 30% wywołań). Tę niedostępność dokumentacja wyłącza z listy usterek do znalezienia: odporność na nią jest tematem bloku P5.

Operacje objęte testem: założenie konta, wpłata, wypłata, przelew wewnętrzny, przelew zewnętrzny, odsetki, dzienny limit wypłat (5000 zł, liczony łącznie dla wypłat i przelewów wychodzących), blokada i odblokowanie, historia w okresie, wyciąg miesięczny.

Numer konta ma 10 cyfr. Ostatnia cyfra jest sumą pierwszych dziewięciu modulo 10. W testach użyto numerów `1000000001`, `2000000002`, `3000000003`, `4000000004` i `5000000005`.

Kontrakt, wobec którego oceniano awarię, wzięto z dokumentacji API: zły numer i zła kwota kończą się `ValueError`, kwota niebędąca liczbą kończy się `TypeError`, brak konta kończy się `KontoNieIstnieje` (także wtedy, gdy przy przelewie nie istnieje jedno z kont), operacja obciążająca zablokowane konto kończy się `KontoZablokowane`, historia obejmuje obie daty graniczne, a wyciąg miesiąca podsumowuje operacje tego miesiąca. Awaria to odstępstwo od tego kontraktu widoczne na wyniku albo na wyjątku. Poprawne odrzucenie złych danych awarią nie jest.

Dotkliwość, stosowana dalej konsekwentnie: krytyczna, gdy saldo staje się ujemne albo przestaje być kwotą pieniężną; poważna, gdy funkcja daje zły wynik albo zły wyjątek, a reszta systemu działa; drobna, gdy skutek operacji jest dobry, a psuje się tylko komunikat.

## 3. Środowisko i podstawowe wywołania

SUT uruchomiono w wirtualnym środowisku `.venv` (Python 3.12), bez dodatkowych bibliotek. Wejście do systemu to `import zespol_C`.

Dziesięć wywołań ścieżki podstawowej przeszło bez wyjątku i ze zgodnym saldem.

Na koncie `1000000001` saldo początkowe wynosiło 1000 zł. Wpłata 200 zł dała 1200 zł, wypłata 150 zł dała 1050 zł, przelew 100 zł na drugie konto dał 950 zł. Odsetki 12% za jeden miesiąc: 950 × 0,01 = 9,50 zł, saldo 959,50 zł. Zaokrąglenie do groszy jest zgodne z kapitalizacją miesięczną opisaną w dokumentacji.

Historia od wczoraj do jutra zwróciła cztery wpisy z dziś: wpłatę, wypłatę, przelew wychodzący i odsetki. Wyciąg bieżącego miesiąca: wpływy 209,50 zł (200 + 9,50), wypływy 250 zł (150 + 100), saldo końcowe 959,50 zł. Zgadza się to z saldem. Blokada drugiego konta i następne odblokowanie zakończyły się bez błędu.

Wniosek z punktu 3: przy danych zwyczajnych SUT księguje, liczy odsetki i składa wyciąg poprawnie.

## 4. Mechanizm logowania awarii

W `zespol_C.py` jest dekorator `niezawodnosc_logger` z instrukcji zajęć. Zapisuje wyjątek do `awarie.jsonl` i rzuca go dalej, więc nie maskuje awarii. Każdy wpis zawiera znacznik czasu, nazwę funkcji, argumenty, typ wyjątku, komunikat i czas od wejścia w funkcję do wyjątku. Wywołanie, które się powiedzie, wpisu nie tworzy.

Dekorator owija wszystkie metody SUT: `Konto`, `BankSystem` i `ZewnetrznyProcesor`.

Sprawdzenie na sesji testowej wypadło zgodnie z tym opisem. Wyjątek widziany przez wywołującego jest tym samym obiektem, który trafia do pliku, a udana wpłata linii logu nie dodaje. Do powtórzenia awarii wystarczą pola `funkcja`, `args` i `komunikat`.

Dwie cechy loggera wpływają na wskaźniki, jeśli policzyć je wprost z pliku. Wyjątek idący przez dwie owinięte metody daje dwie linie: wpłata na brakujące konto zapisuje `_pobierz_konto` i `wplac`, awaria procesora zapisuje `wyslij_przelew` i `przelew_zewnetrzny`. Osobno, błędny wynik bez wyjątku w pliku nie powstaje. W serii z punktu 5 dotyczy to wypłaty z kwoty tekstowej, ujemnego salda, przelewu ponad dzienny limit, pustej historii, złego wyciągu i salda `Infinity`.

## 5. Wywołania eksploracyjne

Po ścieżce podstawowej wykonano jedną ciągłą serię 30 wywołań. W danych są przypadki wymagane w poleceniu: pusty napis, kwoty ujemne i zerowe, liczba bardzo duża (`10**9` oraz 1 000 001), znaki specjalne w numerze (`12-34 56/7`) oraz litery. Osobno sprawdzono brak konta, blokadę, limit dzienny, granice historii, wyciąg za inny miesiąc, wartości `True`, `NaN` i `+inf` oraz stopę procentową spoza zwykłego zakresu.

Czas w tabeli jest czasem od startu tej trzydziestki. „Zgodne” oznacza wynik albo wyjątek przewidziany w dokumentacji.

| Nr | t [ms] | Wywołanie | Wynik | Ocena |
| --- | ---: | --- | --- | --- |
| 1 | 0,00 | `utworz_konto("")` | `ValueError`: nieprawidłowy numer | zgodne |
| 2 | 0,30 | `utworz_konto("123")` | `ValueError`: nieprawidłowy numer | zgodne |
| 3 | 0,37 | `utworz_konto("abcdefghij")` | `ValueError`: nieprawidłowy numer | zgodne |
| 4 | 0,46 | `utworz_konto("12-34 56/7")` | `ValueError`: nieprawidłowy numer | zgodne |
| 5 | 0,57 | `utworz_konto` o 11 cyfrach | `ValueError`: nieprawidłowy numer | zgodne |
| 6 | 0,66 | drugi raz ten sam numer | `ValueError`: `Konto {numer} juz istnieje` | awaria drobna |
| 7 | 0,75 | wpłata −10 | `ValueError`: kwota musi być dodatnia | zgodne |
| 8 | 0,84 | wpłata 0 | `ValueError`: kwota musi być dodatnia | zgodne |
| 9 | 0,93 | wpłata `"100"` | `TypeError`: kwota musi być liczbą | zgodne |
| 10 | 1,02 | wpłata `None` | `TypeError`: kwota musi być liczbą | zgodne |
| 11 | 1,11 | wypłata 1 000 000 000 | `ValueError`: brak środków | zgodne |
| 12 | 1,20 | wypłata −5 | `ValueError`: kwota musi być dodatnia | zgodne |
| 13 | 1,29 | wypłata `"10"` | saldo 959,50 → 949,50 | awaria poważna |
| 14 | 1,31 | wpłata na niezałożone konto | `KontoNieIstnieje` | zgodne |
| 15 | 1,52 | przelew na niezałożone konto | `KeyError` | awaria poważna |
| 16 | 1,62 | przelew −1 | `ValueError`: kwota musi być dodatnia | zgodne |
| 17 | 1,71 | odsetki za 1,5 miesiąca | `TypeError` z `range` | awaria poważna |
| 18 | 1,80 | odsetki za −3 miesiące | zwrot salda 150, bez błędu i bez zmiany | awaria poważna |
| 19 | 1,81 | konto ze saldem początkowym −500 | konto powstaje | awaria krytyczna |
| 20 | 1,82 | wypłata z konta zablokowanego | `KontoZablokowane` z właściwym numerem | zgodne |
| 21 | 1,92 | przelew z konta zablokowanego | `KontoZablokowane`: `Konto {numer_z} jest zablokowane` | awaria drobna |
| 22 | 2,03 | wypłata 1 zł po wykorzystaniu 5000 zł | `ValueError`: limit dzienny | zgodne |
| 23 | 2,12 | przelew 100 zł po tym samym limicie | saldo 15 000 → 14 900, drugie konto +100 | awaria poważna |
| 24 | 2,13 | historia od dziś do dziś | pusta lista, choć tego dnia były operacje | awaria poważna |
| 25 | 2,14 | wyciąg za styczeń 2026 | wpływy stycznia 100 zł, saldo końcowe 14 900 zł | awaria poważna |
| 26 | 2,15 | wpłata `True` | `InvalidOperation` (`ConversionSyntax`) | awaria poważna |
| 27 | 2,24 | wpłata `NaN` | `InvalidOperation` | awaria poważna |
| 28 | 2,33 | wpłata `+inf` | saldo `Infinity` | awaria krytyczna |
| 29 | 2,35 | przelew 1 000 001 przy saldzie 2 000 000 | `ValueError`: limit systemowy, saldo bez zmian | zgodne |
| 30 | 2,44 | odsetki −2400% za 1 miesiąc | saldo −2 000 000,00 zł | awaria krytyczna |

Szesnaście wywołań zachowało się zgodnie z dokumentacją. Czternaście jest awariami. Poprawnie działają między innymi odrzucenie złego numeru, niedodatniej kwoty, napisu przy wpłacie, braku środków, braku konta przy wpłacie, wypłaty z konta zablokowanego, wypłaty ponad 5000 zł oraz przelewu ponad 1 000 000 zł.

Przelew zewnętrzny sprawdzono poza tą trzydziestką, ze sterowanym procesorem. Przy procesorze, który odpowiada, saldo spadło z 500 zł do 460 zł. Przy procesorze, który zawsze zgłasza `ProcesorNiedostepny`, saldo zostało 460 zł. Tych wyjątków nie wliczono do awarii SUT, bo dokumentacja opisuje je jako zamierzoną zawodność integracji.

Próba 20 równoległych wypłat po 100 zł z salda 1000 zł skończyła się saldem 0, dziesięcioma wpisami w historii i dziesięcioma odrzuceniami z braku środków. W tej próbie stan został spójny. Jedno przejście nie rozstrzyga, czy przy innym przeplocie wątków wypłata (bez blokady, którą dokumentacja podaje tylko przy przelewie) potrafi zepsuć saldo.

### Lista awarii z tej serii

Czternaście awarii sprowadza się do dziesięciu unikalnych przyczyn.

| Przyczyna | Typ objawu | Dotkliwość | Co widać na wywołaniu |
| --- | --- | --- | --- |
| Komunikat z literałem zamiast numeru | zły tekst błędu | drobna | Duplikat konta: `Konto {numer} juz istnieje`. Przelew z blokady: `Konto {numer_z} jest zablokowane`. Odrzucenie samej operacji jest prawidłowe. |
| Przelew przy braku konta docelowego | zły wyjątek | poważna | Wpłata na to samo niezałożone konto daje `KontoNieIstnieje`, przelew daje `KeyError`. |
| Wypłata przyjmuje kwotę tekstową | zły skutek | poważna | `wyplac(..., "10")` księguje 10 zł. Ta sama postać przy wpłacie jest odrzucana. |
| Zły wyjątek przy `True` i `NaN` | zły wyjątek | poważna | Zamiast `TypeError` albo `ValueError` wychodzi `InvalidOperation` z komunikatem modułu `decimal`. |
| Przelew omija dzienny limit 5000 zł | zły skutek | poważna | Po odrzuceniu wypłaty 1 zł przelew 100 zł przenosi środki na drugie konto. |
| Liczba miesięcy nie jest sprawdzana | zły wyjątek i cichy brak skutku | poważna | 1,5 miesiąca kończy się `TypeError`. −3 miesiące zwracają saldo bez zmian i bez błędu. |
| Saldo schodzi poniżej zera | zły stan konta | krytyczna | Konto powstaje z saldem −500 zł. Stopa −2400% za miesiąc z 2 000 000 zł daje −2 000 000,00 zł. Wypłata i przelew poniżej zera nie puszczają. |
| Historia w przedziale otwartym | zły wynik | poważna | Dokumentacja: obie daty włącznie. Okno \[dziś, dziś\] jest puste, choć tego dnia konto miało wypłatę i przelew. |
| Wyciąg podaje saldo bieżące | zły wynik | poważna | Styczeń: wpływy 100,00 zł i zero wypływów, a `saldo_koncowe` wynosi 14 900 zł, czyli saldo po operacjach z października. |
| Wpłata nieskończoności | zniszczone saldo | krytyczna | `wplac(+inf)` zostawia na koncie `Decimal('Infinity')`. |

## 6. Wstępne wskaźniki

Wskaźniki liczone są na serii 30 wywołań z punktu 5. Profil jest eksploracyjny: dużo danych skrajnych, mało powtórzeń ścieżki z punktu 3. Intensywność jest przez to wyższa niż przy zwykłej obsłudze konta. Do mianownika awarii wchodzi 14 odchyleń od kontraktu. Nie wchodzą do niego poprawne `ValueError` i `TypeError` ani zamierzone `ProcesorNiedostepny`.

Czas startuje w chwili pierwszego z tych 30 wywołań. Awaria nr 14 wypada po 2,44 ms. Odstępy między kolejnymi awariami, w milisekundach, liczone tak jak w przykładzie z instrukcji (pierwszy odstęp od startu serii):

0,658; 0,636; 0,222; 0,195; 0,093; 0,006; 0,108; 0,203; 0,013; 0,004; 0,011; 0,091; 0,094; 0,106.

Suma odstępów równa się czasowi ostatniej awarii, 2,44 ms.

MTTF = 2,44 ms / 14 = 0,17 ms.

Ta wartość jest średnią z serii puszczonej jedno wywołanie za drugim, bez czasu namysłu użytkownika. Nadaje się jako baseline metodyczny. Do porównania z eksploatacją banku nie nadaje się wprost, bo tam między operacjami są sekundy i minuty, a nie ułamki milisekundy. Przy kolejnych blokach ten sam wzór na tej samej trzydziestce pokaże, czy odstępy rosną.

Gęstość defektów liczy unikalne przyczyny, nie każde powtórzenie tej samej usterki. W `zespol_C.py` jest 174 linii kodu SUT po odjęciu pustych linii, komentarzy, docstringów i samego dekoratora loggera, czyli 0,174 KLOC.

Gęstość = 10 / 0,174 KLOC = 57,5 usterek/KLOC.

MTTR nie był mierzony, bo usterek dziś nie naprawiano. Z tej sesji nie wynika więc ani MTBF, ani dostępność.

| Wskaźnik | Wartość |
| --- | --- |
| Wywołania podstawowe (punkt 3) | 10, wszystkie zgodne |
| Wywołania eksploracyjne (punkt 5) | 30 |
| Awarie zaobserwowane | 14 |
| Unikalne przyczyny | 10 |
| MTTF | 2,44 ms / 14 = 0,17 ms |
| Gęstość defektów | 10 / 0,174 KLOC = 57,5 usterek/KLOC |

Surowe linie `awarie.jsonl` dają inny obraz: jest ich więcej niż awarii użytkownika (zagnieżdżone dekoratory) i nie ma wśród nich ośmiu cichych złych wyników z tej serii (wypłata z napisu, ujemne miesiące, saldo −500, przelew ponad limit, pusta historia, zły wyciąg, saldo `Infinity`, saldo −2 000 000). Baseline na następne zajęcia to 14 awarii i 10 przyczyn, nie liczba linii pliku.

Najbardziej ryzykowne w profilu operacyjnym, w którym klient wpłaca, wypłaca i przelewa, są przelew wewnętrzny oraz saldo: po wyczerpaniu limitu 5000 zł przelew i tak przenosi pieniądze, brak konta docelowego kończy się `KeyError`, a saldo da się zapisać jako ujemne albo jako `Infinity` bez śladu w logu awarii.
