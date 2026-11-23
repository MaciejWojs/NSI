# NSI — System zarządzania kontem bankowym (wariant C)

System emulujący konto bankowe z naciskiem na **mechanizmy odporności**
(retry, circuit breaker, redundancja) w kontekście ćwiczeń P5. Kod jest
celowo „kruchy" w punkcie integracji z zewnętrznym procesorem płatności.

## Wymagania

- **Python ≥ 3.12** (w projekcie ustawiony `3.12` przez plik `.python-version`)
- **[uv](https://docs.astral.sh/uv/)** — menedżer środowiska i pakietów

Zainstaluj `uv`, jeśli go nie masz:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# lub przez pipx / pip:  pip install uv
```

## Uruchomienie

Najszybszy sposób — dwie komendy:

```bash
uv sync          # zbuduj środowisko wirtualne i zainstaluj zależności
uv run main.py   # uruchom program (wyświetli stan systemu + „Hello from nsi!")
```

Nie musisz ręcznie aktywować `.venv` — `uv run` obsługuje to automatycznie.

## Testy

Projekt zakłada pytest (`pytest`, `pytest-cov`).

```bash
uv sync
uv run pytest
```

Osobno, tak jak w pipeline:

```bash
uv run pytest --override-ini="addopts=" tests/test_Konto.py tests/test_BankSystem.py
uv run pytest --override-ini="addopts=" tests/functional-black-box
uv run pytest --override-ini="addopts=" tests/lab5
```

`--override-ini="addopts="` wyłącza globalne opcje pokrycia z `pyproject.toml`. Pełny pomiar (próg 80% gałęzi w `API.py`) zostaje przy `uv run pytest` bez tej flagi.

## Pipeline CI

Konfiguracja: [`.github/workflows/run-tests.yml`](.github/workflows/run-tests.yml).

GitHub Actions uruchamia ją przy każdym `push` i pull requeście. Job, który skończy się niezerowym kodem wyjścia, oznacza cały przebieg jako nieudany. Wynik pytest ani `coverage report` nie jest przechwytywany.

Kolejność:

1. Równolegle, każdy job od nowa pobiera kod, instaluje uv i robi `uv sync`:
   - **Testy jednostkowe (P2)** — `tests/test_Konto.py`, `tests/test_BankSystem.py`
   - **Testy funkcjonalne (P3)** — `tests/functional-black-box`
   - **Testy niefunkcjonalne (P3)** — `tests/lab5` (obciążenie i współbieżność)
2. Każdy z tych jobów zbiera częściowe dane pokrycia (`--cov=API --cov-branch`) i wrzuca je jako artefakt. Próg 80% nie obowiązuje na podzbiorze testów.
3. **Pokrycie kodu** startuje dopiero po sukcesie wszystkich trzech. Łączy dane (`coverage combine`), wypisuje raport z brakującymi liniami i kończy się błędem, gdy pokrycie spadnie poniżej 80%. Raport HTML i `coverage.xml` trafiają do artefaktu `coverage`.

Żeby zobaczyć czerwony przebieg, wystarczy na gałęzi zmienić jedną oczekiwaną wartość w asercji, wypchnąć commit i odczytać log joba, który uruchamia ten plik. Potem przywrócić asercję i wypchnąć poprawkę — pipeline powinien znowu być zielony.

## Docker

Obraz uruchamia ten sam cykl jak lokalnie:

```bash
docker build -t nsi .
docker run --rm nsi
```

## Zależności (`pyproject.toml`)

```toml
dependencies = [
    "pytest>=9.1.1",
    "pytest-cov>=7.1.0",
]
```

