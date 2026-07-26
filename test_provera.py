"""
Provere ispravnosti implementacije (pokretanje: py test_provera.py).

Provere ne zahtevaju nikakvu spoljnu biblioteku. Cilj je da se nezavisno
potvrdi da:
  * topologija (matrica P) odgovara postavci zadatka,
  * matrični metod daje rešenje koje se poklapa sa ručno izvedenim,
  * Džeksonove formule su međusobno konzistentne (Litlov zakon),
  * simulacija konvergira ka analitičkom rešenju i sama je konzistentna,
  * rezultati su reproducibilni (isto seme -> isti rezultat).
"""

import math
import sys

import analiticki
import parametri
import simulacija

_neuspesne = []
_ukupno = 0


def proveri(uslov, opis):
    global _ukupno
    _ukupno += 1
    if uslov:
        print(f"  [ok]    {opis}")
    else:
        print(f"  [GRESKA] {opis}")
        _neuspesne.append(opis)


def blizu(a, b, tolerancija=1e-9):
    if math.isinf(a) or math.isinf(b):
        return a == b
    return abs(a - b) <= tolerancija * max(1.0, abs(a), abs(b))


def relativno(a, b):
    return abs(a - b) / abs(b) if b else abs(a - b)


# ---------------------------------------------------------------------------
def test_topologija():
    print("\n1) Topologija (matrica verovatnoća tranzicija)")
    for K in parametri.K_VREDNOSTI:
        proveri(not parametri.proveri_matricu_prelaza(K),
                f"K={K}: sume redova i opseg verovatnoća su ispravni")
        P = parametri.matrica_prelaza(K)
        kd = parametri.indeksi_korisnickih(K)
        proveri(blizu(sum(P[0][j] for j in kd), 0.40),
                f"K={K}: iz procesora ka korisničkim diskovima ukupno 40%")
        proveri(all(blizu(P[0][j], 0.40 / K) for j in kd),
                f"K={K}: korisnički diskovi imaju jednake verovatnoće (0.40/K)")
        proveri(blizu(P[1][1], 0.25) and blizu(P[1][0], 0.35),
                f"K={K}: iz sistemskog diska 25% isti disk, 35% procesor")
        p_izlaz = parametri.verovatnoce_izlaska(K)
        proveri(all(blizu(p_izlaz[j], 1.0) for j in kd),
                f"K={K}: posle korisničkog diska posao napušta sistem")
        proveri(all(blizu(p_izlaz[i], 0.0) for i in (0, 1, 2, 3)),
                f"K={K}: iz procesora i sistemskih diskova nema izlaska iz sistema")


def test_koeficijenti_poseta():
    print("\n2) Matrični metod — koeficijenti poseta")
    for K in parametri.K_VREDNOSTI:
        V = analiticki.koeficijenti_poseta(K)
        kd = parametri.indeksi_korisnickih(K)
        proveri(analiticki.greska_resenja(K, V) < 1e-12,
                f"K={K}: rezidual max|(I - P^T)V - e| je zanemarljiv")
        # ručno izvedene vrednosti: V_cpu = 1/0.64, V_sd = (0.2, 0.15, 0.1)/0.75 * V_cpu
        proveri(blizu(V[0], 1.5625, 1e-12), f"K={K}: V_CPU = 1.5625")
        proveri(blizu(V[1], 0.20 / 0.75 * 1.5625, 1e-12), f"K={K}: V_SD1 = 0.41667")
        proveri(blizu(V[2], 0.15 / 0.75 * 1.5625, 1e-12), f"K={K}: V_SD2 = 0.3125")
        proveri(blizu(V[3], 0.10 / 0.75 * 1.5625, 1e-12), f"K={K}: V_SD3 = 0.20833")
        proveri(all(blizu(V[j], 1.0 / K, 1e-12) for j in kd),
                f"K={K}: svaki korisnički disk ima V = 1/K")
        proveri(blizu(sum(V[j] for j in kd), 1.0, 1e-12),
                f"K={K}: zbir V korisničkih diskova je 1 (jedan izlaz po poslu)")


def test_granicni_intenzitet():
    print("\n3) Granični intenzitet i kritični resurs")
    ocekivano = {2: 80.0, 3: 120.0, 4: 160.0, 5: 160.0}
    for K in parametri.K_VREDNOSTI:
        alpha_max, kriticni, D = analiticki.granicni_intenzitet(K)
        proveri(blizu(alpha_max, ocekivano[K], 1e-9),
                f"K={K}: alpha_max = {ocekivano[K]:.0f} 1/s")
        tipovi = {parametri.tip_cvora(i) for i in kriticni}
        if K in (2, 3):
            proveri(tipovi == {"korisnicki"},
                    f"K={K}: kritični resurs su korisnički diskovi")
        elif K == 4:
            proveri(tipovi == {"procesor", "korisnicki"},
                    "K=4: kritični su i procesor i korisnički diskovi (isti zahtev)")
        else:
            proveri(tipovi == {"procesor"}, "K=5: kritični resurs je procesor")
        proveri(blizu(max(D), 1.0 / alpha_max, 1e-12),
                f"K={K}: alpha_max = 1 / max(D_i)")


def test_dzekson():
    print("\n4) Džeksonova teorema — konzistentnost formula")
    for K in parametri.K_VREDNOSTI:
        V = analiticki.koeficijenti_poseta(K)
        alpha_max, _, _ = analiticki.granicni_intenzitet(K, V)
        for r in (0.30, 0.55, 0.80):
            rez = analiticki.dzeksonova_analiza(K, r * alpha_max, r, V)
            proveri(all(blizu(c.N, c.X * c.W, 1e-9) for c in rez.cvorovi),
                    f"K={K}, r={r}: Litlov zakon po čvoru (N_i = X_i * W_i)")
            proveri(blizu(rez.T_sistem, rez.dodatno["T_sistem_suma_VW"], 1e-9),
                    f"K={K}, r={r}: T = N/alpha = suma V_i * W_i")
            proveri(blizu(rez.X_sistem, rez.alpha, 1e-9),
                    f"K={K}, r={r}: izlazni protok jednak ulaznom toku")
            rho_max = max(c.rho for c in rez.cvorovi)
            proveri(blizu(rho_max, r, 1e-9),
                    f"K={K}, r={r}: iskorišćenje kritičnog resursa je tačno r")
        rez = analiticki.dzeksonova_analiza(K, alpha_max, 1.0, V)
        proveri(not rez.stabilan and math.isinf(rez.T_sistem),
                f"K={K}, r=1.00: sistem je zasićen, T_sistem = beskonačno")


def test_simulacija_konzistentnost():
    print("\n5) Simulacija — unutrašnja konzistentnost")
    K, r = 3, 0.55
    V = analiticki.koeficijenti_poseta(K)
    alpha_max, _, _ = analiticki.granicni_intenzitet(K, V)
    alpha = r * alpha_max
    mer = simulacija.simuliraj(K, alpha, 600.0, seme=12345)

    proveri(relativno(mer.broj_dolazaka / mer.trajanje, alpha) < 0.02,
            "izmereni intenzitet spoljnih dolazaka odgovara zadatom alpha")
    proveri(abs(mer.broj_dolazaka - mer.broj_izlazaka)
            <= max(20, 0.01 * mer.broj_dolazaka),
            "broj poslova koji su ušli i izašli iz sistema se poklapa")
    kd = parametri.indeksi_korisnickih(K)
    proveri(relativno(sum(mer.X[j] for j in kd), alpha) < 0.02,
            "zbir protoka korisničkih diskova jednak je ulaznom toku")
    proveri(all(relativno(mer.N[i], mer.X[i] * mer.W[i]) < 1e-9
                for i in range(parametri.broj_cvorova(K))),
            "Litlov zakon po čvoru u simulaciji (N_i = X_i * W_i)")
    proveri(relativno(mer.N_sistem / alpha, mer.T_sistem_mereno) < 0.03,
            "Litlov zakon za ceo sistem (N/alpha ~ izmereno vreme u sistemu)")
    proveri(all(0.0 <= rho <= 1.0 for rho in mer.rho),
            "sva iskorišćenja su u opsegu [0, 1]")


def test_simulacija_vs_analitika():
    print("\n6) Simulacija vs analitika (duža simulacija, fiksno seme)")
    for K, r, tol_rho, tol_N in ((2, 0.30, 0.03, 0.08), (5, 0.55, 0.03, 0.08)):
        V = analiticki.koeficijenti_poseta(K)
        alpha_max, _, _ = analiticki.granicni_intenzitet(K, V)
        alpha = r * alpha_max
        an = analiticki.dzeksonova_analiza(K, alpha, r, V)
        mer = simulacija.simuliraj(K, alpha, 1200.0, seme=987)
        najgore_rho = max(relativno(mer.rho[i], an.cvorovi[i].rho)
                          for i in range(parametri.broj_cvorova(K)))
        najgore_N = max(relativno(mer.N[i], an.cvorovi[i].N)
                        for i in range(parametri.broj_cvorova(K)))
        proveri(najgore_rho < tol_rho,
                f"K={K}, r={r}: iskorišćenja odstupaju manje od "
                f"{tol_rho * 100:.0f}% (najviše {najgore_rho * 100:.2f}%)")
        proveri(najgore_N < tol_N,
                f"K={K}, r={r}: broj poslova odstupa manje od "
                f"{tol_N * 100:.0f}% (najviše {najgore_N * 100:.2f}%)")
        proveri(relativno(mer.T_sistem_mereno, an.T_sistem) < tol_N,
                f"K={K}, r={r}: vreme odziva sistema odstupa manje od "
                f"{tol_N * 100:.0f}%")


def test_reproducibilnost():
    print("\n7) Reproducibilnost i usrednjavanje")
    a = simulacija.simuliraj(4, 60.0, 300.0, seme=2024)
    b = simulacija.simuliraj(4, 60.0, 300.0, seme=2024)
    c = simulacija.simuliraj(4, 60.0, 300.0, seme=2025)
    proveri(a.rho == b.rho and a.N == b.N and a.T_sistem_mereno == b.T_sistem_mereno,
            "isto seme daje identičan rezultat")
    proveri(a.rho != c.rho, "različito seme daje različit rezultat")

    lista = [simulacija.simuliraj(4, 60.0, 300.0, seme=s) for s in range(5)]
    usr = simulacija.usrednji(lista, 0.375, 160.0)
    ocekivano = sum(m.rho[0] for m in lista) / len(lista)
    proveri(blizu(usr.cvorovi[0].rho, ocekivano, 1e-12),
            "usrednjavanje daje aritmetičku sredinu ponavljanja")
    proveri(usr.dodatno["broj_ponavljanja"] == 5 and usr.dodatno["std_rho"][0] > 0,
            "usrednjeni rezultat pamti broj ponavljanja i standardnu devijaciju")

    # seme_za mora da da različita semena za različite kombinacije
    semena = {simulacija.seme_za(1, K, i, p)
              for K in parametri.K_VREDNOSTI for i in range(4) for p in range(100)}
    proveri(len(semena) == len(parametri.K_VREDNOSTI) * 4 * 100,
            "sva izvedena semena su međusobno različita")


def main():
    print("=" * 72)
    print("PROVERE ISPRAVNOSTI")
    print("=" * 72)
    test_topologija()
    test_koeficijenti_poseta()
    test_granicni_intenzitet()
    test_dzekson()
    test_simulacija_konzistentnost()
    test_simulacija_vs_analitika()
    test_reproducibilnost()

    print()
    print("=" * 72)
    if _neuspesne:
        print(f"NEUSPEŠNO: {len(_neuspesne)} od {_ukupno} provera")
        for opis in _neuspesne:
            print(f"  - {opis}")
        return 1
    print(f"SVE PROVERE PROŠLE ({_ukupno})")
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    sys.exit(main())
