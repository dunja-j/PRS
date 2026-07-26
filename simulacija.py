"""
Diskretno-dogadjajna simulacija (DES) otvorene mreže iz postavke projekta.

Simulacija NIJE vođena vremenom (nema čekanja/koraka po delta t), već
dogadjajima: održava se kalendar (min-hip) budućih dogadjaja, a simulaciono
vreme "preskače" direktno na trenutak sledećeg dogadjaja.

Tipovi dogadjaja:
  DOLAZAK  - spoljni Poasonov dolazak posla u procesor,
  ODLAZAK  - završetak opsluživanja posla u čvoru i.

Svaki čvor je jedan server sa FCFS redom neograničene dužine i eksponencijalnim
vremenom opsluživanja, tj. tačno onaj M/M/1 model koji Džeksonova teorema
pretpostavlja — zato se rezultati simulacije i analitike mogu direktno porediti.

Rutiranje posle opsluživanja koristi ISTU matricu verovatnoća tranzicija P koju
koristi i analitički deo (parametri.matrica_prelaza), pa su topologije zaista
identične.

Statistika (za svaki čvor):
  * integral broja poslova po vremenu  -> prosečan broj poslova N_i = area_i / T
  * ukupno vreme zauzetosti servera    -> iskorišćenje rho_i = zauzeto_i / T
  * broj završenih opsluživanja        -> protok X_i = zavrseno_i / T
  * vreme odziva servera po prolazu    -> W_i = N_i / X_i  (Litlov zakon)
Za ceo sistem meri se i vreme provedeno u sistemu po poslu (od spoljnog
dolaska do izlaska iz sistema).
"""

from __future__ import annotations

import math
import random
from collections import deque
from dataclasses import dataclass
from heapq import heappop, heappush

import parametri
from rezultat import RezultatCvora, RezultatSistema

DOLAZAK = 0
ODLAZAK = 1

IZLAZ = -1   # posao napušta sistem


# ---------------------------------------------------------------------------
# Pomoćna priprema: kumulativne verovatnoće rutiranja iz matrice P
# ---------------------------------------------------------------------------
def kumulativno_rutiranje(K):
    """
    Iz matrice prelaza P pravi, za svaki čvor, tuple parova
    (kumulativna_verovatnoca, odredisni_cvor).

    Odredište se bira jednim slučajnim brojem u ~ U(0, 1): traži se prvi par
    čija je kumulativna verovatnoća veća od u. Ako u premaši sumu reda, posao
    napušta sistem (za korisničke diskove je red nula, pa se to dešava uvek).
    """
    P = parametri.matrica_prelaza(K)
    tabela = []
    for red in P:
        kum = []
        suma = 0.0
        for j, p in enumerate(red):
            if p > 0.0:
                suma += p
                kum.append((suma, j))
        tabela.append(tuple(kum))
    return tuple(tabela)


# ---------------------------------------------------------------------------
# Rezultat jedne simulacije (sirove izmerene veličine)
# ---------------------------------------------------------------------------
@dataclass
class MerenjaSimulacije:
    K: int
    alpha: float
    trajanje: float            # simulirano vreme rada sistema [s]
    seme: int
    rho: list                  # iskorišćenja po čvoru
    X: list                    # protoci po čvoru [1/s]
    N: list                    # prosečan broj poslova po čvoru
    W: list                    # vreme odziva po prolazu, po čvoru [s]
    broj_dolazaka: int         # spoljni dolasci u posmatranom intervalu
    broj_izlazaka: int         # poslovi koji su napustili sistem
    T_sistem_mereno: float     # srednje vreme u sistemu po završenom poslu [s]
    N_sistem: float            # prosečan broj poslova u celom sistemu
    poslova_u_sistemu_na_kraju: int


# ---------------------------------------------------------------------------
# Jedno izvršavanje simulacije
# ---------------------------------------------------------------------------
def simuliraj(K, alpha, trajanje_s, seme=None):
    """
    Jedno izvršavanje DES simulacije.

    K          - broj korisničkih diskova
    alpha      - intenzitet Poasonovog ulaznog toka [1/s]
    trajanje_s - simulirano vreme rada sistema [s]
    seme       - seme generatora slučajnih brojeva (reproducibilnost)

    Mreža na početku nema nijedan posao i simulira se do trenutka 'kraj'.
    """
    n = parametri.broj_cvorova(K)
    tabela = kumulativno_rutiranje(K)
    kraj = float(trajanje_s)

    rng = random.Random(seme)
    slucajan = rng.random
    log = math.log
    S = parametri.vremena_opsluzivanja(K)
    sredni_medjudolazak = 1.0 / alpha

    # Eksponencijalna slučajna promenljiva sa srednjom vrednošću m generiše se
    # inverznom transformacijom:  F(x) = 1 - exp(-x/m)  =>  x = -m * ln(1 - u),
    # gde je u ~ U(0, 1). Izraz je u petlji ispisan direktno (a ne kao poziv
    # funkcije) jer se izvršava milionima puta po jednoj simulaciji.
    # (1 - slucajan()) je iz (0, 1], pa je logaritam uvek definisan.

    # --- stanje sistema ---
    broj = [0] * n                 # broj poslova u čvoru (red + na obradi)
    red = [deque() for _ in range(n)]   # FCFS red: vremena ulaska poslova u sistem
    na_obradi = [0.0] * n          # vreme ulaska posla koji se trenutno obrađuje
    obrada_od = [0.0] * n          # trenutak početka trenutnog opsluživanja
    zauzet = [False] * n

    # --- akumulatori statistike ---
    povrsina = [0.0] * n           # integral broja poslova po vremenu
    zauzeto = [0.0] * n            # ukupno vreme zauzetosti servera
    zavrseno = [0] * n             # broj završenih opsluživanja
    poslednja_promena = [0.0] * n  # trenutak poslednje promene broja poslova
    dolazaka = 0
    izlazaka = 0
    suma_vremena_u_sistemu = 0.0

    # kalendar dogadjaja: (vreme, tip, cvor)
    kalendar = [(-sredni_medjudolazak * log(1.0 - slucajan()), DOLAZAK,
                 parametri.IDX_PROCESOR)]

    while kalendar:
        t, tip, i = heappop(kalendar)
        if t > kraj:
            break

        if tip == DOLAZAK:
            # sledeći spoljni dolazak (Poasonov tok -> eksponencijalni medjudolasci)
            heappush(
                kalendar,
                (t - sredni_medjudolazak * log(1.0 - slucajan()), DOLAZAK,
                 parametri.IDX_PROCESOR),
            )
            dolazaka += 1
            ulazak = t
            cilj = parametri.IDX_PROCESOR
        else:
            # --- završetak opsluživanja u čvoru i ---
            povrsina[i] += broj[i] * (t - poslednja_promena[i])
            poslednja_promena[i] = t
            zauzeto[i] += t - obrada_od[i]
            zavrseno[i] += 1
            broj[i] -= 1
            ulazak = na_obradi[i]

            # sledeći posao iz reda (FCFS)
            r = red[i]
            if r:
                na_obradi[i] = r.popleft()
                obrada_od[i] = t
                heappush(
                    kalendar,
                    (t - S[i] * log(1.0 - slucajan()), ODLAZAK, i),
                )
            else:
                zauzet[i] = False

            # --- rutiranje: kuda posao ide posle čvora i ---
            u = slucajan()
            cilj = IZLAZ
            for granica, j in tabela[i]:
                if u < granica:
                    cilj = j
                    break

            if cilj == IZLAZ:
                izlazaka += 1
                suma_vremena_u_sistemu += t - ulazak
                continue

        # --- ulazak posla (novog ili pristiglog iz drugog čvora) u čvor 'cilj' ---
        j = cilj
        povrsina[j] += broj[j] * (t - poslednja_promena[j])
        poslednja_promena[j] = t
        broj[j] += 1
        if not zauzet[j]:
            zauzet[j] = True
            na_obradi[j] = ulazak
            obrada_od[j] = t
            heappush(kalendar, (t - S[j] * log(1.0 - slucajan()), ODLAZAK, j))
        else:
            red[j].append(ulazak)

    # --- zatvaranje statistike na kraju posmatranog intervala ---
    for i in range(n):
        povrsina[i] += broj[i] * (kraj - poslednja_promena[i])
        if zauzet[i]:
            zauzeto[i] += kraj - obrada_od[i]

    T = kraj
    rho = [z / T for z in zauzeto]
    X = [c / T for c in zavrseno]
    N = [p / T for p in povrsina]
    W = [
        (povrsina[i] / zavrseno[i]) if zavrseno[i] > 0 else 0.0
        for i in range(n)
    ]

    return MerenjaSimulacije(
        K=K,
        alpha=alpha,
        trajanje=T,
        seme=seme,
        rho=rho,
        X=X,
        N=N,
        W=W,
        broj_dolazaka=dolazaka,
        broj_izlazaka=izlazaka,
        T_sistem_mereno=(
            suma_vremena_u_sistemu / izlazaka if izlazaka > 0 else math.inf
        ),
        N_sistem=math.fsum(N),
        poslova_u_sistemu_na_kraju=sum(broj),
    )


# ---------------------------------------------------------------------------
# Pretvaranje merenja u zajedničku strukturu rezultata
# ---------------------------------------------------------------------------
def u_rezultat(merenja, r, alpha_max, V=None, metod="simulacija", dodatno=None):
    """MerenjaSimulacije -> RezultatSistema (isti tip koji vraća i analitika)."""
    K = merenja.K
    S = parametri.vremena_opsluzivanja(K)
    imena = parametri.imena_cvorova(K)
    puna = parametri.puna_imena_cvorova(K)
    if V is None:
        V = [x / merenja.alpha if merenja.alpha > 0 else 0.0 for x in merenja.X]

    cvorovi = [
        RezultatCvora(
            indeks=i,
            ime=imena[i],
            puno_ime=puna[i],
            tip=parametri.tip_cvora(i),
            S=S[i],
            V=(merenja.X[i] / merenja.alpha if merenja.alpha > 0 else 0.0),
            X=merenja.X[i],
            rho=merenja.rho[i],
            N=merenja.N[i],
            W=merenja.W[i],
        )
        for i in range(parametri.broj_cvorova(K))
    ]

    # Izmerena iskorišćenja fluktuiraju oko prave vrednosti, pa se za kritični
    # resurs uzimaju svi serveri čije je iskorišćenje u okviru 5% od najvećeg —
    # inače bi se, kod resursa koji su stvarno podjednako opterećeni (npr. K
    # korisničkih diskova), kritičnim proglasio slučajno onaj sa najvećim šumom.
    rho_max = max(c.rho for c in cvorovi)
    kriticni = tuple(
        c.indeks for c in cvorovi if abs(c.rho - rho_max) <= 0.05 * max(rho_max, 1e-12)
    )

    osnovno = {
        "trajanje": merenja.trajanje,
        "seme": merenja.seme,
        "broj_dolazaka": merenja.broj_dolazaka,
        "broj_izlazaka": merenja.broj_izlazaka,
        "poslova_u_sistemu_na_kraju": merenja.poslova_u_sistemu_na_kraju,
        "T_sistem_little": (
            merenja.N_sistem / merenja.alpha if merenja.alpha > 0 else math.inf
        ),
    }
    if dodatno:
        osnovno.update(dodatno)

    return RezultatSistema(
        K=K,
        r=r,
        alpha=merenja.alpha,
        alpha_max=alpha_max,
        metod=metod,
        cvorovi=cvorovi,
        N_sistem=merenja.N_sistem,
        T_sistem=merenja.T_sistem_mereno,
        X_sistem=(merenja.broj_izlazaka / merenja.trajanje),
        kriticni=kriticni,
        stabilan=rho_max < 0.99,
        dodatno=osnovno,
    )


# ---------------------------------------------------------------------------
# Usrednjavanje više ponavljanja
# ---------------------------------------------------------------------------
def _srednja_vrednost(vrednosti):
    return math.fsum(vrednosti) / len(vrednosti)


def _standardna_devijacija(vrednosti, srednja=None):
    """Uzoračka standardna devijacija (deljenje sa n - 1)."""
    n = len(vrednosti)
    if n < 2:
        return 0.0
    if srednja is None:
        srednja = _srednja_vrednost(vrednosti)
    return math.sqrt(math.fsum((v - srednja) ** 2 for v in vrednosti) / (n - 1))


def usrednji(lista_merenja, r, alpha_max, metod="simulacija-usrednjeno"):
    """
    Usrednjava rezultate više izvršavanja simulacije za iste parametre (r, K).

    Usrednjava se svaka metrika posebno, a uz srednju vrednost se pamti i
    uzoračka standardna devijacija po ponavljanjima (u polju 'dodatno') —
    ona pokazuje koliko rezultat jedne simulacije fluktuira i zašto
    usrednjavanje smanjuje odstupanje od analitičkog rešenja.
    """
    if not lista_merenja:
        raise ValueError("nema rezultata za usrednjavanje")

    K = lista_merenja[0].K
    n = parametri.broj_cvorova(K)
    m = len(lista_merenja)

    def po_cvoru(atribut):
        return [
            [getattr(mer, atribut)[i] for mer in lista_merenja] for i in range(n)
        ]

    sredine = {}
    devijacije = {}
    for atribut in ("rho", "X", "N", "W"):
        kolone = po_cvoru(atribut)
        sredine[atribut] = [_srednja_vrednost(k) for k in kolone]
        devijacije[atribut] = [
            _standardna_devijacija(k, s) for k, s in zip(kolone, sredine[atribut])
        ]

    T_uzorci = [mer.T_sistem_mereno for mer in lista_merenja]
    N_uzorci = [mer.N_sistem for mer in lista_merenja]
    X_uzorci = [mer.broj_izlazaka / mer.trajanje for mer in lista_merenja]

    prosek = MerenjaSimulacije(
        K=K,
        alpha=lista_merenja[0].alpha,
        trajanje=_srednja_vrednost([mer.trajanje for mer in lista_merenja]),
        seme=None,
        rho=sredine["rho"],
        X=sredine["X"],
        N=sredine["N"],
        W=sredine["W"],
        broj_dolazaka=int(round(_srednja_vrednost(
            [mer.broj_dolazaka for mer in lista_merenja]))),
        broj_izlazaka=int(round(_srednja_vrednost(
            [mer.broj_izlazaka for mer in lista_merenja]))),
        T_sistem_mereno=_srednja_vrednost(T_uzorci),
        N_sistem=_srednja_vrednost(N_uzorci),
        poslova_u_sistemu_na_kraju=int(round(_srednja_vrednost(
            [mer.poslova_u_sistemu_na_kraju for mer in lista_merenja]))),
    )

    rezultat = u_rezultat(prosek, r, alpha_max, metod=metod)
    rezultat.X_sistem = _srednja_vrednost(X_uzorci)
    rezultat.dodatno.update(
        {
            "broj_ponavljanja": m,
            "std_rho": devijacije["rho"],
            "std_X": devijacije["X"],
            "std_N": devijacije["N"],
            "std_W": devijacije["W"],
            "std_T_sistem": _standardna_devijacija(T_uzorci),
            "std_N_sistem": _standardna_devijacija(N_uzorci),
            "T_sistem_min": min(T_uzorci),
            "T_sistem_max": max(T_uzorci),
            "semena": [mer.seme for mer in lista_merenja],
        }
    )
    return rezultat


# ---------------------------------------------------------------------------
# Radni zadatak za paralelno izvršavanje (multiprocessing)
# ---------------------------------------------------------------------------
def seme_za(bazno_seme, K, indeks_r, ponavljanje):
    """Determinističko seme — rezultati su reproducibilni pri istom baznom semenu."""
    return (bazno_seme * 1_000_003 + K * 10_007 + indeks_r * 101 + ponavljanje) % (2**63)


def posao_simulacije(zadatak):
    """
    Jedan posao za radni proces: (K, alpha, trajanje_s, seme, kljuc).
    Vraća (kljuc, MerenjaSimulacije).
    """
    K, alpha, trajanje_s, seme, kljuc = zadatak
    return kljuc, simuliraj(K, alpha, trajanje_s, seme)
