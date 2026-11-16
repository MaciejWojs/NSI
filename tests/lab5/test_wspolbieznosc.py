"""Test współbieżności: wiele wątków wpłaca na to samo konto jednocześnie."""

import threading
from decimal import Decimal

from API import BankSystem

NR_KONTA = "1234567895"
LICZBA_WATKOW = 1000
KWOTA = Decimal("10")
SALDO_POCZATKOWE = Decimal("0")


def test_rownoczesne_wplaty_zachowuja_saldo():
    bank = BankSystem()
    bank.utworz_konto(NR_KONTA, "Wspolbieznosc", SALDO_POCZATKOWE)

    start = threading.Barrier(LICZBA_WATKOW)

    def wykonaj_wplate():
        start.wait()
        bank.wplac(NR_KONTA, KWOTA)

    watki = [threading.Thread(target=wykonaj_wplate) for _ in range(LICZBA_WATKOW)]
    for watek in watki:
        watek.start()
    for watek in watki:
        watek.join()

    oczekiwane = SALDO_POCZATKOWE + LICZBA_WATKOW * KWOTA
    assert bank.konta[NR_KONTA].saldo == oczekiwane
