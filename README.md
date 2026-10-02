# MONTAGEM FRITAX (Ritmada)

**Phonk brésilien · 132 BPM · 2 min 21 · fa mineur**

Fabriqué **entièrement de zéro** : aucun échantillon, aucun fichier externe.
Chaque son est du signal calculé en Python (numpy) :

| Élément | Synthèse |
|---|---|
| Grosse caisse | sinus dont la hauteur tombe de 150 à 45 Hz + clic filtré, saturé |
| Tamborzão (toms) | sinus à hauteur tombante + peau bruitée filtrée |
| Clap | quatre rebonds de bruit dans un filtre de bande |
| Charleys | bruit passé en haut, décroissance très courte, roulements en fin de mesure |
| 808 | sinus saturé, longue queue, glissements de hauteur, écrasé par le kick (pompage) |
| Cowbell | deux carrés désaccordés (f et f × 1,48) dans un filtre de bande |
| Voix | dent de scie (cordes vocales) + banc de formants (a/e/i/o/u) + consonnes bruitées |
| Reverb | convolution avec une réponse fabriquée |
| Finition | pompage, élargissement stéréo, limiteur doux |

## Structure

```
0:00  Intro      riff de cowbell + « montagem » chuchoté
0:15  Drop 1     batterie complète + 808 + refrain scandé
0:43  Coupure    la batterie s'arrête : « vem pro ritmo! »
0:50  Montée     souffle montant
0:57  Drop 2     plus lourd, 808 plus grave
1:25  Calme      demi-temps
1:40  Drop 3     le plus violent + cri final
2:00  Outro      retour au riff
```

## Paroles

```
Montagem ritmada, vem!  (oh!)
Montagem Fritax, uh!
— Vem! Pro ritmo! Vem!
```

## Télécharger

Le morceau est dans les **Releases** de ce dépôt (dossier `Réleases`, en haut à droite).

Le code de fabrication (`phonk_fritax.py`) est inclus : tout est reproductible,
le morceau se régénère à l'identique en 20 secondes.
