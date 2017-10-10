# Format de données

### Fichier de données :

Les données doivent être placées dans le dossier `dat` à la racine du projet, le nom du fichier doit être `data.csv`.

### Format accepté :

Le seul format accepté est CSV : à partir du fichier `ubuntu-fr-cmc-da_170715_after-irc-raw-alignment.ods`, il faut sélectionner les lignes à désirer et les exporter au format CSV, sans marqueur de champs de texte et avec une tabulation comme séparateur. La ligne d'entête doit être supprimée.

### Formats différents :

Si le format de fichier est différent de celui de ce fichier Calc, le code source doit être modifié pour prendre en charge le nouveau format dans les fonctions `load_raw` et `make_legacy_annotations` de la classe `DialogueActCollection` dans le fichier `model.py`.

### Taxonomie :

La taxonomie est définie par défaut dans le fichier `taxonomy.py`, mais peut être modifiée en cours d'utilisation via différentes commandes détaillées plus bas.

# Utilisation

### Annotation :

Les boutons noirs en bas de l'écran indiquent les annotations disponibles pour la dimension active. La dimension active par défaut est `Task`. Le segment actif est le dernier segment affiché, il apparaît en gras. Pour appliquer une annotation, il suffit de cliquer sur le bouton approprié ou de taper une partie suffisamment discriminante du label (par exemple `req dir` pour `request directives`) puis d'appuyer sur "Entrée" pour appliquer le label à l'énoncé et passer au suivant.

### Raccourcis clavier :

#### `Enter`

Valide une entrée dans le champs texte, sélectionne un bouton sur lequel le focus est placé, ou passe au segment suivant en mode annotation si le champs d'entrée de texte est vide.

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

#### Comment : `Control C`

La prochaine entrée créé un commentaire joint au segment actif. Si un commentaire existe déjà pour le segment actif, il est supprimé.

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

#### Remove : `Control R`

Supprime l'annotation du segment actif pour la dimension active.

#### Split : `Control S`

Divise le segment actif en deux, au niveau du mot choisi. Les liens, commentaires, annotations et annotations "legacy" sont préservés.

#### Update : `Control U`

La prochaine entrée correspondra au nouveau nom du label du segment actif, pour la dimension active. Le renommage est appliqué à tous les segment de la collection. Si l'entrée est laissée vide, le label est supprimé de la taxonomie.

#### Undo : `Control Z`

Annule la dernière action effectuée.
