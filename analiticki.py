"""
Analitičko rešavanje otvorene mreže.

Sadržaj:
  1) matrični metod za protoke kroz servere u funkciji od alpha,
  2) granični intenzitet ulaznog toka alpha_max(K) i kritični resurs,
  3) Džeksonova teorema — svi traženi parametri performansi.

--- 1) Matrični metod --------------------------------------------------------
Jednačine ravnoteže protoka za otvorenu mrežu:

        lambda_i = alpha_i + suma_j lambda_j * P[j][i]

odnosno u matričnom obliku (sa predavanja):

        (I - P^T) * lambda = alpha_vektor

Pošto ceo spoljni tok ulazi u procesor, alpha_vektor = alpha * e, gde je
e = [1, 0, 0, ..., 0]^T. Deljenjem sa alpha dobija se sistem za koeficijente
poseta V_i = lambda_i / alpha:

        (I - P^T) * V = e

Rešenje V ne zavisi od alpha, pa su protoci linearne funkcije ulaznog toka:

        X_i(alpha) = V_i * alpha

--- 2) Granični intenzitet ---------------------------------------------------
Uslov stabilnosti (stacionarnog režima) za svaki server je rho_i < 1:

        rho_i = lambda_i / mi_i = V_i * alpha * S_i < 1
    =>  alpha < 1 / (V_i * S_i)      za svako i
    =>  alpha_max = 1 / max_i (V_i * S_i)

Veličina D_i = V_i * S_i je ukupan zahtev posla za resursom i; server sa
najvećim D_i je kritični (najuže grlo) resurs.

--- 3) Džeksonova teorema ---------------------------------------------------
Za otvorenu Džeksonovu mrežu svaki server se ponaša kao nezavisan M/M/1
sistem sa ulaznim tokom lambda_i:

        rho_i = lambda_i * S_i
        N_i   = rho_i / (1 - rho_i)
        W_i   = S_i / (1 - rho_i)         (vreme odziva servera po prolazu)
        N     = suma_i N_i
        T     = N / alpha = suma_i V_i * W_i   (Litlov zakon)
"""

import math

import linearna_algebra as la
import parametri
from rezultat import RezultatCvora, RezultatSistema

# Server se smatra zasićenim ako je rho_i >= 1 - TOLERANCIJA_STABILNOSTI.
# Tolerancija je potrebna zbog aritmetike u pokretnom zarezu: za r = 1.00 je
# alpha = alpha_max, pa rho kritičnog resursa treba da bude tačno 1, ali se
# zbog zaokruživanja može izračunati kao 0.9999999999999999 i dati apsurdno
# velike (a ne beskonačne) vrednosti za N i W.
TOLERANCIJA_STABILNOSTI = 1e-9


# ---------------------------------------------------------------------------
# 1) Koeficijenti poseta i protoci
# ---------------------------------------------------------------------------
def matrica_sistema(K):
    """
    Matrica A = I - P^T koja se koristi u matričnom metodu.
    A[i][j] = delta(i, j) - P[j][i]
    """
    n = parametri.broj_cvorova(K)
    P = parametri.matrica_prelaza(K)
    I = la.jedinicna(n)
    Pt = la.transponuj(P)
    return la.razlika(I, Pt)


def vektor_ulaznog_toka(K, alpha=1.0):
    """Vektor spoljnih dolazaka: ceo tok ulazi u procesor."""
    n = parametri.broj_cvorova(K)
    v = [0.0] * n
    v[parametri.IDX_PROCESOR] = alpha
    return v


def koeficijenti_poseta(K):
    """
    Rešava (I - P^T) * V = e i vraća vektor koeficijenata poseta
    V_i = lambda_i / alpha = X_i / alpha.
    """
    A = matrica_sistema(K)
    e = vektor_ulaznog_toka(K, 1.0)
    return la.resi_sistem(A, e)


def greska_resenja(K, V):
    """Rezidual max|(I - P^T)V - e| — kontrola numeričke tačnosti."""
    A = matrica_sistema(K)
    e = vektor_ulaznog_toka(K, 1.0)
    return la.maksimalna_greska_resenja(A, V, e)


def protoci(K, alpha, V=None):
    """Protoci kroz servere X_i = V_i * alpha [1/s]."""
    if V is None:
        V = koeficijenti_poseta(K)
    return [v * alpha for v in V]


def zahtevi_opsluzivanja(K, V=None):
    """Zahtevi za resursima D_i = V_i * S_i [s]."""
    if V is None:
        V = koeficijenti_poseta(K)
    S = parametri.vremena_opsluzivanja(K)
    return [v * s for v, s in zip(V, S)]


# ---------------------------------------------------------------------------
# 2) Granični intenzitet ulaznog toka i kritični resurs
# ---------------------------------------------------------------------------
def ogranicenja_alfe(K, V=None):
    """
    Za svaki server gornja granica ulaznog toka alpha < 1 / (V_i * S_i).
    Serveri kroz koje posao ne prolazi (V_i = 0) ne ograničavaju alpha.
    """
    D = zahtevi_opsluzivanja(K, V)
    return [(1.0 / d if d > 0.0 else math.inf) for d in D]


def granicni_intenzitet(K, V=None, relativna_tolerancija=1e-9):
    """
    Vraća (alpha_max, kriticni_indeksi, D) gde je:
      alpha_max          - najveći intenzitet za koji je sistem stacionaran,
      kriticni_indeksi   - indeksi servera sa najvećim zahtevom D_i
                           (može ih biti više ako je zahtev isti),
      D                  - vektor zahteva D_i = V_i * S_i [s].
    """
    D = zahtevi_opsluzivanja(K, V)
    D_max = max(D)
    alpha_max = 1.0 / D_max
    kriticni = tuple(
        i for i, d in enumerate(D) if abs(d - D_max) <= relativna_tolerancija * D_max
    )
    return alpha_max, kriticni, D


def kriticni_resurs_za_alfu(K, alpha, V=None, relativna_tolerancija=1e-9):
    """
    Kritični resurs za konkretan alpha. Pošto je rho_i = D_i * alpha, kritični
    resurs ne zavisi od alpha (isti je za svako r) — funkcija postoji da bi to
    bilo eksplicitno u izveštajima.
    """
    _, kriticni, _ = granicni_intenzitet(K, V, relativna_tolerancija)
    return kriticni


# ---------------------------------------------------------------------------
# 3) Džeksonova teorema
# ---------------------------------------------------------------------------
def dzeksonova_analiza(K, alpha, r=None, V=None):
    """
    Sve tražene parametre sistema računa preko Džeksonove teoreme
    (svaki server = nezavisan M/M/1) i vraća RezultatSistema.

    Ako je rho_i >= 1 za neki server, taj server nije u stacionarnom režimu:
    N_i i W_i su beskonačni (math.inf), a rezultat se označava kao nestabilan.
    """
    if V is None:
        V = koeficijenti_poseta(K)
    S = parametri.vremena_opsluzivanja(K)
    imena = parametri.imena_cvorova(K)
    puna = parametri.puna_imena_cvorova(K)
    alpha_max, kriticni, _ = granicni_intenzitet(K, V)

    cvorovi = []
    stabilan = True
    for i in range(parametri.broj_cvorova(K)):
        X = V[i] * alpha
        rho = X * S[i]
        if rho < 1.0 - TOLERANCIJA_STABILNOSTI:
            N = rho / (1.0 - rho)
            W = S[i] / (1.0 - rho)
        else:
            stabilan = False
            N = math.inf
            W = math.inf
        cvorovi.append(
            RezultatCvora(
                indeks=i,
                ime=imena[i],
                puno_ime=puna[i],
                tip=parametri.tip_cvora(i),
                S=S[i],
                V=V[i],
                X=X,
                rho=rho,
                N=N,
                W=W,
            )
        )

    N_sistem = math.fsum(c.N for c in cvorovi) if stabilan else math.inf
    T_sistem = N_sistem / alpha if alpha > 0 else math.inf

    # izlazni protok: posao napušta sistem samo iz korisničkih diskova
    p_izlaz = parametri.verovatnoce_izlaska(K)
    X_sistem = math.fsum(c.X * p_izlaz[c.indeks] for c in cvorovi)

    return RezultatSistema(
        K=K,
        r=r,
        alpha=alpha,
        alpha_max=alpha_max,
        metod="analitika",
        cvorovi=cvorovi,
        N_sistem=N_sistem,
        T_sistem=T_sistem,
        X_sistem=X_sistem,
        kriticni=kriticni,
        stabilan=stabilan,
        dodatno={
            "T_sistem_suma_VW": (
                math.fsum(c.V * c.W for c in cvorovi) if stabilan else math.inf
            ),
            "rezidual": greska_resenja(K, V),
        },
    )


def analiza_svih_slucajeva(K_vrednosti=None, r_vrednosti=None):
    """
    Analitički rezultati za sve kombinacije (K, r) iz postavke.
    Vraća dict {(K, r): RezultatSistema}.
    """
    if K_vrednosti is None:
        K_vrednosti = parametri.K_VREDNOSTI
    if r_vrednosti is None:
        r_vrednosti = parametri.R_VREDNOSTI

    rezultati = {}
    for K in K_vrednosti:
        V = koeficijenti_poseta(K)
        alpha_max, _, _ = granicni_intenzitet(K, V)
        for r in r_vrednosti:
            rezultati[(K, r)] = dzeksonova_analiza(K, r * alpha_max, r=r, V=V)
    return rezultati


def tabela_granicnih_intenziteta(K_vrednosti=None):
    """Lista (K, alpha_max, kriticni_indeksi, D_max) za grafik alpha_max(K)."""
    if K_vrednosti is None:
        K_vrednosti = parametri.K_VREDNOSTI
    tabela = []
    for K in K_vrednosti:
        V = koeficijenti_poseta(K)
        alpha_max, kriticni, D = granicni_intenzitet(K, V)
        tabela.append((K, alpha_max, kriticni, max(D)))
    return tabela
