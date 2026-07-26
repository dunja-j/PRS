"""
Glavni program — pokreće kompletan domaći zadatak.

Redosled izvršavanja:
  1. provera topologije (matrica verovatnoća tranzicija),
  2. analitičko rešavanje (matrični metod + Džeksonova teorema),
  3. simulacija (DES) — jedno izvršavanje i ponovljena izvršavanja sa
     usrednjavanjem, za svaku kombinaciju (K, r),
  4. poređenje rezultata i tabele relativnih odstupanja,
  5. dijagrami.

Primeri pokretanja:
    py main.py                          # podrazumevano: 30 min, 100 ponavljanja
    py main.py --minuti 60              # duže simulirano vreme rada sistema
    py main.py --ponavljanja 20         # manje ponavljanja (brže)
    py main.py --brzo                   # brza provera (5 min, 5 ponavljanja)
    py main.py --bez-simulacije         # samo analitika i dijagrami
    py main.py --procesi 1              # bez paralelizacije
"""

import argparse
import multiprocessing as mp
import os
import sys
import time

import analiticki
import izvestaji
import parametri
import simulacija

OVDE = os.path.dirname(os.path.abspath(__file__))
DIR_REZULTATI = os.path.join(OVDE, "rezultati")
DIR_GRAFICI = os.path.join(OVDE, "grafici")


# ---------------------------------------------------------------------------
# Argumenti komandne linije
# ---------------------------------------------------------------------------
def procitaj_argumente(argv=None):
    p = argparse.ArgumentParser(
        description="Performanse računarskih sistema — analiza i simulacija "
                    "otvorene mreže (procesor + 3 sistemska + K korisničkih diskova).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--minuti", type=float,
                   default=parametri.PODRAZUMEVANO_TRAJANJE_MIN,
                   help="simulirano vreme rada sistema po izvršavanju [min]")
    p.add_argument("--ponavljanja", type=int,
                   default=parametri.PODRAZUMEVANI_BROJ_PONAVLJANJA,
                   help="broj ponavljanja simulacije po kombinaciji (K, r)")
    p.add_argument("--seme", type=int, default=parametri.PODRAZUMEVANO_SEME,
                   help="bazno seme generatora slučajnih brojeva")
    p.add_argument("--procesi", type=int, default=0,
                   help="broj paralelnih procesa (0 = broj jezgara)")
    p.add_argument("--bez-simulacije", action="store_true",
                   help="izvrši samo analitički deo i dijagrame")
    p.add_argument("--bez-grafika", action="store_true",
                   help="ne crtaj dijagrame (npr. ako matplotlib nije instaliran)")
    p.add_argument("--brzo", action="store_true",
                   help="brza provera: 5 min simuliranog vremena, 5 ponavljanja")
    argumenti = p.parse_args(argv)
    if argumenti.brzo:
        argumenti.minuti = 5.0
        argumenti.ponavljanja = 5
    return argumenti


# ---------------------------------------------------------------------------
# Pomoćno ispisivanje
# ---------------------------------------------------------------------------
def _naslov(tekst):
    print()
    print("=" * 78)
    print(tekst)
    print("=" * 78)


def _trajanje(sekunde):
    if sekunde < 60:
        return f"{sekunde:.1f} s"
    return f"{int(sekunde // 60)} min {sekunde % 60:.0f} s"


# ---------------------------------------------------------------------------
# 1) Analitički deo
# ---------------------------------------------------------------------------
def izvrsi_analitiku():
    _naslov("1) ANALITIČKO REŠAVANJE")

    for K in parametri.K_VREDNOSTI:
        problemi = parametri.proveri_matricu_prelaza(K)
        if problemi:
            raise SystemExit(f"Neispravna topologija za K = {K}: {problemi}")
    print("Provera matrice verovatnoća tranzicija: u redu za sve K.")

    tabela_granicnih = analiticki.tabela_granicnih_intenziteta()
    print("\nGranični intenziteti ulaznog toka i kritični resursi:")
    for K, alpha_max, kriticni, D_max in tabela_granicnih:
        print(f"  K = {K}:  alpha_max = {alpha_max:8.4f} 1/s   "
              f"max D_i = {D_max * 1000:7.4f} ms   kritični resurs: "
              + parametri.opis_kriticnih(K, kriticni))

    analitika = analiticki.analiza_svih_slucajeva()

    izvestaji.obezbedi_direktorijum(DIR_REZULTATI)
    f1 = izvestaji.upisi_protoke(DIR_REZULTATI)
    f2 = izvestaji.upisi_analiticke_rezultate(DIR_REZULTATI, analitika)
    print(f"\nUpisano: {os.path.relpath(f1, OVDE)}")
    print(f"Upisano: {os.path.relpath(f2, OVDE)}")
    return analitika, tabela_granicnih


# ---------------------------------------------------------------------------
# 2) Simulacioni deo
# ---------------------------------------------------------------------------
def _napravi_zadatke(analitika, trajanje_s, bazno_seme, ponavljanja):
    """Lista poslova (jedno izvršavanje simulacije = jedan posao)."""
    zadatci = []
    for K in parametri.K_VREDNOSTI:
        for indeks_r, r in enumerate(parametri.R_VREDNOSTI):
            alpha = analitika[(K, r)].alpha
            for ponavljanje in range(ponavljanja):
                seme = simulacija.seme_za(bazno_seme, K, indeks_r, ponavljanje)
                zadatci.append((K, alpha, trajanje_s, seme, (K, r, ponavljanje)))
    return zadatci


def izvrsi_simulaciju(analitika, argumenti):
    _naslov("2) SIMULACIJA (diskretno-dogadjajna)")

    trajanje_s = argumenti.minuti * 60.0
    zadatci = _napravi_zadatke(
        analitika, trajanje_s, argumenti.seme, argumenti.ponavljanja
    )
    procesi = argumenti.procesi or mp.cpu_count()
    procesi = max(1, min(procesi, mp.cpu_count()))

    print(f"Simulirano vreme rada sistema: {argumenti.minuti:g} min "
          f"({trajanje_s:g} s) po izvršavanju")
    print(f"Kombinacija (K, r): {len(parametri.K_VREDNOSTI) * len(parametri.R_VREDNOSTI)}"
          f"   ponavljanja po kombinaciji: {argumenti.ponavljanja}")
    print(f"Ukupno izvršavanja simulacije: {len(zadatci)}   "
          f"paralelnih procesa: {procesi}")
    print()

    pocetak = time.perf_counter()
    merenja = {}

    def zabelezi(rezultat, redni_broj):
        kljuc, mer = rezultat
        merenja.setdefault(kljuc[:2], {})[kljuc[2]] = mer
        if redni_broj % max(1, len(zadatci) // 40) == 0 or redni_broj == len(zadatci):
            proteklo = time.perf_counter() - pocetak
            udeo = redni_broj / len(zadatci)
            print(f"\r  napredak: {redni_broj:5d}/{len(zadatci)} "
                  f"({udeo * 100:5.1f} %)   proteklo {_trajanje(proteklo)}      ",
                  end="", flush=True)

    if procesi == 1:
        for i, zadatak in enumerate(zadatci, start=1):
            zabelezi(simulacija.posao_simulacije(zadatak), i)
    else:
        # svako izvršavanje je nezavisno, pa se poslovi dele na sva jezgra
        with mp.Pool(processes=procesi) as bazen:
            for i, rezultat in enumerate(
                bazen.imap_unordered(simulacija.posao_simulacije, zadatci, chunksize=1),
                start=1,
            ):
                zabelezi(rezultat, i)
    print()
    print(f"Simulacija završena za {_trajanje(time.perf_counter() - pocetak)}.")

    # --- pretvaranje u rezultate: prvo ponavljanje = "jedna simulacija" ---
    simulacija_1 = {}
    usrednjeno = {}
    for K in parametri.K_VREDNOSTI:
        for r in parametri.R_VREDNOSTI:
            po_ponavljanju = merenja[(K, r)]
            alpha_max = analitika[(K, r)].alpha_max
            lista = [po_ponavljanju[i] for i in sorted(po_ponavljanju)]
            simulacija_1[(K, r)] = simulacija.u_rezultat(lista[0], r, alpha_max)
            usrednjeno[(K, r)] = simulacija.usrednji(lista, r, alpha_max)

    f3 = izvestaji.upisi_simulacione_rezultate(
        DIR_REZULTATI, simulacija_1, argumenti.minuti
    )
    f4 = izvestaji.upisi_usrednjene_rezultate(
        DIR_REZULTATI, usrednjeno, argumenti.minuti, argumenti.ponavljanja
    )
    print(f"Upisano: {os.path.relpath(f3, OVDE)}")
    print(f"Upisano: {os.path.relpath(f4, OVDE)}")
    return simulacija_1, usrednjeno


# ---------------------------------------------------------------------------
# 3) Poređenje i 4) dijagrami
# ---------------------------------------------------------------------------
def izvrsi_poredjenje(analitika, simulacija_1, usrednjeno, argumenti):
    _naslov("3) POREĐENJE ANALITIKE I SIMULACIJE")
    putanja, tabele = izvestaji.upisi_poredjenje(
        DIR_REZULTATI, analitika, simulacija_1, usrednjeno,
        argumenti.minuti, argumenti.ponavljanja,
    )
    print(f"Upisano: {os.path.relpath(putanja, OVDE)}\n")
    print(f"{'K':>3}{'r':>7}{'1 simulacija [%]':>20}{'usrednjeno [%]':>18}"
          f"{'odnos':>9}")
    print("-" * 57)
    for K, r, mao_sim, mao_usr, _ in izvestaji.sumarna_tabela(tabele):
        odnos = mao_sim / mao_usr if (mao_sim and mao_usr) else float("nan")
        print(f"{K:>3}{r:>7.2f}{mao_sim:>20.4f}{mao_usr:>18.4f}{odnos:>9.2f}")
    print("(srednje apsolutno relativno odstupanje od analitičkog rešenja)")
    return tabele


def izvrsi_grafike(analitika, tabela_granicnih, simulacija_1, usrednjeno):
    _naslov("4) DIJAGRAMI")
    try:
        import grafici
    except ImportError as greska:
        print(f"Dijagrami preskočeni (matplotlib nije dostupan): {greska}")
        return []
    putanje = grafici.nacrtaj_sve(
        DIR_GRAFICI, analitika, tabela_granicnih, simulacija_1, usrednjeno
    )
    for p in putanje:
        print(f"  {os.path.relpath(p, OVDE)}")
    print(f"Ukupno dijagrama: {len(putanje)}")
    return putanje


# ---------------------------------------------------------------------------
def main(argv=None):
    argumenti = procitaj_argumente(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    ukupno_pocetak = time.perf_counter()
    print(f"Radni direktorijum: {OVDE}")

    analitika, tabela_granicnih = izvrsi_analitiku()

    simulacija_1 = usrednjeno = None
    if not argumenti.bez_simulacije:
        simulacija_1, usrednjeno = izvrsi_simulaciju(analitika, argumenti)
        izvrsi_poredjenje(analitika, simulacija_1, usrednjeno, argumenti)

    if not argumenti.bez_grafika:
        izvrsi_grafike(analitika, tabela_granicnih, simulacija_1, usrednjeno)

    _naslov(f"GOTOVO za {_trajanje(time.perf_counter() - ukupno_pocetak)}")
    print(f"Rezultati: {os.path.relpath(DIR_REZULTATI, OVDE)}")
    print(f"Dijagrami: {os.path.relpath(DIR_GRAFICI, OVDE)}")


if __name__ == "__main__":
    mp.freeze_support()
    main()
