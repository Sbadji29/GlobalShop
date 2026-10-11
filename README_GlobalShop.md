# GlobalShop — Démonstration et exécution

## 1. Présentation

GlobalShop est un prototype de commerce électronique reposant sur une architecture distribuée avec FastAPI, PostgreSQL et Docker Compose. Le projet vise à illustrer la distribution des données, la gestion du stock en concurrence et la réplication PostgreSQL.

## 2. Prérequis

- Docker Desktop installé et démarré.
- Python installé.
- Les dépendances Python du routeur installées.
- Le fichier `docker-compose.yml` et les fichiers de configuration nécessaires présents à la racine du projet.

## 3. Démarrer la base de données

Depuis la racine du projet, démarrer les services définis dans Docker Compose :

```powershell
docker compose up -d
```

Vérifier l'état des conteneurs :

```powershell
docker ps
```

> Si certains services sont déjà démarrés, cette commande ne nécessite pas de les recréer.

## 4. Démarrer l'API FastAPI

Ouvrir un terminal PowerShell dans VS Code :

```powershell
cd router
py -m uvicorn app.main:app --reload
```

L'API est normalement accessible à l'adresse `http://127.0.0.1:8000`. La documentation interactive Swagger est disponible à `http://127.0.0.1:8000/docs`.

## 5. Exécuter le script de démonstration

Dans un deuxième terminal, revenir à la racine du projet :

```powershell
py .\scripts\demo.py
```

Le script vérifie notamment la disponibilité de l'API et la consultation de produits. Les résultats affichés dépendent de l'état courant de l'environnement.

## 6. Exécuter le benchmark de concurrence

Depuis la racine du projet :

```powershell
py .\scripts\benchmark.py
```

Le benchmark envoie des demandes d'achat concurrentes et affiche les résultats observés, notamment les achats acceptés, les refus pour stock insuffisant, la durée et le débit.

**Important :** ce test modifie le stock. Avant de le relancer, vérifier le produit utilisé et sa quantité disponible. Ne pas supposer que le stock a été réinitialisé automatiquement.

## 7. Vérifier la réplication PostgreSQL

La réplication peut être contrôlée depuis PostgreSQL avec les vues système adaptées :
- `pg_stat_replication` sur le nœud principal ;
- `pg_stat_wal_receiver` sur le nœud secondaire.

Un état `streaming` indique que le flux de réplication est actif au moment de la vérification. La configuration actuelle doit être évaluée séparément pour déterminer si le basculement après panne est manuel ou automatique.

## 8. Arrêter les services

Pour arrêter les services lancés avec Docker Compose :

```powershell
docker compose down
```

Cette commande arrête et supprime les conteneurs du projet, mais conserve normalement les volumes nommés. N'ajouter pas `-v` si vous souhaitez préserver les données.

## 9. Points à vérifier avant la démonstration

- Docker Desktop est démarré et les conteneurs attendus sont actifs.
- L'API démarre correctement.
- `scripts/demo.py` s'exécute depuis la racine du projet.
- Le benchmark est lancé seulement après vérification du stock.
- Les fichiers de secrets (par exemple `.env` contenant de vrais mots de passe) ne sont pas partagés publiquement.
- Les commandes et chemins ci-dessus correspondent à la version réellement remise.

## 10. Dépôt du code source

Dépôt GitHub : https://github.com/Sbadji29/GlobalShop
