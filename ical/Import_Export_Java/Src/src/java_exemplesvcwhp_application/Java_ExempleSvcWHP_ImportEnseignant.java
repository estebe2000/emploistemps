package java_exemplesvcwhp_application;

import com.indexeducation.frahtm.hpsvcw.IHpSvcWEnseignants;
import java.util.Date;
import java.text.DateFormat;
import java.text.SimpleDateFormat;
import java.io.BufferedReader;
import java.io.FileReader;
import java.util.GregorianCalendar;
import javax.xml.datatype.DatatypeFactory;
import javax.xml.datatype.XMLGregorianCalendar;

public class Java_ExempleSvcWHP_ImportEnseignant {
    Java_ExempleSvcWHP_View frame;
    IHpSvcWEnseignants      portEnseignant;
    String                  pathImport;

    public Java_ExempleSvcWHP_ImportEnseignant(Java_ExempleSvcWHP_View aFrame,
                                               IHpSvcWEnseignants      aPortEnseignant,
                                               String                  aPath) {
        portEnseignant = aPortEnseignant;
        pathImport     = aPath;
        frame          = aFrame;
    }

    public long AccederOuCreerEnseignant (String aNom,	String aPrenom, String aCode, String aIdent){
        long resultat = 0;
	try {
            if (!aIdent.equals("")){ // s'il y a un identifiant, on accède à l'enseigant par l'identifiant
	        resultat = portEnseignant.accederEnseignantParIdentifiant(aIdent);
		if (!aNom.equals("")) // on modifie le nom s'il est non vide
  		    portEnseignant.modifierNomEnseignant(resultat, aNom);
  		if (!aPrenom.equals("")) // on modifie le prénom s'il est non vide
		    portEnseignant.modifierPrenomEnseignant(resultat, aPrenom);
		if (!aCode.equals("")) // on modifie le code s'il est non vide
		    portEnseignant.modifierCodeEnseignant(resultat, aCode);
	    } else { // s'il n'y a pas d'identifiant, on accède à l'enseignant par code, nom et prénom
	        resultat = portEnseignant.accederEnseignantParNomPrenomEtCode(aNom, aPrenom, aCode);
	    }
	} catch (Exception e1){
	    try { // on crée l'enseignant
	        resultat = portEnseignant.creerEnseignantAvecIdentifiant (aNom, aPrenom, aCode, aIdent);
	    } catch (Exception e2){
  	        // L'identifiant est nouvellement défini mais l'enseignant existe déjà dans la base
                try {
	            resultat = portEnseignant.accederEnseignantParNomPrenomEtCode (aNom, aPrenom, aCode);
	            if (!aIdent.equals("")) // on modifie l'identifiant s'il est non vide
		        portEnseignant.modifierIdentifiantEnseignant (resultat, aIdent);
                } catch (Exception e3) {}
	    }
	}
	return resultat;
    }

    public int getImportEnseignants() {// retourne le nombre d'enseignants importés
        String ligne;
        String [] split       = null;
        int resultat          = 0;
        int splitProfIdent    = -1;
        int splitProfCode     = -1;
        int splitProfNom      = -1;
        int splitProfPrenom   = -1;
        int splitProfDate     = -1;
        int splitProfProprio  = -1;
        int splitProfMail     = -1;
        int splitProfCivilite = -1;
        int splitProfAdr1     = -1;
        int splitProfAdr2     = -1;
        int splitProfCodePost = -1;
        int splitProfVille    = -1;

        try {
            BufferedReader fichier = new BufferedReader (new FileReader(pathImport));
            // on initialise les numeros de colonne sur la premiere ligne
            if ((ligne = fichier.readLine()) != null) {
                ligne = ligne.replaceAll("\n", ";"); //Separateurs : ; ou , ou Tab
                ligne = ligne.replaceAll("\t", ";"); //Separateurs : ; ou , ou Tab
                split = ligne.split(";");            //Separateurs : ; ou , ou Tab

                for (int i= 0; i < split.length; i++) {
                    if (split [i].equalsIgnoreCase("IDENT_ENS"))
                        splitProfIdent = i;
                    else if (split [i].equalsIgnoreCase("CODE_ENS"))
                        splitProfCode = i;
                    else if (split [i].equalsIgnoreCase("NOM_ENS"))
                        splitProfNom = i;
                    else if (split [i].equalsIgnoreCase("PRENOM_ENS"))
                        splitProfPrenom = i;
                    else if (split [i].equalsIgnoreCase("DATE_ENS"))
                        splitProfDate = i;
                    else if (split [i].equalsIgnoreCase("PROP_ENS"))
                        splitProfProprio = i;
                    else if (split [i].equalsIgnoreCase("EMAIL_ENS"))
                        splitProfMail = i;
                    else if (split [i].equalsIgnoreCase("CIV_ENS"))
                        splitProfCivilite = i;
                    else if (split [i].equalsIgnoreCase("ADR1_ENS"))
                        splitProfAdr1 = i;
                    else if (split [i].equalsIgnoreCase("ADR2_ENS"))
                        splitProfAdr2 = i;
                    else if (split [i].equalsIgnoreCase("CODEPOSTAL_ENS"))
                        splitProfCodePost = i;
                    else if (split [i].equalsIgnoreCase("VILLE_ENS"))
                        splitProfVille = i;
                }
            }

            while ((ligne = fichier.readLine()) != null) {  // Lit le fichier ligne par ligne
                ligne = ligne.replaceAll("\n", ";"); //Separateurs : ; ou , ou Tab
                ligne = ligne.replaceAll("\t", ";"); //Separateurs : ; ou , ou Tab
   		split = ligne.split(";");            //Separateurs : ; ou , ou Tab
		try {
                    String enseignantIdent        = "";
                    String enseignantCode 	  = "";
                    String enseignantNom 	  = "";
                    String enseignantPrenom       = "";
                    String enseignantDate         = "";
                    String enseignantProprietaire = "";
                    String enseignantMail         = "";
                    String enseignantCivilite     = "";
                    String enseignantAdresse1     = "";
                    String enseignantAdresse2     = "";
                    String enseignantCodePostal   = "";
                    String enseignantVille        = "";

                    if ((splitProfIdent    != -1) && (splitProfIdent    < split.length))
                        enseignantIdent        = split [splitProfIdent];
                    if ((splitProfCode     != -1) && (splitProfCode     < split.length))
                        enseignantCode 	       = split [splitProfCode];
                    if ((splitProfNom      != -1) && (splitProfNom      < split.length))
                        enseignantNom 	       = split [splitProfNom];
                    if ((splitProfPrenom   != -1) && (splitProfPrenom   < split.length))
                        enseignantPrenom       = split [splitProfPrenom];
                    if ((splitProfDate     != -1) && (splitProfDate     < split.length))
                        enseignantDate         = split [splitProfDate];
                    if ((splitProfProprio  != -1) && (splitProfProprio  < split.length))
                        enseignantProprietaire = split [splitProfProprio];
                    if ((splitProfMail     != -1) && (splitProfMail     < split.length))
                        enseignantMail         = split [splitProfMail];
                    if ((splitProfCivilite != -1) && (splitProfCivilite < split.length))
                        enseignantCivilite     = split [splitProfCivilite];
                    if ((splitProfAdr1     != -1) && (splitProfAdr1     < split.length))
                        enseignantAdresse1     = split [splitProfAdr1];
                    if ((splitProfAdr2     != -1) && (splitProfAdr2     < split.length))
                        enseignantAdresse2     = split[splitProfAdr2];
                    if ((splitProfCodePost != -1) && (splitProfCodePost < split.length))
                        enseignantCodePostal   = split [splitProfCodePost];
                    if ((splitProfVille    != -1) && (splitProfVille    < split.length))
                        enseignantVille        = split [splitProfVille];

	            long enseignantCourant = AccederOuCreerEnseignant (enseignantNom,
			         				       enseignantPrenom,
	 				        		       enseignantCode,
							               enseignantIdent);
                    
                    try { // Modification de la date de naissance
                        if (splitProfDate     != -1)
                            if (!enseignantDate.equals("")) {
                                DateFormat df = new SimpleDateFormat ("dd/MM/yyyy") ;
                                Date lDate = df.parse(enseignantDate);
                                GregorianCalendar gDate = new GregorianCalendar();
                                gDate.setTime(lDate);
                                XMLGregorianCalendar xmlCalendar = DatatypeFactory.newInstance().newXMLGregorianCalendar(gDate);
                                portEnseignant.modifierDateDeNaissanceEnseignant(enseignantCourant, xmlCalendar);
                            }
                    } catch (Exception e) {}

                    try { // Modification du propriétaire
                        if (splitProfProprio  != -1)
                            if (!enseignantProprietaire.equals(""))
                                portEnseignant.modifierProprietaireEnseignant (enseignantCourant,
                                                                               enseignantProprietaire,
                                                                               "");
                    } catch (Exception e) {}
                    try { // Modification de l'adresse mail
                        if (splitProfMail     != -1)
                            if (!enseignantMail.equals(""))
                                portEnseignant.modifierEMailEnseignant (enseignantCourant,
                                                                        enseignantMail);
                    } catch (Exception e) {}
                    try { // Modification de la civilité
                        if (splitProfCivilite != -1)
                            if (!enseignantCivilite.equals(""))
                                portEnseignant.modifierCiviliteEnseignant (enseignantCourant,
                                                                           enseignantCivilite);
                    } catch (Exception e) {}
                    try { // Modification de l'adresse 1
                        if (splitProfAdr1 != -1)
                            if (!enseignantAdresse1.equals(""))
                                portEnseignant.modifierAdresse1Enseignant (enseignantCourant,
                                                                           enseignantAdresse1);
                    } catch (Exception e) {}
                    try { // Modification de l'adresse 2
                        if (splitProfAdr2 != -1)
                            if (!enseignantAdresse2.equals(""))
                                portEnseignant.modifierAdresse2Enseignant (enseignantCourant,
                                                                           enseignantAdresse2);
                    } catch (Exception e) {}
                    try { // Modification du code postal
                        if (splitProfCodePost != -1)
                            if (!enseignantCodePostal.equals(""))
                                portEnseignant.modifierCodePostalEnseignant (enseignantCourant,
                                                                             enseignantCodePostal);
                    } catch (Exception e) {}
                    try { // Modification de la ville
                        if (splitProfVille  != -1)
                            if (!enseignantVille.equals(""))
                                portEnseignant.modifierVilleEnseignant (enseignantCourant,
                                                                        enseignantVille);
                    } catch (Exception e) {}
                    resultat++;
                    frame.EcrireDansZone ("Import des enseignants en cours... : " + resultat + " lignes importés");
                } catch (Exception e) {}
            }
            fichier.close();
        } catch (java.io.IOException ex){
            frame.EcrireDansZone ("pb de lecture sur le fichier: " + ex);
            System.out.println("pb de lecture sur le fichier: " + ex);
        }
        return resultat;
    }
}
