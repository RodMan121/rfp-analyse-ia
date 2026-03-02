from .models import FragmentClassification
from .parser import RawFragment

class RuleBasedClassifier:
    def classify(self, raw: RawFragment) -> FragmentClassification:
        # Implémentation simplifiée par défaut
        return FragmentClassification(
            domaine="Général",
            type_babok="Non-Fonctionnel",
            tags=[],
            priorite_esn="Normale",
            score_complexite=1
        )
