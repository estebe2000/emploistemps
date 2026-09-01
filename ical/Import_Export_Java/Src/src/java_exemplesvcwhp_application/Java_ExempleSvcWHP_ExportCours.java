package java_exemplesvcwhp_application;

import java.util.Date;
import java.util.List;
import java.io.BufferedWriter;
import java.io.FileWriter;
import com.indexeducation.frahtm.hpsvcw.IHpSvcWEnseignants;
import com.indexeducation.frahtm.hpsvcw.IHpSvcWMatieres;
import com.indexeducation.frahtm.hpsvcw.IHpSvcWPromotions;
import com.indexeducation.frahtm.hpsvcw.IHpSvcWCours;
import com.indexeducation.frahtm.hpsvcw.THpSvcWTableauClesEnseignants;
import java.util.GregorianCalendar;
import javax.xml.datatype.DatatypeFactory;
import javax.xml.datatype.XMLGregorianCalendar;

public class Java_ExempleSvcWHP_ExportCours {
    Java_ExempleSvcWHP_View frame;
    IHpSvcWCours            portCours;
    IHpSvcWMatieres         portMatiere;
    IHpSvcWEnseignants      portEnseignant;
    IHpSvcWPromotions       portPromotion;
    Date                    dateDebut;
    Date                    dateFin;
    String                  pathExport;
    String                  separateur;

    public Java_ExempleSvcWHP_ExportCours(Java_ExempleSvcWHP_View aFrame,
                                          IHpSvcWCours            aPortCours,
                                          IHpSvcWMatieres         aPortMatiere,
                                          IHpSvcWEnseignants      aPortEnseignant,
                                          IHpSvcWPromotions       aPortPromotion,
                                          Date                    aDateDebut,
                                          Date                    aDateFin,
                                          String                  aSeparateur,
                                          String                  aPath) {
        portCours      = aPortCours;
        portMatiere    = aPortMatiere;
        portEnseignant = aPortEnseignant;
        portPromotion  = aPortPromotion;
        dateDebut      = aDateDebut;
        dateFin        = aDateFin;
        pathExport     = aPath;
        frame          = aFrame;
        separateur     = aSeparateur;
    }

    public String AjouterElementAChaine (String chaine, String element) {
        String resultat = chaine;
        // Si la chaine est non vide, on sépare par une virgule
        if (resultat.compareTo("") != 0) {
            resultat = resultat + ", ";
        }
        return resultat + element;
    }

    // Affiche la durée sous forme XXHXX
    public String getChaineDuree (Double dureeAAfficher){
        Double dty = dureeAAfficher * 24;
        Integer heure = dty.intValue();
        Double dtz = (dty - heure) * 60;
        Integer minute = (dtz).intValue();
        if (dtz - minute > 0.0006) {// > 1 minute convertie en jour
            minute++; // c'est un problème d'arrondi
            if (minute >= 60) {
                minute = minute - 60; // modulo 60
                heure++;
            }
        }
        String chaine = new String();
        if (minute < 10 )
            chaine = "0";
        return heure + "H" + chaine +  minute;
    }

    public String getChaineEnseignants (long noCours){
        String chaine = new String("");
        THpSvcWTableauClesEnseignants tabEnseignant = portEnseignant.enseignantsCours(noCours);
        List<String> lListeNoms    = portEnseignant.nomsTableauDEnseignants(tabEnseignant).getString();
        List<String> lListePrenoms = portEnseignant.prenomsTableauDEnseignants(tabEnseignant).getString();
        for (int lIndice = 0; lIndice < lListeNoms.size(); lIndice++)
            chaine = AjouterElementAChaine(chaine, lListeNoms.get(lIndice) + " " + lListePrenoms.get(lIndice));
        return chaine;
    }

    public String getChainePromotions (long noCours){
        String chaine = new String("");
        List<String> tabNom = portPromotion.nomsTableauDePromotions(portPromotion.promotionsCours(noCours)).getString();
        for (int lIndice= 0; lIndice < tabNom.size(); lIndice++)
            chaine = AjouterElementAChaine(chaine, tabNom.get(lIndice));
        return chaine;
    }

    public int getExportCours() {// retourne le nombre de cours exportés
        int resultat = 0;

        try {
            BufferedWriter fichier = new BufferedWriter(new FileWriter(pathExport));
            try {
                GregorianCalendar gCalendarDebut = new GregorianCalendar();
                GregorianCalendar gCalendarFin   = new GregorianCalendar();
                gCalendarDebut.setTime(dateDebut);
                gCalendarFin.setTime(dateFin);
                XMLGregorianCalendar xmlCalendarDebut = DatatypeFactory.newInstance().newXMLGregorianCalendar(gCalendarDebut);
                XMLGregorianCalendar xmlCalendarFin   = DatatypeFactory.newInstance().newXMLGregorianCalendar(gCalendarFin);

                List<Long> tabCours = portCours.tousLesCoursEntre2Dates(xmlCalendarDebut,
                                                                        xmlCalendarFin).getTHpSvcWCleCours();

                for (int i=0; i < tabCours.size(); i++) {
                    if (!portCours.coursEstUnCoursPere(tabCours.get(i))) { // On ne compte que les cours fils et simples
                        // Durée
                        fichier.write (getChaineDuree (portCours.dureeCours(tabCours.get(i)))+ separateur);
                        // Matière
                        fichier.write(portMatiere.libelleMatiere (portCours.matiereCours(tabCours.get(i))) + separateur);
                        // Enseignant
                        fichier.write(getChaineEnseignants(tabCours.get(i))+ separateur);
                        // Promotion
                        fichier.write(getChainePromotions(tabCours.get(i)));
                        fichier.newLine();
                        resultat++;
                        frame.EcrireDansZone (" Export en cours... : " + resultat + " cours exportés");
                    }
                }
            } catch (Exception e) {
                e.printStackTrace();
            }
            fichier.close();
        } catch (java.io.IOException ex){
            frame.EcrireDansZone ("pb d'écriture sur le fichier: " + ex);
            System.out.println("pb d'écriture sur le fichier: " + ex);
        }
        return resultat;
    }
}
