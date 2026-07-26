"""
Formatiranje i upisivanje izlaznih fajlova.

Fajlovi koje modul pravi (svi u direktorijumu 'rezultati'):
  1. protoci_analiticki.txt              - matrični metod: P, mi, V = X/alpha, protoci
  2. rezultati_analiticki.txt            - Džeksonova teorema: svi parametri
  3. rezultati_simulacija.txt            - jedna simulacija po (K, r)
  4. rezultati_simulacija_usrednjeno.txt - usrednjeni rezultati N ponavljanja
  5. poredjenje.txt                      - relativna odstupanja simulacije od analitike

Poslednji deo modula (POREĐENJE) računa relativno odstupanje rezultata
simulacije od analitičkog rešenja:

        odstupanje [%] = (simulacija - analitika) / analitika * 100

i to za rezultat JEDNE simulacije i za USREDNJENI rezultat više simulacija.
"""

import math
import os

import analiticki
import parametri

SIRINA = 92


# ---------------------------------------------------------------------------
# Pomoćne funkcije za formatiranje
# ---------------------------------------------------------------------------
def broj(x, sirina=12, decimale=4):
    """Formatira broj u fiksnu širinu; beskonačno i nedefinisano posebno."""
    if x is None:
        return f"{'n/d':>{sirina}}"
    if isinstance(x, float):
        if math.isinf(x):
            return f"{('+inf' if x > 0 else '-inf'):>{sirina}}"
        if math.isnan(x):
            return f"{'nan':>{sirina}}"
    return f"{x:>{sirina}.{decimale}f}"


def linija(znak="-", sirina=SIRINA):
    return znak * sirina


def naslov(tekst, znak="="):
    return f"{linija(znak)}\n{tekst}\n{linija(znak)}"


def _zaglavlje_fajla(naslov_teksta, dodatni_redovi=()):
    redovi = [naslov(naslov_teksta), "", parametri.opis_sistema(), ""]
    redovi.extend(dodatni_redovi)
    if dodatni_redovi:
        redovi.append("")
    return redovi


def upisi_tekst(putanja, redovi):
    with open(putanja, "w", encoding="utf-8") as f:
        f.write("\n".join(redovi).rstrip() + "\n")
    return putanja


def obezbedi_direktorijum(putanja):
    os.makedirs(putanja, exist_ok=True)
    return putanja


# ---------------------------------------------------------------------------
# Tabela performansi po čvorovima (koristi se u više fajlova)
# ---------------------------------------------------------------------------
ZAGLAVLJE_CVOROVA = (
    f"{'Server':<20}{'V_i':>10}{'S_i[ms]':>10}{'X_i[1/s]':>12}"
    f"{'rho_i':>10}{'N_i':>12}{'W_i[ms]':>12}"
)


def _red_cvora(c):
    return (
        f"{c.puno_ime:<20}"
        f"{broj(c.V, 10, 4)}"
        f"{broj(c.S * 1000.0, 10, 3)}"
        f"{broj(c.X, 12, 4)}"
        f"{broj(c.rho, 10, 4)}"
        f"{broj(c.N, 12, 4)}"
        f"{broj(c.W * 1000.0, 12, 4)}"
    )


def tabela_cvorova(rez):
    redovi = [ZAGLAVLJE_CVOROVA, linija()]
    redovi += [_red_cvora(c) for c in rez.cvorovi]
    return redovi


def _sumarni_redovi(rez):
    return [
        linija(),
        f"{'Sistem: N =':<20}{broj(rez.N_sistem, 12, 4)}"
        f"     T_sistem ={broj(rez.T_sistem * 1000.0, 12, 4)} ms"
        f"     X_izlaz ={broj(rez.X_sistem, 12, 4)} 1/s",
        f"Kritični resurs: {rez.imena_kriticnih()}"
        + ("" if rez.stabilan else "   [ZASIĆEN: rho >= 1, nema stacionarnog režima]"),
    ]


# ---------------------------------------------------------------------------
# 1) protoci_analiticki.txt
# ---------------------------------------------------------------------------
def upisi_protoke(direktorijum, K_vrednosti=None, r_vrednosti=None):
    """
    Matrični metod: za svako K upisuje matricu prelaza P, vektor brzina servera,
    rešenje sistema (I - P^T) V = e, tj. odnose protoka i intenziteta ulaznog
    toka V_i = X_i / alpha, i protoke za korišćene vrednosti alpha.
    """
    if K_vrednosti is None:
        K_vrednosti = parametri.K_VREDNOSTI
    if r_vrednosti is None:
        r_vrednosti = parametri.R_VREDNOSTI

    redovi = _zaglavlje_fajla(
        "PROTOCI KROZ SERVERE — MATRIČNI METOD ZA OTVORENE MREŽE",
        (
            "Jednačine ravnoteže protoka:   (I - P^T) * lambda = alpha_vektor",
            "Ceo spoljni tok ulazi u procesor, pa je alpha_vektor = alpha * e,",
            "e = [1, 0, ..., 0]^T. Deljenjem sa alpha dobija se sistem za odnose",
            "protoka i intenziteta ulaznog toka (koeficijente poseta):",
            "",
            "        (I - P^T) * V = e,        V_i = lambda_i / alpha = X_i / alpha",
            "",
            "Protoci su linearne funkcije ulaznog toka:   X_i(alpha) = V_i * alpha.",
        ),
    )

    for K in K_vrednosti:
        V = analiticki.koeficijenti_poseta(K)
        S = parametri.vremena_opsluzivanja(K)
        mi = parametri.brzine_servera(K)
        D = analiticki.zahtevi_opsluzivanja(K, V)
        imena = parametri.imena_cvorova(K)
        puna = parametri.puna_imena_cvorova(K)
        P = parametri.matrica_prelaza(K)
        p_izlaz = parametri.verovatnoce_izlaska(K, P)
        alpha_max, kriticni, _ = analiticki.granicni_intenzitet(K, V)
        n = parametri.broj_cvorova(K)

        redovi += ["", naslov(f"K = {K}   (broj čvorova n = {n})")]

        # --- matrica prelaza ---
        redovi += ["", "Matrica verovatnoća tranzicija P (red = iz, kolona = u):", ""]
        redovi.append(f"{'':<8}" + "".join(f"{ime:>8}" for ime in imena) + f"{'IZLAZ':>8}")
        for i in range(n):
            redovi.append(
                f"{imena[i]:<8}"
                + "".join(f"{P[i][j]:>8.4f}" for j in range(n))
                + f"{p_izlaz[i]:>8.4f}"
            )

        # --- brzine servera ---
        redovi += ["", "Vektor brzina servera mi_i = 1 / S_i:", ""]
        redovi.append(f"{'Server':<20}{'S_i [ms]':>12}{'mi_i [1/s]':>14}")
        redovi.append(linija())
        for i in range(n):
            redovi.append(f"{puna[i]:<20}{broj(S[i] * 1000, 12, 3)}{broj(mi[i], 14, 4)}")

        # --- rešenje matričnog metoda ---
        redovi += [
            "",
            "Rešenje sistema (I - P^T) V = e  —  odnosi protoka i ulaznog toka:",
            "",
            f"{'Server':<20}{'V_i = X_i/alpha':>18}{'D_i = V_i*S_i [ms]':>22}"
            f"{'1/D_i [1/s]':>14}",
            linija(),
        ]
        for i in range(n):
            redovi.append(
                f"{puna[i]:<20}{broj(V[i], 18, 6)}{broj(D[i] * 1000, 22, 4)}"
                f"{broj(1.0 / D[i] if D[i] > 0 else math.inf, 14, 4)}"
            )
        redovi += [
            linija(),
            f"Rezidual max|(I - P^T)V - e| = {analiticki.greska_resenja(K, V):.3e}"
            "   (kontrola tačnosti Gausove eliminacije)",
            f"Suma V_i po korisničkim diskovima = "
            f"{sum(V[i] for i in parametri.indeksi_korisnickih(K)):.6f} "
            "(svaki posao izlazi iz sistema tačno jednom preko korisničkog diska)",
            f"alpha_max = 1 / max(D_i) = {alpha_max:.4f} 1/s   "
            f"kritični resurs: {parametri.opis_kriticnih(K, kriticni)}",
        ]

        # --- protoci za konkretne alpha ---
        redovi += [
            "",
            "Protoci X_i = V_i * alpha za razmatrane intenzitete ulaznog toka "
            "alpha = r * alpha_max [1/s]:",
            "",
        ]
        redovi.append(
            f"{'Server':<20}"
            + "".join(f"{f'r={r:.2f}':>16}" for r in r_vrednosti)
        )
        redovi.append(
            f"{'alpha [1/s]':<20}"
            + "".join(broj(r * alpha_max, 16, 4) for r in r_vrednosti)
        )
        redovi.append(linija())
        for i in range(n):
            redovi.append(
                f"{puna[i]:<20}"
                + "".join(broj(V[i] * r * alpha_max, 16, 4) for r in r_vrednosti)
            )

    return upisi_tekst(os.path.join(direktorijum, "protoci_analiticki.txt"), redovi)


# ---------------------------------------------------------------------------
# 2) rezultati_analiticki.txt
# ---------------------------------------------------------------------------
def upisi_analiticke_rezultate(direktorijum, analitika, K_vrednosti=None,
                               r_vrednosti=None):
    """Svi traženi parametri sistema dobijeni Džeksonovom teoremom."""
    if K_vrednosti is None:
        K_vrednosti = parametri.K_VREDNOSTI
    if r_vrednosti is None:
        r_vrednosti = parametri.R_VREDNOSTI

    redovi = _zaglavlje_fajla(
        "ANALITIČKI REZULTATI — DŽEKSONOVA TEOREMA (svaki server je M/M/1)",
        (
            "rho_i = X_i * S_i            (iskorišćenje servera)",
            "N_i   = rho_i / (1 - rho_i)  (prosečan broj poslova u serveru)",
            "W_i   = S_i / (1 - rho_i)    (vreme odziva servera po jednom prolazu)",
            "N     = suma N_i,   T_sistem = N / alpha = suma V_i * W_i  (Litl)",
        ),
    )

    # --- granični intenziteti i kritični resursi ---
    redovi += [
        naslov("GRANIČNI INTENZITETI ULAZNOG TOKA I KRITIČNI RESURSI", "="),
        "",
        "Uslov stacionarnosti: rho_i = V_i * S_i * alpha < 1 za svako i,",
        "odakle je alpha_max = 1 / max_i(V_i * S_i).",
        "",
        f"{'K':>3}{'alpha_max [1/s]':>18}{'max D_i [ms]':>16}   kritični resurs",
        linija(),
    ]
    for K, alpha_max, kriticni, D_max in analiticki.tabela_granicnih_intenziteta(
        K_vrednosti
    ):
        redovi.append(
            f"{K:>3}{broj(alpha_max, 18, 4)}{broj(D_max * 1000, 16, 4)}   "
            + parametri.opis_kriticnih(K, kriticni)
        )
    redovi += [
        linija(),
        "Napomena: rho_i = D_i * alpha, pa je kritični resurs (server sa najvećim",
        "zahtevom D_i) isti za svako r — r skalira sva iskorišćenja istim faktorom.",
        "",
    ]

    # --- detaljni rezultati ---
    redovi.append(naslov("REZULTATI PO K I r", "="))
    for K in K_vrednosti:
        for r in r_vrednosti:
            rez = analitika[(K, r)]
            redovi += [
                "",
                f"K = {K}   r = {r:.2f}   alpha = {rez.alpha:.4f} 1/s   "
                f"(alpha_max = {rez.alpha_max:.4f} 1/s)",
                linija(),
            ]
            redovi += tabela_cvorova(rez)
            redovi += _sumarni_redovi(rez)
            if not rez.stabilan:
                redovi.append(
                    "  Za r = 1.00 je alpha = alpha_max, pa je rho kritičnog resursa"
                    " jednako 1: M/M/1 red raste"
                )
                redovi.append(
                    "  neograničeno i N_i, W_i, N i T_sistem nemaju konačnu"
                    " stacionarnu vrednost."
                )

    return upisi_tekst(os.path.join(direktorijum, "rezultati_analiticki.txt"), redovi)


# ---------------------------------------------------------------------------
# 3) i 4) simulacioni rezultati
# ---------------------------------------------------------------------------
def _redovi_simulacije(rez, usrednjeno=False):
    d = rez.dodatno
    redovi = [
        "",
        f"K = {rez.K}   r = {rez.r:.2f}   alpha = {rez.alpha:.4f} 1/s   "
        f"(alpha_max = {rez.alpha_max:.4f} 1/s)",
        linija(),
    ]
    redovi += tabela_cvorova(rez)
    redovi += _sumarni_redovi(rez)

    if usrednjeno:
        redovi += [
            "",
            "Standardna devijacija po ponavljanjima "
            f"({d.get('broj_ponavljanja', 0)} simulacija):",
            "",
            f"{'Server':<20}{'std(X_i)':>12}{'std(rho_i)':>12}{'std(N_i)':>12}"
            f"{'std(W_i)[ms]':>14}",
            linija(),
        ]
        for c in rez.cvorovi:
            i = c.indeks
            redovi.append(
                f"{c.puno_ime:<20}{broj(d['std_X'][i], 12, 4)}"
                f"{broj(d['std_rho'][i], 12, 4)}{broj(d['std_N'][i], 12, 4)}"
                f"{broj(d['std_W'][i] * 1000, 14, 4)}"
            )
        redovi += [
            linija(),
            f"std(N) = {d['std_N_sistem']:.6f}   "
            f"std(T_sistem) = {d['std_T_sistem'] * 1000:.6f} ms   "
            f"T_sistem iz {d['broj_ponavljanja']} simulacija: "
            f"min = {d['T_sistem_min'] * 1000:.4f} ms, "
            f"max = {d['T_sistem_max'] * 1000:.4f} ms",
        ]

    redovi += [
        f"Provera Litlovog zakona: N / alpha = "
        f"{broj(d['T_sistem_little'] * 1000, 10, 4)} ms   vs   izmereno srednje vreme"
        f" u sistemu = {broj(rez.T_sistem * 1000, 10, 4)} ms",
        f"Spoljnih dolazaka: {d['broj_dolazaka']}   izlazaka iz sistema: "
        f"{d['broj_izlazaka']}   poslova u sistemu na kraju: "
        f"{d['poslova_u_sistemu_na_kraju']}",
    ]
    if not rez.stabilan:
        redovi.append(
            "  Zasićenje (rho ~ 1): red kritičnog resursa raste tokom celog"
            " simuliranog vremena, pa izmereni N i T"
        )
        redovi.append(
            "  zavise od dužine simulacije i nisu procene stacionarnih vrednosti"
            " (analitički su beskonačni)."
        )
    return redovi


def upisi_simulacione_rezultate(direktorijum, simulacija_1, trajanje_min,
                                K_vrednosti=None, r_vrednosti=None):
    """Rezultati jedne (pojedinačne) simulacije za svako (K, r)."""
    if K_vrednosti is None:
        K_vrednosti = parametri.K_VREDNOSTI
    if r_vrednosti is None:
        r_vrednosti = parametri.R_VREDNOSTI

    redovi = _zaglavlje_fajla(
        "REZULTATI SIMULACIJE (jedno izvršavanje po kombinaciji parametara)",
        (
            f"Simulirano vreme rada sistema: {trajanje_min:.4g} min "
            f"({trajanje_min * 60.0:.4g} s)",
            "Metod: diskretno-dogadjajna simulacija (DES), FCFS red po serveru,",
            "eksponencijalna vremena opsluživanja, Poasonov ulazni tok.",
            "Merenja: rho_i = zauzeto_i/T, X_i = zavrseno_i/T, N_i = integral"
            " broja poslova/T, W_i = N_i/X_i.",
        ),
    )
    for K in K_vrednosti:
        for r in r_vrednosti:
            redovi += _redovi_simulacije(simulacija_1[(K, r)], usrednjeno=False)
    return upisi_tekst(os.path.join(direktorijum, "rezultati_simulacija.txt"), redovi)


def upisi_usrednjene_rezultate(direktorijum, usrednjeno, trajanje_min,
                               broj_ponavljanja, K_vrednosti=None,
                               r_vrednosti=None):
    """Usrednjeni rezultati više ponavljanja simulacije za svako (K, r)."""
    if K_vrednosti is None:
        K_vrednosti = parametri.K_VREDNOSTI
    if r_vrednosti is None:
        r_vrednosti = parametri.R_VREDNOSTI

    redovi = _zaglavlje_fajla(
        f"USREDNJENI REZULTATI {broj_ponavljanja} SIMULACIJA PO KOMBINACIJI"
        " PARAMETARA (r, K)",
        (
            f"Simulirano vreme rada sistema po izvršavanju: {trajanje_min:.4g} min "
            f"({trajanje_min * 60.0:.4g} s)",
            f"Broj ponavljanja po kombinaciji (r, K): {broj_ponavljanja}",
            "Svako izvršavanje koristi različito seme generatora slučajnih brojeva,",
            "pa su ponavljanja nezavisne realizacije istog stohastičkog procesa.",
            "Uz srednju vrednost prikazana je i uzoračka standardna devijacija po"
            " ponavljanjima.",
        ),
    )
    for K in K_vrednosti:
        for r in r_vrednosti:
            redovi += _redovi_simulacije(usrednjeno[(K, r)], usrednjeno=True)
    return upisi_tekst(
        os.path.join(direktorijum, "rezultati_simulacija_usrednjeno.txt"), redovi
    )


# ==========================================================================
# POREĐENJE ANALITIKE I SIMULACIJE
# ==========================================================================
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
