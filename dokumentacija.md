# Performanse računarskih sistema — analiza i simulacija otvorene mreže

Ovaj dokument opisuje analitičko rešavanje i simulaciju multiprogramskog računara modelovanog otvorenom mrežom sa procesorom, tri sistemska diska i **K** korisničkih diskova (K = 2..5), i poredi dobijene rezultate. Sve tabele u dokumentu generisane su iz stvarnih rezultata programa.

## 1. Opis sistema i model

Poasonov tok poslova intenziteta α pristiže na procesor. Vremena opsluživanja su eksponencijalna, a redovi su neograničeni sa FCFS disciplinom, pa je svaki servisni centar M/M/1 sistem, a cela mreža otvorena **Džeksonova mreža**.

**Parametri servisnih centara**

| Server | Oznaka | Srednje vreme opsluživanja S_i | μ_i = 1/S_i [1/s] |
|---|---|---|---|
| Procesor | CPU | 4 ms | 250 |
| Sistemski disk 1 | SD1 | 10 ms | 100 |
| Sistemski disk 2 | SD2 | 15 ms | 66.667 |
| Sistemski disk 3 | SD3 | 15 ms | 66.667 |
| Korisnički disk (svaki od K) | KD | 25 ms | 40 |

Verovatnoće tranzicija (matrica **P**):

- posle procesora: 20% SD1, 15% SD2, 10% SD3, 40% neki od K korisničkih diskova (po 0.40/K), 15% povratak u red procesora;
- posle sistemskog diska: 35% red procesora, 25% ponovo isti disk, 40% neki od K korisničkih diskova (po 0.40/K);
- posle korisničkog diska: posao napušta sistem (verovatnoća 1).

Zbir verovatnoća u redovima procesora i sistemskih diskova je 1 — iz tih čvorova posao ne može da napusti sistem; jedini izlaz iz sistema je preko korisničkog diska. Program to eksplicitno proverava pre računanja (`parametri.proveri_matricu_prelaza`).

Parametri pokretanja koji su dali rezultate u ovom dokumentu: simulirano vreme rada sistema **30 min** po izvršavanju, **100** ponavljanja po kombinaciji (K, r), bazno seme generatora slučajnih brojeva **20260726**.

## 2. Analitičko rešavanje

### 2.1 Matrični metod — protoci kroz servere

Za otvorenu mrežu važe jednačine ravnoteže protoka: protok kroz server i jednak je zbiru spoljnog toka koji ulazi u taj server i svih unutrašnjih tokova koji u njega dolaze iz ostalih servera:

```
lambda_i = alpha_i + suma_j ( lambda_j * P[j][i] )

odnosno matrično:   (I - P^T) * lambda = alpha_vektor
```

Pošto ceo spoljni tok ulazi u procesor, važi alpha_vektor = α·e, gde je e = [1, 0, …, 0]ᵀ. Deljenjem sa α dobija se sistem koji ne zavisi od α:

```
(I - P^T) * V = e,      V_i = lambda_i / alpha = X_i / alpha
```

V_i je koeficijent poseta, tj. traženi odnos protoka kroz server i intenziteta ulaznog toka. Sistem se u programu rešava Gausovom eliminacijom sa parcijalnim pivotiranjem (`linearna_algebra.resi_sistem`), a tačnost se kontroliše rezidualom max|(I − Pᵀ)V − e| (reda 10⁻¹⁶). Protoci su onda linearne funkcije ulaznog toka: **X_i(α) = V_i · α**.

**Koeficijenti poseta V_i = X_i/α (rešenje sistema (I − Pᵀ)V = e)**

| K | V_CPU | V_SD1 | V_SD2 | V_SD3 | V_KD (po disku) | Σ V_KD |
|---|---|---|---|---|---|---|
| 2 | 1.562500 | 0.416667 | 0.312500 | 0.208333 | 0.500000 | 1.000000 |
| 3 | 1.562500 | 0.416667 | 0.312500 | 0.208333 | 0.333333 | 1.000000 |
| 4 | 1.562500 | 0.416667 | 0.312500 | 0.208333 | 0.250000 | 1.000000 |
| 5 | 1.562500 | 0.416667 | 0.312500 | 0.208333 | 0.200000 | 1.000000 |

Koeficijenti poseta procesora i sistemskih diskova ne zavise od K: V_CPU = 1/0.64 = 1.5625, V_SD1 = 0.4167, V_SD2 = 0.3125, V_SD3 = 0.2083. Svaki korisnički disk ima V = 1/K, a njihov zbir je uvek tačno 1 — svaki posao izlazi iz sistema preko tačno jednog korisničkog diska, što je nezavisna provera ispravnosti rešenja.

### 2.2 Granični intenzitet ulaznog toka α_max(K) i kritični resurs

Sistem je u stacionarnom režimu dok je svaki server neopterećen preko svog kapaciteta:

```
rho_i = lambda_i / mi_i = V_i * alpha * S_i < 1
  =>  alpha < 1 / (V_i * S_i)   za svako i
  =>  alpha_max = 1 / max_i (V_i * S_i)
```

Veličina D_i = V_i · S_i je ukupan zahtev jednog posla za serverom i. Server sa najvećim D_i je **kritični resurs** (usko grlo) i on prvi dostiže iskorišćenje 1.

**Zahtevi D_i = V_i·S_i, granični intenzitet i kritični resurs**

| K | D_CPU [ms] | D_SD1 [ms] | D_SD2 [ms] | D_SD3 [ms] | D_KD [ms] | α_max [1/s] | kritični resurs |
|---|---|---|---|---|---|---|---|
| 2 | 6.2500 | 4.1667 | 4.6875 | 3.1250 | 12.5000 | 80.0000 | svi korisnički diskovi |
| 3 | 6.2500 | 4.1667 | 4.6875 | 3.1250 | 8.3333 | 120.0000 | svi korisnički diskovi |
| 4 | 6.2500 | 4.1667 | 4.6875 | 3.1250 | 6.2500 | 160.0000 | Procesor i svi korisnički diskovi |
| 5 | 6.2500 | 4.1667 | 4.6875 | 3.1250 | 5.0000 | 160.0000 | Procesor |

Zahtev procesora je konstantan (D_CPU = 1.5625 · 4 ms = 6.25 ms), dok zahtev jednog korisničkog diska opada sa K (D_KD = (1/K) · 25 ms = 25/K ms) jer se isti posao ravnomerno deli na više diskova. Zato za K = 2 i K = 3 usko grlo čine korisnički diskovi, za **K = 4 zahtevi procesora i korisničkog diska su jednaki (6.25 ms) i oba resursa su kritična**, a za K = 5 kritičan postaje procesor. Time α_max prestaje da raste sa K: dodavanje petog korisničkog diska više ne povećava kapacitet sistema jer je procesor postao ograničenje.

![Zavisnost graničnog intenziteta ulaznog toka α_max od broja korisničkih diskova K](grafici/alpha_max_vs_K.png)

*Zavisnost graničnog intenziteta ulaznog toka α_max od broja korisničkih diskova K*

### 2.3 Džeksonova teorema — parametri performansi

Po Džeksonovoj teoremi, stacionarna raspodela otvorene mreže je proizvod raspodela pojedinačnih čvorova, pa se svaki server analizira kao nezavisan M/M/1 sistem sa ulaznim tokom λ_i = V_i · α:

```
X_i   = V_i * alpha                 (protok kroz server)
rho_i = X_i * S_i                   (iskorišćenje servera)
N_i   = rho_i / (1 - rho_i)         (prosečan broj poslova u serveru)
W_i   = S_i / (1 - rho_i)           (vreme odziva servera po prolazu)
N     = suma_i N_i
T     = N / alpha = suma_i V_i * W_i    (Litlov zakon)
```

**Analitički rezultati za r = 0.30**

| K | α [1/s] | ρ_CPU | ρ_SD1 | ρ_SD2 | ρ_SD3 | ρ_KD | N (sistem) | T_sistem [ms] |
|---|---|---|---|---|---|---|---|---|
| 2 | 24.00 | 0.1500 | 0.1000 | 0.1125 | 0.0750 | 0.3000 | 1.3526 | 56.3569 |
| 3 | 36.00 | 0.2250 | 0.1500 | 0.1688 | 0.1125 | 0.3000 | 2.0823 | 57.8410 |
| 4 | 48.00 | 0.3000 | 0.2000 | 0.2250 | 0.1500 | 0.3000 | 2.8597 | 59.5760 |
| 5 | 48.00 | 0.3000 | 0.2000 | 0.2250 | 0.1500 | 0.2400 | 2.7243 | 56.7565 |

**Analitički rezultati za r = 0.55**

| K | α [1/s] | ρ_CPU | ρ_SD1 | ρ_SD2 | ρ_SD3 | ρ_KD | N (sistem) | T_sistem [ms] |
|---|---|---|---|---|---|---|---|---|
| 2 | 44.00 | 0.2750 | 0.1833 | 0.2062 | 0.1375 | 0.5500 | 3.4675 | 78.8070 |
| 3 | 66.00 | 0.4125 | 0.2750 | 0.3094 | 0.2062 | 0.5500 | 5.4559 | 82.6653 |
| 4 | 88.00 | 0.5500 | 0.3667 | 0.4125 | 0.2750 | 0.5500 | 7.7715 | 88.3125 |
| 5 | 88.00 | 0.5500 | 0.3667 | 0.4125 | 0.2750 | 0.4400 | 6.8112 | 77.3998 |

**Analitički rezultati za r = 0.80**

| K | α [1/s] | ρ_CPU | ρ_SD1 | ρ_SD2 | ρ_SD3 | ρ_KD | N (sistem) | T_sistem [ms] |
|---|---|---|---|---|---|---|---|---|
| 2 | 64.00 | 0.4000 | 0.2667 | 0.3000 | 0.2000 | 0.8000 | 9.7089 | 151.7012 |
| 3 | 96.00 | 0.6000 | 0.4000 | 0.4500 | 0.3000 | 0.8000 | 15.4134 | 160.5565 |
| 4 | 128.00 | 0.8000 | 0.5333 | 0.6000 | 0.4000 | 0.8000 | 23.3095 | 182.1057 |
| 5 | 128.00 | 0.8000 | 0.5333 | 0.6000 | 0.4000 | 0.6400 | 16.1984 | 126.5501 |

**Analitički rezultati za r = 1.00**

| K | α [1/s] | ρ_CPU | ρ_SD1 | ρ_SD2 | ρ_SD3 | ρ_KD | N (sistem) | T_sistem [ms] |
|---|---|---|---|---|---|---|---|---|
| 2 | 80.00 | 0.5000 | 0.3333 | 0.3750 | 0.2500 | 1.0000 | ∞ | ∞ |
| 3 | 120.00 | 0.7500 | 0.5000 | 0.5625 | 0.3750 | 1.0000 | ∞ | ∞ |
| 4 | 160.00 | 1.0000 | 0.6667 | 0.7500 | 0.5000 | 1.0000 | ∞ | ∞ |
| 5 | 160.00 | 1.0000 | 0.6667 | 0.7500 | 0.5000 | 0.8000 | ∞ | ∞ |

Za r = 1.00 je α = α_max, pa kritični resurs ima ρ = 1. M/M/1 red tada nije stacionaran: N_i = ρ/(1−ρ) i W_i = S/(1−ρ) teže beskonačnosti, pa su N i T_sistem beskonačni (u tabelama označeno sa ∞). To je granični slučaj koji realni sistem ne može da održi, a u simulaciji se vidi kao red koji neprekidno raste.

## 3. Simulacija

### 3.1 Metod: diskretno-dogadjajna simulacija (DES)

Simulacija nije vođena vremenom (nema koraka Δt ni čekanja na serveru), već **dogadjajima**: program održava kalendar budućih dogadjaja (min-hip uređen po vremenu) i simulaciono vreme skače direktno na trenutak sledećeg dogadjaja. Takav pristup ne troši vreme na intervale u kojima se ništa ne dešava i daje tačno iste rezultate kao vremenski vođena simulacija sa beskonačno malim korakom.

Postoje dva tipa dogadjaja:

- **DOLAZAK** — spoljni dolazak posla u procesor. Poasonov tok znači eksponencijalne međudolazne intervale, pa se pri svakom dolasku odmah zakazuje sledeći, u trenutku t + Exp(α).
- **ODLAZAK** — završetak opsluživanja posla u čvoru i. Tada se, ako red nije prazan, uzima sledeći posao (FCFS) i zakazuje njegov odlazak u t + Exp(μ_i), a posao koji je završen rutira se dalje.

Rutiranje koristi **istu matricu verovatnoća tranzicija P** koju koristi i analitički deo: iz reda matrice se unapred izračunaju kumulativne verovatnoće, pa se odredište bira jednim slučajnim brojem u ~ U(0,1). Ako u premaši sumu reda, posao napušta sistem — za korisničke diskove je suma reda nula, pa oni uvek izbacuju posao iz sistema.

```
dogadjaj = (vreme, tip, cvor)
kalendar = min-hip po vremenu

dok kalendar nije prazan:
    (t, tip, i) = izvadi_najraniji(kalendar)
    ako t > kraj_simulacije: prekini
    ako tip == DOLAZAK:
        zakazi (t + Exp(alpha), DOLAZAK, procesor)
        cilj = procesor;  ulazak = t
    inace:                                  # ODLAZAK iz cvora i
        azuriraj statistiku cvora i;  broj[i] -= 1
        ako red[i] nije prazan:
            uzmi sledeci posao (FCFS)
            zakazi (t + Exp(mi_i), ODLAZAK, i)
        cilj = rutiraj(i)                   # po matrici P
        ako cilj == IZLAZ: zabelezi vreme u sistemu;  nastavi
    # ulazak posla u cvor 'cilj'
    azuriraj statistiku cvora cilj;  broj[cilj] += 1
    ako je server slobodan: zakazi (t + Exp(mi_cilj), ODLAZAK, cilj)
    inace: dodaj posao u red[cilj]
```

### 3.2 Prikupljanje statistike

Statistika se prikuplja bez ikakve pretpostavke o raspodeli — samo iz onoga što se u simulaciji dogodilo:

```
rho_i = (ukupno vreme zauzetosti servera i) / T
X_i   = (broj zavrsenih opsluzivanja u cvoru i) / T
N_i   = (integral broja poslova u cvoru i po vremenu) / T
W_i   = N_i / X_i                        (Litlov zakon po cvoru)
T_sistem = (zbir vremena provedenih u sistemu) / (broj izaslih poslova)
```

Integral broja poslova računa se inkrementalno: pri svakoj promeni broja poslova u čvoru dodaje se (trenutni broj) × (vreme od poslednje promene). Vreme provedeno u sistemu meri se tako što svaki posao nosi trenutak svog spoljnog dolaska kroz celu mrežu. Kao kontrola, program uz izmereno srednje vreme u sistemu ispisuje i vrednost N/α — po Litlovom zakonu te dve vrednosti moraju da se poklope, i u rezultatima se poklapaju na nekoliko decimala.

Mreža na početku simulacije je prazna, pa sistem prvo prolazi kroz prelazni režim, što blago potcenjuje N i T. Uticaj je pri podrazumevanom trajanju od 30 minuta zanemarljiv (prelazni režim traje reda sekunde), a program ipak ima opciju `--zagrevanje` kojom se početni interval izbacuje iz statistike.

### 3.3 Ponavljanje i usrednjavanje

Za svaku kombinaciju (K, r) simulacija se ponavlja zadati broj puta, svaki put sa drugim semenom generatora slučajnih brojeva, pa su ponavljanja nezavisne realizacije istog stohastičkog procesa. Rezultati se usrednjavaju metriku po metriku, a uz srednju vrednost se računa i uzoračka standardna devijacija (upisana u `rezultati_simulacija_usrednjeno.txt`). Semena se izvode determinističkim pravilom iz baznog semena, pa je celo pokretanje programa ponovljivo.

Podrazumevano simulirano vreme rada sistema je 0.5 h = 30 min i može se promeniti opcijom `--minuti`. Rezultati u ovom dokumentu dobijeni su sa 30 min po izvršavanju i 100 ponavljanja po kombinaciji (K, r), tj. ukupno 1600 izvršavanja simulacije.

## 4. Poređenje analitičkih i simulacionih rezultata

Relativno odstupanje računa se kao (simulacija − analitika) / analitika · 100 %. Kompletne tabele za sve metrike i sve slučajeve nalaze se u `rezultati/poredjenje.txt`; ovde su prikazane ključne veličine u zavisnosti od broja korisničkih diskova K.

**r = 0.30 — iskorišćenje procesora**

| K | analitika | 1 simulacija | odst. [%] | usrednjeno (100 sim.) | odst. [%] |
|---|---|---|---|---|---|
| 2 | 0.15000 | 0.14773 | -1.516 | 0.14995 | -0.035 |
| 3 | 0.22500 | 0.22428 | -0.319 | 0.22500 | +0.000 |
| 4 | 0.30000 | 0.29815 | -0.615 | 0.29983 | -0.055 |
| 5 | 0.30000 | 0.30063 | +0.211 | 0.29984 | -0.052 |

**r = 0.30 — iskorišćenje korisničkog diska**

| K | analitika | 1 simulacija | odst. [%] | usrednjeno (100 sim.) | odst. [%] |
|---|---|---|---|---|---|
| 2 | 0.30000 | 0.29808 | -0.639 | 0.29983 | -0.056 |
| 3 | 0.30000 | 0.29865 | -0.449 | 0.29997 | -0.009 |
| 4 | 0.30000 | 0.30007 | +0.024 | 0.29982 | -0.061 |
| 5 | 0.24000 | 0.24185 | +0.770 | 0.23998 | -0.009 |

**r = 0.30 — vreme odziva procesora [ms]**

| K | analitika | 1 simulacija | odst. [%] | usrednjeno (100 sim.) | odst. [%] |
|---|---|---|---|---|---|
| 2 | 4.70588 | 4.66356 | -0.899 | 4.70694 | +0.022 |
| 3 | 5.16129 | 5.14721 | -0.273 | 5.16006 | -0.024 |
| 4 | 5.71429 | 5.67877 | -0.621 | 5.71143 | -0.050 |
| 5 | 5.71429 | 5.72083 | +0.115 | 5.71537 | +0.019 |

**r = 0.30 — vreme odziva korisničkog diska [ms]**

| K | analitika | 1 simulacija | odst. [%] | usrednjeno (100 sim.) | odst. [%] |
|---|---|---|---|---|---|
| 2 | 35.71429 | 35.58001 | -0.376 | 35.65487 | -0.166 |
| 3 | 35.71429 | 35.58205 | -0.370 | 35.65974 | -0.153 |
| 4 | 35.71429 | 35.92202 | +0.582 | 35.71043 | -0.011 |
| 5 | 32.89474 | 33.23222 | +1.026 | 32.91032 | +0.047 |

**r = 0.30 — vreme odziva sistema [ms]**

| K | analitika | 1 simulacija | odst. [%] | usrednjeno (100 sim.) | odst. [%] |
|---|---|---|---|---|---|
| 2 | 56.35693 | 56.26381 | -0.165 | 56.28292 | -0.131 |
| 3 | 57.84099 | 57.60459 | -0.409 | 57.76354 | -0.134 |
| 4 | 59.57605 | 59.77350 | +0.331 | 59.57328 | -0.005 |
| 5 | 56.75650 | 57.04130 | +0.502 | 56.78743 | +0.054 |

**r = 0.55 — iskorišćenje procesora**

| K | analitika | 1 simulacija | odst. [%] | usrednjeno (100 sim.) | odst. [%] |
|---|---|---|---|---|---|
| 2 | 0.27500 | 0.27579 | +0.286 | 0.27524 | +0.088 |
| 3 | 0.41250 | 0.40978 | -0.660 | 0.41248 | -0.006 |
| 4 | 0.55000 | 0.54862 | -0.250 | 0.55014 | +0.025 |
| 5 | 0.55000 | 0.54713 | -0.522 | 0.55013 | +0.023 |

**r = 0.55 — iskorišćenje korisničkog diska**

| K | analitika | 1 simulacija | odst. [%] | usrednjeno (100 sim.) | odst. [%] |
|---|---|---|---|---|---|
| 2 | 0.55000 | 0.55026 | +0.048 | 0.54991 | -0.017 |
| 3 | 0.55000 | 0.54905 | -0.173 | 0.55019 | +0.034 |
| 4 | 0.55000 | 0.54639 | -0.657 | 0.55017 | +0.031 |
| 5 | 0.44000 | 0.43793 | -0.471 | 0.44008 | +0.019 |

**r = 0.55 — vreme odziva procesora [ms]**

| K | analitika | 1 simulacija | odst. [%] | usrednjeno (100 sim.) | odst. [%] |
|---|---|---|---|---|---|
| 2 | 5.51724 | 5.56275 | +0.825 | 5.51883 | +0.029 |
| 3 | 6.80851 | 6.77566 | -0.483 | 6.80954 | +0.015 |
| 4 | 8.88889 | 8.92519 | +0.408 | 8.89153 | +0.030 |
| 5 | 8.88889 | 8.78177 | -1.205 | 8.89066 | +0.020 |

**r = 0.55 — vreme odziva korisničkog diska [ms]**

| K | analitika | 1 simulacija | odst. [%] | usrednjeno (100 sim.) | odst. [%] |
|---|---|---|---|---|---|
| 2 | 55.55556 | 55.80278 | +0.445 | 55.49910 | -0.102 |
| 3 | 55.55556 | 55.98395 | +0.771 | 55.62035 | +0.117 |
| 4 | 55.55556 | 54.84508 | -1.279 | 55.59964 | +0.079 |
| 5 | 44.64286 | 44.11872 | -1.174 | 44.66720 | +0.055 |

**r = 0.55 — vreme odziva sistema [ms]**

| K | analitika | 1 simulacija | odst. [%] | usrednjeno (100 sim.) | odst. [%] |
|---|---|---|---|---|---|
| 2 | 78.80699 | 79.23557 | +0.544 | 78.77910 | -0.035 |
| 3 | 82.66532 | 82.82510 | +0.193 | 82.70259 | +0.045 |
| 4 | 88.31246 | 87.60171 | -0.805 | 88.35286 | +0.046 |
| 5 | 77.39976 | 76.35543 | -1.349 | 77.42787 | +0.036 |

**r = 0.80 — iskorišćenje procesora**

| K | analitika | 1 simulacija | odst. [%] | usrednjeno (100 sim.) | odst. [%] |
|---|---|---|---|---|---|
| 2 | 0.40000 | 0.40067 | +0.166 | 0.40007 | +0.017 |
| 3 | 0.60000 | 0.59658 | -0.571 | 0.60009 | +0.016 |
| 4 | 0.80000 | 0.80000 | -0.000 | 0.79949 | -0.064 |
| 5 | 0.80000 | 0.80236 | +0.294 | 0.79952 | -0.060 |

**r = 0.80 — iskorišćenje korisničkog diska**

| K | analitika | 1 simulacija | odst. [%] | usrednjeno (100 sim.) | odst. [%] |
|---|---|---|---|---|---|
| 2 | 0.80000 | 0.80239 | +0.298 | 0.80018 | +0.023 |
| 3 | 0.80000 | 0.79962 | -0.047 | 0.80025 | +0.032 |
| 4 | 0.80000 | 0.80085 | +0.107 | 0.79982 | -0.023 |
| 5 | 0.64000 | 0.64191 | +0.298 | 0.63979 | -0.033 |

**r = 0.80 — vreme odziva procesora [ms]**

| K | analitika | 1 simulacija | odst. [%] | usrednjeno (100 sim.) | odst. [%] |
|---|---|---|---|---|---|
| 2 | 6.66667 | 6.64917 | -0.262 | 6.66351 | -0.047 |
| 3 | 10.00000 | 9.86028 | -1.397 | 9.99845 | -0.015 |
| 4 | 20.00000 | 20.10281 | +0.514 | 19.92378 | -0.381 |
| 5 | 20.00000 | 20.67281 | +3.364 | 19.93043 | -0.348 |

**r = 0.80 — vreme odziva korisničkog diska [ms]**

| K | analitika | 1 simulacija | odst. [%] | usrednjeno (100 sim.) | odst. [%] |
|---|---|---|---|---|---|
| 2 | 125.00000 | 130.75843 | +4.607 | 125.41018 | +0.328 |
| 3 | 125.00000 | 128.90588 | +3.125 | 125.52744 | +0.422 |
| 4 | 125.00000 | 125.36614 | +0.293 | 125.24896 | +0.199 |
| 5 | 69.44444 | 69.52008 | +0.109 | 69.41081 | -0.048 |

**r = 0.80 — vreme odziva sistema [ms]**

| K | analitika | 1 simulacija | odst. [%] | usrednjeno (100 sim.) | odst. [%] |
|---|---|---|---|---|---|
| 2 | 151.70116 | 157.55532 | +3.859 | 152.11688 | +0.274 |
| 3 | 160.55646 | 164.07524 | +2.192 | 161.08518 | +0.329 |
| 4 | 182.10565 | 182.65079 | +0.299 | 182.19232 | +0.048 |
| 5 | 126.55010 | 128.20059 | +1.304 | 126.34130 | -0.165 |

**r = 1.00 — iskorišćenje procesora**

| K | analitika | 1 simulacija | odst. [%] | usrednjeno (100 sim.) | odst. [%] |
|---|---|---|---|---|---|
| 2 | 0.50000 | 0.50218 | +0.436 | 0.49979 | -0.043 |
| 3 | 0.75000 | 0.75377 | +0.502 | 0.74969 | -0.042 |
| 4 | 1.00000 | 0.99641 | -0.359 | 0.99795 | -0.205 |
| 5 | 1.00000 | 0.99689 | -0.311 | 0.99805 | -0.195 |

**r = 1.00 — iskorišćenje korisničkog diska**

| K | analitika | 1 simulacija | odst. [%] | usrednjeno (100 sim.) | odst. [%] |
|---|---|---|---|---|---|
| 2 | 1.00000 | 0.99761 | -0.239 | 0.99587 | -0.413 |
| 3 | 1.00000 | 0.99536 | -0.464 | 0.99571 | -0.429 |
| 4 | 1.00000 | 0.99459 | -0.541 | 0.99448 | -0.552 |
| 5 | 0.80000 | 0.79852 | -0.185 | 0.79833 | -0.209 |

**r = 1.00 — vreme odziva procesora [ms]**

| K | analitika | 1 simulacija | odst. [%] | usrednjeno (100 sim.) | odst. [%] |
|---|---|---|---|---|---|
| 2 | 8.00000 | 8.04061 | +0.508 | 7.99448 | -0.069 |
| 3 | 16.00000 | 16.49299 | +3.081 | 15.96145 | -0.241 |
| 4 | ∞ | 976.55483 | — | 1658.54785 | — |
| 5 | ∞ | 1142.93459 | — | 1531.90774 | — |

**r = 1.00 — vreme odziva korisničkog diska [ms]**

| K | analitika | 1 simulacija | odst. [%] | usrednjeno (100 sim.) | odst. [%] |
|---|---|---|---|---|---|
| 2 | ∞ | 4039.01985 | — | 5145.38914 | — |
| 3 | ∞ | 8294.15319 | — | 4860.31267 | — |
| 4 | ∞ | 3094.76082 | — | 4296.60818 | — |
| 5 | 125.00000 | 125.17593 | +0.141 | 123.83323 | -0.933 |

**r = 1.00 — vreme odziva sistema [ms]**

| K | analitika | 1 simulacija | odst. [%] | usrednjeno (100 sim.) | odst. [%] |
|---|---|---|---|---|---|
| 2 | ∞ | 4050.94527 | — | 5150.92678 | — |
| 3 | ∞ | 8304.12676 | — | 4887.47927 | — |
| 4 | ∞ | 4649.29960 | — | 6896.34813 | — |
| 5 | ∞ | 1940.56756 | — | 2546.89343 | — |

**Srednje apsolutno relativno odstupanje od analitičkog rešenja, po slučaju**

| K | r | 1 simulacija [%] | usrednjeno [%] | odnos | broj metrika |
|---|---|---|---|---|---|
| 2 | 0.30 | 0.9403 | 0.1025 | 9.18 | 23 |
| 3 | 0.30 | 0.3891 | 0.0754 | 5.16 | 23 |
| 4 | 0.30 | 0.5361 | 0.0679 | 7.90 | 23 |
| 5 | 0.30 | 0.6624 | 0.0597 | 11.09 | 23 |
| 2 | 0.55 | 0.6548 | 0.0837 | 7.82 | 23 |
| 3 | 0.55 | 0.7193 | 0.0744 | 9.67 | 23 |
| 4 | 0.55 | 0.6551 | 0.0415 | 15.77 | 23 |
| 5 | 0.55 | 0.8845 | 0.0325 | 27.21 | 23 |
| 2 | 0.80 | 1.2760 | 0.1229 | 10.39 | 23 |
| 3 | 0.80 | 1.1119 | 0.1172 | 9.48 | 23 |
| 4 | 0.80 | 0.2062 | 0.1203 | 1.71 | 23 |
| 5 | 0.80 | 1.1986 | 0.1391 | 8.62 | 23 |
| 2 | 1.00 | 0.4913 | 0.1234 | 3.98 | 19 |
| 3 | 1.00 | 0.6861 | 0.1434 | 4.78 | 19 |
| 4 | 1.00 | 0.8137 | 0.4152 | 1.96 | 17 |
| 5 | 1.00 | 1.0779 | 0.3540 | 3.04 | 19 |

Prosečno po svim slučajevima, jedna simulacija odstupa od analitičkog rešenja **0.769 %**, a usrednjeni rezultat **0.130 %** — dakle oko **5.9 puta** manje. Usrednjeni rezultat je bliži analitičkom u 16 od 16 posmatranih slučajeva.

Odnos odstupanja posmatran po pojedinačnom slučaju je informativniji od odnosa proseka. Za stacionarne slučajeve (r < 1.00) on iznosi u proseku **10.3**, što je blizu teorijski očekivanog √100 = 10. Za r = 1.00 odnos je manji (u proseku 3.4) jer tamo preostalo odstupanje ne potiče od statističke fluktuacije, koja se usrednjavanjem smanjuje, već od toga što sistem uopšte nije u stacionarnom režimu — takvu grešku usrednjavanje ne može da ukloni.

### 4.1 Odgovori na postavljena pitanja

**Šta se može zaključiti o rezultatima simulacije i usrednjenim rezultatima više simulacija?** Obe vrste rezultata potvrđuju analitičko rešenje: iskorišćenja i protoci se poklapaju već u jednoj simulaciji (odstupanja reda desetinke procenta), jer su to veličine koje se akumuliraju kroz stotine hiljada dogadjaja. Veća odstupanja javljaju se kod N_i, W_i i T_sistem, i to utoliko više ukoliko je opterećenje veće — kod jako iskorišćenih servera dužina reda ima veliku varijansu, pa ista dužina simulacije daje manje pouzdanu procenu.

**Koji rezultati imaju manje relativno odstupanje?** Usrednjeni rezultati više simulacija, u praktično svim slučajevima i za sve metrike, kako pokazuje sumarna tabela iznad.

**Kako i zašto broj izvršenih simulacija utiče na relativno odstupanje?** Svako izvršavanje daje slučajnu procenu čija je srednja vrednost tačna (nepristrasna), ali koja odstupa zbog varijanse. Za n nezavisnih ponavljanja standardna greška srednje vrednosti opada kao σ/√n, pa se očekuje da usrednjavanje 100 simulacija smanji tipično odstupanje oko √100 = 10 puta u odnosu na jednu simulaciju. Zbog toga povećanje broja ponavljanja daje sve manji dobitak: da bi se greška prepolovila, broj simulacija se mora učetvorostručiti. Isti efekat ima i produžavanje simuliranog vremena jedne simulacije, jer i ono povećava broj nezavisnih uzoraka u proceni.

Ostatak odstupanja koji se ne smanjuje usrednjavanjem potiče od sistematskih efekata: prelazni režim na početku (mreža kreće prazna) i poslovi koji su na kraju simulacije još u sistemu, pa ne ulaze u srednje vreme odziva. Oba efekta su relativno manja što je simulacija duža.

### 4.2 Granični slučaj r = 1.00

Za r = 1.00 kritični resurs ima ρ = 1 i analitički nema stacionarno rešenje (N i T su beskonačni), pa relativno odstupanje nije definisano. Simulacija ipak daje konačan broj, ali on nije procena stacionarne vrednosti — red kritičnog resursa raste tokom celog simuliranog vremena, pa izmereno T_sistem zavisi od toga koliko dugo je simulacija trajala i sa dužim trajanjem bi bilo veće. To je i praktična ilustracija zašto se realni sistemi ne projektuju da rade na granici kapaciteta.

**r = 1.00: zasićenje kritičnog resursa**

| K | T_sistem analitički | T_sistem 1 sim. [ms] | T_sistem usrednjeno [ms] | max ρ (simulacija) | poslova u sistemu na kraju |
|---|---|---|---|---|---|
| 2 | ∞ | 4050.95 | 5150.93 | 0.9960 | 597 |
| 3 | ∞ | 8304.13 | 4887.48 | 0.9960 | 841 |
| 4 | ∞ | 4649.30 | 6896.35 | 0.9979 | 1585 |
| 5 | ∞ | 1940.57 | 2546.89 | 0.9980 | 623 |

## 5. Dijagrami

Dijagrami su konstruisani na osnovu analitičkih rezultata, kako zadatak traži. Na svakom dijagramu krive su različitih boja i simbola, sa legendom.

### 5.1 Iskorišćenje resursa u funkciji od K

![Iskorišćenje procesora, sistemskih diskova i korisničkog diska u funkciji od K, za r = 0.30](grafici/iskoriscenja_r030.png)

*Iskorišćenje procesora, sistemskih diskova i korisničkog diska u funkciji od K, za r = 0.30*

![Iskorišćenje procesora, sistemskih diskova i korisničkog diska u funkciji od K, za r = 0.55](grafici/iskoriscenja_r055.png)

*Iskorišćenje procesora, sistemskih diskova i korisničkog diska u funkciji od K, za r = 0.55*

![Iskorišćenje procesora, sistemskih diskova i korisničkog diska u funkciji od K, za r = 0.80](grafici/iskoriscenja_r080.png)

*Iskorišćenje procesora, sistemskih diskova i korisničkog diska u funkciji od K, za r = 0.80*

![Iskorišćenje procesora, sistemskih diskova i korisničkog diska u funkciji od K, za r = 1.00](grafici/iskoriscenja_r100.png)

*Iskorišćenje procesora, sistemskih diskova i korisničkog diska u funkciji od K, za r = 1.00*

Za fiksno α iskorišćenje procesora ne bi zavisilo od K (ρ_CPU = D_CPU·α = 6.25 ms · α), a iskorišćenje pojedinačnog korisničkog diska opadalo bi kao (25/K) ms · α, jer se isti posao deli na više diskova. Na dijagramima, međutim, α nije fiksno nego prati kapacitet sistema (α = r·α_max(K)), pa krive nisu monotone: dok α_max raste (K = 2, 3, 4), raste i opterećenje procesora, a korisnički diskovi ostaju na ρ = r jer su oni usko grlo. Prelazak sa K = 4 na K = 5 ne povećava α (α_max ostaje 160 1/s), pa iskorišćenje korisničkih diskova naglo pada, dok procesor ostaje na ρ = r kao novi kritični resurs.

### 5.2 Vreme odziva servera u funkciji od K

![Vreme odziva servera (po jednom prolazu) u funkciji od K, za r = 0.30](grafici/vremena_odziva_servera_r030.png)

*Vreme odziva servera (po jednom prolazu) u funkciji od K, za r = 0.30*

![Vreme odziva servera (po jednom prolazu) u funkciji od K, za r = 0.55](grafici/vremena_odziva_servera_r055.png)

*Vreme odziva servera (po jednom prolazu) u funkciji od K, za r = 0.55*

![Vreme odziva servera (po jednom prolazu) u funkciji od K, za r = 0.80](grafici/vremena_odziva_servera_r080.png)

*Vreme odziva servera (po jednom prolazu) u funkciji od K, za r = 0.80*

![Vreme odziva servera (po jednom prolazu) u funkciji od K, za r = 1.00](grafici/vremena_odziva_servera_r100.png)

*Vreme odziva servera (po jednom prolazu) u funkciji od K, za r = 1.00*

### 5.3 Vreme odziva sistema u funkciji od K

![Vreme odziva sistema T u funkciji od K, za r = 0.30](grafici/vreme_odziva_sistema_r030.png)

*Vreme odziva sistema T u funkciji od K, za r = 0.30*

![Vreme odziva sistema T u funkciji od K, za r = 0.55](grafici/vreme_odziva_sistema_r055.png)

*Vreme odziva sistema T u funkciji od K, za r = 0.55*

![Vreme odziva sistema T u funkciji od K, za r = 0.80](grafici/vreme_odziva_sistema_r080.png)

*Vreme odziva sistema T u funkciji od K, za r = 0.80*

![Vreme odziva sistema T u funkciji od K, za r = 1.00](grafici/vreme_odziva_sistema_r100.png)

*Vreme odziva sistema T u funkciji od K, za r = 1.00*

Vreme odziva sistema raste sa K sve dok kritični resurs ostaje korisnički disk, jer se sa svakim dodatim diskom povećava i α = r·α_max, pa i opterećenje ostalih resursa. Kod K = 5 ulazni tok se ne povećava (α_max ostaje 160 1/s), a posao se deli na više diskova, pa T ponovo opada. Za r = 1.00 nijedna tačka nije konačna, pa je na tom dijagramu, radi poređenja, sivom bojom prikazana kriva za r = 0.99 — ona pokazuje koliko naglo T raste pri približavanju granici kapaciteta.

### 5.4 Dodatno: poređenje analitike i simulacije

![Vreme odziva sistema — analitika, jedna simulacija i usrednjena simulacija, za r = 0.30](grafici/poredjenje_T_sistem_r030.png)

*Vreme odziva sistema — analitika, jedna simulacija i usrednjena simulacija, za r = 0.30*

![Vreme odziva sistema — analitika, jedna simulacija i usrednjena simulacija, za r = 0.55](grafici/poredjenje_T_sistem_r055.png)

*Vreme odziva sistema — analitika, jedna simulacija i usrednjena simulacija, za r = 0.55*

![Vreme odziva sistema — analitika, jedna simulacija i usrednjena simulacija, za r = 0.80](grafici/poredjenje_T_sistem_r080.png)

*Vreme odziva sistema — analitika, jedna simulacija i usrednjena simulacija, za r = 0.80*

![Vreme odziva sistema — analitika, jedna simulacija i usrednjena simulacija, za r = 1.00](grafici/poredjenje_T_sistem_r100.png)

*Vreme odziva sistema — analitika, jedna simulacija i usrednjena simulacija, za r = 1.00*

![Iskorišćenje resursa — analitika (linije) i usrednjena simulacija (simboli), za r = 0.30](grafici/poredjenje_iskoriscenja_r030.png)

*Iskorišćenje resursa — analitika (linije) i usrednjena simulacija (simboli), za r = 0.30*

![Iskorišćenje resursa — analitika (linije) i usrednjena simulacija (simboli), za r = 0.55](grafici/poredjenje_iskoriscenja_r055.png)

*Iskorišćenje resursa — analitika (linije) i usrednjena simulacija (simboli), za r = 0.55*

![Iskorišćenje resursa — analitika (linije) i usrednjena simulacija (simboli), za r = 0.80](grafici/poredjenje_iskoriscenja_r080.png)

*Iskorišćenje resursa — analitika (linije) i usrednjena simulacija (simboli), za r = 0.80*

![Iskorišćenje resursa — analitika (linije) i usrednjena simulacija (simboli), za r = 1.00](grafici/poredjenje_iskoriscenja_r100.png)

*Iskorišćenje resursa — analitika (linije) i usrednjena simulacija (simboli), za r = 1.00*

## 6. Kritični resurs za svaku kombinaciju (r, K)

Pošto je ρ_i = D_i · α, a α = r · α_max samo skalira sva iskorišćenja istim faktorom, **kritični resurs zavisi isključivo od K, ne i od r**. Vrednost r određuje koliko je kritični resurs opterećen: ρ kritičnog resursa je tačno jednako r.

**Kritični resurs po kombinaciji parametara**

| r | K | kritični resurs | ρ kritičnog resursa |
|---|---|---|---|
| 0.30 | 2 | svi korisnički diskovi | 0.3000 |
| 0.30 | 3 | svi korisnički diskovi | 0.3000 |
| 0.30 | 4 | Procesor i svi korisnički diskovi | 0.3000 |
| 0.30 | 5 | Procesor | 0.3000 |
| 0.55 | 2 | svi korisnički diskovi | 0.5500 |
| 0.55 | 3 | svi korisnički diskovi | 0.5500 |
| 0.55 | 4 | Procesor i svi korisnički diskovi | 0.5500 |
| 0.55 | 5 | Procesor | 0.5500 |
| 0.80 | 2 | svi korisnički diskovi | 0.8000 |
| 0.80 | 3 | svi korisnički diskovi | 0.8000 |
| 0.80 | 4 | Procesor i svi korisnički diskovi | 0.8000 |
| 0.80 | 5 | Procesor | 0.8000 |
| 1.00 | 2 | svi korisnički diskovi | 1.0000 |
| 1.00 | 3 | svi korisnički diskovi | 1.0000 |
| 1.00 | 4 | Procesor i svi korisnički diskovi | 1.0000 |
| 1.00 | 5 | Procesor | 1.0000 |

Za K = 2 i K = 3 usko grlo su korisnički diskovi; za K = 4 procesor i korisnički diskovi imaju identičan zahtev (6.25 ms) pa su svi kritični; za K = 5 kritičan je procesor. Praktična posledica: povećavanje broja korisničkih diskova poboljšava kapacitet sistema samo do K = 4, posle čega je procesor ograničenje i dalja ulaganja u diskove ne povećavaju α_max.

## 7. Zaključak

- Matrični metod daje koeficijente poseta koji ne zavise od α, pa su protoci kroz sve servere linearne funkcije ulaznog toka; zbir koeficijenata poseta korisničkih diskova je tačno 1, što potvrđuje ispravnost postavljenog sistema jednačina.
- Granični intenzitet je α_max = 80, 120, 160 i 160 1/s za K = 2, 3, 4 i 5; kritični resurs prelazi sa korisničkih diskova na procesor između K = 4 (gde su izjednačeni) i K = 5.
- Simulacija nezavisno potvrđuje analitičko rešenje: iskorišćenja i protoci se poklapaju sa odstupanjima reda desetinke procenta, a vremena odziva i dužine redova nešto više odstupaju pri visokom opterećenju.
- Usrednjavanje više nezavisnih simulacija smanjuje odstupanje približno kao 1/√n, pa je usrednjeni rezultat znatno bliži analitičkom nego rezultat jedne simulacije.
- Za r = 1.00 analitičko rešenje ne postoji (ρ = 1), a simulacija pokazuje red koji neprekidno raste — oba metoda se slažu da sistem na granici kapaciteta nije upotrebljiv.

Dva metoda se međusobno proveravaju: analitika daje tačne vrednosti pod pretpostavkama Džeksonove mreže i trenutna je, ali važi samo dok su te pretpostavke ispunjene i samo za stacionarni režim; simulacija ne zahteva te pretpostavke i primenljiva je i na sisteme koji se ne mogu rešiti analitički, ali daje procene sa statističkom greškom koja se smanjuje tek dužim ili ponovljenim izvršavanjem.

## 8. Sadržaj priloga

| Fajl | Sadržaj |
|---|---|
| `parametri.py` | ulazni parametri sistema, matrica prelaza P, vektor brzina servera |
| `linearna_algebra.py` | Gausova eliminacija sa parcijalnim pivotiranjem |
| `analiticki.py` | matrični metod, α_max i kritični resurs, Džeksonova teorema |
| `simulacija.py` | diskretno-dogadjajna simulacija i usrednjavanje ponavljanja |
| `izvestaji.py` | formatiranje i upis izlaznih fajlova |
| `poredjenje.py` | relativna odstupanja i tabele poređenja |
| `grafici.py` | crtanje svih dijagrama |
| `dokumentacija.py` | generisanje ovog dokumenta |
| `main.py` | glavni program (pokreće sve) |
| `rezultati/protoci_analiticki.txt` | matrica P, brzine servera, V_i = X_i/α, protoci |
| `rezultati/rezultati_analiticki.txt` | α_max i kritični resursi, svi parametri po Džeksonu |
| `rezultati/rezultati_simulacija.txt` | rezultati jedne simulacije po kombinaciji (K, r) |
| `rezultati/rezultati_simulacija_usrednjeno.txt` | usrednjeni rezultati ponovljenih simulacija sa standardnim devijacijama |
| `rezultati/poredjenje.txt` | tabele relativnih odstupanja i sumarna tabela |
| `grafici/*.png` | svi dijagrami |
