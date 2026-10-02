#!/usr/bin/env python3
# ============================================================
#  MONTAGEM FRITAX - phonk bresilien (montagem / ritmada)
#  Tout est synthetise ici : batterie tamborzao, 808, cowbell,
#  charleys, voix par formants, reverb, limiteur.
#  Aucun echantillon, aucun fichier externe : que du signal.
# ============================================================
import numpy as np
import wave, sys, os

SR = 44100
TAU = 2 * np.pi
rng = np.random.default_rng(20261002)

# ------------------------------------------------------------
#  outils
# ------------------------------------------------------------
def t_array(duree):
    return np.arange(int(SR * duree)) / SR

def env_exp(n, attaque, chute):
    """enveloppe : attaque lineaire courte puis decroissance exponentielle"""
    a = max(1, int(attaque * SR))
    e = np.ones(n)
    e[:a] = np.linspace(0, 1, a)
    reste = n - a
    if reste > 0:
        e[a:] = np.exp(-np.arange(reste) / (SR * chute))
    return e

def noise(n):
    return rng.uniform(-1, 1, n)

def filtre_fft(x, reponse):
    """filtrage statique rapide : on multiplie le spectre par une reponse"""
    n = len(x)
    N = 1 << int(np.ceil(np.log2(n)))
    X = np.fft.rfft(x, N)
    f = np.fft.rfftfreq(N, 1 / SR)
    H = reponse(f)
    return np.fft.irfft(X * H, N)[:n]

def bande(f0, Q):
    def rep(f):
        return 1.0 / np.sqrt(1 + (Q * (f / max(f0, 1e-6) - f0 / np.maximum(f, 1e-6))) ** 2)
    return rep

def passe_bas(fc, pente=2):
    def rep(f):
        return 1.0 / np.sqrt(1 + (f / fc) ** (2 * pente))
    return rep

def passe_haut(fc, pente=2):
    def rep(f):
        return 1.0 / np.sqrt(1 + (fc / np.maximum(f, 1e-6)) ** (2 * pente))
    return rep

def resonateurs(x, formants, bandes):
    """filtre par banc de formants (voix)"""
    y = np.zeros_like(x)
    for f, b in zip(formants, bandes):
        y += filtre_fft(x, bande(f, f / b)) * b ** 0.5
    return y / (len(formants) * 0.6)

# ------------------------------------------------------------
#  les instruments
# ------------------------------------------------------------
def synth_kick(duree=0.42):
    t = t_array(duree)
    f = 150 * np.exp(-t * 34) + 45                     # chute de hauteur -> "coup"
    ph = np.cumsum(TAU * f / SR)
    corps = np.sin(ph) * env_exp(len(t), 0.001, 0.085)
    clic = filtre_fft(noise(len(t)), passe_haut(1400)) * env_exp(len(t), 0.0005, 0.004) * 0.45
    return np.tanh((corps * 1.5 + clic) * 1.8) * 0.95

def synth_tom(freq, duree=0.28):
    t = t_array(duree)
    f = freq * (1 + 0.5 * np.exp(-t * 45))
    ph = np.cumsum(TAU * f / SR)
    corps = np.sin(ph) * env_exp(len(t), 0.001, 0.055)
    peau = filtre_fft(noise(len(t)), bande(freq * 1.6, 1.2)) * env_exp(len(t), 0.001, 0.02) * 0.5
    return np.tanh((corps + peau) * 1.6) * 0.8

def synth_clap(duree=0.30):
    t = t_array(duree)
    y = np.zeros(len(t))
    for i, d in enumerate([0.0, 0.008, 0.016, 0.024]):   # trois rebonds + le corps
        n = noise(int(SR * (duree - d)))
        y[int(SR * d):int(SR * d) + len(n)] += filtre_fft(n, bande(1500, 0.9)) * (1.0 - 0.2 * i)
    return y * env_exp(len(y), 0.001, 0.055) * 0.55

def synth_hat(duree=0.09, ouvert=False):
    t = t_array(duree)
    n = noise(len(t))
    h = filtre_fft(n, passe_haut(6500, 3))
    chute = 0.09 if ouvert else 0.016
    return h * env_exp(len(t), 0.0005, chute) * (0.30 if ouvert else 0.22)

def synth_cowbell(freq, duree=0.20, gain=0.36):
    """LE son phonk : deux carres desaccordes dans un filtre de bande"""
    t = t_array(duree)
    a = np.sign(np.sin(TAU * freq * t))
    b = np.sign(np.sin(TAU * freq * 1.48 * t))
    y = filtre_fft(a + b, bande(freq * 3.4, 1.1))
    return y * env_exp(len(t), 0.0006, 0.055) * gain

def synth_808(freq, duree=1.2, glisse=None):
    t = t_array(duree)
    f = np.full(len(t), freq)
    if glisse:
        f = freq * np.exp(-t * 3.2) + glisse * (1 - np.exp(-t * 3.2))
    ph = np.cumsum(TAU * f / SR)
    sub = np.sin(ph)
    return np.tanh(sub * 2.4) * env_exp(len(t), 0.004, 0.42) * 0.9

def synth_voix(voyelle, freq, duree=0.32, glisse=0.0, vibrato=0.0):
    """voix de synthese : cordes vocales (dent de scie) + formants"""
    t = t_array(duree)
    f = freq * (1 + glisse * t / max(duree, 1e-6))
    if vibrato:
        f = f * (1 + vibrato * np.sin(TAU * 5.5 * t))
    ph = np.cumsum(TAU * f / SR)
    cordes = 2 * ((ph / TAU) % 1.0) - 1                  # dent de scie = richesse harmonique
    cordes += 0.5 * np.sign(np.sin(ph * 2))              # un peu de rugosite
    FORM = {
        "a":  ((730, 1090, 2440), (80, 90, 120)),
        "e":  ((530, 1840, 2480), (60, 90, 120)),
        "i":  ((270, 2290, 3010), (60, 90, 120)),
        "o":  ((570, 840, 2410),  (80, 80, 120)),
        "u":  ((300, 870, 2240),  (60, 80, 120)),
        "m":  ((250, 1000, 1800), (60, 80, 120)),
        "v":  ((400, 1400, 2200), (70, 90, 120)),
    }
    fm, bm = FORM.get(voyelle, FORM["a"])
    y = resonateurs(cordes, fm, bm)
    return y * env_exp(len(t), 0.012, 0.13) * 0.5

def synth_syllabe(voyelle, freq, duree=0.22, consonne=None, force=1.0):
    """une syllabe chantee : formants + explosion de consonne (sons percussifs)"""
    voix = synth_voix(voyelle, freq, duree, glisse=-0.06)
    if consonne:
        nn = int(SR * 0.030)
        t = np.arange(nn) / SR
        if consonne in "ptkgbd":                      # explosives : bruit tres court
            b = filtre_fft(noise(nn), bande(2200, 1.6)) * np.exp(-t * 260) * 0.9
        elif consonne in "fvsz":                      # fricatives : souffle
            b = filtre_fft(noise(nn), bande(5000 if consonne in "sz" else 3000, 0.8)) * \
                env_exp(nn, 0.004, 0.020) * 0.7
        elif consonne == "m":                          # nasale : bourdonnement grave
            b = np.sin(TAU * 120 * t) * env_exp(nn, 0.003, 0.018) * 0.5
        else:                                          # "r"
            b = filtre_fft(noise(nn), bande(1600, 1.2)) * env_exp(nn, 0.002, 0.025) * 0.6
        taille = min(len(b), len(voix))
        voix[:taille] += b[:taille] * force
    return voix * force

def chant(syllabes, pas_depart, pas_unite, grille, gain=0.55):
    """place des syllabes sur la grille (en doubles-croches), renvoie un tableau"""
    total = len(grille)
    sortie = np.zeros(total)
    for (pas, voyelle, freq, consonne) in syllabes:
        debut = int(SR * (pas_depart + pas * pas_unite))
        s = synth_syllabe(voyelle, freq, consonne=consonne)
        fin = min(debut + len(s), total)
        if fin > debut:
            sortie[debut:fin] += s[:fin - debut] * gain
    return sortie * gain

def synth_impact(duree=1.4):
    t = t_array(duree)
    bas = np.sin(np.cumsum(TAU * (110 * np.exp(-t * 6) + 38) / SR))
    souffle = filtre_fft(noise(len(t)), passe_bas(700, 2))
    return (bas * 0.7 + souffle * 0.5) * env_exp(len(t), 0.002, 0.35) * 0.8

def synth_riser(duree=2.0, haut=False):
    """montee : bruit filtre dont la coupure glisse (recouvrement-additif)"""
    n = int(SR * duree)
    x = noise(n)
    T, hop = 4096, 2048
    y = np.zeros(n + T)
    poids = np.zeros(n + T)
    f = np.fft.rfftfreq(T, 1 / SR)
    win = np.hanning(T)
    for debut in range(0, n, hop):
        seg = np.zeros(T)
        fin = min(T, n - debut)
        seg[:fin] = x[debut:debut + fin]
        fc = 250 * (2 ** (5 * debut / n)) if haut else 250 * (2 ** (4 * debut / n))
        rep = passe_haut(fc, 2) if haut else passe_bas(fc, 2)
        y[debut:debut + T] += np.fft.irfft(np.fft.rfft(seg * win) * rep(f), T)
        poids[debut:debut + T] += win
    y = y[:n] / np.maximum(poids[:n], 1e-6)
    return y * (np.linspace(0, 1, n) ** 2) * 0.35

def reverb(x, duree=1.6, mix=0.28, couleur=4500):
    """reverb par convolution avec une reponse synthetisee (queues lisses)"""
    n = int(SR * duree)
    t = np.arange(n) / SR
    ir = noise(n) * np.exp(-t * 2.6)
    ir = filtre_fft(ir, passe_bas(couleur, 2))
    ir[:int(SR * 0.008)] *= np.linspace(0, 1, int(SR * 0.008))   # pre-delai court
    ir /= np.abs(ir).max() + 1e-9
    N = 1 << int(np.ceil(np.log2(len(x) + n)))
    Y = np.fft.irfft(np.fft.rfft(x, N) * np.fft.rfft(ir, N), N)[:len(x)]
    return (1 - mix) * x + mix * Y / (np.abs(Y).max() + 1e-9) * np.abs(x).max()

# ------------------------------------------------------------
#  le morceau
# ------------------------------------------------------------
BPM = 132
NOIRE = 60 / BPM
DOUBLE = NOIRE / 4                       # une double-croche
MESURE = NOIRE * 4

# grille : positions en doubles-croches dans une mesure de 16 pas
KICKS = [0, 4, 8, 12]                    # quatre temps (funk carioca)
KICKS_POUSSE = [6, 14]                   # les "poussees" bresiliennes
TOMS = [(2, 165), (3, 210), (5, 185), (7, 240), (10, 195), (11, 170), (13, 220), (15, 190)]
CLAPS = [4, 12]
HATS = list(range(16))
ROULADE = [14.0, 14.5, 15.0, 15.25, 15.5, 15.75]      # roulade de fin de mesure

# riff de cowbell (phonk) sur 2 mesures, en La mineur
RIFF = [(0, 440), (1.5, 440), (2, 523.25), (3, 440), (4, 659.25), (6, 587.33), (7, 523.25), (8, 440),
        (9.5, 440), (10, 523.25), (11, 440), (12, 659.25), (13, 587.33), (14, 493.88), (15, 440)]

# basse 808 : fondamentale + glissements
BASSE = {0: (55.0, None), 6: (55.0, 41.2), 8: (65.4, None), 14: (49.0, 55.0)}

# ------------------------------------------------------------------
#  PAROLES (en doubles-croches depuis le debut de la section)
#  « Montagem Ritmada » version Fritax :
#     MON-TA-GEM  RI-TMA-DA  ... VEM!  (x2)  ...  MON-TA-GEM FRI-TAX  UH!
#  chaque syllabe : (pas, voyelle, hauteur, consonne d'attaque)
# ------------------------------------------------------------------
REFRAIN = [
    (0,  "o", 196.00, "m"), (2,  "a", 220.00, "t"), (5,  "e", 196.00, "g"),
    (8,  "i", 246.94, "r"), (10, "a", 233.08, "t"), (13, "a", 220.00, "d"),
    (16, "e", 261.63, "v"), (18, "o", 246.94, None),                    # VEM! OH!
    (24, "o", 196.00, "m"), (26, "a", 220.00, "t"), (29, "e", 196.00, "g"),
    (32, "i", 293.66, "f"), (34, "a", 261.63, "t"), (37, "u", 220.00, None),  # FRI-TAX UH!
]
APPEL = [                                                     # « vem pro ritmo! »
    (0, "e", 233.08, "v"), (3, "o", 220.00, "p"),
    (6, "i", 246.94, "r"), (8, "o", 220.00, "t"), (11, "o", 196.00, "m"),
]
CRI = [(0, "u", 174.61, None), (2, "a", 220.00, None)]        # « uh! ah! »
INTRO_VOIX = [(0, "o", 164.81, "m"), (2, "a", 174.61, "t"), (5, "e", 146.83, "g")]

# plan du morceau : (nom, mesures, intensite 0-3, elements)
PLAN = [
    ("intro",   8, 0, "cowbell_muet"),
    ("drop1",  16, 1, "complet"),
    ("break",   4, 0, "coupure"),
    ("monte",   4, 0, "riser"),
    ("drop2",  16, 2, "complet_plus"),
    ("calme",   8, 1, "demi_temps"),
    ("drop3",  16, 3, "complet_max"),
    ("outro",   4, 0, "cowbell_muet"),
]

def construire():
    total_mesures = sum(p[1] for p in PLAN)
    total = int(SR * (total_mesures * MESURE + 3.0))
    pistes = {"batt": np.zeros(total), "808": np.zeros(total), "cow": np.zeros(total),
              "hat": np.zeros(total), "voix": np.zeros(total), "fx": np.zeros(total)}
    pos = 0
    for nom, mesures, intens, quoi in PLAN:
        for m in range(mesures):
            t0 = int(SR * ((pos + m) * MESURE))
            def poser(piste, ech, gain=1.0, pan=0.0):
                fin = min(t0 + len(ech), total)
                if fin > t0:
                    pistes[piste][t0:fin] += ech[:fin - t0] * gain

            def poser_chant(syllabes, gain=0.55):
                """place des syllabes chantees depuis le debut de la mesure"""
                for pas, voy, f, cons in syllabes:
                    deb = t0 + int(SR * pas * DOUBLE)
                    s = synth_syllabe(voy, f, consonne=cons)
                    fin = min(deb + len(s), total)
                    if fin > deb:
                        pistes["voix"][deb:fin] += s[:fin - deb] * gain

            deuxieme_moitie = (m % 2 == 1)
            if quoi == "cowbell_muet":
                for pas, f in RIFF:                          # riff plus present en intro
                    if pas % 2 == 0 or (m % 4 == 3):
                        poser("cow", synth_cowbell(f, gain=0.42))
                if m % 4 == 3:
                    poser("hat", synth_hat(0.12, ouvert=True), gain=1.2)
                if m % 2 == 1:
                    poser("hat", synth_hat(), gain=0.5)
                if m == 0:
                    poser_chant(INTRO_VOIX, gain=0.40)          # « montagem » tout doux
                if nom == "outro" and m == 2:
                    poser_chant(INTRO_VOIX, gain=0.30)
                continue

            if quoi == "coupure":
                if m == 0:
                    poser("fx", synth_impact())
                for pas in (0, 6, 10):
                    poser("hat", synth_hat(), gain=0.5)
                if m == 0:
                    poser_chant(APPEL, gain=0.62)               # « vem pro ritmo! »
                else:
                    poser("voix", synth_voix("e", 196, 0.45, glisse=-0.25))
                continue

            if quoi == "riser":
                poser("fx", synth_riser(MESURE, haut=(m >= 2)))
                for pas in (0, 4, 8, 12):
                    poser("hat", synth_hat(), gain=0.6)
                if m == 3:
                    poser("voix", synth_voix("a", 165, 0.5, glisse=0.5))
                continue

            # --- passages avec batterie ---
            for pas in KICKS:
                poser("batt", synth_kick())
            if quoi != "demi_temps":
                for pas in KICKS_POUSSE:
                    poser("batt", synth_kick(), gain=0.75)
            for pas, f in TOMS:
                if quoi == "demi_temps" and pas % 4:
                    continue
                g = 0.9 if intens >= 2 else 0.7
                poser("batt", synth_tom(f), gain=g, pan=0.15 if pas % 2 else -0.15)
            for pas in CLAPS:
                g = 0.9 if intens >= 2 else 0.7
                poser("batt", synth_clap(), gain=g)
            for pas in HATS:
                if quoi == "demi_temps" and pas % 2:
                    continue
                poser("hat", synth_hat(), gain=0.9 if pas % 4 == 0 else 0.6,
                      pan=0.22 if pas % 2 else -0.22)
                if pas in (3, 7, 11, 15) and intens >= 2:      # doubles pour la "ritmada"
                    poser("hat", synth_hat(), gain=0.45, pan=0.3)
            if intens >= 1:
                for p in ROULADE:
                    poser("hat", synth_hat(0.08), gain=0.5 + 0.1 * (p % 1),
                          pan=0.35 if int(p) % 2 else -0.35)
            # 808
            for pas, (f, glisse) in BASSE.items():
                poser("808", synth_808(f, glisse=glisse))
            # cowbell / melodie
            for pas, f in RIFF:
                if quoi == "demi_temps" and pas % 2:
                    continue
                poser("cow", synth_cowbell(f, gain=0.34 if intens >= 2 else 0.30),
                      pan=0.2 if pas % 2 else -0.2)
            # voix : le refrain scande (2 mesures) puis les cris
            if m % 8 == 0:
                poser_chant(REFRAIN, gain=0.60)
            elif m % 8 == 4:
                poser_chant(CRI, gain=0.68)
            if intens >= 2 and m % 8 == 7:
                poser("voix", synth_voix("a", 196, 0.5, glisse=0.35, vibrato=0.01))
        pos += mesures
    return pistes, total, total_mesures

# ------------------------------------------------------------
#  mixage
# ------------------------------------------------------------
def melanger(pistes, total):
    batt = pistes["batt"]
    # pompage : le kick ecrase le reste
    env = np.abs(batt)
    env = np.convolve(env, np.ones(int(SR * 0.12)) / int(SR * 0.12), mode="same")
    pompe = 1.0 - 0.55 * np.clip(env / (env.max() + 1e-9), 0, 1)

    gauche = np.zeros(total); droite = np.zeros(total)
    for nom, ech, centre, larg in [("batt", batt, 0.0, 0.35), ("808", pistes["808"], 0.0, 0.0),
                                   ("cow", pistes["cow"], 0.0, 0.75), ("hat", pistes["hat"], 0.3, 0.85),
                                   ("voix", pistes["voix"], 0.0, 0.5), ("fx", pistes["fx"], 0.0, 0.9)]:
        if nom in ("cow", "voix", "fx"):
            ech = ech * pompe
        if nom == "808":
            ech = ech * pompe
        gauche += ech * (1 - centre) * np.sqrt((1 - larg) / 2 + larg / 2)
        droite += ech * (1 + centre) * np.sqrt((1 - larg) / 2 + larg / 2)
    # largeur par delai sur les aigus
    aig = pistes["hat"] + pistes["cow"] * 0.4
    d = int(SR * 0.006)
    gauche = gauche + np.concatenate([np.zeros(d), -aig[:-d]]) * 0.10
    droite = droite + np.concatenate([np.zeros(d), aig[:-d]]) * 0.10

    st = np.stack([gauche, droite])
    st = np.stack([reverb(st[0], mix=0.20), reverb(st[1], mix=0.20)])
    st = np.tanh(st * 1.15) * 0.92                       # limiteur doux
    st /= (np.abs(st).max() + 1e-9) * 1.06               # tete a -0.5 dB
    return st

def ecrire_wav(st, chemin):
    data = (np.clip(st.T, -1, 1) * 32767).astype("<i2").tobytes()
    with wave.open(chemin, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(data)

if __name__ == "__main__":
    print("fabrication...")
    pistes, total, mesures = construire()
    print(f"  {mesures} mesures, {total/SR:.1f} s")
    st = melanger(pistes, total)
    ecrire_wav(st, "/tmp/phonk_fritax.wav")
    print("  WAV :", os.path.getsize("/tmp/phonk_fritax.wav") // 1024, "Ko")
    try:
        import lameenc
        enc = lameenc.Encoder()
        enc.set_bit_rate(192); enc.set_in_sample_rate(SR)
        enc.set_channels(2); enc.set_quality(2)
        mp3 = enc.encode((np.clip(st.T, -1, 1) * 32767).astype("<i2").tobytes())
        mp3 += enc.flush()
        open("/tmp/phonk_fritax.mp3", "wb").write(bytes(mp3))
        print("  MP3 :", os.path.getsize("/tmp/phonk_fritax.mp3") // 1024, "Ko")
    except Exception as e:
        print("  (encodeur MP3 :", e, ")")
