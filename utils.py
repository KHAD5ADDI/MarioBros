"""
Module contenant des fonctions utilitaires pour la suppression d'avertissements
et d'autres fonctionnalités communes.
"""

import os
import warnings
import contextlib
import ctypes

def suppress_pygame_warnings():
    """
    Supprime les avertissements libpng et autres avertissements non critiques 
    lors de l'initialisation de Pygame.
    
    Cette fonction utilise le module warnings de Python pour filtrer les avertissements.
    """
    # Ignorer tous les avertissements de ResourceWarning (causés par libpng)
    warnings.filterwarnings("ignore", category=ResourceWarning)
    
    # Ignorer spécifiquement les avertissements libpng
    os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"  # Cacher le message "Hello from pygame"
    
    # Sous Windows, nous pouvons utiliser SetErrorMode pour supprimer les boîtes de dialogue d'erreur
    if os.name == 'nt':
        # SetErrorMode pour supprimer les popups d'erreur système
        SEM_NOGPFAULTERRORBOX = 0x0002  # Ne pas afficher les boîtes de dialogue d'erreur Windows
        ctypes.windll.kernel32.SetErrorMode(SEM_NOGPFAULTERRORBOX)
    
    @contextlib.contextmanager
    def stderr_redirected(to=os.devnull):
        """
        Contexte qui redirige temporairement stderr vers un fichier.
        """
        import sys
        
        # Sauvegarde le stderr actuel
        old_stderr = sys.stderr
        
        # Redirige vers le fichier spécifié
        if to is None:
            yield old_stderr
            return
            
        # Ouvre le fichier de destination et redirige stderr
        with open(to, 'w') as file:
            sys.stderr = file
            try:
                yield file
            finally:
                # Restaure le stderr original
                sys.stderr = old_stderr
    
    return stderr_redirected