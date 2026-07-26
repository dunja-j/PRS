"""
Zajedničke strukture za rezultate.

Istu strukturu popunjavaju i analitički metod (Džeksonova teorema) i
simulacija, pa modul za izveštaje i poređenje ne mora da zna odakle rezultat
dolazi. Time je poređenje analitika <-> simulacija svedeno na poređenje dva
objekta istog tipa.
"""

from dataclasses import dataclass, field

import parametri


@dataclass
class RezultatCvora:
    """Performanse jednog servisnog centra."""

    indeks: int
    ime: str
    puno_ime: str
    tip: str                      # 'procesor' | 'sistemski' | 'korisnicki'
    S: float                      # srednje vreme opsluživanja [s]
    V: float                      # koeficijent poseta V_i = X_i / alpha
    X: float                      # protok [1/s]
    rho: float                    # iskorišćenje [-]
    N: float                      # prosečan broj poslova (u redu + na obradi)
    W: float                      # vreme odziva servera po prolazu [s]


@dataclass
class RezultatSistema:
    """Performanse cele mreže za jedan par (K, alpha)."""

    K: int
    r: float
    alpha: float                  # intenzitet ulaznog toka [1/s]
    alpha_max: float              # granični intenzitet za dato K [1/s]
    metod: str                    # 'analitika' | 'simulacija' | 'simulacija-usrednjeno'
    cvorovi: list = field(default_factory=list)
    N_sistem: float = 0.0         # prosečan broj poslova u celom sistemu
    T_sistem: float = 0.0         # vreme odziva sistema [s]
    X_sistem: float = 0.0         # protok sistema (izlazni) [1/s]
    kriticni: tuple = ()          # indeksi kritičnih (najviše iskorišćenih) resursa
    stabilan: bool = True         # da li je rho_i < 1 za sve i
    dodatno: dict = field(default_factory=dict)   # metod-specifični podaci

    # -- pomoćni pristup ---------------------------------------------------
    def cvor(self, indeks):
        return self.cvorovi[indeks]

    def po_tipu(self, tip):
        return [c for c in self.cvorovi if c.tip == tip]

    def korisnicki_cvorovi(self):
        return self.po_tipu("korisnicki")

    def korisnicki_prosek(self, atribut):
        """
        Srednja vrednost metrike po korisničkim diskovima. Analitički su svi
        korisnički diskovi identični; u simulaciji se malo razlikuju zbog
        statističke fluktuacije, pa se usrednjavaju.
        """
        vrednosti = [getattr(c, atribut) for c in self.korisnicki_cvorovi()]
        return sum(vrednosti) / len(vrednosti)

    def imena_kriticnih(self):
        return parametri.opis_kriticnih(self.K, self.kriticni)
