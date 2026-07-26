"""
Minimalna linearna algebra potrebna za matrični metod rešavanja otvorenih mreža.

Namerno je implementirana "od nule" (bez numpy-a) da bi program mogao da se
pokrene na svakoj standardnoj Python instalaciji i da bi matrični metod
sa predavanja bio vidljiv u kodu.
"""


class SingularnaMatrica(Exception):
    """Sistem jednačina nema jedinstveno rešenje."""


def jedinicna(n):
    """Jedinična matrica I dimenzija n x n."""
    return [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]


def transponuj(A):
    """Transponovana matrica A^T."""
    return [list(kolona) for kolona in zip(*A)]


def razlika(A, B):
    """Razlika matrica A - B."""
    return [[a - b for a, b in zip(red_a, red_b)] for red_a, red_b in zip(A, B)]


def pomnozi_matricu_vektorom(A, x):
    """Proizvod A * x."""
    return [sum(a * xi for a, xi in zip(red, x)) for red in A]


def resi_sistem(A, b, tolerancija=1e-12):
    """
    Rešava sistem linearnih jednačina A * x = b Gausovom eliminacijom sa
    parcijalnim pivotiranjem. Matrica A i vektor b se ne menjaju.

    Vraća listu x. Diže SingularnaMatrica ako je sistem singularan.
    """
    n = len(A)
    if any(len(red) != n for red in A) or len(b) != n:
        raise ValueError("dimenzije matrice A i vektora b se ne poklapaju")

    # proširena matrica [A | b] — radimo nad kopijom
    M = [list(red) + [b[i]] for i, red in enumerate(A)]

    for kolona in range(n):
        # --- parcijalno pivotiranje: najveći element po apsolutnoj vrednosti ---
        pivot_red = max(range(kolona, n), key=lambda r: abs(M[r][kolona]))
        if abs(M[pivot_red][kolona]) < tolerancija:
            raise SingularnaMatrica(
                f"matrica je singularna (pivot u koloni {kolona} je ~0)"
            )
        if pivot_red != kolona:
            M[kolona], M[pivot_red] = M[pivot_red], M[kolona]

        pivot = M[kolona][kolona]
        # --- eliminacija ispod pivota ---
        for red in range(kolona + 1, n):
            faktor = M[red][kolona] / pivot
            if faktor == 0.0:
                continue
            M[red][kolona] = 0.0
            for k in range(kolona + 1, n + 1):
                M[red][k] -= faktor * M[kolona][k]

    # --- povratna substitucija ---
    x = [0.0] * n
    for red in range(n - 1, -1, -1):
        suma = M[red][n] - sum(M[red][k] * x[k] for k in range(red + 1, n))
        x[red] = suma / M[red][red]
    return x


def maksimalna_greska_resenja(A, x, b):
    """
    Norma reziduala max|A*x - b| — koristi se kao kontrola tačnosti rešenja
    dobijenog Gausovom eliminacijom.
    """
    Ax = pomnozi_matricu_vektorom(A, x)
    return max(abs(v - bi) for v, bi in zip(Ax, b))
