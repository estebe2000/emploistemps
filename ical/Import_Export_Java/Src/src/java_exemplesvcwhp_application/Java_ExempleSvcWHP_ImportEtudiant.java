package java_exemplesvcwhp_application;

import com.indexeducation.frahtm.hpsvcw.IHpSvcWEtudiants;
import com.indexeducation.frahtm.hpsvcw.IHpSvcWPromotions;
import com.indexeducation.frahtm.hpsvcw.IHpSvcWTDOptions;
import java.util.Date;
import java.text.DateFormat;
import java.text.SimpleDateFormat;
import java.io.BufferedReader;
import java.io.FileReader;
import java.util.GregorianCalendar;
import javax.xml.datatype.DatatypeFactory;
import javax.xml.datatype.XMLGregorianCalendar;

public class Java_ExempleSvcWHP_ImportEtudiant {
    Java_ExempleSvcWHP_View frame;
    IHpSvcWEtudiants        portEtudiant;
    IHpSvcWPromotions       portPromotion;
    IHpSvcWTDOptions        portTDOption;
    String                  pathImport;

    public Java_ExempleSvcWHP_ImportEtudiant(Java_ExempleSvcWHP_View aFrame,
                                             IHpSvcWEtudiants        aPortEtudiant,
                                             IHpSvcWPromotions       aPortPromotion,
                                             IHpSvcWTDOptions        aPortTDOption,
                                             String                  aPath) {
        portEtudiant   = aPortEtudiant;
        portPromotion  = aPortPromotion;
        portTDOption   = aPortTDOption;
        pathImport     = aPath;
        frame          = aFrame;
    }

    public long AccederOuCreerPromotion (String aLibelle, String aCode, String aIdent){
        long resultat = 0;
	try {
	    if (!aIdent.equals("")){ // s'il y a un identifiant, on accède au diplôme par l'identifiant
		resultat =portPromotion.accederPromotionParIdentifiant(aIdent);
		if (!aLibelle.equals("")) // on modifie le libelle s'il est non vide
		    portPromotion.modifierNomPromotion(resultat, aLibelle);
		if (!aCode.equals("")) // on modifie le code s'il est non vide
		    portPromotion.modifierCodePromotion(resultat, aCode);
	    } else { // s'il n'y a pas d'identifiant, on accède au diplôme par code et libelle
	        resultat = portPromotion.accederPromotionParNomEtCode(aLibelle, aCode);
	    }
	} catch (Exception e1) {
	    try { // on crée le diplôme
	        resultat = portPromotion.creerPromotionAvecIdentifiant(aLibelle, aCode, aIdent);
   	    } catch (Exception e2) {
                try {
	            // L'identifiant est nouvellement défini mais le diplôme existe déjà dans la base
		    resultat = portPromotion.accederPromotionParNomEtCode(aLibelle, aCode);
		    if (!aIdent.equals(""))// on modifie l'identifiant s'il est non vide
		        portPromotion.modifierIdentifiantPromotion(resultat, aIdent);
                } catch (Exception e3) {}
	    }
	}
        return resultat;
    }

    public long AccederOuCreerPartition (long aPromotion, String aLibelle){
        long resultat = 0;
	try { // On accede à la partition par diplôme et libelle
	    resultat = portTDOption.accederPartitionParPromotionEtNom (aPromotion, aLibelle);
	} catch (Exception e) {
	    try { // sinon on la crée
                resultat = portTDOption.creerPartitionDeLaPromotion (aPromotion, aLibelle);
	    } catch (Exception e1) {}
	}
        return resultat;
    }

    public long AccederOuCreerTD (String aLibelle, String aCode, String aIdent){

        long resultat = 0;
	String [] splitLibelle   = null;
	String [] splitCode      = null;
	String [] splitIdent     = null;
	String lTDIdent          = "";
	String lTDLibelle        = "";
	String lTDCode           = "";
	String lPartitionLibelle = "";
	String lPromotionIdent   = "";
	String lPromotionLibelle = "";
	String lPromotionCode    = "";

	try {
            aLibelle = aLibelle.replaceAll(">", "<"); //<Promotion><Partition>TD  // 1 3 4
            splitLibelle = aLibelle.split("<");       // Sous la syntaxe : <nom_du_diplôme><Partition>nom_du_td

            aCode = aCode.replaceAll(">", "<");   //<Promotion><Partition>TD  // 1 3 4
            splitCode = aCode.split("<");         // Sous la syntaxe : <code_du_diplôme><Partition>code_du_td

            aIdent = aIdent.replaceAll(">", "<"); //<Promotion><Partition>TD  // 1 3 4
            splitIdent = aIdent.split("<");       // Sous la syntaxe : <ident_du_diplôme><Partition>ident_du_td

            if (splitIdent.length   == 5){
                lTDIdent        = splitIdent[4];         // ident_du_td
                lPromotionIdent = splitIdent[1];         // ident_du_diplôme
            }
            if (splitLibelle.length == 5){
                lTDLibelle        = splitLibelle[4];     // nom_du_td
                lPromotionLibelle = splitLibelle[1];     // nom_du_diplôme
                lPartitionLibelle = splitLibelle[3];     // partition
            }
            if (splitCode.length    == 5){
                lTDCode        = splitCode[4];           // code_du_td
                lPromotionCode = splitCode[1];           // code_du_diplôme
            }

            try {
                if (!aIdent.equals("")){  // s'il y a un identifiant, on accède au TD par l'identifiant
                    resultat = portTDOption.accederTDOptionParIdentifiant (lTDIdent);
                    if (!lTDLibelle.equals("")) // on modifie le libelle s'il est non vide
                        portTDOption.modifierNomTDOption  (resultat, lTDLibelle);
                    if (!lTDCode.equals("")) // on modifie le code s'il est non vide
                        portTDOption.modifierCodeTDOption (resultat, lTDCode);
                } else { // s'il n'y a pas d'identifiant, on accede a la promotion, à la partition puis au TD par code et libelle
                    long lPromotion = AccederOuCreerPromotion (lPromotionLibelle, lPromotionCode, lPromotionIdent);
                    long lPartition = AccederOuCreerPartition (lPromotion, lPartitionLibelle);
                    resultat = portTDOption.accederTDParPartitionNomEtCode (lPartition, lTDLibelle, lTDCode);
                }
            } catch  (Exception e){
                try { // on cree le TD
                    long lPromotion = AccederOuCreerPromotion (lPromotionLibelle, lPromotionCode, lPromotionIdent);
                    long lPartition = AccederOuCreerPartition (lPromotion, lPartitionLibelle);
                    resultat = portTDOption.creerTDAvecIdentifiant (lPartition, lTDLibelle, lTDCode, lTDIdent);
                } catch  (Exception e1){
                    // L'identifiant est nouvellement défini mais le TD existe déjà dans la base
                    long lPromotion = AccederOuCreerPromotion (lPromotionLibelle, lPromotionCode, lPromotionIdent);
                    long lPartition = AccederOuCreerPartition (lPromotion, lPartitionLibelle);
                    resultat = portTDOption.accederTDParPartitionNomEtCode (lPartition, lTDLibelle, lTDCode);
                    if (!aIdent.equals("")) // on modifie l'identifiant s'il est non vide
                        portTDOption.modifierIdentifiantTDOption (resultat, lTDIdent);
                }
            }
	} catch  (Exception e){}
        return resultat;
    }

    public long AccederOuCreerOption (String aLibelle, String aCode, String aIdent){

        long resultat = 0;
        String [] splitLibelle   = null;
        String [] splitCode      = null;
        String [] splitIdent     = null;
        String lOptionIdent      = "";
        String lOptionLibelle    = "";
        String lOptionCode       = "";
        String lPromotionIdent   = "";
        String lPromotionLibelle = "";
        String lPromotionCode    = "";

        try {
            aLibelle = aLibelle.replaceAll(">", "<"); //<Promotion>Option  // 1 2
            splitLibelle = aLibelle.split("<");       // Sous la syntaxe : <nom_du_diplôme>nom_de_l_option

            aCode = aCode.replaceAll(">", "<"); //<Promotion>Option  // 1 2
            splitCode = aCode.split("<");      // Sous la syntaxe : <code_du_diplôme>code_de_l_option

            aIdent = aIdent.replaceAll(">", "<"); //<Promotion>Option  // 1 2
            splitIdent = aIdent.split("<");       // Sous la syntaxe : <Ident_du_diplôme>Ident_de_l_option

            // Identifiant
            if (splitIdent.length   == 3){
                lOptionIdent    = splitIdent[2];           //Ident_de_l_option
                lPromotionIdent = splitIdent[1];           //Ident_du_diplôme
            }
            // Libelle
            if (splitLibelle.length == 3){
                lOptionLibelle    = splitLibelle[2];       //nom_de_l_option
                lPromotionLibelle = splitLibelle[1];       //nom_du_diplôme
            }
            // Code
            if (splitCode.length    == 3){
                lOptionCode    = splitCode[2];             //code_de_l_option
                lPromotionCode = splitCode[1];             //code_du_diplôme
            }

            try {
                if (!aIdent.equals("")){ // s'il y a un identifiant, on accede à l'option par l'identifiant
                    resultat = portTDOption.accederTDOptionParIdentifiant (lOptionIdent);
                    if (!lOptionLibelle.equals("")) // on modifie le libelle s'il est non vide
                        portTDOption.modifierNomTDOption  (resultat, lOptionLibelle);
                    if (!lOptionCode.equals(""))    // on modifie le code s'il est non vide
                        portTDOption.modifierCodeTDOption (resultat, lOptionCode);
                } else { // s'il n'y a pas d'identifiant, on accede a la promotion puis à l'option par code et libelle
                    long lPromotion = AccederOuCreerPromotion (lPromotionLibelle, lPromotionCode, lPromotionIdent);
                    resultat = portTDOption.accederOptionParPromotionNomEtCode(lPromotion, lOptionLibelle, lOptionCode);
                }
            } catch  (Exception e){
                try { // On cree l'option
                    long lPromotion = AccederOuCreerPromotion (lPromotionLibelle, lPromotionCode, lPromotionIdent);
                    resultat = portTDOption.creerOptionDeLaPromotionAvecIdentifiant(lPromotion, lOptionLibelle, lOptionCode, lOptionIdent);
                } catch  (Exception e2){
                    // L'identifiant est nouvellement défini mais l'option existe déjà dans la base
                    long lPromotion = AccederOuCreerPromotion (lPromotionLibelle, lPromotionCode, lPromotionIdent);
                    resultat = portTDOption.accederOptionParPromotionNomEtCode(lPromotion, lOptionLibelle, lOptionCode);
                    if (!aIdent.equals("")) // on modifie l'identifiant s'il est non vide
                        portTDOption.modifierIdentifiantTDOption (resultat, lOptionIdent);
                }
            }
        } catch  (Exception e){}
        return resultat;
    }
    
    public long AccederOuCreerEtudiant (String aNom, String aPrenom, String aDate, String aIdent){
        long resultat = 0;
	Date lDate;
        try { // on convertie la chaine en date
            DateFormat df = new SimpleDateFormat ("dd/MM/yyyy") ;
            lDate = df.parse(aDate);
        } catch (Exception e) {
            lDate = new Date ();
        }

        try {
            GregorianCalendar gDate = new GregorianCalendar();
            gDate.setTime(lDate);
            XMLGregorianCalendar xmlCalendar = DatatypeFactory.newInstance().newXMLGregorianCalendar(gDate);

            try {
                if (!aIdent.equals("")){ // s'il y a un identifiant
                    resultat = portEtudiant.accederEtudiantParIdentifiant(aIdent);
                    if (!aNom.equals("")) // on modifie le nom s'il est non vide
                        portEtudiant.modifierNomEtudiant(resultat, aNom);
                    if (!aPrenom.equals("")) // on modifie le prénom s'il est non vide
                        portEtudiant.modifierPrenomEtudiant(resultat, aPrenom);
                    if (!aDate.equals("")) // on modifie la date si elle est non vide
                        portEtudiant.modifierDateDeNaissanceEtudiant(resultat, xmlCalendar);
                } else { // s'il n'y a pas d'identifiant, on accède à l'étudiant par nom, prénom et date de naissance
                    resultat = portEtudiant.accederEtudiantsParNomPrenomEtDateDeNaissance(aNom, aPrenom, xmlCalendar).getTHpSvcWCleEtudiant().get(0);
                }
            } catch (Exception e1){
                try { // on essaye de créer l'étudiant
                    resultat = portEtudiant.creerEtudiantAvecIdentifiant (aNom, aPrenom, xmlCalendar, aIdent);
                } catch (Exception e2){
                    // L'identifiant est nouvellement défini mais l'étudiant existe déjà dans la base
                    try {
                        resultat = portEtudiant.accederEtudiantsParNomPrenomEtDateDeNaissance (aNom, aPrenom, xmlCalendar).getTHpSvcWCleEtudiant().get(0);
                        if (!aIdent.equals("")) // on modifie l'identifiant s'il est non vide
                            portEtudiant.modifierIdentifiantEtudiant (resultat, aIdent);
                    } catch (Exception e3) {
                        frame.EcrireDansZone("Import en cours... : La gestion des étudiants n'est pas active dans HYPERPLANNING.");
                    }
                }
            }
        } catch (Exception e){}
	return resultat;
    }

    public Boolean ColonnePromotionEstUnTD (String aLibelle, String aIdentifiant) {
        Boolean result = false;
        String [] splitLibelle = null;
        String [] splitIdent   = null;
	  
        try {
            aLibelle = aLibelle.replaceAll(">", "<"); //<Promotion><Partition>TD  // 1 3 4
            splitLibelle = aLibelle.split("<");

            aIdentifiant = aIdentifiant.replaceAll(">", "<"); //<Promotion><Partition>TD  // 1 3 4
            splitIdent = aIdentifiant.split("<");

            if (splitIdent.length == 5)   // si la chaine est sous la forme <ident_du_diplôme><partition>ident_du_Td
                result = true;
            if (splitLibelle.length == 5) // si la chaine est sous la forme <nom_du_diplôme><partition>nom_du_Td
                result = true;
        } catch (Exception e) {}
        return result;
    }

    public Boolean ColonnePromotionEstUneOption (String aLibelle, String aIdentifiant) {
        Boolean result = false;
        String [] splitLibelle = null;
        String [] splitIdent   = null;

        try {
            aLibelle = aLibelle.replaceAll(">", "<"); //<Promotion>Option  // 1 2
            splitLibelle = aLibelle.split("<");

            aIdentifiant = aIdentifiant.replaceAll(">", "<"); //<Promotion>Option  // 1 2
            splitIdent = aIdentifiant.split("<");

            if (splitIdent.length == 3)   // si la chaine est sous la forme <ident_du_diplôme>ident_de_l_option
                result = true;
            if (splitLibelle.length == 3) // si la chaine est sous la forme <nom_du_diplôme>nom_de_l_option
                result = true;
        } catch (Exception e) {}
        return result;
    }
    
    public int getImportEtudiants() {// retourne le nombre d'enseignant qui ont été importés
        String ligne;
        String [] split          = null;
        int resultat             = 0;
        int splitEleveIdent      = -1;
        int splitEleveNom        = -1;
        int splitElevePrenom     = -1;
        int splitEleveDate       = -1;
        int splitEleveProprio    = -1;
        int splitEleveMail       = -1;
        int splitPromotionIdent  = -1;
        int splitPromotionCode   = -1;
        int splitPromotionNom    = -1;
        int splitPromotionProprio= -1;
        int splitEleveNumNat     = -1;
        int splitEleveSexe       = -1;

        try {
            BufferedReader fichier = new BufferedReader (new FileReader(pathImport));
            // on initialise les numeros de colonne sur la premiere ligne
            if ((ligne = fichier.readLine()) != null) {
                ligne = ligne.replaceAll("\n", ";"); //Separateurs : ; ou , ou Tab
                ligne = ligne.replaceAll("\t", ";"); //Separateurs : ; ou , ou Tab
                split = ligne.split(";");            //Separateurs : ; ou , ou Tab

                for (int i= 0; i < split.length; i++) {
                    if (split [i].equalsIgnoreCase("IDENT_ETU"))
                        splitEleveIdent = i;
                    else if (split [i].equalsIgnoreCase("NOM_ETU"))
                        splitEleveNom = i;
                    else if (split [i].equalsIgnoreCase("PRENOM_ETU"))
                        splitElevePrenom = i;
                    else if (split [i].equalsIgnoreCase("DATE_ETU"))
                        splitEleveDate = i;
                    else if (split [i].equalsIgnoreCase("PROP_ETU"))
                        splitEleveProprio = i;
                    else if (split [i].equalsIgnoreCase("IDENT_DIP"))
                        splitPromotionIdent = i;
                    else if (split [i].equalsIgnoreCase("CODE_DIP"))
                        splitPromotionCode = i;
                    else if (split [i].equalsIgnoreCase("NOM_DIP"))
                        splitPromotionNom = i;
                    else if (split [i].equalsIgnoreCase("PROP_DIP"))
                        splitPromotionProprio = i;
                    else if (split [i].equalsIgnoreCase("NUMERONAT_ETU"))
                        splitEleveNumNat = i;
                    else if (split [i].equalsIgnoreCase("EMAIL_ETU"))
                        splitEleveMail = i;
                    else if (split [i].equalsIgnoreCase("SEXE_ETU"))
                        splitEleveSexe = i;
                }
            }

            while ((ligne = fichier.readLine()) != null) {  // Lit le fichier ligne par ligne
                ligne = ligne.replaceAll("\n", ";"); //Separateurs : ; ou , ou Tab
                ligne = ligne.replaceAll("\t", ";"); //Separateurs : ; ou , ou Tab
                split = ligne.split(";");            //Separateurs : ; ou , ou Tab
                try {
                    String etudiantIdent          = "";
                    String etudiantNom 	          = "";
                    String etudiantPrenom         = "";
                    String etudiantDate           = "";
                    String etudiantProprietaire   = "";
                    String etudiantNumero         = "";
                    String etudiantMail           = "";
                    String etudiantSexe           = "";
                    String PromotionIdent         = "";
                    String PromotionCode          = "";
                    String PromotionLibelle       = "";
                    String PromotionProprietaire  = "";

                    if ((splitEleveIdent     != -1) && (splitEleveIdent     < split.length))
                        etudiantIdent         = split [splitEleveIdent];
                    if ((splitEleveNom       != -1) && (splitEleveNom       < split.length))
                        etudiantNom 	      = split [splitEleveNom];
                    if ((splitElevePrenom    != -1) && (splitElevePrenom    < split.length))
                        etudiantPrenom 	      = split [splitElevePrenom];
                    if ((splitEleveDate      != -1) && (splitEleveDate      < split.length))
                        etudiantDate          = split [splitEleveDate];
                    if ((splitEleveProprio   != -1) && (splitEleveProprio   < split.length))
                        etudiantProprietaire  = split [splitEleveProprio];
                    if ((splitPromotionIdent != -1) && (splitPromotionIdent   < split.length))
                        PromotionIdent        = split [splitPromotionIdent];
                    if ((splitPromotionCode  != -1) && (splitPromotionCode    < split.length))
                        PromotionCode         = split [splitPromotionCode];
                    if ((splitPromotionNom   != -1) && (splitPromotionNom     < split.length))
                        PromotionLibelle      = split [splitPromotionNom];
                    if ((splitPromotionProprio!= -1) && (splitPromotionProprio < split.length))
                        PromotionProprietaire = split [splitPromotionProprio];
                    if ((splitEleveNumNat    != -1) && (splitEleveNumNat    < split.length))
                        etudiantNumero        = split [splitEleveNumNat];
                    if ((splitEleveMail      != -1) && (splitEleveMail      < split.length))
                        etudiantMail          = split [splitEleveMail];
                    if ((splitEleveSexe      != -1) && (splitEleveSexe      < split.length))
                        etudiantSexe          = split [splitEleveSexe];

	            long etudiantCourant = AccederOuCreerEtudiant (etudiantNom, etudiantPrenom, etudiantDate, etudiantIdent);

                    try { // Modification du proprietaire
                        if (splitEleveProprio      != -1)
                            if (!etudiantProprietaire.equals(""))
                                portEtudiant.modifierProprietaireEtudiant (etudiantCourant, etudiantProprietaire, "");
                    } catch (Exception e) {}
                    try { // Modification du numero national
                        if (splitEleveNumNat  != -1)
                            if (!etudiantNumero.equals(""))
                                portEtudiant.modifierNumeroDOrdreEtudiant(etudiantCourant, etudiantNumero);
                    } catch (Exception e) {}

                    try { // Modification de l'adresse mail
                        if (splitEleveMail     != -1)
                            if (!etudiantMail.equals(""))
                                portEtudiant.modifierEMailEtudiant (etudiantCourant, etudiantMail);
                    } catch (Exception e) {}
                    try { // Modification du sexe
                        if (splitEleveSexe != -1)
                            if (!etudiantSexe.equals(""))
                                portEtudiant.modifierSexeEtudiant (etudiantCourant, etudiantSexe);
                    } catch (Exception e) {}

                    if (ColonnePromotionEstUnTD(PromotionLibelle, PromotionIdent)) {	        // TD
                        long lPromotionCourante = AccederOuCreerTD(PromotionLibelle, PromotionCode, PromotionIdent);
                        try { // Modification du proprietaire
                            if (splitPromotionProprio      != -1)
                                if (!PromotionProprietaire.equals(""))
                                    portTDOption.modifierProprietaireTDOption (lPromotionCourante, PromotionProprietaire, "");
                        } catch (Exception e) {}
                        try { // Modification du TD de l'étudiant
                            portEtudiant.ajouterEtudiantATDOption (etudiantCourant, lPromotionCourante);
                        } catch (Exception e) {}
                    }else{  // option ou Promotion
                        if (ColonnePromotionEstUneOption(PromotionLibelle, PromotionIdent)) {	// option
                            long lPromotionCourante = AccederOuCreerOption (PromotionLibelle, PromotionCode, PromotionIdent);
                            try { // Modification du proprietaire
                                if (splitPromotionProprio      != -1)
                                    if (!PromotionProprietaire.equals(""))
                                        portTDOption.modifierProprietaireTDOption (lPromotionCourante, PromotionProprietaire, "");
                            } catch (Exception e) {}
                            try { // Modification du TD de l'étudiant
                                portEtudiant.ajouterEtudiantATDOption (etudiantCourant, lPromotionCourante);
                            } catch (Exception e) {}
                        }else{                                                            // Diplôme
                            long lPromotionCourante = AccederOuCreerPromotion (PromotionLibelle, PromotionCode, PromotionIdent);
                            try { // Modification du proprietaire
                                if (splitPromotionProprio      != -1)
                                    if (!PromotionProprietaire.equals(""))
                                        portPromotion.modifierProprietairePromotion (lPromotionCourante, PromotionProprietaire, "");
                            } catch (Exception e) {}
                            try { // Modification du diplôme de l'étudiant
                                portEtudiant.ajouterEtudiantALaPromotion(etudiantCourant, lPromotionCourante);
                            } catch (Exception e) {}
                        }
                    }
                    if (etudiantCourant != 0){
                        resultat++;
                        frame.EcrireDansZone ("Import des étudiants en cours... : " + resultat + " lignes importés");
                    }
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
