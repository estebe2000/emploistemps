# Arrête l'exécution à la première erreur
$ErrorActionPreference='stop';

[String]$lPrefixeWsdl='http://monserveur/hpsw/wsdl/SansTypeSimple';

# Fenêtre d'authentification
$lIdentification = Get-Credential;

# Interfaces utilisées
$lAdmin = New-WebServiceProxy -uri "$lPrefixeWsdl/IHpSvcWAdmin" -Credential $lIdentification;
$lMatieres = New-WebServiceProxy -uri "$lPrefixeWsdl/IHpSvcWMatieres" -Credential $lIdentification;

# Affichage de la version
"Connecté à " + $lAdmin.Version();

# Affichage du nombre de matières
"Il y a {0:D} matières dans la base" -f $lMatieres.NombreMatieres();

# Affichage de la liste des matières
$lCles = $lMatieres.ToutesLesMatieres();
$lCles = $lMatieres.TrierTableauDeMatieresParLibelleEtCode($lCles);
$lCodes = $lMatieres.CodesTableauDeMatieres($lCles);
$lLibelles = $lMatieres.LibellesTableauDeMatieres($lCles);
$lLibellesLongs = $lMatieres.LibellesLongsTableauDeMatieres($lCles);
for ($lIndice = 0; $lIndice -lt $lCles.Count; $lIndice++) {"{0,3:D} {1,-8} {2,-20} {3}" -f $lCles[$lIndice], $lCodes[$lIndice], $lLibelles[$lIndice], $lLibellesLongs[$lIndice]};
