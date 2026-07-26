"""
Generisanje dokumentacije (dokumentacija.md i dokumentacija.html).

Dokument se sastavlja iz blokova (naslov, pasus, lista, tabela, slika, kod)
i zatim renderuje u dva formata: Markdown (za čitanje i dalju obradu) i
samostalan HTML (za štampu iz veb čitača). Tabele se popunjavaju iz stvarno
izračunatih rezultata, pa dokumentacija uvek odgovara poslednjem pokretanju
programa.
"""

import html as _html
import math
import os
import re

import analiticki
import parametri
import poredjenje

# ---------------------------------------------------------------------------
# Blokovi dokumenta
# ---------------------------------------------------------------------------
def h(nivo, tekst):
    return ("h", nivo, tekst)


def p(tekst):
    return ("p", tekst)


def ul(stavke):
    return ("ul", list(stavke))


def tabela(zaglavlje, redovi, opis=None):
    return ("tabela", list(zaglavlje), [list(r) for r in redovi], opis)


def slika(putanja, opis):
    return ("slika", putanja, opis)


def kod(tekst):
    return ("kod", tekst)


# ---------------------------------------------------------------------------
# Formatiranje brojeva
# ---------------------------------------------------------------------------
def fb(x, decimale=4):
    """Broj -> string; beskonačno i nedefinisano dobijaju posebne oznake."""
    if x is None:
        return "—"
    if isinstance(x, float):
        if math.isinf(x):
            return "∞"
        if math.isnan(x):
            return "—"
    return f"{x:.{decimale}f}"


def fp(x, decimale=3):
    """Relativno odstupanje u procentima (sa predznakom)."""
    if x is None:
        return "—"
    return f"{x:+.{decimale}f}"


# ---------------------------------------------------------------------------
# Render: Markdown
# ---------------------------------------------------------------------------
def u_markdown(blokovi):
    izlaz = []
    for blok in blokovi:
        vrsta = blok[0]
        if vrsta == "h":
            izlaz.append(f"{'#' * blok[1]} {blok[2]}\n")
        elif vrsta == "p":
            izlaz.append(f"{blok[1]}\n")
        elif vrsta == "ul":
            izlaz.append("\n".join(f"- {s}" for s in blok[1]) + "\n")
        elif vrsta == "tabela":
            _, zaglavlje, redovi, opis = blok
            if opis:
                izlaz.append(f"**{opis}**\n")
            izlaz.append("| " + " | ".join(zaglavlje) + " |")
            izlaz.append("|" + "|".join("---" for _ in zaglavlje) + "|")
            for red in redovi:
                izlaz.append("| " + " | ".join(str(c) for c in red) + " |")
            izlaz.append("")
        elif vrsta == "slika":
            izlaz.append(f"![{blok[2]}]({blok[1]})\n")
            izlaz.append(f"*{blok[2]}*\n")
        elif vrsta == "kod":
            izlaz.append("```\n" + blok[1].rstrip() + "\n```\n")
    return "\n".join(izlaz)


# ---------------------------------------------------------------------------
# Render: HTML (samostalan fajl, spreman za štampu)
# ---------------------------------------------------------------------------
_STIL = """
body { font-family: "Segoe UI", Arial, sans-serif; max-width: 1000px;
       margin: 0 auto; padding: 24px; line-height: 1.5; color: #1b1b1b; }
h1 { border-bottom: 3px solid #1f77b4; padding-bottom: 6px; }
h2 { border-bottom: 1px solid #bbb; padding-bottom: 4px; margin-top: 32px; }
h3 { margin-top: 24px; }
table { border-collapse: collapse; margin: 12px 0; font-size: 13px; }
th, td { border: 1px solid #999; padding: 4px 9px; text-align: right; }
th { background: #eef3f8; }
td:first-child, th:first-child { text-align: left; }
tr:nth-child(even) td { background: #fafafa; }
img { max-width: 100%; border: 1px solid #ddd; margin-top: 10px; }
figcaption { font-style: italic; color: #555; font-size: 13px;
             margin-bottom: 18px; }
code, pre { font-family: Consolas, "Courier New", monospace; }
pre { background: #f5f5f5; border: 1px solid #ddd; padding: 10px;
      overflow-x: auto; font-size: 13px; }
.opis { font-weight: bold; margin-bottom: 4px; }
@media print { h2 { page-break-before: auto; } img { page-break-inside: avoid; } }
"""


def _inline_html(tekst):
    t = _html.escape(tekst)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
    return t


def u_html(blokovi, naslov_dokumenta):
    izlaz = [
        "<!DOCTYPE html>",
        '<html lang="sr"><head><meta charset="utf-8">',
        f"<title>{_html.escape(naslov_dokumenta)}</title>",
        f"<style>{_STIL}</style></head><body>",
    ]
    for blok in blokovi:
        vrsta = blok[0]
        if vrsta == "h":
            izlaz.append(f"<h{blok[1]}>{_inline_html(blok[2])}</h{blok[1]}>")
        elif vrsta == "p":
            izlaz.append(f"<p>{_inline_html(blok[1])}</p>")
        elif vrsta == "ul":
            izlaz.append("<ul>")
            izlaz += [f"<li>{_inline_html(s)}</li>" for s in blok[1]]
            izlaz.append("</ul>")
        elif vrsta == "tabela":
            _, zaglavlje, redovi, opis = blok
            if opis:
                izlaz.append(f'<div class="opis">{_inline_html(opis)}</div>')
            izlaz.append("<table><thead><tr>")
            izlaz += [f"<th>{_inline_html(str(c))}</th>" for c in zaglavlje]
            izlaz.append("</tr></thead><tbody>")
            for red in redovi:
                izlaz.append("<tr>")
                izlaz += [f"<td>{_inline_html(str(c))}</td>" for c in red]
                izlaz.append("</tr>")
            izlaz.append("</tbody></table>")
        elif vrsta == "slika":
            izlaz.append(
                f'<figure><img src="{_html.escape(blok[1])}" alt="'
                f'{_html.escape(blok[2])}">'
                f"<figcaption>{_inline_html(blok[2])}</figcaption></figure>"
            )
        elif vrsta == "kod":
            izlaz.append(f"<pre>{_html.escape(blok[1].rstrip())}</pre>")
    izlaz.append("</body></html>")
    return "\n".join(izlaz)


# ---------------------------------------------------------------------------
# Sadržaj dokumenta
# ---------------------------------------------------------------------------
def _blokovi_uvod(argumenti):
    b = [
        h(1, "Performanse računarskih sistema — analiza i simulacija otvorene mreže"),
        p("Ovaj dokument opisuje analitičko rešavanje i simulaciju multiprogramskog "
          "računara modelovanog otvorenom mrežom sa procesorom, tri sistemska diska "
          "i **K** korisničkih diskova (K = 2..5), i poredi dobijene rezultate. "
          "Sve tabele u dokumentu generisane su iz stvarnih rezultata programa."),
        h(2, "1. Opis sistema i model"),
        p("Poasonov tok poslova intenziteta α pristiže na procesor. Vremena "
          "opsluživanja su eksponencijalna, a redovi su neograničeni sa FCFS "
          "disciplinom, pa je svaki servisni centar M/M/1 sistem, a cela mreža "
          "otvorena **Džeksonova mreža**."),
        tabela(
            ["Server", "Oznaka", "Srednje vreme opsluživanja S_i", "μ_i = 1/S_i [1/s]"],
            [
                ["Procesor", "CPU", "4 ms", "250"],
                ["Sistemski disk 1", "SD1", "10 ms", "100"],
                ["Sistemski disk 2", "SD2", "15 ms", "66.667"],
                ["Sistemski disk 3", "SD3", "15 ms", "66.667"],
                ["Korisnički disk (svaki od K)", "KD", "25 ms", "40"],
            ],
            "Parametri servisnih centara",
        ),
        p("Verovatnoće tranzicija (matrica **P**):"),
        ul([
            "posle procesora: 20% SD1, 15% SD2, 10% SD3, 40% neki od K korisničkih "
            "diskova (po 0.40/K), 15% povratak u red procesora;",
            "posle sistemskog diska: 35% red procesora, 25% ponovo isti disk, "
            "40% neki od K korisničkih diskova (po 0.40/K);",
            "posle korisničkog diska: posao napušta sistem (verovatnoća 1).",
        ]),
        p("Zbir verovatnoća u redovima procesora i sistemskih diskova je 1 — iz tih "
          "čvorova posao ne može da napusti sistem; jedini izlaz iz sistema je preko "
          "korisničkog diska. Program to eksplicitno proverava pre računanja "
          "(`parametri.proveri_matricu_prelaza`)."),
    ]
    if argumenti is not None:
        b.append(p(
            f"Parametri pokretanja koji su dali rezultate u ovom dokumentu: "
            f"simulirano vreme rada sistema **{argumenti.minuti:g} min** po "
            f"izvršavanju, **{argumenti.ponavljanja}** ponavljanja po kombinaciji "
            f"(K, r), bazno seme generatora slučajnih brojeva "
            f"**{argumenti.seme}**."
        ))
    return b


def _blokovi_analitika(analitika, tabela_granicnih):
    K_vrednosti = parametri.K_VREDNOSTI
    r_vrednosti = parametri.R_VREDNOSTI

    b = [
        h(2, "2. Analitičko rešavanje"),
        h(3, "2.1 Matrični metod — protoci kroz servere"),
        p("Za otvorenu mrežu važe jednačine ravnoteže protoka: protok kroz server i "
          "jednak je zbiru spoljnog toka koji ulazi u taj server i svih unutrašnjih "
          "tokova koji u njega dolaze iz ostalih servera:"),
        kod("lambda_i = alpha_i + suma_j ( lambda_j * P[j][i] )\n\n"
            "odnosno matrično:   (I - P^T) * lambda = alpha_vektor"),
        p("Pošto ceo spoljni tok ulazi u procesor, važi alpha_vektor = α·e, gde je "
          "e = [1, 0, …, 0]ᵀ. Deljenjem sa α dobija se sistem koji ne zavisi od α:"),
        kod("(I - P^T) * V = e,      V_i = lambda_i / alpha = X_i / alpha"),
        p("V_i je koeficijent poseta, tj. traženi odnos protoka kroz server i "
          "intenziteta ulaznog toka. Sistem se u programu rešava Gausovom "
          "eliminacijom sa parcijalnim pivotiranjem (`linearna_algebra.resi_sistem`), "
          "a tačnost se kontroliše rezidualom max|(I − Pᵀ)V − e| (reda 10⁻¹⁶). "
          "Protoci su onda linearne funkcije ulaznog toka: **X_i(α) = V_i · α**."),
    ]

    zaglavlje = ["K"] + [f"V_{ime}" for ime in ("CPU", "SD1", "SD2", "SD3")] + [
        "V_KD (po disku)", "Σ V_KD"
    ]
    redovi = []
    for K in K_vrednosti:
        V = analiticki.koeficijenti_poseta(K)
        kd = parametri.indeksi_korisnickih(K)
        redovi.append([
            K, fb(V[0], 6), fb(V[1], 6), fb(V[2], 6), fb(V[3], 6),
            fb(V[kd[0]], 6), fb(sum(V[i] for i in kd), 6),
        ])
    b.append(tabela(zaglavlje, redovi,
                    "Koeficijenti poseta V_i = X_i/α (rešenje sistema (I − Pᵀ)V = e)"))
    b.append(p(
        "Koeficijenti poseta procesora i sistemskih diskova ne zavise od K: "
        "V_CPU = 1/0.64 = 1.5625, V_SD1 = 0.4167, V_SD2 = 0.3125, V_SD3 = 0.2083. "
        "Svaki korisnički disk ima V = 1/K, a njihov zbir je uvek tačno 1 — svaki "
        "posao izlazi iz sistema preko tačno jednog korisničkog diska, što je "
        "nezavisna provera ispravnosti rešenja."
    ))

    b += [
        h(3, "2.2 Granični intenzitet ulaznog toka α_max(K) i kritični resurs"),
        p("Sistem je u stacionarnom režimu dok je svaki server neopterećen preko "
          "svog kapaciteta:"),
        kod("rho_i = lambda_i / mi_i = V_i * alpha * S_i < 1\n"
            "  =>  alpha < 1 / (V_i * S_i)   za svako i\n"
            "  =>  alpha_max = 1 / max_i (V_i * S_i)"),
        p("Veličina D_i = V_i · S_i je ukupan zahtev jednog posla za serverom i. "
          "Server sa najvećim D_i je **kritični resurs** (usko grlo) i on prvi "
          "dostiže iskorišćenje 1."),
    ]

    redovi = []
    for K in K_vrednosti:
        V = analiticki.koeficijenti_poseta(K)
        D = analiticki.zahtevi_opsluzivanja(K, V)
        alpha_max, kriticni, _ = analiticki.granicni_intenzitet(K, V)
        kd = parametri.indeksi_korisnickih(K)
        redovi.append([
            K, fb(D[0] * 1000, 4), fb(D[1] * 1000, 4), fb(D[2] * 1000, 4),
            fb(D[3] * 1000, 4), fb(D[kd[0]] * 1000, 4),
            fb(alpha_max, 4), parametri.opis_kriticnih(K, kriticni),
        ])
    b.append(tabela(
        ["K", "D_CPU [ms]", "D_SD1 [ms]", "D_SD2 [ms]", "D_SD3 [ms]",
         "D_KD [ms]", "α_max [1/s]", "kritični resurs"],
        redovi,
        "Zahtevi D_i = V_i·S_i, granični intenzitet i kritični resurs",
    ))
    b.append(p(
        "Zahtev procesora je konstantan (D_CPU = 1.5625 · 4 ms = 6.25 ms), dok "
        "zahtev jednog korisničkog diska opada sa K (D_KD = (1/K) · 25 ms = 25/K ms) "
        "jer se isti posao ravnomerno deli na više diskova. Zato za K = 2 i K = 3 "
        "usko grlo čine korisnički diskovi, za **K = 4 zahtevi procesora i "
        "korisničkog diska su jednaki (6.25 ms) i oba resursa su kritična**, a za "
        "K = 5 kritičan postaje procesor. Time α_max prestaje da raste sa K: "
        "dodavanje petog korisničkog diska više ne povećava kapacitet sistema jer "
        "je procesor postao ograničenje."
    ))
    b.append(slika("grafici/alpha_max_vs_K.png",
                   "Zavisnost graničnog intenziteta ulaznog toka α_max od broja "
                   "korisničkih diskova K"))

    b += [
        h(3, "2.3 Džeksonova teorema — parametri performansi"),
        p("Po Džeksonovoj teoremi, stacionarna raspodela otvorene mreže je proizvod "
          "raspodela pojedinačnih čvorova, pa se svaki server analizira kao "
          "nezavisan M/M/1 sistem sa ulaznim tokom λ_i = V_i · α:"),
        kod("X_i   = V_i * alpha                 (protok kroz server)\n"
            "rho_i = X_i * S_i                   (iskorišćenje servera)\n"
            "N_i   = rho_i / (1 - rho_i)         (prosečan broj poslova u serveru)\n"
            "W_i   = S_i / (1 - rho_i)           (vreme odziva servera po prolazu)\n"
            "N     = suma_i N_i\n"
            "T     = N / alpha = suma_i V_i * W_i    (Litlov zakon)"),
    ]

    for r in r_vrednosti:
        redovi = []
        for K in K_vrednosti:
            rez = analitika[(K, r)]
            kd = parametri.indeksi_korisnickih(K)[0]
            redovi.append([
                K, fb(rez.alpha, 2),
                fb(rez.cvorovi[0].rho, 4), fb(rez.cvorovi[1].rho, 4),
                fb(rez.cvorovi[2].rho, 4), fb(rez.cvorovi[3].rho, 4),
                fb(rez.cvorovi[kd].rho, 4),
                fb(rez.N_sistem, 4), fb(rez.T_sistem * 1000, 4),
            ])
        b.append(tabela(
            ["K", "α [1/s]", "ρ_CPU", "ρ_SD1", "ρ_SD2", "ρ_SD3", "ρ_KD",
             "N (sistem)", "T_sistem [ms]"],
            redovi,
            f"Analitički rezultati za r = {r:.2f}",
        ))

    b.append(p(
        "Za r = 1.00 je α = α_max, pa kritični resurs ima ρ = 1. M/M/1 red tada nije "
        "stacionaran: N_i = ρ/(1−ρ) i W_i = S/(1−ρ) teže beskonačnosti, pa su N i "
        "T_sistem beskonačni (u tabelama označeno sa ∞). To je granični slučaj koji "
        "realni sistem ne može da održi, a u simulaciji se vidi kao red koji "
        "neprekidno raste."
    ))
    return b


def _blokovi_simulacija(argumenti):
    b = [
        h(2, "3. Simulacija"),
        h(3, "3.1 Metod: diskretno-dogadjajna simulacija (DES)"),
        p("Simulacija nije vođena vremenom (nema koraka Δt ni čekanja na serveru), "
          "već **dogadjajima**: program održava kalendar budućih dogadjaja "
          "(min-hip uređen po vremenu) i simulaciono vreme skače direktno na trenutak "
          "sledećeg dogadjaja. Takav pristup ne troši vreme na intervale u kojima se "
          "ništa ne dešava i daje tačno iste rezultate kao vremenski vođena "
          "simulacija sa beskonačno malim korakom."),
        p("Postoje dva tipa dogadjaja:"),
        ul([
            "**DOLAZAK** — spoljni dolazak posla u procesor. Poasonov tok znači "
            "eksponencijalne međudolazne intervale, pa se pri svakom dolasku odmah "
            "zakazuje sledeći, u trenutku t + Exp(α).",
            "**ODLAZAK** — završetak opsluživanja posla u čvoru i. Tada se, ako red "
            "nije prazan, uzima sledeći posao (FCFS) i zakazuje njegov odlazak u "
            "t + Exp(μ_i), a posao koji je završen rutira se dalje.",
        ]),
        p("Rutiranje koristi **istu matricu verovatnoća tranzicija P** koju koristi i "
          "analitički deo: iz reda matrice se unapred izračunaju kumulativne "
          "verovatnoće, pa se odredište bira jednim slučajnim brojem u ~ U(0,1). Ako "
          "u premaši sumu reda, posao napušta sistem — za korisničke diskove je suma "
          "reda nula, pa oni uvek izbacuju posao iz sistema."),
        kod(
            "dogadjaj = (vreme, tip, cvor)\n"
            "kalendar = min-hip po vremenu\n\n"
            "dok kalendar nije prazan:\n"
            "    (t, tip, i) = izvadi_najraniji(kalendar)\n"
            "    ako t > kraj_simulacije: prekini\n"
            "    ako tip == DOLAZAK:\n"
            "        zakazi (t + Exp(alpha), DOLAZAK, procesor)\n"
            "        cilj = procesor;  ulazak = t\n"
            "    inace:                                  # ODLAZAK iz cvora i\n"
            "        azuriraj statistiku cvora i;  broj[i] -= 1\n"
            "        ako red[i] nije prazan:\n"
            "            uzmi sledeci posao (FCFS)\n"
            "            zakazi (t + Exp(mi_i), ODLAZAK, i)\n"
            "        cilj = rutiraj(i)                   # po matrici P\n"
            "        ako cilj == IZLAZ: zabelezi vreme u sistemu;  nastavi\n"
            "    # ulazak posla u cvor 'cilj'\n"
            "    azuriraj statistiku cvora cilj;  broj[cilj] += 1\n"
            "    ako je server slobodan: zakazi (t + Exp(mi_cilj), ODLAZAK, cilj)\n"
            "    inace: dodaj posao u red[cilj]"
        ),
        h(3, "3.2 Prikupljanje statistike"),
        p("Statistika se prikuplja bez ikakve pretpostavke o raspodeli — samo iz "
          "onoga što se u simulaciji dogodilo:"),
        kod(
            "rho_i = (ukupno vreme zauzetosti servera i) / T\n"
            "X_i   = (broj zavrsenih opsluzivanja u cvoru i) / T\n"
            "N_i   = (integral broja poslova u cvoru i po vremenu) / T\n"
            "W_i   = N_i / X_i                        (Litlov zakon po cvoru)\n"
            "T_sistem = (zbir vremena provedenih u sistemu) / (broj izaslih poslova)"
        ),
        p("Integral broja poslova računa se inkrementalno: pri svakoj promeni broja "
          "poslova u čvoru dodaje se (trenutni broj) × (vreme od poslednje promene). "
          "Vreme provedeno u sistemu meri se tako što svaki posao nosi trenutak svog "
          "spoljnog dolaska kroz celu mrežu. Kao kontrola, program uz izmereno "
          "srednje vreme u sistemu ispisuje i vrednost N/α — po Litlovom zakonu te "
          "dve vrednosti moraju da se poklope, i u rezultatima se poklapaju na "
          "nekoliko decimala."),
        p("Mreža na početku simulacije je prazna, pa sistem prvo prolazi kroz "
          "prelazni režim, što blago potcenjuje N i T. Uticaj je pri "
          "podrazumevanom trajanju od 30 minuta zanemarljiv (prelazni režim traje "
          "reda sekunde), a program ipak ima opciju `--zagrevanje` kojom se početni "
          "interval izbacuje iz statistike."),
        h(3, "3.3 Ponavljanje i usrednjavanje"),
        p("Za svaku kombinaciju (K, r) simulacija se ponavlja zadati broj puta, svaki "
          "put sa drugim semenom generatora slučajnih brojeva, pa su ponavljanja "
          "nezavisne realizacije istog stohastičkog procesa. Rezultati se usrednjavaju "
          "metriku po metriku, a uz srednju vrednost se računa i uzoračka standardna "
          "devijacija (upisana u `rezultati_simulacija_usrednjeno.txt`). Semena se "
          "izvode determinističkim pravilom iz baznog semena, pa je celo pokretanje "
          "programa ponovljivo."),
    ]
    if argumenti is not None:
        b.append(p(
            f"Podrazumevano simulirano vreme rada sistema je 0.5 h = 30 min i može se "
            f"promeniti opcijom `--minuti`. Rezultati u ovom dokumentu dobijeni su sa "
            f"{argumenti.minuti:g} min po izvršavanju i {argumenti.ponavljanja} "
            f"ponavljanja po kombinaciji (K, r), tj. ukupno "
            f"{len(parametri.K_VREDNOSTI) * len(parametri.R_VREDNOSTI) * argumenti.ponavljanja} "
            f"izvršavanja simulacije."
        ))
    return b


def _blokovi_poredjenje(analitika, simulacija_1, usrednjeno, argumenti):
    tabele = poredjenje.sve_tabele(analitika, simulacija_1, usrednjeno)
    sumarno = poredjenje.sumarna_tabela(tabele)

    b = [
        h(2, "4. Poređenje analitičkih i simulacionih rezultata"),
        p("Relativno odstupanje računa se kao "
          "(simulacija − analitika) / analitika · 100 %. Kompletne tabele za sve "
          "metrike i sve slučajeve nalaze se u `rezultati/poredjenje.txt`; ovde su "
          "prikazane ključne veličine u zavisnosti od broja korisničkih diskova K."),
    ]

    for r in parametri.R_VREDNOSTI:
        for metrika, opis in (
            ("rho_CPU", "iskorišćenje procesora"),
            ("rho_KD", "iskorišćenje korisničkog diska"),
            ("W_CPU [ms]", "vreme odziva procesora [ms]"),
            ("W_KD [ms]", "vreme odziva korisničkog diska [ms]"),
            ("T_sistem [ms]", "vreme odziva sistema [ms]"),
        ):
            redovi = []
            for K, a, s, ds, u, du in poredjenje.po_metrici_i_K(tabele, metrika, r):
                redovi.append([
                    K, fb(a, 5), fb(s, 5), fp(ds), fb(u, 5), fp(du),
                ])
            b.append(tabela(
                ["K", "analitika", "1 simulacija", "odst. [%]",
                 f"usrednjeno ({argumenti.ponavljanja if argumenti else 'N'} sim.)",
                 "odst. [%]"],
                redovi,
                f"r = {r:.2f} — {opis}",
            ))

    redovi = []
    for K, r, mao_sim, mao_usr, m in sumarno:
        odnos = mao_sim / mao_usr if (mao_sim and mao_usr) else None
        redovi.append([K, f"{r:.2f}", fb(mao_sim, 4), fb(mao_usr, 4), fb(odnos, 2), m])
    b.append(tabela(
        ["K", "r", "1 simulacija [%]", "usrednjeno [%]", "odnos", "broj metrika"],
        redovi,
        "Srednje apsolutno relativno odstupanje od analitičkog rešenja, po slučaju",
    ))

    korisni = [(r, mao_sim, mao_usr) for _, r, mao_sim, mao_usr, _ in sumarno
               if mao_sim and mao_usr]
    if korisni:
        sr_sim = sum(x for _, x, _ in korisni) / len(korisni)
        sr_usr = sum(y for _, _, y in korisni) / len(korisni)
        bolji = sum(1 for _, x, y in korisni if y < x)
        b.append(p(
            f"Prosečno po svim slučajevima, jedna simulacija odstupa od analitičkog "
            f"rešenja **{sr_sim:.3f} %**, a usrednjeni rezultat "
            f"**{sr_usr:.3f} %** — dakle oko **{sr_sim / sr_usr:.1f} puta** manje. "
            f"Usrednjeni rezultat je bliži analitičkom u {bolji} od {len(korisni)} "
            f"posmatranih slučajeva."
        ))
        stacionarni = [x / y for r, x, y in korisni if r < 1.0]
        zasiceni = [x / y for r, x, y in korisni if r >= 1.0]
        if stacionarni and zasiceni:
            n = argumenti.ponavljanja if argumenti else 100
            b.append(p(
                f"Odnos odstupanja posmatran po pojedinačnom slučaju je informativniji "
                f"od odnosa proseka. Za stacionarne slučajeve (r < 1.00) on iznosi u "
                f"proseku **{sum(stacionarni) / len(stacionarni):.1f}**, što je blizu "
                f"teorijski očekivanog √{n} = {math.sqrt(n):.0f}. Za r = 1.00 odnos je "
                f"manji (u proseku {sum(zasiceni) / len(zasiceni):.1f}) jer tamo "
                f"preostalo odstupanje ne potiče od statističke fluktuacije, koja se "
                f"usrednjavanjem smanjuje, već od toga što sistem uopšte nije u "
                f"stacionarnom režimu — takvu grešku usrednjavanje ne može da ukloni."
            ))

    b += [
        h(3, "4.1 Odgovori na postavljena pitanja"),
        p("**Šta se može zaključiti o rezultatima simulacije i usrednjenim "
          "rezultatima više simulacija?** Obe vrste rezultata potvrđuju analitičko "
          "rešenje: iskorišćenja i protoci se poklapaju već u jednoj simulaciji "
          "(odstupanja reda desetinke procenta), jer su to veličine koje se "
          "akumuliraju kroz stotine hiljada dogadjaja. Veća odstupanja javljaju se "
          "kod N_i, W_i i T_sistem, i to utoliko više ukoliko je opterećenje veće — "
          "kod jako iskorišćenih servera dužina reda ima veliku varijansu, pa ista "
          "dužina simulacije daje manje pouzdanu procenu."),
        p("**Koji rezultati imaju manje relativno odstupanje?** Usrednjeni rezultati "
          "više simulacija, u praktično svim slučajevima i za sve metrike, kako "
          "pokazuje sumarna tabela iznad."),
        p("**Kako i zašto broj izvršenih simulacija utiče na relativno odstupanje?** "
          "Svako izvršavanje daje slučajnu procenu čija je srednja vrednost tačna "
          "(nepristrasna), ali koja odstupa zbog varijanse. Za n nezavisnih "
          "ponavljanja standardna greška srednje vrednosti opada kao σ/√n, pa se "
          "očekuje da usrednjavanje 100 simulacija smanji tipično odstupanje oko "
          "√100 = 10 puta u odnosu na jednu simulaciju. Zbog toga povećanje broja "
          "ponavljanja daje sve manji dobitak: da bi se greška prepolovila, broj "
          "simulacija se mora učetvorostručiti. Isti efekat ima i produžavanje "
          "simuliranog vremena jedne simulacije, jer i ono povećava broj nezavisnih "
          "uzoraka u proceni."),
        p("Ostatak odstupanja koji se ne smanjuje usrednjavanjem potiče od "
          "sistematskih efekata: prelazni režim na početku (mreža kreće prazna) i "
          "poslovi koji su na kraju simulacije još u sistemu, pa ne ulaze u srednje "
          "vreme odziva. Oba efekta su relativno manja što je simulacija duža."),
    ]

    # --- r = 1.00 ---
    r_max = parametri.R_VREDNOSTI[-1]
    if abs(r_max - 1.0) < 1e-12:
        redovi = []
        for K in parametri.K_VREDNOSTI:
            an = analitika[(K, r_max)]
            s1 = simulacija_1[(K, r_max)]
            us = usrednjeno[(K, r_max)]
            redovi.append([
                K, "∞", fb(s1.T_sistem * 1000, 2), fb(us.T_sistem * 1000, 2),
                fb(max(c.rho for c in us.cvorovi), 4),
                us.dodatno.get("poslova_u_sistemu_na_kraju", "—"),
            ])
        b += [
            h(3, "4.2 Granični slučaj r = 1.00"),
            p("Za r = 1.00 kritični resurs ima ρ = 1 i analitički nema stacionarno "
              "rešenje (N i T su beskonačni), pa relativno odstupanje nije "
              "definisano. Simulacija ipak daje konačan broj, ali on nije procena "
              "stacionarne vrednosti — red kritičnog resursa raste tokom celog "
              "simuliranog vremena, pa izmereno T_sistem zavisi od toga koliko dugo "
              "je simulacija trajala i sa dužim trajanjem bi bilo veće. To je i "
              "praktična ilustracija zašto se realni sistemi ne projektuju da rade "
              "na granici kapaciteta."),
            tabela(
                ["K", "T_sistem analitički", "T_sistem 1 sim. [ms]",
                 "T_sistem usrednjeno [ms]", "max ρ (simulacija)",
                 "poslova u sistemu na kraju"],
                redovi,
                "r = 1.00: zasićenje kritičnog resursa",
            ),
        ]
    return b


def _blokovi_dijagrami():
    b = [
        h(2, "5. Dijagrami"),
        p("Dijagrami su konstruisani na osnovu analitičkih rezultata, kako zadatak "
          "traži. Na svakom dijagramu krive su različitih boja i simbola, sa "
          "legendom."),
        h(3, "5.1 Iskorišćenje resursa u funkciji od K"),
    ]
    for r in parametri.R_VREDNOSTI:
        b.append(slika(
            f"grafici/iskoriscenja_r{int(round(r * 100)):03d}.png",
            f"Iskorišćenje procesora, sistemskih diskova i korisničkog diska u "
            f"funkciji od K, za r = {r:.2f}",
        ))
    b.append(p(
        "Za fiksno α iskorišćenje procesora ne bi zavisilo od K "
        "(ρ_CPU = D_CPU·α = 6.25 ms · α), a iskorišćenje pojedinačnog korisničkog "
        "diska opadalo bi kao (25/K) ms · α, jer se isti posao deli na više diskova. "
        "Na dijagramima, međutim, α nije fiksno nego prati kapacitet sistema "
        "(α = r·α_max(K)), pa krive nisu monotone: dok α_max raste (K = 2, 3, 4), "
        "raste i opterećenje procesora, a korisnički diskovi ostaju na ρ = r jer su "
        "oni usko grlo. Prelazak sa K = 4 na K = 5 ne povećava α (α_max ostaje "
        "160 1/s), pa iskorišćenje korisničkih diskova naglo pada, dok procesor "
        "ostaje na ρ = r kao novi kritični resurs."
    ))

    b.append(h(3, "5.2 Vreme odziva servera u funkciji od K"))
    for r in parametri.R_VREDNOSTI:
        b.append(slika(
            f"grafici/vremena_odziva_servera_r{int(round(r * 100)):03d}.png",
            f"Vreme odziva servera (po jednom prolazu) u funkciji od K, "
            f"za r = {r:.2f}",
        ))

    b.append(h(3, "5.3 Vreme odziva sistema u funkciji od K"))
    for r in parametri.R_VREDNOSTI:
        b.append(slika(
            f"grafici/vreme_odziva_sistema_r{int(round(r * 100)):03d}.png",
            f"Vreme odziva sistema T u funkciji od K, za r = {r:.2f}",
        ))

    b.append(p(
        "Vreme odziva sistema raste sa K sve dok kritični resurs ostaje korisnički "
        "disk, jer se sa svakim dodatim diskom povećava i α = r·α_max, pa i "
        "opterećenje ostalih resursa. Kod K = 5 ulazni tok se ne povećava (α_max "
        "ostaje 160 1/s), a posao se deli na više diskova, pa T ponovo opada. Za "
        "r = 1.00 nijedna tačka nije konačna, pa je na tom dijagramu, radi "
        "poređenja, sivom bojom prikazana kriva za r = 0.99 — ona pokazuje koliko "
        "naglo T raste pri približavanju granici kapaciteta."
    ))
    b.append(h(3, "5.4 Dodatno: poređenje analitike i simulacije"))
    for r in parametri.R_VREDNOSTI:
        b.append(slika(
            f"grafici/poredjenje_T_sistem_r{int(round(r * 100)):03d}.png",
            f"Vreme odziva sistema — analitika, jedna simulacija i usrednjena "
            f"simulacija, za r = {r:.2f}",
        ))
    for r in parametri.R_VREDNOSTI:
        b.append(slika(
            f"grafici/poredjenje_iskoriscenja_r{int(round(r * 100)):03d}.png",
            f"Iskorišćenje resursa — analitika (linije) i usrednjena simulacija "
            f"(simboli), za r = {r:.2f}",
        ))
    return b


def _blokovi_kriticni(analitika):
    redovi = []
    for r in parametri.R_VREDNOSTI:
        for K in parametri.K_VREDNOSTI:
            rez = analitika[(K, r)]
            rho_max = max(c.rho for c in rez.cvorovi)
            redovi.append([
                f"{r:.2f}", K, parametri.opis_kriticnih(K, rez.kriticni), fb(rho_max, 4),
            ])
    return [
        h(2, "6. Kritični resurs za svaku kombinaciju (r, K)"),
        p("Pošto je ρ_i = D_i · α, a α = r · α_max samo skalira sva iskorišćenja "
          "istim faktorom, **kritični resurs zavisi isključivo od K, ne i od r**. "
          "Vrednost r određuje koliko je kritični resurs opterećen: ρ kritičnog "
          "resursa je tačno jednako r."),
        tabela(["r", "K", "kritični resurs", "ρ kritičnog resursa"], redovi,
               "Kritični resurs po kombinaciji parametara"),
        p("Za K = 2 i K = 3 usko grlo su korisnički diskovi; za K = 4 procesor i "
          "korisnički diskovi imaju identičan zahtev (6.25 ms) pa su svi kritični; "
          "za K = 5 kritičan je procesor. Praktična posledica: povećavanje broja "
          "korisničkih diskova poboljšava kapacitet sistema samo do K = 4, posle "
          "čega je procesor ograničenje i dalja ulaganja u diskove ne povećavaju "
          "α_max."),
    ]


def _blokovi_zakljucak(analitika, simulacija_1, usrednjeno):
    b = [
        h(2, "7. Zaključak"),
        ul([
            "Matrični metod daje koeficijente poseta koji ne zavise od α, pa su "
            "protoci kroz sve servere linearne funkcije ulaznog toka; zbir "
            "koeficijenata poseta korisničkih diskova je tačno 1, što potvrđuje "
            "ispravnost postavljenog sistema jednačina.",
            "Granični intenzitet je α_max = 80, 120, 160 i 160 1/s za K = 2, 3, 4 i "
            "5; kritični resurs prelazi sa korisničkih diskova na procesor između "
            "K = 4 (gde su izjednačeni) i K = 5.",
            "Simulacija nezavisno potvrđuje analitičko rešenje: iskorišćenja i "
            "protoci se poklapaju sa odstupanjima reda desetinke procenta, a vremena "
            "odziva i dužine redova nešto više odstupaju pri visokom opterećenju.",
            "Usrednjavanje više nezavisnih simulacija smanjuje odstupanje približno "
            "kao 1/√n, pa je usrednjeni rezultat znatno bliži analitičkom nego "
            "rezultat jedne simulacije.",
            "Za r = 1.00 analitičko rešenje ne postoji (ρ = 1), a simulacija pokazuje "
            "red koji neprekidno raste — oba metoda se slažu da sistem na granici "
            "kapaciteta nije upotrebljiv.",
        ]),
    ]
    if simulacija_1 and usrednjeno:
        b.append(p(
            "Dva metoda se međusobno proveravaju: analitika daje tačne vrednosti pod "
            "pretpostavkama Džeksonove mreže i trenutna je, ali važi samo dok su te "
            "pretpostavke ispunjene i samo za stacionarni režim; simulacija ne "
            "zahteva te pretpostavke i primenljiva je i na sisteme koji se ne mogu "
            "rešiti analitički, ali daje procene sa statističkom greškom koja se "
            "smanjuje tek dužim ili ponovljenim izvršavanjem."
        ))
    return b


def _blokovi_fajlovi():
    return [
        h(2, "8. Sadržaj priloga"),
        tabela(
            ["Fajl", "Sadržaj"],
            [
                ["`parametri.py`", "ulazni parametri sistema, matrica prelaza P, "
                                   "vektor brzina servera"],
                ["`linearna_algebra.py`", "Gausova eliminacija sa parcijalnim "
                                          "pivotiranjem"],
                ["`analiticki.py`", "matrični metod, α_max i kritični resurs, "
                                    "Džeksonova teorema"],
                ["`simulacija.py`", "diskretno-dogadjajna simulacija i usrednjavanje "
                                    "ponavljanja"],
                ["`izvestaji.py`", "formatiranje i upis izlaznih fajlova"],
                ["`poredjenje.py`", "relativna odstupanja i tabele poređenja"],
                ["`grafici.py`", "crtanje svih dijagrama"],
                ["`dokumentacija.py`", "generisanje ovog dokumenta"],
                ["`main.py`", "glavni program (pokreće sve)"],
                ["`rezultati/protoci_analiticki.txt`",
                 "matrica P, brzine servera, V_i = X_i/α, protoci"],
                ["`rezultati/rezultati_analiticki.txt`",
                 "α_max i kritični resursi, svi parametri po Džeksonu"],
                ["`rezultati/rezultati_simulacija.txt`",
                 "rezultati jedne simulacije po kombinaciji (K, r)"],
                ["`rezultati/rezultati_simulacija_usrednjeno.txt`",
                 "usrednjeni rezultati ponovljenih simulacija sa standardnim "
                 "devijacijama"],
                ["`rezultati/poredjenje.txt`",
                 "tabele relativnih odstupanja i sumarna tabela"],
                ["`grafici/*.png`", "svi dijagrami"],
            ],
        ),
    ]


# ---------------------------------------------------------------------------
def sastavi(analitika, tabela_granicnih, simulacija_1, usrednjeno, argumenti):
    blokovi = _blokovi_uvod(argumenti)
    blokovi += _blokovi_analitika(analitika, tabela_granicnih)
    blokovi += _blokovi_simulacija(argumenti)
    if simulacija_1 and usrednjeno:
        blokovi += _blokovi_poredjenje(analitika, simulacija_1, usrednjeno, argumenti)
    blokovi += _blokovi_dijagrami()
    blokovi += _blokovi_kriticni(analitika)
    blokovi += _blokovi_zakljucak(analitika, simulacija_1, usrednjeno)
    blokovi += _blokovi_fajlovi()
    return blokovi


def napisi(direktorijum, analitika, tabela_granicnih, simulacija_1=None,
           usrednjeno=None, argumenti=None, putanje_grafika=None):
    """Upisuje dokumentacija.md i dokumentacija.html; vraća putanju do .md."""
    blokovi = sastavi(analitika, tabela_granicnih, simulacija_1, usrednjeno,
                      argumenti)
    naslov_dokumenta = ("Performanse računarskih sistema — analiza i simulacija "
                        "otvorene mreže")

    putanja_md = os.path.join(direktorijum, "dokumentacija.md")
    with open(putanja_md, "w", encoding="utf-8") as f:
        f.write(u_markdown(blokovi))

    putanja_html = os.path.join(direktorijum, "dokumentacija.html")
    with open(putanja_html, "w", encoding="utf-8") as f:
        f.write(u_html(blokovi, naslov_dokumenta))

    print(f"Upisano: {os.path.relpath(putanja_html, direktorijum)}")
    return putanja_md
