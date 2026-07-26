"""
Parametri sistema iz postavke projekta (Performanse računarskih sistema).

Sistem: multiprogramski računar modelovan OTVORENOM mrežom u stacionarnom režimu.
  - 1 procesor,
  - 3 sistemska diska,
  - K korisničkih diskova (K = 2..5).

Poasonov tok poslova intenziteta alpha pristiže na procesor. Sva vremena
opsluživanja imaju eksponencijalnu raspodelu, pa je svaki servisni centar
M/M/1 (Džeksonova mreža).

Indeksiranje čvorova (za dato K, ukupno 4 + K čvorova):
    0            -> procesor
    1, 2, 3      -> sistemski diskovi 1, 2, 3
    4 .. 3 + K   -> korisnički diskovi 1 .. K

Sva vremena u kodu su u SEKUNDAMA; u izveštajima se prikazuju u milisekundama.
"""

# ---------------------------------------------------------------------------
# Vremena opsluživanja [s]
# ---------------------------------------------------------------------------
S_PROCESOR = 0.004                        # Sp  = 4 ms
S_SISTEMSKI = (0.010, 0.015, 0.015)       # Sd1 = 10 ms, Sd2 = Sd3 = 15 ms
S_KORISNICKI = 0.025                      # Sdk = 25 ms

# ---------------------------------------------------------------------------
# Verovatnoće tranzicija
# ---------------------------------------------------------------------------
# Posle procesorske obrade:
P_CPU_SISTEMSKI = (0.20, 0.15, 0.10)      # ka 1., 2. i 3. sistemskom disku
P_CPU_KORISNICKI = 0.40                   # ka nekom od K korisničkih (ravnomerno)
P_CPU_CPU = 0.15                          # natrag u procesorski red

# Posle pristupa nekom sistemskom disku:
P_SD_CPU = 0.35                           # bez obrade, natrag u procesorski red
P_SD_ISTI = 0.25                          # ponavlja se obrada na istom disku
P_SD_KORISNICKI = 0.40                    # ka nekom od K korisničkih (ravnomerno)

# Posle pristupa korisničkom disku proces napušta sistem (verovatnoća 1).

# ---------------------------------------------------------------------------
# Opseg parametara zadatka
# ---------------------------------------------------------------------------
K_MIN, K_MAX = 2, 5
K_VREDNOSTI = tuple(range(K_MIN, K_MAX + 1))
R_VREDNOSTI = (0.30, 0.55, 0.80, 1.00)

PODRAZUMEVANO_TRAJANJE_MIN = 30.0         # 0.5 h simuliranog vremena rada sistema
PODRAZUMEVANI_BROJ_PONAVLJANJA = 100
PODRAZUMEVANO_SEME = 20260726             # bazno seme za reproducibilnost

# ---------------------------------------------------------------------------
# Struktura mreže
# ---------------------------------------------------------------------------
IDX_PROCESOR = 0
IDX_SISTEMSKI = (1, 2, 3)
IDX_PRVI_KORISNICKI = 4


def broj_cvorova(K):
    """Ukupan broj servisnih centara u mreži za dato K."""
    return 4 + K


def indeksi_korisnickih(K):
    """Indeksi korisničkih diskova za dato K."""
    return tuple(range(IDX_PRVI_KORISNICKI, IDX_PRVI_KORISNICKI + K))


def imena_cvorova(K):
    """Kratka imena čvorova (za tabele)."""
    imena = ["CPU", "SD1", "SD2", "SD3"]
    imena += [f"KD{i}" for i in range(1, K + 1)]
    return imena


def puna_imena_cvorova(K):
    """Puna imena čvorova (za čitljive izveštaje)."""
    imena = ["Procesor", "Sistemski disk 1", "Sistemski disk 2", "Sistemski disk 3"]
    imena += [f"Korisnički disk {i}" for i in range(1, K + 1)]
    return imena


def tip_cvora(indeks):
    """'procesor' | 'sistemski' | 'korisnicki' — koristi se pri grupisanju rezultata."""
    if indeks == IDX_PROCESOR:
        return "procesor"
    if indeks in IDX_SISTEMSKI:
        return "sistemski"
    return "korisnicki"


def opis_kriticnih(K, indeksi):
    """
    Čitljiv opis skupa kritičnih resursa. Korisnički diskovi su međusobno
    identični, pa se, kada su svi kritični, sažimaju u jedan naziv.
    """
    if not indeksi:
        return "-"
    puna = puna_imena_cvorova(K)
    korisnicki_indeksi = set(indeksi_korisnickih(K))
    korisnicki = [i for i in indeksi if i in korisnicki_indeksi]
    delovi = [puna[i] for i in indeksi if i not in korisnicki_indeksi]
    if len(korisnicki) == K:
        delovi.append("svi korisnički diskovi")
    else:
        delovi.extend(puna[i] for i in korisnicki)
    return " i ".join(delovi)


def vremena_opsluzivanja(K):
    """Vektor srednjih vremena opsluživanja S_i [s]."""
    return [S_PROCESOR, *S_SISTEMSKI] + [S_KORISNICKI] * K


def brzine_servera(K):
    """Vektor brzina servera mi_i = 1 / S_i [1/s]."""
    return [1.0 / s for s in vremena_opsluzivanja(K)]


def matrica_prelaza(K):
    """
    Matrica verovatnoća tranzicija P dimenzija n x n, gde je n = 4 + K.

    P[i][j] je verovatnoća da posao posle opsluživanja u čvoru i pređe u čvor j.
    Suma reda je 1 za procesor i sistemske diskove, a 0 za korisničke diskove
    (posao iz korisničkog diska napušta sistem, pa je verovatnoća izlaska
    1 - suma reda = 1).
    """
    n = broj_cvorova(K)
    P = [[0.0] * n for _ in range(n)]
    kd = indeksi_korisnickih(K)
    p_po_korisnickom = P_CPU_KORISNICKI / K          # ravnomerno po K diskova

    # --- red procesora ---
    for k, j in enumerate(IDX_SISTEMSKI):
        P[IDX_PROCESOR][j] = P_CPU_SISTEMSKI[k]
    for j in kd:
        P[IDX_PROCESOR][j] = p_po_korisnickom
    P[IDX_PROCESOR][IDX_PROCESOR] = P_CPU_CPU

    # --- redovi sistemskih diskova ---
    p_sd_po_korisnickom = P_SD_KORISNICKI / K
    for i in IDX_SISTEMSKI:
        P[i][IDX_PROCESOR] = P_SD_CPU
        P[i][i] = P_SD_ISTI
        for j in kd:
            P[i][j] = p_sd_po_korisnickom

    # --- redovi korisničkih diskova: sve nule (posao izlazi iz sistema) ---
    return P


def verovatnoce_izlaska(K, P=None):
    """Verovatnoća da posao napusti sistem posle opsluživanja u čvoru i."""
    if P is None:
        P = matrica_prelaza(K)
    return [1.0 - sum(red) for red in P]


def proveri_matricu_prelaza(K, tolerancija=1e-12):
    """
    Provera konzistentnosti topologije: svaka verovatnoća je iz [0, 1], a suma
    svakog reda je 1 (procesor, sistemski diskovi) ili 0 (korisnički diskovi).
    Vraća listu poruka o problemima (prazna lista = sve je u redu).
    """
    P = matrica_prelaza(K)
    problemi = []
    for i, red in enumerate(P):
        for j, p in enumerate(red):
            if p < -tolerancija or p > 1.0 + tolerancija:
                problemi.append(f"P[{i}][{j}] = {p} nije iz [0, 1]")
        suma = sum(red)
        ocekivano = 0.0 if i in indeksi_korisnickih(K) else 1.0
        if abs(suma - ocekivano) > 1e-9:
            problemi.append(
                f"suma reda {i} je {suma:.12f}, a očekuje se {ocekivano:.1f}"
            )
    return problemi


def opis_sistema():
    """Kratak tekstualni opis ulaznih parametara — ide u zaglavlja izveštaja."""
    return (
        "Vremena opsluživanja: Sp = 4 ms, Sd1 = 10 ms, Sd2 = Sd3 = 15 ms, "
        "Sdk = 25 ms (eksponencijalna raspodela)\n"
        "Rutiranje posle procesora: 20% SD1, 15% SD2, 10% SD3, "
        "40% korisnički diskovi (ravnomerno), 15% natrag u red procesora\n"
        "Rutiranje posle sistemskog diska: 35% red procesora, 25% isti disk, "
        "40% korisnički diskovi (ravnomerno)\n"
        "Posle korisničkog diska posao napušta sistem."
    )
