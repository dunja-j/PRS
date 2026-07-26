"""
Poređenje analitičkih i simulacionih rezultata.

Za svaku kombinaciju (K, r) računa se relativno odstupanje rezultata
simulacije od analitičkog (Džeksonovog) rešenja:

        odstupanje [%] = (simulacija - analitika) / analitika * 100

Porede se dve vrste simulacionih rezultata:
  * rezultat JEDNE simulacije,
  * USREDNJENI rezultat više (podrazumevano 100) nezavisnih simulacija.

Modul vraća strukturirane tabele koje koriste i tekstualni izveštaj
(rezultati/poredjenje.txt) i dokumentacija (dokumentacija.md).
"""

import math
import os

import parametri
from izvestaji import broj, linija, naslov, upisi_tekst

# Metrike koje se porede — (oznaka, jedinica, funkcija koja iz RezultatSistema
# izvlači vrednost u prikaznoj jedinici)
KLJUCNE_METRIKE = ("rho_CPU", "rho_KD", "W_CPU [ms]", "W_KD [ms]", "N", "T_sistem [ms]")


def _cvor_po_imenu(rez, ime):
    for c in rez.cvorovi:
        if c.ime == ime:
            return c
    raise KeyError(ime)


def vrednosti_metrika(rez):
    """
    Uređeni dict {oznaka_metrike: vrednost_u_prikaznoj_jedinici} za jedan
    RezultatSistema. Korisnički diskovi su statistički identični, pa se
    prikazuje njihova srednja vrednost (oznaka 'KD').
    """
    v = {}
    for ime in ("CPU", "SD1", "SD2", "SD3"):
        c = _cvor_po_imenu(rez, ime)
        v[f"X_{ime} [1/s]"] = c.X
        v[f"rho_{ime}"] = c.rho
        v[f"N_{ime}"] = c.N
        v[f"W_{ime} [ms]"] = c.W * 1000.0
    v["X_KD [1/s]"] = rez.korisnicki_prosek("X")
    v["rho_KD"] = rez.korisnicki_prosek("rho")
    v["N_KD"] = rez.korisnicki_prosek("N")
    v["W_KD [ms]"] = rez.korisnicki_prosek("W") * 1000.0
    v["N"] = rez.N_sistem
    v["T_sistem [ms]"] = rez.T_sistem * 1000.0
    v["X_izlaz [1/s]"] = rez.X_sistem
    return v


def relativno_odstupanje(vrednost_sim, vrednost_anal):
    """
    Relativno odstupanje u procentima. Vraća None kada odstupanje nije
    definisano (analitička vrednost je 0, beskonačna ili nedefinisana) —
    to se dešava za r = 1.00, gde zasićeni resurs analitički ima N = W = inf.
    """
    if vrednost_anal is None or vrednost_sim is None:
        return None
    if (
        math.isinf(vrednost_anal)
        or math.isnan(vrednost_anal)
        or math.isinf(vrednost_sim)
        or math.isnan(vrednost_sim)
        or vrednost_anal == 0.0
    ):
        return None
    return (vrednost_sim - vrednost_anal) / vrednost_anal * 100.0


def tabela_slucaja(rez_anal, rez_sim, rez_usr):
    """
    Za jedan slučaj (K, r) vraća listu redova
    (oznaka, analitika, simulacija, odstupanje_sim, usrednjeno, odstupanje_usr).
    """
    a = vrednosti_metrika(rez_anal)
    s = vrednosti_metrika(rez_sim)
    u = vrednosti_metrika(rez_usr)
    redovi = []
    for oznaka in a:
        redovi.append(
            (
                oznaka,
                a[oznaka],
                s[oznaka],
                relativno_odstupanje(s[oznaka], a[oznaka]),
                u[oznaka],
                relativno_odstupanje(u[oznaka], a[oznaka]),
            )
        )
    return redovi


def srednje_apsolutno_odstupanje(redovi):
    """
    Srednje apsolutno relativno odstupanje po slučaju, odvojeno za jednu
    simulaciju i za usrednjene rezultate. Uzimaju se samo metrike za koje je
    odstupanje definisano. Vraća (mao_sim, mao_usr, broj_metrika).
    """
    ds = [abs(red[3]) for red in redovi if red[3] is not None]
    du = [abs(red[5]) for red in redovi if red[5] is not None]
    mao_sim = sum(ds) / len(ds) if ds else None
    mao_usr = sum(du) / len(du) if du else None
    return mao_sim, mao_usr, len(ds)


def sve_tabele(analitika, simulacija_1, usrednjeno, K_vrednosti=None,
               r_vrednosti=None):
    """Vraća dict {(K, r): redovi_tabele} za sve kombinacije parametara."""
    if K_vrednosti is None:
        K_vrednosti = parametri.K_VREDNOSTI
    if r_vrednosti is None:
        r_vrednosti = parametri.R_VREDNOSTI
    return {
        (K, r): tabela_slucaja(
            analitika[(K, r)], simulacija_1[(K, r)], usrednjeno[(K, r)]
        )
        for K in K_vrednosti
        for r in r_vrednosti
    }


def sumarna_tabela(tabele, K_vrednosti=None, r_vrednosti=None):
    """
    Srednje apsolutno relativno odstupanje po svakom slučaju (K, r):
    lista (K, r, mao_sim, mao_usr, broj_metrika).
    """
    if K_vrednosti is None:
        K_vrednosti = parametri.K_VREDNOSTI
    if r_vrednosti is None:
        r_vrednosti = parametri.R_VREDNOSTI
    izlaz = []
    for r in r_vrednosti:
        for K in K_vrednosti:
            mao_sim, mao_usr, m = srednje_apsolutno_odstupanje(tabele[(K, r)])
            izlaz.append((K, r, mao_sim, mao_usr, m))
    return izlaz


def po_metrici_i_K(tabele, metrika, r, K_vrednosti=None):
    """
    Zavisnost jedne metrike od K za fiksno r:
    lista (K, analitika, simulacija, odst_sim, usrednjeno, odst_usr).
    """
    if K_vrednosti is None:
        K_vrednosti = parametri.K_VREDNOSTI
    izlaz = []
    for K in K_vrednosti:
        for red in tabele[(K, r)]:
            if red[0] == metrika:
                izlaz.append((K,) + red[1:])
                break
    return izlaz


# ---------------------------------------------------------------------------
# Tekstualni izveštaj
# ---------------------------------------------------------------------------
_ZAGLAVLJE = (
    f"{'Metrika':<16}{'Analitika':>14}{'1 simulacija':>15}{'odst.[%]':>11}"
    f"{'Usrednjeno':>15}{'odst.[%]':>11}"
)


def _red_teksta(red):
    oznaka, a, s, ds, u, du = red
    return (
        f"{oznaka:<16}{broj(a, 14, 5)}{broj(s, 15, 5)}{broj(ds, 11, 3)}"
        f"{broj(u, 15, 5)}{broj(du, 11, 3)}"
    )


def upisi_poredjenje(direktorijum, analitika, simulacija_1, usrednjeno,
                     trajanje_min, broj_ponavljanja, K_vrednosti=None,
                     r_vrednosti=None):
    """Upisuje rezultati/poredjenje.txt sa tabelama relativnih odstupanja."""
    if K_vrednosti is None:
        K_vrednosti = parametri.K_VREDNOSTI
    if r_vrednosti is None:
        r_vrednosti = parametri.R_VREDNOSTI

    tabele = sve_tabele(analitika, simulacija_1, usrednjeno, K_vrednosti, r_vrednosti)

    redovi = [
        naslov("POREĐENJE ANALITIČKIH I SIMULACIONIH REZULTATA"),
        "",
        "odstupanje [%] = (simulacija - analitika) / analitika * 100",
        "",
        f"Simulirano vreme rada sistema: {trajanje_min:.4g} min",
        f"Broj ponavljanja za usrednjene rezultate: {broj_ponavljanja}",
        "",
        "Za r = 1.00 je alpha = alpha_max, pa kritični resurs ima rho = 1:"
        " analitičke vrednosti",
        "N_i, W_i, N i T_sistem su beskonačne, a odstupanje nije definisano"
        " (oznaka 'n/d').",
        "",
        naslov("1) SVE METRIKE PO SLUČAJEVIMA (K, r)", "="),
    ]

    for K in K_vrednosti:
        for r in r_vrednosti:
            tabela = tabele[(K, r)]
            mao_sim, mao_usr, m = srednje_apsolutno_odstupanje(tabela)
            redovi += [
                "",
                f"K = {K}   r = {r:.2f}   "
                f"alpha = {analitika[(K, r)].alpha:.4f} 1/s",
                linija(),
                _ZAGLAVLJE,
                linija(),
            ]
            redovi += [_red_teksta(red) for red in tabela]
            redovi += [
                linija(),
                f"Srednje apsolutno relativno odstupanje ({m} metrika): "
                f"1 simulacija = {broj(mao_sim, 9, 3)} %,   "
                f"usrednjeno = {broj(mao_usr, 9, 3)} %",
            ]

    # --- zavisnost od K za fiksno r ---
    redovi += ["", naslov("2) ZAVISNOST KLJUČNIH METRIKA OD K (za svako r)", "=")]
    for r in r_vrednosti:
        redovi += ["", f"r = {r:.2f}", linija("=")]
        for metrika in KLJUCNE_METRIKE:
            redovi += [
                "",
                f"Metrika: {metrika}",
                f"{'K':>3}{'Analitika':>14}{'1 simulacija':>15}{'odst.[%]':>11}"
                f"{'Usrednjeno':>15}{'odst.[%]':>11}",
                linija(),
            ]
            for K, a, s, ds, u, du in po_metrici_i_K(tabele, metrika, r, K_vrednosti):
                redovi.append(
                    f"{K:>3}{broj(a, 14, 5)}{broj(s, 15, 5)}{broj(ds, 11, 3)}"
                    f"{broj(u, 15, 5)}{broj(du, 11, 3)}"
                )

    # --- sumarna tabela ---
    redovi += [
        "",
        naslov("3) SREDNJE APSOLUTNO RELATIVNO ODSTUPANJE PO SLUČAJU", "="),
        "",
        f"{'K':>3}{'r':>7}{'1 simulacija [%]':>20}{'usrednjeno [%]':>18}"
        f"{'odnos':>10}",
        linija(),
    ]
    for K, r, mao_sim, mao_usr, _ in sumarna_tabela(tabele, K_vrednosti, r_vrednosti):
        odnos = (
            mao_sim / mao_usr if (mao_sim and mao_usr and mao_usr > 0) else None
        )
        redovi.append(
            f"{K:>3}{r:>7.2f}{broj(mao_sim, 20, 4)}{broj(mao_usr, 18, 4)}"
            f"{broj(odnos, 10, 2)}"
        )
    redovi += [
        linija(),
        "Kolona 'odnos' pokazuje koliko je puta odstupanje jedne simulacije veće od",
        "odstupanja usrednjenih rezultata. Za n nezavisnih ponavljanja standardna",
        "greška srednje vrednosti opada kao 1/sqrt(n), pa se za n = 100 očekuje odnos",
        "reda veličine 10 (uz statističku fluktuaciju samog odnosa).",
    ]

    return upisi_tekst(os.path.join(direktorijum, "poredjenje.txt"), redovi), tabele
