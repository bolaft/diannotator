# Format de données d'entrée

### Emplacement :

Il est recommandé de placer les fichiers de données dans le dossier `csv` à la racine du projet.

### Format :

Le seul format accepté est CSV. Le fichier doit contenir une ligne d'entête et autant de lignes supplémentaires qu'il n'y a de segments dialogiques à annoter. Consultez le fichier `csv/ubuntu-irc-fr.csv` pour observer un exemple. Les colonnes sont :

#### `time`

Contient une chaîne de caractères représentant l'heure d'envoi du message.

#### `date`

Contient une chaîne de caractères représentant la date d'envoi du message.

#### `segment`

Contient le segment fonctionnel sur lequel s'appliquent les annotations. Si la colonne est vide pour un segment, cela doit signifier que le message (`raw`) a été fusionné avec le précédent (comme dans le format multi-tab de DiAML).

#### `raw`

Contient le texte brut du message. Si le message a été segmenté, la colonne `raw` doit être remplie uniquement pour le premier segment, et laissée vide pour les segments qui suivent (comme dans le format multi-tab de DiAML).

#### `participant`

Contient le nom ou l'identifiant du participant qui a produit le message.

#### `<nom de dimension>` (optionnel)

Les colonnes portant un nom de dimension servent à charger les annotations "legacy" (pour l'aide à l'annotation). Par exemple, on peut avoir la valeur `check contact` dans la colonne `contact management`. Les dimensions et leurs labels doivent respecter la nomenclature de la taxonomie employée.

#### `<nom de dimension>-value` (optionnel)

Les colonnes portant un nom de dimension suffixé de `-value` doivent contenir la valeur du qualifieur pour cette dimension. Par exemple, on peut avoir la valeur `inform` dans la colonne `emotion` et `happiness` dans la colonne `emotion-value`. Les dimensions et leurs labels doivent respecter la nomenclature de la taxonomie employée.

### Taxonomie :

La taxonomie est définie par défaut dans le fichier `taxonomy.py`, mais peut être modifiée en cours d'utilisation via différentes commandes détaillées plus bas.

# Utilisation

### Annotation :

Les boutons noirs en bas de l'écran indiquent les annotations disponibles pour la dimension active. La dimension active par défaut est `Task`. Le segment actif est le dernier segment affiché, il apparaît en gras. Pour appliquer une annotation, il suffit de cliquer sur le bouton approprié ou de taper une partie suffisamment discriminante du label (par exemple `req dir` pour `request directives`) puis d'appuyer sur "Entrée" pour appliquer le label à l'énoncé et passer au suivant.

### Raccourcis clavier :

#### `Enter`

Valide une entrée dans le champ texte, sélectionne un bouton sur lequel le focus est placé, ou passe au segment suivant en mode annotation si le champs d'entrée de texte est vide.

#### `Down Arrow`

Passe au segment suivant.

#### `Up Arrow`

Passe au segment précédent.

#### `Page Down`

Descend de dix segments.

#### `Page Up`

Remonte de dix segments.

#### `Delete`

Supprime le segment actif.

#### `F11`

Alterne en le mode plein écran et le mode fenêtré.

#### `Escape`

Quitte l'application. 

#### `Tab`

Passe le focus de bouton en bouton.

#### `Control O`

Ouvre le dialogue de chargement de fichier.

#### `Control Shift S`

Ouvre le dialogue de sauvegarde de fichier.

#### `Control Shift E`

Ouvre le dialogue d'export au format .json ou .csv.

### Commandes spéciales :

#### Add : `Control A`

La prochaine entrée créé un nouveau label ajouté en tant que fonction spécifique à la dimension active.

#### Dimension : `Control D`

Permet de choisir la dimension active.

#### Filter : `Control F`

Les segments sont filtrés pour ne plus afficher que les segments annotés avec le même label que le segment actif pour la dimension active. Si le segment n'est pas annoté pour la dimension active, le filtre est créé sur le label "legacy" du segment actif pour la dimension active.

#### Jump : `Control J`

Permet d'entrer l'index d'un segment et de s'y déplacer immédiatement.

#### Link : `Control L`

Si le segment actif n'est lié à aucun autre segment, propose d'entrer l'index du segment cible puis créé le lien. Si le segment a déjà un lien vers un autre segment, le lien est supprimé.

#### Merge : `Control M`

Fusionne le segment actif à celui qui le précède. Les liens, commentaires, annotations et annotations "legacy" sont préservés.

#### Note : `Control N`

La prochaine entrée créé un commentaire joint au segment actif. Si un commentaire existe déjà pour le segment actif, il est supprimé.

#### Remove : `Control R`

Supprime l'annotation du segment actif pour la dimension active.

#### Split : `Control S`

Divise le segment actif en deux, au niveau du mot choisi. Les liens, commentaires, annotations et annotations "legacy" sont préservés.

#### Update : `Control U`

La prochaine entrée correspondra au nouveau nom du label du segment actif, pour la dimension active. Le renommage est appliqué à tous les segment de la collection. Si l'entrée est laissée vide, le label est supprimé de la taxonomie.

#### Undo : `Control Z`

Annule la dernière action effectuée.
