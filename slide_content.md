# Full Video to Clips v3 — Présentation du Projet

---

## Slide 1 — Titre
**Full Video to Clips v3**
*صانع مقاطع الفيديو v3*

Transformez n'importe quelle vidéo en 10 clips TikTok-ready en quelques secondes.

Dépôt GitHub : `hakomjaeop-lab/full-video-to-clips-v3`
Déploiement : Render (Docker)

---

## Slide 2 — Le problème résolu : découper une vidéo manuellement prend trop de temps
Créer du contenu court-format pour TikTok, Instagram Reels ou YouTube Shorts à partir d'une longue vidéo est une tâche répétitive et chronophage. Les créateurs de contenu doivent :
- Importer la vidéo dans un éditeur
- Découper manuellement chaque segment
- Recadrer au format vertical 9:16
- Exporter chaque clip individuellement

**Full Video to Clips v3** automatise entièrement ce processus en une seule opération via une interface web simple.

---

## Slide 3 — Ce que fait l'application en une phrase
L'application reçoit une vidéo, la divise automatiquement en **10 clips égaux** au format **TikTok 9:16 (720×1280)**, puis supprime la vidéo originale pour économiser l'espace disque.

| Fonctionnalité | Détail |
|---|---|
| Nombre de clips | 10 clips égaux |
| Format de sortie | MP4, 720×1280 (9:16) |
| Suppression auto | Vidéo originale supprimée après traitement |
| Interface | Web (navigateur) |

---

## Slide 4 — Architecture technique : Flask + FFmpeg + Docker
Le projet repose sur une stack légère et efficace :

- **Flask** : framework web Python pour gérer les routes HTTP et le rendu HTML
- **FFmpeg / ffprobe** : moteur de traitement vidéo (découpage, recadrage, encodage)
- **Gunicorn** : serveur WSGI de production
- **Docker** : conteneurisation pour un déploiement reproductible
- **Render** : plateforme cloud de déploiement via `render.yaml`

---

## Slide 5 — Flux de traitement vidéo : 5 étapes automatisées
```
[Upload] → [Lecture durée] → [Calcul segments] → [FFmpeg x10] → [Suppression original]
```

1. L'utilisateur uploade un fichier vidéo via le formulaire web
2. `ffprobe` mesure la durée totale de la vidéo (en secondes)
3. La durée est divisée par 10 pour calculer la longueur de chaque clip
4. `ffmpeg` génère 10 clips avec recadrage `crop=ih*(9/16):ih` et encodage H.264
5. La vidéo originale est supprimée automatiquement après traitement

---

## Slide 6 — La commande FFmpeg au cœur du moteur de découpe
La commande FFmpeg utilisée garantit qualité et rapidité :

```bash
ffmpeg -y -ss {start} -t {duration}
  -i {input}
  -vf "crop=ih*(9/16):ih,scale=720:1280"
  -c:v libx264 -crf 28 -preset ultrafast
  -c:a aac -b:a 64k
  {output_clip.mp4}
```

- `-preset ultrafast` : encodage rapide pour économiser les ressources Render
- `crf 28` : bon compromis qualité/taille de fichier
- `crop=ih*(9/16):ih` : recadrage centré au ratio 9:16

---

## Slide 7 — Interface utilisateur : simple, en arabe, orientée RTL
L'interface est entièrement en **arabe** avec support RTL natif :

- Formulaire d'upload avec sélecteur de fichier vidéo
- Bouton de soumission avec indicateur de chargement (`showLoading()`)
- Affichage de la liste des clips générés avec liens de téléchargement
- Bouton **"حذف الكل"** (Supprimer tout) pour nettoyer les clips via l'API `/delete_all`

L'interface est minimaliste et fonctionnelle, pensée pour une utilisation rapide sans configuration.

---

## Slide 8 — Déploiement sur Render : configuration Docker en 3 lignes
Le fichier `render.yaml` configure le déploiement automatique :

```yaml
services:
  - type: web
    name: full-video-to-clips-v3
    runtime: docker
    envVars:
      - key: PORT
        value: 10000
```

- Le `Dockerfile` installe Python 3.11, FFmpeg, et les dépendances Python
- Gunicorn écoute sur le port `10000` (injecté par Render via `$PORT`)
- Le déploiement est entièrement reproductible grâce à la conteneurisation

---

## Slide 9 — Évolution du projet : 4 commits, 4 améliorations majeures
| Commit | Description |
|---|---|
| `823cf41` | Création initiale : suppression auto + bouton de suppression manuelle |
| `444dcef` | Ajout du format TikTok 9:16 et découpage en 10 clips égaux |
| `888f976` | Compatibilité Render + chemins absolus pour la stabilité |
| `009fb94` | Ajout du Dockerfile + stabilisation du traitement FFmpeg |

Le projet a évolué rapidement vers une solution robuste et déployable en production.

---

## Slide 10 — Points forts et cas d'usage
**Points forts :**
- Aucune configuration requise pour l'utilisateur final
- Traitement entièrement côté serveur (pas de dépendance JavaScript lourde)
- Sécurité : utilisation de `secure_filename` et liste de commandes (pas d'injection shell)
- Gestion des erreurs avec logging détaillé

**Cas d'usage :**
- Créateurs de contenu TikTok / Reels / Shorts
- Agences de marketing digital
- Automatisation de la production de contenu vidéo court-format

---

## Slide 11 — Améliorations possibles pour les prochaines versions
| Amélioration | Impact |
|---|---|
| Choix du nombre de clips (pas seulement 10) | Flexibilité accrue |
| Sélection du point de recadrage (gauche/centre/droite) | Meilleure qualité visuelle |
| Barre de progression en temps réel (WebSocket) | Meilleure UX |
| Stockage cloud (S3 / Cloudinary) | Persistance des clips |
| Authentification utilisateur | Multi-utilisateurs |

---

## Slide 12 — Conclusion : un outil prêt pour la production
**Full Video to Clips v3** est une application web fonctionnelle, déployée sur Render, qui automatise entièrement la création de clips TikTok-ready à partir de n'importe quelle vidéo.

- **Stack** : Python · Flask · FFmpeg · Docker · Render
- **Dépôt** : `hakomjaeop-lab/full-video-to-clips-v3`
- **Statut** : Déployé et opérationnel

> "رفع الفيديو → 10 مقاطع TikTok جاهزة → حذف الأصل تلقائياً"
> (Uploadez → 10 clips TikTok prêts → Original supprimé automatiquement)
