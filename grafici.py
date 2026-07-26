"""
Crtanje traženih dijagrama (matplotlib).

Dijagrami se prave na osnovu analitičkih rezultata (kako zadatak traži), uz
dodatna dva skupa dijagrama koji analitiku porede sa simulacijom.

  alpha_max_vs_K.png                 - granični intenzitet u funkciji od K
  iskoriscenja_r{rr}.png             - rho(K) za procesor, sistemske i korisnički disk
  vremena_odziva_servera_r{rr}.png   - W(K) za procesor, sistemske i korisnički disk
  vreme_odziva_sistema_r{rr}.png     - T_sistem(K)
  poredjenje_T_sistem_r{rr}.png      - T_sistem(K): analitika vs simulacija (dodatno)
  poredjenje_iskoriscenja_r{rr}.png  - rho(K): analitika vs simulacija (dodatno)

Za r = 1.00 kritični resurs ima rho = 1, pa su N, W i T_sistem beskonačni —
takve tačke se ne mogu nacrtati i na dijagramu se eksplicitno naglašavaju.
"""

import math
import os

import matplotlib

matplotlib.use("Agg")   # crtanje u fajl, bez grafičkog okruženja

import matplotlib.pyplot as plt   # noqa: E402

import parametri   # noqa: E402

# (oznaka u legendi, boja, marker) za pet krivih koje se crtaju zajedno
STIL = {
    "CPU": ("Procesor", "#1f77b4", "o", "-"),
    "SD1": ("Sistemski disk 1 (10 ms)", "#d62728", "s", "--"),
    "SD2": ("Sistemski disk 2 (15 ms)", "#2ca02c", "^", "--"),
    "SD3": ("Sistemski disk 3 (15 ms)", "#9467bd", "v", "--"),
    "KD": ("Korisnički disk (25 ms)", "#ff7f0e", "D", "-"),
}
REDOSLED = ("CPU", "SD1", "SD2", "SD3", "KD")


def oznaka_r(r):
    """r = 0.55 -> 'r055' (za imena fajlova)."""
    return f"r{int(round(r * 100)):03d}"


def _vrednost(rez, kljuc, atribut):
    """Vrednost metrike za jednu od pet krivih ('CPU', 'SD1', ..., 'KD')."""
    if kljuc == "KD":
        return rez.korisnicki_prosek(atribut)
    for c in rez.cvorovi:
        if c.ime == kljuc:
            return getattr(c, atribut)
    raise KeyError(kljuc)


def _konacne_tacke(x, y):
    """Zadržava samo parove sa konačnim y (beskonačne vrednosti se ne crtaju)."""
    parovi = [(xi, yi) for xi, yi in zip(x, y) if yi is not None and math.isfinite(yi)]
    if not parovi:
        return [], []
    return [p[0] for p in parovi], [p[1] for p in parovi]


def _napomena_o_beskonacnim(ax, x, y, tekst):
    """Ako neka tačka nije konačna, upisuje napomenu na dijagram."""
    beskonacne = [xi for xi, yi in zip(x, y) if yi is None or not math.isfinite(yi)]
    if beskonacne:
        ax.text(
            0.02,
            0.96,
            f"{tekst}\nK = {', '.join(str(k) for k in sorted(set(beskonacne)))}",
            transform=ax.transAxes,
            va="top",
            ha="left",
            fontsize=8,
            bbox=dict(boxstyle="round", facecolor="#fff3cd", edgecolor="#c8a415"),
        )
    return bool(beskonacne)


def _uredi(ax, naslov, x_oznaka, y_oznaka, K_vrednosti):
    ax.set_title(naslov)
    ax.set_xlabel(x_oznaka)
    ax.set_ylabel(y_oznaka)
    ax.set_xticks(list(K_vrednosti))
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="best", fontsize=9)


def _sacuvaj(fig, direktorijum, ime):
    putanja = os.path.join(direktorijum, ime)
    fig.tight_layout()
    fig.savefig(putanja, dpi=150)
    plt.close(fig)
    return putanja


# ---------------------------------------------------------------------------
# alpha_max(K)
# ---------------------------------------------------------------------------
def crtaj_granicni_intenzitet(direktorijum, tabela):
    """tabela = lista (K, alpha_max, kriticni_indeksi, D_max) iz analiticki.py."""
    K = [red[0] for red in tabela]
    alpha_max = [red[1] for red in tabela]

    fig, ax = plt.subplots(figsize=(7.5, 5))
    ax.plot(K, alpha_max, color="#1f77b4", marker="o", linewidth=2,
            label=r"$\alpha_{max}(K) = 1 / \max_i(V_i S_i)$")

    for k, am, kriticni, _ in tabela:
        puna = parametri.puna_imena_cvorova(k)
        # kritični resursi istog tipa se sažimaju u jedan naziv
        if all(parametri.tip_cvora(i) == "korisnicki" for i in kriticni):
            opis = "korisnički diskovi"
        elif len(kriticni) == 1:
            opis = puna[kriticni[0]]
        else:
            opis = "procesor i korisnički diskovi"
        ax.annotate(
            f"{am:.0f} 1/s\n({opis})",
            xy=(k, am),
            xytext=(0, -34 if k < 4 else 12),
            textcoords="offset points",
            ha="center",
            fontsize=8,
        )

    ax.set_ylim(0, max(alpha_max) * 1.25)
    ax.set_xlim(min(K) - 0.35, max(K) + 0.35)
    _uredi(
        ax,
        "Granični intenzitet ulaznog toka u funkciji od broja korisničkih diskova",
        "K (broj korisničkih diskova)",
        r"$\alpha_{max}$ [1/s]",
        K,
    )
    return _sacuvaj(fig, direktorijum, "alpha_max_vs_K.png")


# ---------------------------------------------------------------------------
# rho(K) i W(K) za fiksno r
# ---------------------------------------------------------------------------
def crtaj_iskoriscenja(direktorijum, analitika, r, K_vrednosti=None):
    if K_vrednosti is None:
        K_vrednosti = parametri.K_VREDNOSTI
    fig, ax = plt.subplots(figsize=(7.5, 5))
    for kljuc in REDOSLED:
        ime, boja, marker, stil = STIL[kljuc]
        y = [_vrednost(analitika[(K, r)], kljuc, "rho") for K in K_vrednosti]
        ax.plot(K_vrednosti, y, color=boja, marker=marker, linestyle=stil,
                linewidth=1.8, markersize=7, label=ime)
    ax.axhline(1.0, color="black", linewidth=1, linestyle=":")
    ax.text(K_vrednosti[0], 1.005, r"granica stabilnosti $\rho = 1$", fontsize=8)
    ax.set_ylim(0, 1.12)
    _uredi(
        ax,
        f"Iskorišćenje resursa u funkciji od K   (r = {r:.2f}, "
        r"$\alpha = r\,\alpha_{max}$)",
        "K (broj korisničkih diskova)",
        r"iskorišćenje $\rho$",
        K_vrednosti,
    )
    return _sacuvaj(fig, direktorijum, f"iskoriscenja_{oznaka_r(r)}.png")


def crtaj_vremena_odziva_servera(direktorijum, analitika, r, K_vrednosti=None):
    if K_vrednosti is None:
        K_vrednosti = parametri.K_VREDNOSTI
    fig, ax = plt.subplots(figsize=(7.5, 5))
    ima_beskonacnih = False
    for kljuc in REDOSLED:
        ime, boja, marker, stil = STIL[kljuc]
        y = [
            _vrednost(analitika[(K, r)], kljuc, "W") * 1000.0 for K in K_vrednosti
        ]
        xs, ys = _konacne_tacke(K_vrednosti, y)
        ax.plot(xs, ys, color=boja, marker=marker, linestyle=stil,
                linewidth=1.8, markersize=7, label=ime)
        if any(not math.isfinite(v) for v in y):
            ima_beskonacnih = True
    if ima_beskonacnih:
        ax.text(
            0.02, 0.96,
            "Nedostaju tačke za zasićene resurse:\n"
            r"$\rho = 1 \Rightarrow W = S/(1-\rho) \to \infty$",
            transform=ax.transAxes, va="top", ha="left", fontsize=8,
            bbox=dict(boxstyle="round", facecolor="#fff3cd", edgecolor="#c8a415"),
        )
    _uredi(
        ax,
        f"Vreme odziva servera (po prolazu) u funkciji od K   (r = {r:.2f})",
        "K (broj korisničkih diskova)",
        "W [ms]",
        K_vrednosti,
    )
    return _sacuvaj(fig, direktorijum, f"vremena_odziva_servera_{oznaka_r(r)}.png")


def crtaj_vreme_odziva_sistema(direktorijum, analitika, r, K_vrednosti=None):
    if K_vrednosti is None:
        K_vrednosti = parametri.K_VREDNOSTI
    y = [analitika[(K, r)].T_sistem * 1000.0 for K in K_vrednosti]
    fig, ax = plt.subplots(figsize=(7.5, 5))
    xs, ys = _konacne_tacke(K_vrednosti, y)
    ax.plot(xs, ys, color="#8c564b", marker="o", linewidth=2, markersize=8,
            label=r"$T_{sistem}(K) = N/\alpha = \sum_i V_i W_i$")
    for x, v in zip(xs, ys):
        ax.annotate(f"{v:.2f}", xy=(x, v), xytext=(0, 8),
                    textcoords="offset points", ha="center", fontsize=8)
    if not xs:
        # Sve tačke su beskonačne (r = 1.00). Da dijagram ne bi ostao prazan,
        # dodaje se referentna kriva za r nešto manje od 1, koja pokazuje kako
        # T_sistem eksplodira pri približavanju granici kapaciteta.
        import analiticki   # lokalni import: potreban samo u ovom slučaju

        r_ref = 0.99
        y_ref = []
        for K in K_vrednosti:
            V = analiticki.koeficijenti_poseta(K)
            alpha_max, _, _ = analiticki.granicni_intenzitet(K, V)
            rez = analiticki.dzeksonova_analiza(K, r_ref * alpha_max, r_ref, V)
            y_ref.append(rez.T_sistem * 1000.0)
        ax.plot(K_vrednosti, y_ref, color="#7f7f7f", marker="s", linestyle="--",
                linewidth=1.5, markersize=7,
                label=f"referentno: r = {r_ref:.2f} (konačno)")
        for x, v in zip(K_vrednosti, y_ref):
            ax.annotate(f"{v:.1f}", xy=(x, v), xytext=(0, 8),
                        textcoords="offset points", ha="center", fontsize=8)
        ax.set_ylim(0, max(y_ref) * 1.35)
        ax.text(0.5, 0.13,
                "Za r = 1.00 je " r"$\rho = 1$" " za kritični resurs, pa je\n"
                r"$T_{sistem} \to \infty$ za svako K — nema tačaka za crtanje."
                "\nSiva kriva je vrednost za r = 0.99, radi poređenja.",
                transform=ax.transAxes, ha="center", va="center", fontsize=9,
                bbox=dict(boxstyle="round", facecolor="#fff3cd",
                          edgecolor="#c8a415"))
    else:
        _napomena_o_beskonacnim(
            ax, K_vrednosti, y,
            r"$T_{sistem} \to \infty$ (zasićen kritični resurs) za:"
        )
    _uredi(
        ax,
        f"Vreme odziva sistema u funkciji od K   (r = {r:.2f})",
        "K (broj korisničkih diskova)",
        r"$T_{sistem}$ [ms]",
        K_vrednosti,
    )
    return _sacuvaj(fig, direktorijum, f"vreme_odziva_sistema_{oznaka_r(r)}.png")


# ---------------------------------------------------------------------------
# Dodatni dijagrami: analitika vs simulacija
# ---------------------------------------------------------------------------
def crtaj_poredjenje_vremena_odziva(direktorijum, analitika, simulacija_1,
                                    usrednjeno, r, K_vrednosti=None):
    if K_vrednosti is None:
        K_vrednosti = parametri.K_VREDNOSTI
    fig, ax = plt.subplots(figsize=(7.5, 5))
    skupovi = (
        ("Analitika (Džekson)", analitika, "#1f77b4", "o", "-"),
        ("Simulacija (1 izvršavanje)", simulacija_1, "#d62728", "x", "--"),
        ("Simulacija (usrednjeno)", usrednjeno, "#2ca02c", "s", ":"),
    )
    for ime, izvor, boja, marker, stil in skupovi:
        y = [izvor[(K, r)].T_sistem * 1000.0 for K in K_vrednosti]
        xs, ys = _konacne_tacke(K_vrednosti, y)
        ax.plot(xs, ys, color=boja, marker=marker, linestyle=stil,
                linewidth=1.8, markersize=8, label=ime)
    if r >= 1.0:
        ax.text(
            0.02, 0.96,
            "Analitički je " r"$T_{sistem} = \infty$" " (zasićenje),\n"
            "a simulacija daje konačnu vrednost koja\nzavisi od dužine simulacije.",
            transform=ax.transAxes, va="top", ha="left", fontsize=8,
            bbox=dict(boxstyle="round", facecolor="#fff3cd", edgecolor="#c8a415"),
        )
    _uredi(
        ax,
        f"Vreme odziva sistema: analitika vs simulacija   (r = {r:.2f})",
        "K (broj korisničkih diskova)",
        r"$T_{sistem}$ [ms]",
        K_vrednosti,
    )
    return _sacuvaj(fig, direktorijum, f"poredjenje_T_sistem_{oznaka_r(r)}.png")


def crtaj_poredjenje_iskoriscenja(direktorijum, analitika, usrednjeno, r,
                                  K_vrednosti=None):
    if K_vrednosti is None:
        K_vrednosti = parametri.K_VREDNOSTI
    fig, ax = plt.subplots(figsize=(7.5, 5))
    for kljuc in REDOSLED:
        ime, boja, marker, stil = STIL[kljuc]
        ya = [_vrednost(analitika[(K, r)], kljuc, "rho") for K in K_vrednosti]
        yu = [_vrednost(usrednjeno[(K, r)], kljuc, "rho") for K in K_vrednosti]
        ax.plot(K_vrednosti, ya, color=boja, linestyle=stil, linewidth=1.6,
                label=f"{ime} — analitika")
        ax.plot(K_vrednosti, yu, color=boja, linestyle="none", marker=marker,
                markersize=8, markerfacecolor="none", label=f"{ime} — simulacija")
    ax.set_ylim(0, 1.12)
    ax.legend(loc="best", fontsize=7, ncol=2)
    ax.set_title(
        f"Iskorišćenje resursa: analitika vs usrednjena simulacija   (r = {r:.2f})"
    )
    ax.set_xlabel("K (broj korisničkih diskova)")
    ax.set_ylabel(r"iskorišćenje $\rho$")
    ax.set_xticks(list(K_vrednosti))
    ax.grid(True, linestyle=":", alpha=0.6)
    return _sacuvaj(fig, direktorijum, f"poredjenje_iskoriscenja_{oznaka_r(r)}.png")


# ---------------------------------------------------------------------------
# Sve odjednom
# ---------------------------------------------------------------------------
def nacrtaj_sve(direktorijum, analitika, tabela_granicnih, simulacija_1=None,
                usrednjeno=None, K_vrednosti=None, r_vrednosti=None):
    """Crta sve dijagrame i vraća listu putanja do napravljenih fajlova."""
    if K_vrednosti is None:
        K_vrednosti = parametri.K_VREDNOSTI
    if r_vrednosti is None:
        r_vrednosti = parametri.R_VREDNOSTI
    os.makedirs(direktorijum, exist_ok=True)

    putanje = [crtaj_granicni_intenzitet(direktorijum, tabela_granicnih)]
    for r in r_vrednosti:
        putanje.append(crtaj_iskoriscenja(direktorijum, analitika, r, K_vrednosti))
        putanje.append(
            crtaj_vremena_odziva_servera(direktorijum, analitika, r, K_vrednosti)
        )
        putanje.append(
            crtaj_vreme_odziva_sistema(direktorijum, analitika, r, K_vrednosti)
        )
    if simulacija_1 and usrednjeno:
        for r in r_vrednosti:
            putanje.append(
                crtaj_poredjenje_vremena_odziva(
                    direktorijum, analitika, simulacija_1, usrednjeno, r, K_vrednosti
                )
            )
            putanje.append(
                crtaj_poredjenje_iskoriscenja(
                    direktorijum, analitika, usrednjeno, r, K_vrednosti
                )
            )
    return putanje
