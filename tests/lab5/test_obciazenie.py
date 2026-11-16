"""Test obciążeniowy: 10 000 wpłat sekwencyjnie i równolegle, z pomiarem czasu."""

import threading
import time
from decimal import Decimal

from API import BankSystem

NR_SEKWENCYJNY = "1234567895"
NR_ROWNOLEGLE = "1111111119"
LICZBA_OPERACJI = 1_000_000
LICZBA_WATKOW = 10
KWOTA = Decimal("1")


def _wplaty(bank, numer, ile):
    for _ in range(ile):
        bank.wplac(numer, KWOTA)


def test_czas_wplat_sekwencyjnie_i_rownolegle():
    bank_sekw = BankSystem()
    bank_sekw.utworz_konto(NR_SEKWENCYJNY, "Sekwencja", 0)

    start = time.perf_counter()
    _wplaty(bank_sekw, NR_SEKWENCYJNY, LICZBA_OPERACJI)
    czas_sekw = time.perf_counter() - start

    bank_par = BankSystem()
    bank_par.utworz_konto(NR_ROWNOLEGLE, "Rownolegle", 0)
    na_watek = LICZBA_OPERACJI // LICZBA_WATKOW

    start = time.perf_counter()
    watki = [
        threading.Thread(target=_wplaty, args=(bank_par, NR_ROWNOLEGLE, na_watek))
        for _ in range(LICZBA_WATKOW)
    ]
    for watek in watki:
        watek.start()
    for watek in watki:
        watek.join()
    czas_par = time.perf_counter() - start

    print(
        f"\n{LICZBA_OPERACJI} wplat sekwencyjnie: {czas_sekw:.4f} s "
        f"({LICZBA_OPERACJI / czas_sekw:.0f} op/s)"
    )
    print(
        f"{LICZBA_OPERACJI} wplat rownolegle ({LICZBA_WATKOW} watkow): {czas_par:.4f} s "
        f"({LICZBA_OPERACJI / czas_par:.0f} op/s)"
    )

    assert bank_sekw.konta[NR_SEKWENCYJNY].saldo == Decimal(LICZBA_OPERACJI)
