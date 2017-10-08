# Format de donées

### Fichier de données :

Les données doivent être placées dans le dossier "data" à la racine du projet, le nom du fichier doit être "data.csv".

### Format accepté :

Le seul format accepté est CSV : à partir du fichier "ubuntu-fr-cmc-da_170715_after-irc-raw-alignment.ods", il faut sélectionner les lignes à désirer et les exporter au format CSV, sans marqueur de champs de texte et avec une tabulation comme séparateur. La ligne "header" doit être supprimée.

### Formats différents :

Si le format de fichier est différent de celui de ce fichier Calc, le code source doit être modifié pour prendre en charge le nouveau format dans les fonctions "load_raw" et "make_legacy_annotations" de la classe DialogueActCollection dans le fichier model.py.

### Taxonomie :

La taxonomie est définie par défaut dans le fichier python taxonomy.py, mais peut être modifiée en cours d'utilisation directement dans l'interface du programme.

# Chargement et sauvegarde

Une fois les données présentes dans le dossier data, il faut les charger dans l'application en exécutant le script initialize_collection.py. Les modifications effectuées en cours d'annotation sont automatiquement sauvegardées en tant qu'objet DialogueActCollection sérialisé avec pickle. Le fichier de sauvegarde est le fichier save.pic du dossier data. C'est ce fichier qui est chargé en mémoire automatiquement au lancement de l'application.

Pour effectuer un backup de la sauvegarde, il faut exécuter le fichier save_backup.py. Ce programme créé un backup dans le dossier data, dont le nom correspond au nombre de secondes depuis l'époque Unix.
