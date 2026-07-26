# Performanse računarskih sistema — domaći zadatak

Analiza i simulacija multiprogramskog računara modelovanog **otvorenom mrežom**:
procesor + 3 sistemska diska + **K** korisničkih diskova (K = 2..5), za ulazne
tokove α = r · α_max, r ∈ {0.30, 0.55, 0.80, 1.00}.

Program radi tri stvari:

1. **analitički** rešava mrežu (matrični metod za protoke + Džeksonova teorema),
2. **simulira** je diskretno-dogadjajnom simulacijom (DES),
3. **poredi** rezultate, crta dijagrame i generiše dokumentaciju.

## Pokretanje

Potreban je Python 3.10+ (razvijano i testirano na Python 3.13). Za dijagrame je
potreban `matplotlib`; sve ostalo koristi isključivo standardnu biblioteku
(linearna algebra je implementirana ručno, bez `numpy`-a). Python je
interpretirani jezik, pa su priloženi izvorni fajlovi ujedno i program spreman
za izvršavanje — nije potrebno prevođenje.

```bash
py main.py
```

Podrazumevano: 30 min (0.5 h) simuliranog vremena rada sistema po izvršavanju i
100 ponavljanja po kombinaciji (K, r), tj. 1600 izvršavanja simulacije.
Izvršavanja se raspoređuju na sva jezgra procesora; na računaru sa 8 jezgara
ceo proračun traje oko 8 minuta.

Korisne opcije:

```bash
py main.py --brzo
```

| Opcija | Značenje | Podrazumevano |
|---|---|---|
| `--minuti M` | simulirano vreme rada sistema po izvršavanju [min] | 30 |
| `--ponavljanja N` | broj ponavljanja simulacije po kombinaciji (K, r) | 100 |
| `--zagrevanje M` | početni interval čija se statistika odbacuje [min] | 0 |
| `--seme S` | bazno seme generatora slučajnih brojeva | 20260726 |
| `--procesi N` | broj paralelnih procesa (0 = broj jezgara) | 0 |
| `--brzo` | brza provera: 5 min, 5 ponavljanja | — |
| `--ucitaj` | ne simuliraj ponovo, iskoristi rezultate poslednje simulacije (`kes_simulacije.pkl`) | — |
| `--bez-simulacije` | samo analitika i dijagrami | — |
| `--bez-grafika` | ne crtaj dijagrame | — |
| `--bez-dokumentacije` | ne generiši dokumentaciju | — |

Posle uspešnog pokretanja rezultati simulacije se čuvaju u `kes_simulacije.pkl`,
pa se izveštaji, dijagrami i dokumentacija mogu ponovo generisati za nekoliko
sekundi, bez ponovnog simuliranja:

```bash
py main.py --ucitaj
```

Rezultati su reproducibilni: isto bazno seme daje identične rezultate jer se
seme svakog pojedinačnog izvršavanja izvodi determinističkim pravilom iz
baznog semena, broja K, indeksa r i rednog broja ponavljanja.

## Struktura

| Fajl | Sadržaj |
|---|---|
| `parametri.py` | ulazni parametri sistema, matrica verovatnoća tranzicija P, vektor brzina servera |
| `linearna_algebra.py` | Gausova eliminacija sa parcijalnim pivotiranjem (bez numpy-a) |
| `analiticki.py` | matrični metod, α_max i kritični resurs, Džeksonova teorema |
| `simulacija.py` | diskretno-dogadjajna simulacija i usrednjavanje ponavljanja |
| `rezultat.py` | zajedničke strukture rezultata (isti tip za analitiku i simulaciju) |
| `izvestaji.py` | formatiranje i upis izlaznih fajlova |
| `poredjenje.py` | relativna odstupanja i tabele poređenja |
| `grafici.py` | crtanje svih dijagrama |
| `dokumentacija.py` | generisanje dokumentacije (`.md` i `.html`) |
| `main.py` | glavni program |
| `test_provera.py` | provere ispravnosti (pokreće se sa `py test_provera.py`) |

## Izlazni fajlovi

Direktorijum `rezultati/`:

| Fajl | Sadržaj |
|---|---|
| `protoci_analiticki.txt` | matrica P, brzine servera, V_i = X_i/α i protoci (zadatak 1) |
| `rezultati_analiticki.txt` | α_max i kritični resursi (zadatak 2), svi parametri po Džeksonu (zadatak 3) |
| `rezultati_simulacija.txt` | rezultati jedne simulacije po kombinaciji (K, r) |
| `rezultati_simulacija_usrednjeno.txt` | usrednjeni rezultati ponovljenih simulacija + standardne devijacije |
| `poredjenje.txt` | tabele relativnih odstupanja i sumarna tabela |

Direktorijum `grafici/`: `alpha_max_vs_K.png`, `iskoriscenja_r*.png`,
`vremena_odziva_servera_r*.png`, `vreme_odziva_sistema_r*.png` i dodatno
`poredjenje_T_sistem_r*.png`, `poredjenje_iskoriscenja_r*.png`.

Dokumentacija: `dokumentacija.md` i `dokumentacija.html` (HTML je pogodan za
štampu — otvoriti u veb čitaču i odštampati).

## Ukratko o metodama

**Analitika.** Iz jednačina ravnoteže protoka (I − Pᵀ)·λ = α_vektor, deljenjem
sa α, dobija se sistem (I − Pᵀ)·V = e za koeficijente poseta V_i = X_i/α, koji
se rešava Gausovom eliminacijom. Iz uslova ρ_i = V_i·S_i·α < 1 sledi
α_max = 1/max_i(V_i·S_i), a resurs sa najvećim zahtevom D_i = V_i·S_i je
kritični. Po Džeksonovoj teoremi svaki server je nezavisan M/M/1:
ρ_i = X_i·S_i, N_i = ρ_i/(1−ρ_i), W_i = S_i/(1−ρ_i), T = ΣN_i/α = ΣV_i·W_i.

**Simulacija.** DES sa kalendarom dogadjaja (min-hip): simulaciono vreme skače
na trenutak sledećeg dogadjaja, bez koraka po vremenu i bez čekanja. Dogadjaji
su spoljni dolazak i završetak opsluživanja. Rutiranje koristi istu matricu P
kao analitika. Mere se iskorišćenja (vreme zauzetosti servera), protoci (broj
završenih opsluživanja), prosečan broj poslova (integral po vremenu) i vreme u
sistemu po poslu.
