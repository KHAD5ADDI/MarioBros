"""
Script correctif pour résoudre les problèmes du jeu Super Mario Python:
1. Mario invisible 
2. Checkpoint invisible
3. Passage automatique au niveau suivant

Pour utiliser ce script:
- Exécutez-le depuis le dossier racine du jeu
- Il créera des fichiers de sauvegarde
- Il corrigera automatiquement les problèmes
"""

import os
import shutil
import pygame

def backup_file(filepath):
    """Crée une sauvegarde du fichier s'il n'en existe pas déjà une"""
    backup_path = filepath + ".backup"
    if not os.path.exists(backup_path):
        print(f"Création d'une sauvegarde de {filepath}...")
        shutil.copy2(filepath, backup_path)
    else:
        print(f"Une sauvegarde de {filepath} existe déjà")

def fix_mario_class():
    """Corrige la classe Mario pour le rendre visible"""
    mario_path = "entities/Mario.py"
    backup_file(mario_path)
    
    with open(mario_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Réparer le problème de syntaxe avec la méthode render
    if "self.invincibilityFrames = 20    def render" in content:
        content = content.replace(
            "self.invincibilityFrames = 20    def render", 
            "self.invincibilityFrames = 20\n\n    def render"
        )
        print("✓ Correction de la syntaxe dans Mario.py")
    
    # Remplacer la méthode render par une version qui force l'affichage de Mario
    # Nous devons rechercher la méthode render et la remplacer en entier
    render_start = content.find("def render(self, camera):")
    if render_start > 0:
        # Trouver la fin de la méthode (chercher soit une autre définition de méthode, soit la fin de la classe)
        next_def = content.find("def ", render_start + 20)
        if next_def == -1:
            # Pas d'autre méthode, trouver la fin du fichier
            render_end = len(content)
        else:
            render_end = content.rfind("\n", 0, next_def)
        
        # Extraire la méthode render complète
        old_render = content[render_start:render_end]
        
        # Créer une nouvelle méthode render
        new_render = """def render(self, camera):
        \"\"\"
        Affiche Mario à l'écran à la bonne position et orientation.
        Force l'affichage de Mario avec un rectangle coloré pour assurer la visibilité.
        \"\"\"
        try:
            # Position pour l'affichage
            render_x = self.rect.x - camera.x
            render_y = self.rect.y
            
            # FORCER LA VISIBILITÉ: Dessiner un grand rectangle coloré
            pygame.draw.rect(self.screen, (255, 0, 0), (render_x, render_y, self.rect.width, self.rect.height), 0)  # Rectangle rouge plein
            pygame.draw.rect(self.screen, (255, 255, 0), (render_x, render_y, self.rect.width, self.rect.height), 3)  # Bordure jaune épaisse
            
            # Ajouter un texte "MARIO" au-dessus du personnage pour le repérer facilement
            font = pygame.font.Font(None, 20)
            text = font.render("MARIO", True, (255, 255, 255))
            self.screen.blit(text, (render_x, render_y - 20))
            
            # Afficher l'animation si disponible (en supplément du rectangle)
            if hasattr(self.traits["goTrait"], "animation"):
                animation = self.traits["goTrait"].animation
                if hasattr(animation, "image") and animation.image is not None:
                    try:
                        if self.traits["goTrait"].heading == 1:
                            self.screen.blit(animation.image, (render_x, render_y))
                        else:
                            flipped = pygame.transform.flip(animation.image, True, False)
                            self.screen.blit(flipped, (render_x, render_y))
                    except Exception as e:
                        print(f"Erreur lors de l'affichage de l'animation: {e}")
            
            # Toujours ajouter un point central pour améliorer la visibilité
            pygame.draw.circle(self.screen, (0, 0, 255), 
                             (render_x + self.rect.width // 2, render_y + self.rect.height // 2), 5, 0)  # Point bleu au centre
            
        except Exception as e:
            print(f"ERREUR GRAVE dans le rendu de Mario: {e}")
            import traceback
            traceback.print_exc()"""
        
        # Remplacer l'ancienne méthode par la nouvelle
        content = content.replace(old_render, new_render)
        print("✓ Remplacement de la méthode render de Mario")
    
    # Écrire le contenu modifié dans le fichier
    with open(mario_path, 'w', encoding='utf-8') as file:
        file.write(content)
    
    print("✓ Mario.py modifié avec succès")

def fix_checkpoint():
    """Améliorer la visibilité du checkpoint et empêcher le passage automatique au niveau suivant"""
    checkpoint_path = "entities/Checkpoint.py"
    backup_file(checkpoint_path)
    
    with open(checkpoint_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Remplacer la taille du checkpoint par une taille plus grande
    if "self.rect = pygame.Rect(x, y, 64, 64)" in content:
        content = content.replace(
            "self.rect = pygame.Rect(x, y, 64, 64)",
            "self.rect = pygame.Rect(x, y, 96, 96)  # Checkpoint agrandi pour meilleure visibilité"
        )
        print("✓ Taille du checkpoint augmentée")
    
    # Ajouter l'animation du checkpoint
    if "def drawCheckpoint(self):" in content:
        old_draw = """def drawCheckpoint(self):
        if self.state == 0:
            self.screen.blit(self.sprites.spriteCollection.get("checkpoint").image, 
                            (self.rect.x - self.camera.x, self.rect.y))
        else:
            self.screen.blit(self.sprites.spriteCollection.get("checkpoint-flipped").image, 
                            (self.rect.x - self.camera.x, self.rect.y))"""
        
        new_draw = """def drawCheckpoint(self):
        # Rendre le checkpoint beaucoup plus visible avec une animation pulsante
        import math
        
        # Position de base pour le rendu
        x = self.rect.x - self.camera.x
        y = self.rect.y
        
        # Créer une animation pulsante (scaling)
        pulse_factor = 1.0 + 0.2 * math.sin(pygame.time.get_ticks() / 200)  # Pulsation lente
        
        # Calculer la nouvelle taille
        original_width = 64
        original_height = 64
        pulse_width = int(original_width * pulse_factor)
        pulse_height = int(original_height * pulse_factor)
        
        # Dessiner un rectangle clignotant derrière le checkpoint
        flash_intensity = int(127 + 127 * math.sin(pygame.time.get_ticks() / 100))
        pygame.draw.rect(self.screen, (flash_intensity, flash_intensity, 0), 
                        (x - 10, y - 10, self.rect.width + 20, self.rect.height + 20), 0)
        
        # Mettre le checkpoint au centre du rectangle
        x_centered = x + (self.rect.width - pulse_width) // 2
        y_centered = y + (self.rect.height - pulse_height) // 2
        
        # Dessiner l'image selon l'état
        checkpoint_img = self.sprites.spriteCollection.get("checkpoint-flipped" if self.state else "checkpoint").image
        # Redimensionner l'image pour l'animation de pulsation
        scaled_img = pygame.transform.scale(checkpoint_img, (pulse_width, pulse_height))
        self.screen.blit(scaled_img, (x_centered, y_centered))
        
        # Ajouter un texte "CHECKPOINT" au-dessus
        font = pygame.font.Font(None, 24)
        text = font.render("CHECKPOINT", True, (255, 255, 255))
        text_rect = text.get_rect(centerx=x + self.rect.width // 2, y=y - 30)
        self.screen.blit(text, text_rect)"""
        
        content = content.replace(old_draw, new_draw)
        print("✓ Animation du checkpoint améliorée")
    
    # Écrire le contenu modifié
    with open(checkpoint_path, 'w', encoding='utf-8') as file:
        file.write(content)
    
    print("✓ Checkpoint.py modifié avec succès")

def fix_mario_env():
    """Corriger l'environnement Mario pour empêcher le passage automatique au niveau suivant"""
    env_path = "ai/mario_env.py"
    backup_file(env_path)
    
    with open(env_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Chercher la partie où le checkpoint est géré
    checkpoint_handler_start = content.find("# Vérifier si Mario a atteint le checkpoint")
    
    if checkpoint_handler_start > 0:
        # Trouver la fin du gestionnaire de checkpoint
        checkpoint_handler_end = content.find("print(f\"===== FIN HANDLE_GAMEPLAY =====\")", checkpoint_handler_start)
        
        # La partie du code qui gère le checkpoint
        old_checkpoint_code = content[checkpoint_handler_start:checkpoint_handler_end]
        
        # Créer un nouveau code de gestion qui affiche un message de victoire et attend une interaction
        new_checkpoint_code = """# Vérifier si Mario a atteint le checkpoint
        if self.mario.rect.x >= self.checkpoint_position:
            print("VICTOIRE! Mario a atteint le checkpoint!")
            reward += 1000  # Grosse récompense pour avoir atteint le checkpoint
            self.game_state = "checkpoint_reached"
            self.done = True
            self.games_played += 1
            
            # Afficher un message de victoire
            font = pygame.font.Font(None, 48)
            victory_text = font.render("CHECKPOINT ATTEINT!", True, (255, 255, 0))
            text_rect = victory_text.get_rect(center=(self.screen.get_width()//2, self.screen.get_height()//2))
            self.screen.blit(victory_text, text_rect)
            
            # Dessiner une bordure clignotante autour de l'écran
            border_thickness = 10
            border_color = (255, 255, 0)  # Jaune
            pygame.draw.rect(self.screen, border_color, 
                           (0, 0, self.screen.get_width(), self.screen.get_height()), border_thickness)
            
            # Ajouter une instruction pour indiquer comment continuer
            continue_font = pygame.font.Font(None, 24)
            
            # Message différent selon qu'on est en mode agent ou en mode manuel
            if self.agent_type == "human":
                continue_text = continue_font.render("Appuyez sur ESPACE pour continuer", True, (255, 255, 255))
            else:
                continue_text = continue_font.render("Appuyez sur n'importe quelle touche pour continuer", True, (255, 255, 255))
                
            continue_rect = continue_text.get_rect(center=(self.screen.get_width()//2, self.screen.get_height()//2 + 50))
            self.screen.blit(continue_text, continue_rect)
            
            pygame.display.update()
            
            # Attendre que l'utilisateur appuie sur une touche pour continuer
            waiting = True
            wait_start_time = time.time()
            wait_timeout = 5.0  # 5 secondes d'attente maximum en mode IA
            
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            pygame.quit()
                            sys.exit()
                        else:
                            waiting = False
                
                # En mode agent, on peut également sortir de l'attente après un délai
                if self.agent_type != "human" and (time.time() - wait_start_time) > wait_timeout:
                    waiting = False
                    
                time.sleep(0.1)  # Éviter de surcharger le CPU
        """
        
        # Remplacer l'ancien code par le nouveau
        content = content.replace(old_checkpoint_code, new_checkpoint_code)
        print("✓ Gestion du checkpoint améliorée dans mario_env.py")
    
    # Corriger la partie du rendu de Mario dans handle_gameplay
    mario_render_start = content.find("# Dessiner Mario explicitement")
    if mario_render_start > 0:
        # Trouver la fin du code de rendu de Mario
        mario_render_end = content.find("except Exception as e:", mario_render_start)
        mario_render_end = content.find("\n", mario_render_end + 10)
        
        # Extraire l'ancien code de rendu de Mario
        old_mario_render = content[mario_render_start:mario_render_end]
        
        # Créer un nouveau code de rendu pour Mario
        new_mario_render = """# Dessiner Mario explicitement sans utiliser sa méthode render() (qui pourrait être cassée)
            print(f"Dessin de Mario à la position: {self.mario.rect.x},{self.mario.rect.y}")
            
            # 1. D'abord dessiner un grand rectangle très visible pour représenter Mario
            mario_x = self.mario.rect.x - self.mario.camera.x
            mario_y = self.mario.rect.y
            
            # Rectangle rouge rempli avec bordure jaune
            pygame.draw.rect(self.screen, (255, 0, 0), 
                           (mario_x, mario_y, self.mario.rect.width, self.mario.rect.height), 0)
            pygame.draw.rect(self.screen, (255, 255, 0), 
                           (mario_x, mario_y, self.mario.rect.width, self.mario.rect.height), 3)
            
            # Ajouter un texte "MARIO" au-dessus du personnage pour le repérer facilement
            font = pygame.font.Font(None, 24)
            text = font.render("MARIO", True, (255, 255, 255))
            self.screen.blit(text, (mario_x, mario_y - 20))
            
            # Ajouter un point central pour améliorer la visibilité
            pygame.draw.circle(self.screen, (0, 0, 255), 
                             (mario_x + self.mario.rect.width // 2, 
                              mario_y + self.mario.rect.height // 2), 5, 0)
            
            # 2. Ensuite, essayer d'afficher l'animation actuelle de Mario si disponible
            if hasattr(self.mario.traits["goTrait"], "animation"):
                animation = self.mario.traits["goTrait"].animation
                if hasattr(animation, "image") and animation.image is not None:
                    try:
                        if self.mario.traits["goTrait"].heading == 1:
                            self.screen.blit(animation.image, (mario_x, mario_y))
                        else:
                            flipped = pygame.transform.flip(animation.image, True, False)
                            self.screen.blit(flipped, (mario_x, mario_y))
                    except Exception as e:
                        print(f"Erreur lors de l'affichage de l'animation: {e}")
            
            # Ne pas appeler self.mario.render() car ça pourrait causer des problèmes"""
        
        # Remplacer l'ancien code par le nouveau
        content = content.replace(old_mario_render, new_mario_render)
        print("✓ Rendu de Mario amélioré dans mario_env.py")
    
    # Écrire le contenu modifié
    with open(env_path, 'w', encoding='utf-8') as file:
        file.write(content)
    
    print("✓ mario_env.py modifié avec succès")

def fix_level():
    """Corriger le niveau pour rendre le checkpoint plus visible"""
    level_path = "classes/Level.py"
    backup_file(level_path)
    
    with open(level_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Modifier la hauteur du checkpoint pour qu'il soit plus visible
    if "elif level[y][x] == 7:" in content:
        old_code = """elif level[y][x] == 7:
                self.addCheckPoints((x * 32, y * 32 - (3 * 32)))"""
        
        new_code = """elif level[y][x] == 7:
                # Position modifiée du checkpoint pour qu'il soit plus visible
                # Réduire la hauteur à 2 tuiles au lieu de 3 pour qu'il soit visible
                self.addCheckPoints((x * 32, y * 32 - (2 * 32)))"""
        
        content = content.replace(old_code, new_code)
        print("✓ Position du checkpoint améliorée")
    
    # Écrire le contenu modifié
    with open(level_path, 'w', encoding='utf-8') as file:
        file.write(content)
    
    print("✓ Level.py modifié avec succès")

if __name__ == "__main__":
    print("=== SCRIPT DE CORRECTION DU JEU MARIO ===")
    print("Ce script va corriger les problèmes suivants:")
    print("1. Mario invisible")
    print("2. Checkpoint invisible")
    print("3. Passage automatique au niveau suivant")
    print("\nDémarrage des corrections...\n")
    
    try:
        # Appliquer toutes les corrections
        fix_mario_class()
        fix_checkpoint()
        fix_mario_env()
        fix_level()
        
        print("\n=== TOUTES LES CORRECTIONS ONT ÉTÉ APPLIQUÉES AVEC SUCCÈS ===")
        print("Vous pouvez maintenant lancer le jeu avec python main.py")
        print("Si vous rencontrez des problèmes, des fichiers de sauvegarde ont été créés (.backup)")
    except Exception as e:
        print(f"\nERREUR LORS DE L'APPLICATION DES CORRECTIONS: {e}")
        import traceback
        traceback.print_exc()
        print("\nVeuillez réessayer ou appliquer les corrections manuellement")
