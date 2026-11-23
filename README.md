# TP5 - Design patterns (Factory Method, Abstract Factory, Singleton)

Lancer le jeu : `py game_tp5.py`   (Python 3 + `pip install pygame`)
Tests (logique pure) : `py -m pip install pytest` puis `py -m pytest test_tp5.py`

Le TP4 (`tp4/`, `game_oop.py`, `homework_monsters.py`, `game_tp4.py`) n'est PAS modifie.
Tout le TP5 est dans `tp5/` (le plateau, le rendu et l'app du TP4 sont simplement etendus).

## Workshop (cahier de TP, pages 75-81)
| Fichier | Contenu |
|---|---|
| `workshop/part1_factory_method.py` | sans pattern -> Simple Factory -> Factory Method (SCT / SCR) + application stock (Manager / Seller / Visitor) |
| `workshop/part2_abstract_factory.py` | formes 2D / 3D : ShapeFactory, ShapeFactory2D, ShapeFactory3D |
| `workshop/part3_singleton.py` | Singleton, fichier unique, base de donnees unique, acces simultanes limites |
| `workshop/part4_builder.py` | Story (Facebook/Instagram/Youtube), Sandwich nomme, Voiture a options |

Chaque fichier se lance seul : `py workshop/part1_factory_method.py`

## Homework W5 DP (3 taches choisies, page 133)
| Tache | Pattern | Fichier |
|---|---|---|
| Monstres differents a la demande (Zombie, Dragon, Robot) | **Factory Method** | `tp5/monsters.py` |
| Mondes differents par niveau (Space / Fantasy : fond + monstres + recompenses) | **Abstract Factory** | `tp5/worlds.py` |
| Un seul joueur principal (nombre de joueurs configurable) | **Singleton** | `tp5/singleton.py` |

Integration au jeu (`tp5/board.py`, `tp5/render.py`, `tp5/app.py`) :
- `CreatorEnemyFactory` remplace `EnemyFactory` avec la meme interface -> le reste du jeu ne change pas.
- Chaque niveau utilise un monde (Space = niveaux impairs, Fantasy = niveaux pairs) : son fond, ses monstres, ses recompenses (Space : pieces x1.5 + power-ups de vitesse ; Fantasy : power-ups de survie).
- `PlayerManager` (Singleton) garde l'unique joueur ; `set_max_players(2)` suffit pour un mode duo.

Ajouter un monstre : une classe Monster + un `MonsterCreator` + `factory.register(...)`.
Ajouter un monde : une `WorldFactory` + ses produits, puis l'ajouter a `WorldRotation`.
