# GuidedAgent.py

import numpy as np
import random
import pygame
import os
import pickle
import cv2  # Pour la détection du checkpoint

class GuidedAgent:
    """
    Agent guidé pour Super Mario Python
    
    Cet agent utilise des informations structurées sur l'environnement
    pour prendre des décisions plus informées et peut apprendre de ses erreurs
    grâce à l'apprentissage par renforcement.
    """
    
    def __init__(self):
        # Paramètres de l'agent
        self.exploration_rate = 0.3  # Taux d'exploration initial
        self.min_exploration_rate = 0.05  # Taux minimal d'exploration
        self.exploration_decay = 0.995  # Taux de décroissance de l'exploration
        
        # Initialiser les poids pour différentes caractéristiques
        self.weights = {
            "distance_to_enemy": -2.0,  # Pénalité pour être proche d'un ennemi
            "distance_to_coin": 1.0,    # Récompense pour être proche d'une pièce
            "forward_progress": 4.0,    # Préférence pour avancer (augmenté)
            "jump_over_gap": 2.5,       # Récompense pour sauter par-dessus un trou
            "jump_over_enemy": 3.0,     # Récompense pour sauter par-dessus un ennemi
        }
        
        # Historique des actions et états
        self.last_action = None
        self.last_position = (0, 0)
        self.position_history = []  # Garder trace des dernières positions
        
        # Variables supplémentaires pour améliorer la prise de décision
        self.jump_cooldown = 0
        self.consecutive_same_actions = 0
        self.stuck_counter = 0
        self.right_bias_counter = 0  # Pour favoriser le mouvement vers la droite
        
        # Variables pour alterner les actions en cas de blocage
        self.force_alternate = False
        self.alternating_actions = ['right', 'jump', 'right', 'right']
        self.alternating_index = 0
        
        # Compteur pour les menus
        self.menu_action_counter = 0
        
        # Mémoire d'apprentissage par renforcement
        self.learning_rate = 0.1  # Taux d'apprentissage
        self.discount_factor = 0.9  # Facteur de réduction pour les récompenses futures
        self.q_table = {}  # Table Q pour stocker les valeurs d'action-état
        self.experience_buffer = []  # Tampon d'expérience pour l'apprentissage
        self.max_buffer_size = 1000  # Taille maximale du tampon
        
        # Charger la table Q si elle existe
        self.model_path = "ai_memory.pkl"
        self.load_memory()
        
        # Chargement de l'image de checkpoint pour la détection
        checkpoint_path = os.path.join("img", "checkpoint.jpg")
        if os.path.exists(checkpoint_path):
            self.checkpoint_image = cv2.imread(checkpoint_path)
            if self.checkpoint_image is not None:
                self.checkpoint_image = cv2.cvtColor(self.checkpoint_image, cv2.COLOR_BGR2RGB)
                print("Image de checkpoint chargée avec succès")
            else:
                print("Erreur lors du chargement de l'image de checkpoint")
                self.checkpoint_image = None
        else:
            print(f"Image de checkpoint non trouvée à {checkpoint_path}")
            self.checkpoint_image = None
            
        # Compteur de parties et statistiques
        self.game_count = 0
        self.wins = 0
        self.losses = 0
        self.max_score = 0
        self.total_distance = 0
        self.last_episode_state = None
        self.last_episode_action = None
        
    def choose_action(self, state):
        """
        Sélectionne une action en fonction de l'état actuel
        """
        try:
            # Actions possibles
            actions = ['left', 'right', 'jump', 'idle']
            
            # Vérifier l'état du jeu
            game_state = state.get("game_state", "playing")
            
            # Logique spécifique pour le menu
            if game_state == "menu":
                return self.handle_menu_action()
                
            # Logique pour le game over
            if game_state == "game_over":
                # Après game over, préférer l'action jump pour redémarrer
                return 'jump'
            
            # À partir d'ici, on est dans le jeu normal
            
            # Si on est en mode alternance forcée (pour débloquer Mario)
            if self.force_alternate:
                action = self.alternating_actions[self.alternating_index]
                self.alternating_index = (self.alternating_index + 1) % len(self.alternating_actions)
                
                # Sortir du mode alternance après un cycle complet
                if self.alternating_index == 0:
                    self.force_alternate = False
                
                print(f"Action forcée (alternance): {action}")
                return action
            
            # Explorer avec une certaine probabilité (epsilon-greedy)
            if random.random() < self.exploration_rate:
                # Augmenter la probabilité de sauter pendant l'exploration aléatoire
                jump_probability = 0.5  # 50% de chances de sauter
                if random.random() < jump_probability:
                    action = 'jump'
                else:
                    # Pour les autres cas, favoriser le mouvement vers la droite
                    action = random.choice(['right', 'right', 'right', 'left'])
                print(f"Action aléatoire: {action} (avec priorité au saut)")
                return action
            
            # Gérer les événements pygame
            pygame.event.pump()
            
            # Récupérer les informations d'état
            mario_pos = state["mario_pos"]
            mario_vel = state["mario_vel"]
            nearby_objects = state["nearby_objects"]
            
            # Afficher des informations de débogage (réduites)
            print(f"Position: {mario_pos}, Vitesse: {mario_vel}, Objets: {len(nearby_objects)}")
            
            # Calculer les scores pour chaque action
            action_scores = {
                'left': 0,
                'right': self.weights["forward_progress"],  # Préférer aller à droite
                'jump': 2.0,  # Augmenter la valeur de base du saut
                'idle': 0
            }
            
            # Réduire le cooldown du saut, mais moins qu'avant pour permettre plus de sauts
            if self.jump_cooldown > 0:
                self.jump_cooldown -= 1
                action_scores['jump'] -= 1.0  # Pénalité réduite pour sauter fréquemment
            
            # Détecter les ennemis à l'avant
            enemies_ahead = False
            enemies_close = False
            
            # Analyser les objets proches
            ground_tiles_ahead = []
            ground_tiles_below = []
            coins_above = False
            
            for obj in nearby_objects:
                rel_x, rel_y, obj_type = obj
                
                # Détecter les ennemis
                if "Goomba" in obj_type or "Koopa" in obj_type:
                    if 0 < rel_x < 80 and abs(rel_y) < 50:  # Ennemi à droite proche
                        enemies_ahead = True
                        if rel_x < 40:  # Très proche
                            enemies_close = True
                            action_scores['jump'] += self.weights["jump_over_enemy"] * 1.5
                            print("Ennemi très proche, je saute!")
                        else:
                            action_scores['jump'] += self.weights["jump_over_enemy"]
                            print("Ennemi détecté devant, je saute!")
                
                # Détecter les objets à collecter
                if any(item in obj_type for item in ["Coin", "CoinBox", "RandomBox", "Mushroom"]):
                    # Item au-dessus de Mario
                    if abs(rel_x) < 16 and -150 < rel_y < -20:
                        coins_above = True
                        action_scores['jump'] += self.weights["distance_to_coin"] * 1.5  # Bonus augmenté
                        print("Bonus au-dessus, je saute!")
                    # Item devant Mario
                    elif 0 < rel_x < 100:
                        action_scores['right'] += self.weights["distance_to_coin"] * 0.5
                        # Aussi, essayer de sauter de temps en temps pour les objets devant
                        if random.random() < 0.3:  # 30% de chance de sauter pour explorer
                            action_scores['jump'] += 1.0
                
                # Identifier les tuiles du sol
                if "Tile" in obj_type:
                    # Tuiles directement sous Mario
                    if abs(rel_x) < 16 and 0 < rel_y < 32:
                        ground_tiles_below.append(obj)
                    # Tuiles devant Mario (pour détecter les trous)
                    elif 16 < rel_x < 96 and -10 < rel_y < 40:
                        ground_tiles_ahead.append(obj)
            
            # Vérifier s'il y a un sol devant (sinon, c'est un trou)
            if len(ground_tiles_ahead) == 0 and mario_vel[0] >= 0:
                # Pas de sol détecté devant = probablement un trou
                action_scores['jump'] += self.weights["jump_over_gap"] * 2
                print("Trou détecté, je saute!")
            
            # Si on est en l'air, continuer à avancer
            if len(ground_tiles_below) == 0 and mario_vel[1] != 0:
                action_scores['right'] += 1.0  # Continuer sur l'élan
                # Moins pénaliser le saut en l'air pour permettre des sauts multiples
                action_scores['jump'] -= 1.0  # Pénalité réduite pour sauter en l'air
            
            # Gérer le cas où Mario est bloqué
            current_pos = tuple(mario_pos)
            self.position_history.append(current_pos)
            if len(self.position_history) > 20:
                self.position_history.pop(0)
            
            # Calculer le mouvement récent
            recent_movement = 0
            if len(self.position_history) > 10:
                recent_movement = abs(self.position_history[-1][0] - self.position_history[0][0])
            
            # Si Mario n'a pas bougé significativement récemment
            if recent_movement < 10:
                self.stuck_counter += 1
                print(f"Peu de mouvement récent: {recent_movement}, compteur bloqué: {self.stuck_counter}")
                
                if self.stuck_counter > 10:  # Réagir plus rapidement au blocage
                    print("Je semble bloqué, je vais essayer de sauter!")
                    # Favoriser le saut pour se débloquer
                    self.force_alternate = True
                    # Modifier la séquence pour inclure plus de sauts
                    self.alternating_actions = ['jump', 'right', 'jump', 'right', 'jump']
                    self.alternating_index = 0
                    self.stuck_counter = 0
                    return 'jump'  # Commencer par un saut immédiatement
            else:
                self.stuck_counter = max(0, self.stuck_counter - 1)
            
            # Biais pour aller à droite après avoir sauté
            if self.last_action == 'jump':
                action_scores['right'] += 1.5  # Réduire pour équilibrer avec plus de sauts
                self.right_bias_counter = 3
            
            if self.right_bias_counter > 0:
                action_scores['right'] += 1.0
                self.right_bias_counter -= 1
            
            # Réduire le cooldown de saut pour permettre des sauts plus fréquents
            if self.last_action == 'jump' and self.jump_cooldown <= 0:
                self.jump_cooldown = 5  # Réduit de 8 à 5 frames
            
            # Sauter périodiquement pendant les déplacements
            if self.last_action == 'right':
                self.consecutive_same_actions += 1
                # Augmenter la fréquence des sauts "exploratoires"
                if self.consecutive_same_actions > 20:  # Réduit de 40 à 20
                    action_scores['jump'] += 3.0  # Augmenté pour favoriser le saut
                    print("Avancé sans sauter récemment, je tente un saut exploratoire")
            else:
                self.consecutive_same_actions = 0
            
            # Ajouter un facteur aléatoire pour les sauts exploratoires
            if random.random() < 0.15 and mario_vel[1] == 0:  # 15% de chance de faire un saut aléatoire si au sol
                action_scores['jump'] += 2.5
                print("Saut aléatoire exploratoire!")
            
            # Choisir l'action avec le score le plus élevé
            best_action = max(action_scores, key=action_scores.get)
            self.last_action = best_action
            
            # Diminuer graduellement le taux d'exploration, mais plus lentement
            self.exploration_rate = max(self.min_exploration_rate, 
                                    self.exploration_rate * 0.998)  # Réduit le taux de décroissance
            
            print(f"Action: {best_action}, Scores: {action_scores}")
            return best_action
            
        except Exception as e:
            print(f"ERREUR dans choose_action: {e}")
            # En cas d'erreur, essayer de sauter plutôt que simplement aller à droite
            return random.choice(['right', 'jump'])  # 50% de chance de sauter en cas d'erreur
    
    def handle_menu_action(self):
        """
        Gère les actions spécifiques au menu
        Utilise une séquence spécifique pour naviguer efficacement dans le menu
        """
        # Séquence d'actions pour naviguer dans le menu
        menu_sequence = ['right', 'jump', 'right', 'right', 'jump']
        
        # Incrémenter le compteur et obtenir l'action correspondante
        action = menu_sequence[self.menu_action_counter % len(menu_sequence)]
        self.menu_action_counter += 1
        
        print(f"Action de menu: {action}, compteur: {self.menu_action_counter}")
        return action
    
    def distance(self, pos1, pos2):
        """Calcule la distance euclidienne entre deux points"""
        return ((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2) ** 0.5
    
    def train(self, state, action, reward, next_state, done):
        """
        Entraîne l'agent avec une nouvelle expérience
        """
        # Mettre à jour la table Q
        self.update(state, action, reward, next_state, done)
        
        # Si l'épisode est terminé, mettre à jour les statistiques
        if done:
            self.game_count += 1
            
            # Vérifier si c'est une victoire (détection du checkpoint) ou une défaite
            if reward > 50:  # Récompense élevée indique probablement un checkpoint
                self.wins += 1
                print(f"Victoire! Ratio de victoires: {self.wins}/{self.game_count} ({(self.wins/self.game_count)*100:.1f}%)")
            else:
                self.losses += 1
                print(f"Défaite. Ratio de victoires: {self.wins}/{self.game_count} ({(self.wins/self.game_count)*100:.1f}%)")
            
            # Mémoriser les erreurs et ajuster les poids en conséquence
            if reward < 0 and self.last_episode_state is not None and self.last_episode_action is not None:
                # Si la récompense est négative, ajuster les poids pour éviter les mêmes erreurs
                print("Apprentissage à partir d'une erreur...")
                if "jump_over_gap" in self.weights and self.last_episode_action == "jump":
                    self.weights["jump_over_gap"] *= 1.05  # Augmenter légèrement
                elif "forward_progress" in self.weights and self.last_episode_action == "right":
                    self.weights["forward_progress"] *= 0.95  # Diminuer légèrement
                
                print(f"Poids ajustés: {self.weights}")
            
            # Sauvegarder l'état et l'action de cet épisode
            self.last_episode_state = state
            self.last_episode_action = action
        
        # Faire également un apprentissage par experience replay
        if len(self.experience_buffer) > 10:
            # Échantillonner aléatoirement des expériences du tampon
            batch_size = min(10, len(self.experience_buffer))
            batch = random.sample(self.experience_buffer, batch_size)
            
            # Mettre à jour la table Q pour chaque expérience du lot
            for exp_state, exp_action, exp_reward, exp_next_state, exp_done in batch:
                self.update(exp_state, exp_action, exp_reward, exp_next_state, exp_done)
    
    def update(self, state, action, reward, next_state, done):
        """
        Met à jour la mémoire de l'agent en fonction de l'expérience vécue
        """
        # Liste des actions disponibles
        actions = ['left', 'right', 'jump', 'idle']
        
        # Ajouter l'expérience au tampon
        self.experience_buffer.append((state, action, reward, next_state, done))
        if len(self.experience_buffer) > self.max_buffer_size:
            self.experience_buffer.pop(0)
        
        # Mise à jour de la table Q par apprentissage par renforcement
        try:
            # Créer des clés simples pour les états
            if "mario_pos" in state:
                state_key = f"{int(state['mario_pos'][0])}-{int(state['mario_pos'][1])}"
                
                if "mario_pos" in next_state:
                    next_state_key = f"{int(next_state['mario_pos'][0])}-{int(next_state['mario_pos'][1])}"
                else:
                    next_state_key = "terminal"
                
                # Initialiser les valeurs Q si nécessaire
                if state_key not in self.q_table:
                    self.q_table[state_key] = {a: 0.0 for a in actions}
                if next_state_key != "terminal" and next_state_key not in self.q_table:
                    self.q_table[next_state_key] = {a: 0.0 for a in actions}
                
                # Calculer la valeur Q actuelle
                current_q = self.q_table[state_key].get(action, 0.0)
                
                # Calculer la valeur Q maximale pour l'état suivant
                if next_state_key != "terminal":
                    max_future_q = max(self.q_table[next_state_key].values())
                else:
                    max_future_q = 0.0
                
                # Mise à jour de la valeur Q en utilisant la formule de Bellman
                new_q = (1 - self.learning_rate) * current_q + self.learning_rate * (reward + self.discount_factor * max_future_q)
                self.q_table[state_key][action] = new_q
                
                print(f"Mise à jour Q: État {state_key}, Action {action}, Récompense {reward}, Nouvelle valeur Q {new_q:.2f}")
        except Exception as e:
            print(f"Erreur lors de la mise à jour de la table Q: {e}")
        
        # Sauvegarder la mémoire périodiquement
        if done:
            self.save_memory()
            print("Sauvegarde de la mémoire d'IA après fin d'épisode")
    
    def load_memory(self):
        """
        Charge la mémoire (table Q) depuis un fichier
        """
        if os.path.exists(self.model_path):
            with open(self.model_path, "rb") as f:
                self.q_table = pickle.load(f)
            print("Mémoire chargée avec succès")
        else:
            print("Aucune mémoire trouvée, utilisation des valeurs par défaut")
            self.q_table = {}
    
    def save_memory(self):
        """
        Sauvegarde la mémoire (table Q) dans un fichier
        """
        with open(self.model_path, "wb") as f:
            pickle.dump(self.q_table, f)
        print("Mémoire sauvegardée avec succès")
    
    def detect_checkpoint(self, screen):
        """
        Détecte la présence d'un checkpoint en comparant l'écran actuel avec l'image du checkpoint
        """
        if self.checkpoint_image is not None:
            # Redimensionner l'image du checkpoint pour qu'elle corresponde à la taille de l'écran
            checkpoint_resized = cv2.resize(self.checkpoint_image, (screen.get_width(), screen.get_height()))
            
            # Convertir l'écran en tableau numpy
            screen_array = pygame.surfarray.array3d(screen)
            
            # Calculer la différence entre l'écran et l'image du checkpoint
            diff = cv2.absdiff(checkpoint_resized, screen_array)
            
            # Convertir en niveaux de gris
            diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            
            # Seuiller l'image pour obtenir un masque binaire
            _, mask = cv2.threshold(diff_gray, 25, 255, cv2.THRESH_BINARY)
            
            # Calculer le pourcentage de pixels différents
            non_zero_count = cv2.countNonZero(mask)
            total_count = mask.size
            difference_ratio = non_zero_count / total_count
            
            print(f"Ratio de différence: {difference_ratio}")
            
            # Si le ratio de différence est faible, on considère que le checkpoint est détecté
            if difference_ratio < 0.05:
                print("Checkpoint détecté")
                return True
        
        return False