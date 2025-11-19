# Synthèse : Impact des pratiques agricoles sur la fertilité des sols en Agriculture Biologique

## Contexte et Objectifs
L'agriculture biologique (AB) est positionnée comme une alternative durable, mais son impact à long terme sur la fertilité des sols suscite des interrogations, notamment concernant le risque de baisse des stocks de nutriments (phosphore, potassium) . Ce document synthétise une étude basée sur deux dispositifs complémentaires : l'observatoire régional **QualiSolsBio** (Grand Est) et le suivi long terme (16 années) de l'installation expérimentale de l'**INRAE ASTER** à Mirecourt .

L'objectif est de déterminer dans quelle mesure les pratiques culturales (rotations, travail du sol, fertilisation) influencent les trajectoires de fertilité chimique des sols .

## Méthodologie : Une approche transférable

Pour permettre la réplication de cette analyse sur d'autres territoires ou systèmes, la méthodologie suivante a été déployée :

1.  **Collecte de données multiscalaires :**
    * **Spatial :** Comparaison de parcelles agriculteurs via l'observatoire (23 parcelles en Grand Est) pour capturer la variabilité pédoclimatique et des pratiques .
    * **Temporel :** Suivi de points de fertilité fixes sur 16 ans (2006-2022) avec des analyses de sol réalisées tous les 4 ans .

2.  **Traitement statistique (Le cœur du modèle) :**
    * **Classification des pratiques :** Création d'indicateurs pour qualifier les rotations (courtes/longues, diversifiées), le travail du sol (labour superficiel/profond) et la fertilisation (fréquence, nature des effluents) .
    * **Typologie des évolutions :** Utilisation d'Analyses en Composantes Principales (ACP) et de Classifications Hiérarchiques Ascendantes (CAH) pour grouper les parcelles selon l'évolution de leurs paramètres chimiques (C, N, P, K, CEC) .
    * **Arbre de décision :** Utilisation de la méthode CART pour hiérarchiser les facteurs explicatifs des évolutions de fertilité et identifier les règles de décision .

## Résultats Clés et Leviers d'Action

L'étude démontre que l'AB est compatible avec le maintien de la fertilité chimique, sous réserve de certaines pratiques .

### 1. L'importance cruciale des rotations
L'arbre de décision identifie le **type de rotation** comme la variable la plus discriminante pour l'évolution de la fertilité .
* **Rotations courtes avec prairies :** Elles sont associées à une fertilité stable (carbone, azote) et peu variable . La fréquence élevée de prairies temporaires favorise le maintien de la fertilité .
* **Rotations longues :** Elles peuvent entraîner une plus grande variabilité de la fertilité chimique, nécessitant une vigilance accrue .

### 2. Le rôle de la fertilisation et du pâturage
* Les conduites intégrant une fertilisation fréquente et diversifiée (effluents liquides et solides + pâturage) sont corrélées à un maintien global de la fertilité .
* À l'inverse, une fertilisation peu fréquente basée uniquement sur des amendements solides, sans pâturage, est associée à une forte variabilité ou une baisse des teneurs en phosphore et potassium .

### 3. L'impact nuancé du travail du sol
Dans le cadre de cette étude, le travail du sol ne semble pas être lié aux autres variables (rotation, fertilisation) de manière significative pour expliquer l'évolution globale . Cependant, le labour superficiel semble associé à une meilleure stabilité des paramètres chimiques .

## Conditions de Réplication et Mise en Place Ailleurs

Pour utiliser cette approche comme outil de pilotage ou de diagnostic sur d'autres territoires :

* **Nécessité de données historiques :** La pertinence du modèle repose sur la disponibilité de données de long terme ; l'évolution de certaines propriétés ne devient significative qu'après des dizaines d'années .
* **Caractérisation fine des amendements :** Il est crucial de classifier les intrants organiques selon leurs propriétés chimiques réelles (C/N, teneurs en P, K, N) plutôt que par leur simple dénomination (fumier, lisier) pour comprendre leur impact .
* **Adaptation aux spécificités locales :** L'arbre de décision produit est spécifique au système de polyculture-élevage d'ASTER . Une réplication ailleurs nécessiterait de ré-entraîner le modèle sur des données locales pour obtenir des règles adaptées au contexte pédoclimatique.
* **Indicateurs complémentaires :** Pour affiner le diagnostic, l'intégration de l'indicateur STIR (intensité du travail du sol) est recommandée pour mieux nuancer les pratiques de travail du sol .

## Conclusions Opérationnelles

* **Maintenir la fertilité en AB est possible :** Cela passe prioritairement par l'intégration de l'élevage (pâturage) et une place importante des prairies temporaires dans les rotations .
* **Vigilance sur le Phosphore et le Potassium :** Des situations de baisse de fertilité (déstockage P et K) ont été observées, soulignant le risque dans les systèmes où les exportations ne sont pas compensées par une fertilisation adéquate .
* **Outil d'aide à la décision :** La méthode développée (croisement typologies/trajectoires) permet d'identifier les pratiques à risque et de concevoir des systèmes de culture plus résilients .