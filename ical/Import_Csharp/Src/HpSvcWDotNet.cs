using System;
using System.ServiceModel;
using HpSvcW.Authentification;
using HpSvcWDotNet.HpSvcW;

namespace HpSvcWDotNet {
  class TestHpSvcWDotNet {

	public UInt32 AccederOuCreerEnseignant (HpSvcWEnseignantsClient AConnexionEnseignants,
											string ANom,
											string APrenom,
											string ACode,
											string AIdent){

	  UInt32 Result = 0;
	  try {
		if (AIdent != ""){ // s'il y a un identifiant, on accède à l'enseignant par l'identifiant
		  Result = AConnexionEnseignants.AccederEnseignantParIdentifiant (AIdent);
		  if (ANom != "") // on modifie le nom s'il est non vide
			AConnexionEnseignants.ModifierNomEnseignant (Result, ANom);
		  if (APrenom != "") // on modifie le prénom s'il est non vide
			AConnexionEnseignants.ModifierPrenomEnseignant (Result, APrenom);
		  if (ACode != "") // on modifie le code s'il est non vide
			AConnexionEnseignants.ModifierCodeEnseignant (Result, ACode);
		} else { // s'il n'y a pas d'identifiant, on accède à l'enseignant par code, nom et prénom
		  Result = AConnexionEnseignants.AccederEnseignantParNomPrenomEtCode (ANom,
																			  APrenom,
																			  ACode);
		}
	  } catch {
		try { // on crée l'enseignant
		  Result = AConnexionEnseignants.CreerEnseignantAvecIdentifiant (ANom,
																		 APrenom,
																		 ACode,
																		 AIdent);
		} catch {
		  // L'identifiant est nouvellement défini mais l'enseignant existe déjà dans la base
		  Result = AConnexionEnseignants.AccederEnseignantParNomPrenomEtCode (ANom,
																			  APrenom,
																			  ACode);
		  if (AIdent != "") // on modifie l'identifiant s'il est non vide
			AConnexionEnseignants.ModifierIdentifiantEnseignant (Result, AIdent);
		}
	  }
	  return Result;
	}

	public UInt32 AccederOuCreerDiplome (HpSvcWPromotionsClient AConnexionPromotions,
										 string ALibelle,
										 string ACode,
										 string AIdent){

	  UInt32 Result = 0;
	  try {
		if (AIdent != ""){ // s'il y a un identifiant, on accède au diplôme par l'identifiant
		  Result = AConnexionPromotions.AccederPromotionParIdentifiant (AIdent);
		  if (ALibelle != "") // on modifie le libelle s'il est non vide
			AConnexionPromotions.ModifierNomPromotion (Result, ALibelle);
		  if (ACode != "") // on modifie le code s'il est non vide
			AConnexionPromotions.ModifierCodePromotion (Result, ACode);
		} else { // s'il n'y a pas d'identifiant, on accède au diplôme par code et libelle
		  Result = AConnexionPromotions.AccederPromotionParNomEtCode (ALibelle, ACode);
		}
	  } catch {
		try { // on crée le diplôme
		  Result = AConnexionPromotions.CreerPromotionAvecIdentifiant (ALibelle, ACode, AIdent);
		} catch {
		  // L'identifiant est nouvellement défini mais le diplôme existe déjà dans la base
		  Result = AConnexionPromotions.AccederPromotionParNomEtCode (ALibelle, ACode);
		  if (AIdent != "")// on modifie l'identifiant s'il est non vide
			AConnexionPromotions.ModifierIdentifiantPromotion (Result, AIdent);
		}
	  }
	  return Result;
	}

	public UInt32 AccederOuCreerPartition (HpSvcWTDOptionsClient AConnexionTDOptions,
										   UInt32 ADiplome,
										   string ALibelle){

	  UInt32 Result = 0;
	  try { // On accede à la partition par diplôme et libelle
		Result = AConnexionTDOptions.AccederPartitionParPromotionEtNom (ADiplome, ALibelle);
	  } catch {
		try { // sinon on la crée
		  Result = AConnexionTDOptions.CreerPartitionDeLaPromotion (ADiplome, ALibelle);
		} catch {}
	  }
	  return Result;
	}

	public UInt32 AccederOuCreerTD (HpSvcWTDOptionsClient AConnexionTD,
                                    HpSvcWPromotionsClient AConnexionDiplome,
									string ALibelle,
									string ACode,
									string AIdent){

	  UInt32 Result = 0;
	  string delimStr = "<>"; //<Diplome><Partition>TD  // 1 3 4
	  string [] splitLibelle   = null;
	  string [] splitCode      = null;
	  string [] splitIdent     = null;
	  char [] delimiter        = delimStr.ToCharArray();
	  string LTDIdent          = "";
	  string LTDLibelle        = "";
	  string LTDCode           = "";
	  string LPartitionLibelle = "";
	  string LDiplomeIdent     = "";
	  string LDiplomeLibelle   = "";
	  string LDiplomeCode      = "";

	  try {
		splitLibelle = ALibelle.Split (delimiter); // Sous la syntaxe : <nom_du_diplôme><Partition>nom_du_td
		splitCode    = ACode.Split (delimiter);    // Sous la syntaxe : <code_du_diplôme><Partition>code_du_td
		splitIdent   = AIdent.Split (delimiter);   // Sous la syntaxe : <ident_du_diplôme><Partition>ident_du_td

		if (splitIdent.Length   == 5){
		  LTDIdent      = splitIdent[4];           // ident_du_td
		  LDiplomeIdent = splitIdent[1];           // ident_du_diplôme
		}
		if (splitLibelle.Length == 5){
		  LTDLibelle        = splitLibelle[4];     // nom_du_td
		  LDiplomeLibelle   = splitLibelle[1];     // nom_du_diplôme
		  LPartitionLibelle = splitLibelle[3];     // partition
		}
		if (splitCode.Length    == 5){
		  LTDCode      = splitCode[4];             // code_du_td
		  LDiplomeCode = splitCode[1];             // code_du_diplôme
		}

		try {
		  if (AIdent != ""){  // s'il y a un identifiant, on accède au TD par l'identifiant
			Result = AConnexionTD.AccederTDOptionParIdentifiant (LTDIdent);
			if (LTDLibelle != "") // on modifie le libelle s'il est non vide
			  AConnexionTD.ModifierNomTDOption  (Result, LTDLibelle);
			if (LTDCode != "") // on modifie le code s'il est non vide
			  AConnexionTD.ModifierCodeTDOption (Result, LTDCode);
		  } else { // s'il n'y a pas d'identifiant, on accede au diplome, à la partition puis au TD par code et libelle
			UInt32 LDiplome = AccederOuCreerDiplome (AConnexionDiplome,
													 LDiplomeLibelle,
													 LDiplomeCode,
													 LDiplomeIdent);
			UInt32 LPartition = AccederOuCreerPartition (AConnexionTD,
														 LDiplome,
														 LPartitionLibelle);
			Result = AConnexionTD.AccederTDParPartitionNomEtCode (LPartition,
																  LTDLibelle,
																  LTDCode);
		  }
		} catch {
		  try { // on cree le TD
			UInt32 LDiplome = AccederOuCreerDiplome (AConnexionDiplome,
													 LDiplomeLibelle,
													 LDiplomeCode,
													 LDiplomeIdent);
			UInt32 LPartition = AccederOuCreerPartition (AConnexionTD,
														 LDiplome,
														 LPartitionLibelle);
			Result = AConnexionTD.CreerTDAvecIdentifiant (LPartition,
														  LTDLibelle,
														  LTDCode,
														  LTDIdent);
		  } catch {
			// L'identifiant est nouvellement défini mais le TD existe déjà dans la base
			UInt32 LDiplome = AccederOuCreerDiplome (AConnexionDiplome,
													 LDiplomeLibelle,
													 LDiplomeCode,
													 LDiplomeIdent);
			UInt32 LPartition = AccederOuCreerPartition (AConnexionTD,
														 LDiplome,
														 LPartitionLibelle);
			Result = AConnexionTD.AccederTDParPartitionNomEtCode (LPartition,
																  LTDLibelle,
																  LTDCode);
			if (AIdent != "") // on modifie l'identifiant s'il est non vide
			 AConnexionTD.ModifierIdentifiantTDOption (Result, LTDIdent);
		  }
		}
	  } catch {}
	  return Result;
	}

	public UInt32 AccederOuCreerOption(HpSvcWTDOptionsClient AConnexionTD,
                                        HpSvcWPromotionsClient AConnexionDiplome,
										string ALibelle,
										string ACode,
										string AIdent){

	  UInt32 Result = 0;
	  string delimStr = "<>"; //<Diplome>Option  // 1 2
	  string [] splitLibelle = null;
	  string [] splitCode    = null;
	  string [] splitIdent   = null;
	  char [] delimiter      = delimStr.ToCharArray();
	  string LOptionIdent    = "";
	  string LOptionLibelle  = "";
	  string LOptionCode     = "";
	  string LDiplomeIdent   = "";
	  string LDiplomeLibelle = "";
	  string LDiplomeCode    = "";

	  try {
		splitLibelle = ALibelle.Split (delimiter); // Sous la syntaxe : <nom_du_diplôme>nom_de_l_option
		splitCode    = ACode.Split (delimiter);    // Sous la syntaxe : <code_du_diplôme>code_de_l_option
		splitIdent   = AIdent.Split (delimiter);   // Sous la syntaxe : <Ident_du_diplôme>Ident_de_l_option

		// Identifiant
		if (splitIdent.Length   == 3){
		  LOptionIdent  = splitIdent[2];           //Ident_de_l_option
		  LDiplomeIdent = splitIdent[1];           //Ident_du_diplôme
		}
		// Libelle
		if (splitLibelle.Length == 3){
		  LOptionLibelle  = splitLibelle[2];       //nom_de_l_option
		  LDiplomeLibelle = splitLibelle[1];       //nom_du_diplôme
		}
		// Code
		if (splitCode.Length    == 3){
		  LOptionCode  = splitCode[2];             //code_de_l_option
		  LDiplomeCode = splitCode[1];             //code_du_diplôme
		}

	    try {
		  if (AIdent != ""){ // s'il y a un identifiant, on accede à l'option par l'identifiant
			Result = AConnexionTD.AccederTDOptionParIdentifiant (LOptionIdent);
			if (LOptionLibelle != "") // on modifie le libelle s'il est non vide
			  AConnexionTD.ModifierNomTDOption  (Result, LOptionLibelle);
			if (LOptionCode != "")    // on modifie le code s'il est non vide
			  AConnexionTD.ModifierCodeTDOption (Result, LOptionCode);
		  } else { // s'il n'y a pas d'identifiant, on accede au diplome puis à l'option par code et libelle
			UInt32 LDiplome = AccederOuCreerDiplome (AConnexionDiplome,
													 LDiplomeLibelle,
													 LDiplomeCode,
													 LDiplomeIdent);
			Result = AConnexionTD.AccederOptionParPromotionNomEtCode (LDiplome, LOptionLibelle, LOptionCode);
		  }
		} catch {
		  try { // On cree l'option
			UInt32 LDiplome = AccederOuCreerDiplome (AConnexionDiplome,
													 LDiplomeLibelle,
													 LDiplomeCode,
													 LDiplomeIdent);
			Result = AConnexionTD.CreerOptionDeLaPromotionAvecIdentifiant (LDiplome, LOptionLibelle, LOptionCode, LOptionIdent);
		  } catch {
			// L'identifiant est nouvellement défini mais l'option existe déjà dans la base
			UInt32 LDiplome = AccederOuCreerDiplome (AConnexionDiplome,
													 LDiplomeLibelle,
													 LDiplomeCode,
													 LDiplomeIdent);
			Result = AConnexionTD.AccederOptionParPromotionNomEtCode (LDiplome, LOptionLibelle, LOptionCode);
			if (AIdent != "") // on modifie l'identifiant s'il est non vide
			 AConnexionTD.ModifierIdentifiantTDOption (Result, LOptionIdent);
		  }
		}
	  } catch {}
	  return Result;
	}

	public UInt32 AccederOuCreerEtudiant (HpSvcWEtudiantsClient AConnexionEtudiants,
										  string ANom,
										  string APrenom,
										  string ADate,
										  string AIdent){

	  UInt32 Result = 0;
      DateTime LDate;
	  try { // on convertie la chaine en date
		LDate = Convert.ToDateTime (ADate);
	  } catch {
	    // Date par défaut dans HP
		LDate = DateTime.MinValue.Date.AddYears(1898);
	  }
	  try {
		if (AIdent != ""){   // s'il y a un identifiant
		  Result = AConnexionEtudiants.AccederEtudiantParIdentifiant (AIdent);
		  if (ANom != "")    // on modifie le nom s'il est non vide
			AConnexionEtudiants.ModifierNomEtudiant (Result, ANom);
		  if (APrenom != "") // on modifie le prénom s'il est non vide
			AConnexionEtudiants.ModifierPrenomEtudiant (Result, APrenom);
		  if (ADate != "")   // on modifie la date de naissance si elle est non vide
			AConnexionEtudiants.ModifierDateDeNaissanceEtudiant (Result, LDate.ToString("o"));
		} else { // s'il n'y a pas d'identifiant, on accède à l'étudiant par nom, prénom et date de naissance
			Result = AConnexionEtudiants.AccederEtudiantsParNomPrenomEtDateDeNaissance (ANom, APrenom, LDate.ToString("o")) [0];
		}
	  } catch {
		try { // on essaye de créer l'étudiant
		  Result = AConnexionEtudiants.CreerEtudiantAvecIdentifiant (ANom, APrenom, LDate.ToString("o"), AIdent);
		} catch {
		  // L'identifiant est nouvellement défini mais l'étudiant existe déjà dans la base
		  Result = AConnexionEtudiants.AccederEtudiantsParNomPrenomEtDateDeNaissance (ANom, APrenom, LDate.ToString("o")) [0];
		  if (AIdent != "") // on modifie l'identifiant s'il est non vide
			AConnexionEtudiants.ModifierIdentifiantEtudiant (Result, AIdent);
		}
	  }
	  return Result;
	}

	public Boolean ColonneDiplomeEstUnTD (String ALibelle, String AIdentifiant) {
	  Boolean Result = false;

	  string delimStr = "<>"; //<Diplome><Partition>TD  // 1 3 4

	  string [] splitLibelle = null;
	  string [] splitIdent   = null;
	  char [] delimiter = delimStr.ToCharArray();

	  try {
		splitLibelle = ALibelle.Split (delimiter);
		splitIdent   = AIdentifiant.Split (delimiter);

		if (splitIdent.Length == 5)   // si la chaine est sous la forme <ident_du_diplôme><partition>ident_du_Td
		  Result = true;
		if (splitLibelle.Length == 5) // si la chaine est sous la forme <nom_du_diplôme><partition>nom_du_Td
		  Result = true;
	  } catch {}
	  return Result;
	}

	public Boolean ColonneDiplomeEstUneOption (String ALibelle, String AIdentifiant) {
	  Boolean Result = false;

	  string delimStr = "<>"; //<Diplome>Option  // 1 2

	  string [] splitLibelle = null;
	  string [] splitIdent   = null;
	  char [] delimiter = delimStr.ToCharArray();

	  try {
		splitLibelle = ALibelle.Split (delimiter);
		splitIdent   = AIdentifiant.Split (delimiter);

		if (splitIdent.Length == 3)   // si la chaine est sous la forme <ident_du_diplôme>ident_de_l_option
		  Result = true;
		if (splitLibelle.Length == 3) // si la chaine est sous la forme <nom_du_diplôme>nom_de_l_option
		  Result = true;
	  } catch {}
	  return Result;
	}

	public void MajEtudiants(HpSvcWEtudiantsClient AConnexionEtudiants, HpSvcWPromotionsClient AConnexionPromotions, HpSvcWTDOptionsClient AConnexionTDOptions){
	  int counter = 0;
	  string line;
	  string EtudiantIdent;
	  string EtudiantNom;
	  string EtudiantPrenom;
	  string EtudiantDate;
	  string EtudiantProprietaire;
	  string EtudiantNumero;
	  string EtudiantMail;
	  string EtudiantSexe;
	  string DiplomeIdent;
	  string DiplomeCode;
	  string DiplomeLibelle;
	  string DiplomeProprietaire;
	  string delimStr = ";,	"; //Separateurs : ; ou , ou Tab
	  string [] split = null;
	  int SplitEleveIdent    = -1;
	  int SplitEleveNom      = -1;
	  int SplitElevePrenom   = -1;
	  int SplitEleveDate     = -1;
	  int SplitEleveProprio  = -1;
	  int SplitDiplomeIdent  = -1;
	  int SplitDiplomeCode   = -1;
	  int SplitDiplomeNom    = -1;
	  int SplitDiplomeProprio= -1;
	  int SplitEleveNumNat   = -1;
	  int SplitEleveMail     = -1;
	  int SplitEleveSexe     = -1;
	  char [] delimiter = delimStr.ToCharArray();
	  UInt32 EtudiantCourant;
	  UInt32 DiplomeCourant;

	  // Lit le fichier ligne par ligne
	  try {
		 System.IO.StreamReader file = new System.IO.StreamReader (".\\MiseAJourEtudiant.txt",
																   System.Text.Encoding.Default);
		// on initialise les numeros de colonne sur la premiere ligne
		if ((line = file.ReadLine()) != null) {
		  split = line.Split (delimiter);
		  for (int i= 0; i < split.Length; i++) {
			switch (split [i].ToUpper())  {
			  case "IDENT_ETU"     : SplitEleveIdent = i;
			  break;
			  case "NOM_ETU"       : SplitEleveNom = i;
			  break;
			  case "PRENOM_ETU"    : SplitElevePrenom = i;
			  break;
			  case "DATE_ETU"      : SplitEleveDate = i;
			  break;
			  case "PROP_ETU"      : SplitEleveProprio = i;
			  break;
			  case "IDENT_DIP"     : SplitDiplomeIdent = i;
			  break;
			  case "CODE_DIP"      : SplitDiplomeCode = i;
			  break;
			  case "NOM_DIP"       : SplitDiplomeNom = i;
			  break;
			  case "PROP_DIP"      : SplitDiplomeProprio = i;
			  break;
			  case "NUMERONAT_ETU" : SplitEleveNumNat = i;
			  break;
			  case "EMAIL_ETU"     : SplitEleveMail = i;
			  break;
			  case "SEXE_ETU"      : SplitEleveSexe = i;
			  break;
			}
		  }
		}

		while ((line = file.ReadLine()) != null) {
		  split = line.Split (delimiter);
		  try {
			EtudiantIdent        = "";
			EtudiantNom 	     = "";
			EtudiantPrenom       = "";
			EtudiantDate         = "";
			EtudiantProprietaire = "";
			DiplomeIdent         = "";
			DiplomeCode          = "";
			DiplomeLibelle       = "";
			DiplomeProprietaire  = "";
			EtudiantNumero       = "";
			EtudiantMail         = "";
			EtudiantSexe         = "";
			if (SplitEleveIdent     != -1)
			EtudiantIdent            = split[SplitEleveIdent];
			if (SplitEleveNom       != -1)
			EtudiantNom 	         = split[SplitEleveNom];
			if (SplitElevePrenom    != -1)
			EtudiantPrenom           = split[SplitElevePrenom];
			if (SplitEleveDate      != -1)
			EtudiantDate             = split[SplitEleveDate];
			if (SplitEleveProprio   != -1)
			EtudiantProprietaire     = split[SplitEleveProprio];
			if (SplitDiplomeIdent   != -1)
			DiplomeIdent             = split[SplitDiplomeIdent];
			if (SplitDiplomeCode    != -1)
			DiplomeCode              = split[SplitDiplomeCode];
			if (SplitDiplomeNom     != -1)
			DiplomeLibelle           = split[SplitDiplomeNom];
			if (SplitDiplomeProprio != -1)
			DiplomeProprietaire      = split[SplitDiplomeProprio];
			if (SplitEleveNumNat    != -1)
			EtudiantNumero           = split[SplitEleveNumNat];
			if (SplitEleveMail      != -1)
			EtudiantMail             = split[SplitEleveMail];
			if (SplitEleveSexe      != -1)
			EtudiantSexe             = split[SplitEleveSexe];

			// Etudiant
			EtudiantCourant = AccederOuCreerEtudiant (AConnexionEtudiants, EtudiantNom, EtudiantPrenom, EtudiantDate, EtudiantIdent);
			try { // Modification du proprietaire
			  if (SplitEleveProprio      != -1)
				if (EtudiantProprietaire != "")
  				  AConnexionEtudiants.ModifierProprietaireEtudiant (EtudiantCourant, EtudiantProprietaire, "");
			} catch {}
			try { // Modification du numero national
			  if (SplitEleveNumNat      != -1)
				if (EtudiantNumero != "")
				  AConnexionEtudiants.ModifierNumeroDOrdreEtudiant (EtudiantCourant, EtudiantNumero);
			} catch {}
			try { // Modification de l'E-Mail
			  if (SplitEleveMail      != -1)
				if (EtudiantMail != "")
				  AConnexionEtudiants.ModifierEMailEtudiant (EtudiantCourant, EtudiantMail);
			} catch {}
			try { // Modification du sexe
			  if (SplitEleveSexe      != -1)
				if (EtudiantSexe != "")
				  AConnexionEtudiants.ModifierSexeEtudiant (EtudiantCourant, EtudiantSexe);
			} catch {}

			if (ColonneDiplomeEstUnTD (DiplomeLibelle, DiplomeIdent)) {	        // TD
			  DiplomeCourant = AccederOuCreerTD (AConnexionTDOptions, AConnexionPromotions, DiplomeLibelle, DiplomeCode, DiplomeIdent);
			  try { // Modification du proprietaire
				if (SplitDiplomeProprio      != -1)
				  if (DiplomeProprietaire != "")
				  AConnexionTDOptions.ModifierProprietaireTDOption (DiplomeCourant, DiplomeProprietaire, "");
			  } catch {}

			  try { // Modification du TD de l'étudiant
				AConnexionEtudiants.AjouterEtudiantATDOption (EtudiantCourant, DiplomeCourant);
			  } catch {}
			}else{  // option ou diplome
			  if (ColonneDiplomeEstUneOption (DiplomeLibelle, DiplomeIdent)) {	// option
				DiplomeCourant = AccederOuCreerOption (AConnexionTDOptions, AConnexionPromotions, DiplomeLibelle, DiplomeCode, DiplomeIdent);
				try { // Modification du proprietaire
				  if (SplitDiplomeProprio      != -1)
					if (DiplomeProprietaire != "")
					  AConnexionTDOptions.ModifierProprietaireTDOption (DiplomeCourant, DiplomeProprietaire , "");
				} catch {}

				try { // Modification du TD de l'étudiant
				  AConnexionEtudiants.AjouterEtudiantATDOption (EtudiantCourant, DiplomeCourant);
				} catch {}
			  }else{                                                            // Diplôme
				DiplomeCourant = AccederOuCreerDiplome (AConnexionPromotions, DiplomeLibelle, DiplomeCode, DiplomeIdent);
				try { // Modification du proprietaire
				  if (SplitDiplomeProprio      != -1)
					if (DiplomeProprietaire != "")
				      AConnexionPromotions.ModifierProprietairePromotion (DiplomeCourant, DiplomeProprietaire, "");
				} catch {}

				try { // Modification du diplôme de l'étudiant
				  AConnexionEtudiants.AjouterEtudiantALaPromotion (EtudiantCourant, DiplomeCourant);
				} catch {}
			  }
			}
			counter++;
		  } catch {}
		}
		Console.WriteLine ("Mise à jour des étudiants éffectuée (" + counter + " lignes lues).");

		file.Close();
	  } catch {
		Console.WriteLine ("Impossible de trouver le fichier concernant les étudiants : '.\\MiseAJourEtudiant.txt'");
	  }
	}

	public void MajEnseignants (HpSvcWEnseignantsClient AConnexionEnseignants){
	  int counter = 0;
	  string line;
	  string EnseignantIdent;
	  string EnseignantCode;
	  string EnseignantNom;
	  string EnseignantPrenom;
	  string EnseignantDate;
	  string EnseignantProprietaire;
	  string EnseignantMail;
	  string EnseignantCivilite;
	  string EnseignantAdresse1;
	  string EnseignantAdresse2;
	  string EnseignantCodePostal;
	  string EnseignantVille;
	  string delimStr = ";,	"; //Separateurs : ; ou , ou Tab
	  string [] split = null;
	  int SplitProfIdent    = -1;
	  int SplitProfCode     = -1;
	  int SplitProfNom      = -1;
	  int SplitProfPrenom   = -1;
	  int SplitProfDate     = -1;
	  int SplitProfProprio  = -1;
	  int SplitProfMail     = -1;
	  int SplitProfCivilite = -1;
	  int SplitProfAdr1     = -1;
	  int SplitProfAdr2     = -1;
	  int SplitProfCodePost = -1;
	  int SplitProfVille    = -1;
	  char [] delimiter = delimStr.ToCharArray();
	  DateTime LDate;
	  UInt32 EnseignantCourant;

	  // Lit le fichier ligne par ligne
	  try {
		System.IO.StreamReader file = new System.IO.StreamReader(".\\MiseAJourEnseignant.txt",
																 System.Text.Encoding.Default);
		// on initialise les numeros de colonne sur la premiere ligne
		if ((line = file.ReadLine()) != null) {
		  split = line.Split (delimiter);
		  for (int i= 0; i < split.Length; i++) {
			switch (split [i].ToUpper())  {
			  case "IDENT_ENS"      : SplitProfIdent = i;
			  break;
			  case "CODE_ENS"       : SplitProfCode = i;
			  break;
			  case "NOM_ENS"        : SplitProfNom = i;
			  break;
			  case "PRENOM_ENS"     : SplitProfPrenom = i;
			  break;
			  case "DATE_ENS"       : SplitProfDate = i;
			  break;
			  case "PROP_ENS"       : SplitProfProprio = i;
			  break;
			  case "EMAIL_ENS"      : SplitProfMail = i;
			  break;
			  case "CIV_ENS"        : SplitProfCivilite = i;
			  break;
			  case "ADR1_ENS"       : SplitProfAdr1 = i;
			  break;
			  case "ADR2_ENS"       : SplitProfAdr2 = i;
			  break;
			  case "CODEPOSTAL_ENS" : SplitProfCodePost = i;
			  break;
			  case "VILLE_ENS"      : SplitProfVille = i;
			  break;
			}
		  }
		}
		// on lit les données
		while ((line = file.ReadLine()) != null) {
		  split = line.Split (delimiter);
		  try {
			EnseignantIdent        = "";
			EnseignantCode 	       = "";
			EnseignantNom 	       = "";
			EnseignantPrenom       = "";
			EnseignantDate         = "";
			EnseignantProprietaire = "";
			EnseignantMail         = "";
			EnseignantCivilite     = "";
			EnseignantAdresse1     = "";
			EnseignantAdresse2     = "";
			EnseignantCodePostal   = "";
			EnseignantVille        = "";
			if (SplitProfIdent    != -1)
			EnseignantIdent        = split [SplitProfIdent];
			if (SplitProfCode     != -1)
			EnseignantCode 	       = split [SplitProfCode];
			if (SplitProfNom      != -1)
			EnseignantNom 	       = split [SplitProfNom];
			if (SplitProfPrenom   != -1)
			EnseignantPrenom       = split [SplitProfPrenom];
			if (SplitProfDate     != -1)
			EnseignantDate         = split [SplitProfDate];
			if (SplitProfProprio  != -1)
			EnseignantProprietaire = split [SplitProfProprio];
			if (SplitProfMail     != -1)
			EnseignantMail         = split [SplitProfMail];
			if (SplitProfCivilite != -1)
			EnseignantCivilite     = split [SplitProfCivilite];
			if (SplitProfAdr1     != -1)
			EnseignantAdresse1     = split [SplitProfAdr1];
			if (SplitProfAdr2     != -1)
			EnseignantAdresse2     = split [SplitProfAdr2];
			if (SplitProfCodePost != -1)
			EnseignantCodePostal   = split [SplitProfCodePost];
			if (SplitProfVille    != -1)
			EnseignantVille        = split [SplitProfVille];

			EnseignantCourant = AccederOuCreerEnseignant (AConnexionEnseignants,
														  EnseignantNom,
														  EnseignantPrenom,
														  EnseignantCode,
														  EnseignantIdent);
			try { // Modification de la date de naissance
			  if (SplitProfDate     != -1)
				if (EnseignantDate != "") {
				  LDate = Convert.ToDateTime (EnseignantDate);
				  AConnexionEnseignants.ModifierDateDeNaissanceEnseignant(EnseignantCourant, LDate.ToString("o"));
				}
			} catch {}
			try { // Modification du propriétaire
			  if (SplitProfProprio  != -1)
				if (EnseignantProprietaire != "")
				  AConnexionEnseignants.ModifierProprietaireEnseignant  (EnseignantCourant,
																		 EnseignantProprietaire, "");
			} catch {}
			try { // Modification de l'adresse mail
			  if (SplitProfMail     != -1)
				if (EnseignantMail != "")
				  AConnexionEnseignants.ModifierEMailEnseignant  (EnseignantCourant,
																  EnseignantMail);
			} catch {}
			try { // Modification de la civilité
			  if (SplitProfCivilite != -1)
				if (EnseignantCivilite != "")
				  AConnexionEnseignants.ModifierCiviliteEnseignant  (EnseignantCourant,
																	 EnseignantCivilite);
			} catch {}
			try { // Modification de l'adresse 1
			  if (SplitProfAdr1 != -1)
				if (EnseignantAdresse1 != "")
				  AConnexionEnseignants.ModifierAdresse1Enseignant  (EnseignantCourant,
																	 EnseignantAdresse1);
			} catch {}
			try { // Modification de l'adresse 2
			  if (SplitProfAdr2 != -1)
				if (EnseignantAdresse2 != "")
				  AConnexionEnseignants.ModifierAdresse2Enseignant  (EnseignantCourant,
									   							     EnseignantAdresse2);
			} catch {}
			try { // Modification du code postal
			  if (SplitProfCodePost != -1)
				if (EnseignantCodePostal != "")
				  AConnexionEnseignants.ModifierCodePostalEnseignant  (EnseignantCourant,
																       EnseignantCodePostal);
			} catch {}
			try { // Modification de la ville
			  if (SplitProfVille  != -1)
				if (EnseignantVille != "")
				  AConnexionEnseignants.ModifierVilleEnseignant  (EnseignantCourant,
																  EnseignantVille);
			} catch {}
			counter++;
		  } catch {}
		}
		Console.WriteLine ("Mise à jour des enseignants éffectuée (" + counter + " lignes lues).");

		file.Close();
	  } catch {
		Console.WriteLine ("Impossible de trouver le fichier concernant les enseignants : '.\\MiseAJourEnseignant.txt'");
	  }
	}

	static void Main (string[] args) {
	  String StrAdresse;
	  String StrPort;
      String StrRacine;
      String StrLogin;
	  String StrMDP;
	  if (args.Length < 4) {
        Console.WriteLine ("Exemple C# V 1.4");
        Console.WriteLine ("----------------");
        Console.WriteLine ("");
		Console.WriteLine ("Connexion à HYPERPLANNING Service WEB");
		Console.WriteLine ("-------------------------------------");
		Console.WriteLine ("");
		Console.WriteLine ("Saisir l'adresse du service web puis appuyer sur <enter> :");
		StrAdresse  = Console.ReadLine();
		Console.WriteLine ("");
		Console.WriteLine ("Saisir le port d'écoute du service web puis appuyer sur <enter> :");
		StrPort  = Console.ReadLine();
        Console.WriteLine("");
        Console.WriteLine("Saisir la racine du service web puis appuyer sur <enter> :");
        StrRacine = Console.ReadLine();
        Console.WriteLine("");
		Console.WriteLine ("Saisir le login puis appuyer sur <enter> :");
		StrLogin  = Console.ReadLine();
		Console.WriteLine ("");
		Console.WriteLine ("Saisir le mot de passe puis appuyer sur <enter> :");
		StrMDP    = Console.ReadLine();
	  } else {
		StrAdresse  = args[0];
		StrPort     = args[1];
        StrRacine   = args[2];
        StrLogin    = args[3];
		StrMDP      = args[4];
	  }
	  Console.WriteLine ("");
	  Console.WriteLine ("--------------------------------------------------");
	  Console.WriteLine ("");

	  string URLSvcW = "http://" + StrAdresse + ":" + StrPort + "/" + StrRacine;
	  try {
        AuthentificationHpSvcW lAuthentification = new AuthentificationHpSvcW(StrLogin, StrMDP);
        // Interfaces utilisées
        HpSvcWAdminClient       lAdmin       = new HpSvcWAdminClient();
        HpSvcWEtudiantsClient   lEtudiants   = new HpSvcWEtudiantsClient();
        HpSvcWPromotionsClient  lPromotions  = new HpSvcWPromotionsClient();
        HpSvcWEnseignantsClient lEnseignants = new HpSvcWEnseignantsClient();
        HpSvcWTDOptionsClient   lTDOptions   = new HpSvcWTDOptionsClient();

        // Authentification
        lAdmin.Endpoint.Behaviors.Add(lAuthentification);
        lEtudiants.Endpoint.Behaviors.Add(lAuthentification);
        lPromotions.Endpoint.Behaviors.Add(lAuthentification);
        lEnseignants.Endpoint.Behaviors.Add(lAuthentification);
        lTDOptions.Endpoint.Behaviors.Add(lAuthentification);

        // Modification de l'adresse IP et du port de connexion
        string lAdresseAdmin      = lAdmin.Endpoint.Address.ToString();
        string lAdresseEtudiant   = lEtudiants.Endpoint.Address.ToString();
        string lAdressePromotion  = lPromotions.Endpoint.Address.ToString();
        string lAdresseEnseignant = lEnseignants.Endpoint.Address.ToString();
        string lAdresseTDOption   = lTDOptions.Endpoint.Address.ToString();
        lAdmin.Endpoint.Address       = new EndpointAddress(URLSvcW + lAdresseAdmin.Substring(lAdresseAdmin.LastIndexOf("/")));
        lEtudiants.Endpoint.Address   = new EndpointAddress(URLSvcW + lAdresseEtudiant.Substring(lAdresseEtudiant.LastIndexOf("/")));
        lPromotions.Endpoint.Address  = new EndpointAddress(URLSvcW + lAdressePromotion.Substring(lAdressePromotion.LastIndexOf("/")));
        lEnseignants.Endpoint.Address = new EndpointAddress(URLSvcW + lAdresseEnseignant.Substring(lAdresseEnseignant.LastIndexOf("/")));
        lTDOptions.Endpoint.Address   = new EndpointAddress(URLSvcW + lAdresseTDOption.Substring(lAdresseTDOption.LastIndexOf("/")));

		//Affichage de la version
		Console.WriteLine (lAdmin.Version () + " connecté");
		Console.WriteLine ("");
		Console.WriteLine ("--------------------------------------------------");
		Console.WriteLine ("");

		TestHpSvcWDotNet SWeb = new TestHpSvcWDotNet ();
		SWeb.MajEnseignants (lEnseignants);
		SWeb.MajEtudiants (lEtudiants, lPromotions, lTDOptions);
	  } catch {
		Console.WriteLine ("Le service web d'Hyperplanning n'a pas pu être trouvé.");
		Console.WriteLine ("Veuillez vérifier : ");
		Console.WriteLine ("- que le planning est publié par le service web d'Hyperplanning");
		Console.WriteLine ("- login et mot de passe (ceux de l'utilisateur ayant démaré le service web)");
		Console.WriteLine ("- les paramètres de communication (URL du service web : " + URLSvcW + ")");
	  }
	  Console.WriteLine ("");
	  Console.WriteLine ("Appuyer sur <enter> pour finir le programme...");
	  Console.ReadLine();
	}
  }
}


