<?php

// URL du document WSDL de HYPERPLANNING Service web
$WSDL = "http://localhost:80/hpsw/wsdl/RpcEncoded";

// L'identifiant et le mot de passe du compte "service web"
// SÉCURITÉ : ne jamais coder les identifiants en dur.
// Fournir via variables d'environnement (HP_SW_LOGIN / HP_SW_PASS) ou remplacer les placeholders.
$LOGIN = getenv('HP_SW_LOGIN') ?: 'LOGIN_SERVICE_WEB';
$PASS = getenv('HP_SW_PASS') ?: 'MOT_DE_PASSE_SERVICE_WEB';

// Creation du client SOAP
$client = new SoapClient($WSDL, array('login'=> $LOGIN,'password'=> $PASS));

// Affichage du nombre d'enseignants
$NombreEnseignants = $client->NombreEnseignants();
print "<strong>$NombreEnseignants enseignants.</strong><br/>\n";

//  Affichage des "Nom et Prénom" des enseignants
$Enseignants = $client->TousLesEnseignants();
print "<strong>Nom et Prénom des enseignants :</strong><br/>\n";

foreach ($Enseignants as $Enseignant_ID) {
        $NomEnseignant = $client->NomEnseignant($Enseignant_ID);
        $PrenomEnseignant = $client->PrenomEnseignant($Enseignant_ID);
        print "$NomEnseignant $PrenomEnseignant<br/>\n";
}
?>
