/*
 * Java_ExempleSvcWHP_View.java
 */

package java_exemplesvcwhp_application;

import org.jdesktop.application.Action;
import org.jdesktop.application.ResourceMap;
import org.jdesktop.application.SingleFrameApplication;
import org.jdesktop.application.FrameView;
import org.jdesktop.application.TaskMonitor;
import javax.swing.Timer;
import javax.swing.Icon;
import javax.swing.JDialog;
import javax.swing.JFrame;
import javax.swing.JFileChooser;
import javax.xml.ws.BindingProvider;
import java.util.Date;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.File;
import com.indexeducation.frahtm.hpsvcw.HpSvcWAdmin;
import com.indexeducation.frahtm.hpsvcw.HpSvcWDonnees;
import com.indexeducation.frahtm.hpsvcw.IHpSvcWAdmin;
import com.indexeducation.frahtm.hpsvcw.IHpSvcWEnseignants;
import com.indexeducation.frahtm.hpsvcw.IHpSvcWPromotions;
import com.indexeducation.frahtm.hpsvcw.IHpSvcWCours;
import com.indexeducation.frahtm.hpsvcw.IHpSvcWEtudiants;
import com.indexeducation.frahtm.hpsvcw.IHpSvcWMatieres;
import com.indexeducation.frahtm.hpsvcw.IHpSvcWTDOptions;

/**
 * The application's main frame.
 */
public class Java_ExempleSvcWHP_View extends FrameView {

    private enum GenreImportExport {
        ExportCours,
        ImportEnseignant,
        ImportEtudiant
    };

    public Java_ExempleSvcWHP_View(SingleFrameApplication app) {
        super(app);

        initComponents();

        // status bar initialization - message timeout, idle icon and busy animation, etc
        ResourceMap resourceMap = getResourceMap();
        int messageTimeout = resourceMap.getInteger("StatusBar.messageTimeout");
        messageTimer = new Timer(messageTimeout, new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                statusMessageLabel.setText("");
            }
        });
        messageTimer.setRepeats(false);
        int busyAnimationRate = resourceMap.getInteger("StatusBar.busyAnimationRate");
        for (int i = 0; i < busyIcons.length; i++) {
            busyIcons[i] = resourceMap.getIcon("StatusBar.busyIcons[" + i + "]");
        }
        busyIconTimer = new Timer(busyAnimationRate, new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                busyIconIndex = (busyIconIndex + 1) % busyIcons.length;
                statusAnimationLabel.setIcon(busyIcons[busyIconIndex]);
            }
        });
        idleIcon = resourceMap.getIcon("StatusBar.idleIcon");
        statusAnimationLabel.setIcon(idleIcon);
        progressBar.setVisible(false);

        // connecting action tasks to status bar via TaskMonitor
        TaskMonitor taskMonitor = new TaskMonitor(getApplication().getContext());
        taskMonitor.addPropertyChangeListener(new java.beans.PropertyChangeListener() {
            public void propertyChange(java.beans.PropertyChangeEvent evt) {
                String propertyName = evt.getPropertyName();
                if ("started".equals(propertyName)) {
                    if (!busyIconTimer.isRunning()) {
                        statusAnimationLabel.setIcon(busyIcons[0]);
                        busyIconIndex = 0;
                        busyIconTimer.start();
                    }
                    progressBar.setVisible(true);
                    progressBar.setIndeterminate(true);
                } else if ("done".equals(propertyName)) {
                    busyIconTimer.stop();
                    statusAnimationLabel.setIcon(idleIcon);
                    progressBar.setVisible(false);
                    progressBar.setValue(0);
                } else if ("message".equals(propertyName)) {
                    String text = (String)(evt.getNewValue());
                    statusMessageLabel.setText((text == null) ? "" : text);
                    messageTimer.restart();
                } else if ("progress".equals(propertyName)) {
                    int value = (Integer)(evt.getNewValue());
                    progressBar.setVisible(true);
                    progressBar.setIndeterminate(false);
                    progressBar.setValue(value);
                }
            }
        });
        getFrame().setResizable(false);
        // On initialise les dates de debut et fin avec la date d'aujourd'hui
        Date dateDuJour = new Date ();
        jDateChooserDebut.setDate(dateDuJour);
        jDateChooserFin.setDate(dateDuJour);
    }

    // Afficher un message dans la zone adequate de l'interface
    public void EcrireDansZone(String texteAAfficher){
        LabelSvcW.setText(texteAAfficher);
    }

    // Modifier l'adresse IP et le port de connexion au service web
    // ainsi que l'identifiant et le mot de passe
    public void InitialiserSvcW(BindingProvider aPort,
                                String aAddrIp,
                                String aAddrPort,
                                String aRacine,
                                String aUser,
                                String aPassword){
        aPort.getRequestContext().put(BindingProvider.USERNAME_PROPERTY, aUser);
        aPort.getRequestContext().put(BindingProvider.PASSWORD_PROPERTY, aPassword);
        String addresse = (String)aPort.getRequestContext().get(BindingProvider.ENDPOINT_ADDRESS_PROPERTY);
        aPort.getRequestContext().put(BindingProvider.ENDPOINT_ADDRESS_PROPERTY,
                                      "http://" + aAddrIp + ":" + aAddrPort + "/" + aRacine + addresse.substring(addresse.lastIndexOf("/")));
    }

    @Action
    public void showAboutBox() {
        if (aboutBox == null) {
            JFrame mainFrame = Java_ExempleSvcWHP_Application.getApplication().getMainFrame();
            aboutBox = new Java_ExempleSvcWHP_AboutBox(mainFrame);
            aboutBox.setLocationRelativeTo(mainFrame);
        }
        Java_ExempleSvcWHP_Application.getApplication().show(aboutBox);
    }

    /** This method is called from within the constructor to
     * initialize the form.
     * WARNING: Do NOT modify this code. The content of this method is
     * always regenerated by the Form Editor.
     */
    @SuppressWarnings("unchecked")
    // <editor-fold defaultstate="collapsed" desc="Generated Code">//GEN-BEGIN:initComponents
    private void initComponents() {

        mainPanel = new javax.swing.JPanel();
        jTabbedPaneOnglet = new javax.swing.JTabbedPane();
        jPanelExportCours = new javax.swing.JPanel();
        jButtonExporterCours = new javax.swing.JButton();
        jLabelDateDebut = new javax.swing.JLabel();
        jLabelDateFin = new javax.swing.JLabel();
        jLabelFichierExportCours = new javax.swing.JLabel();
        jLabelCheminExportCours = new javax.swing.JLabel();
        jButtonModifierCheminCours = new javax.swing.JButton();
        jTFSeparateur = new javax.swing.JTextField();
        jLabelSeparateur = new javax.swing.JLabel();
        jDateChooserDebut = new com.toedter.calendar.JDateChooser();
        jDateChooserFin = new com.toedter.calendar.JDateChooser();
        jPanelImportEnseignant = new javax.swing.JPanel();
        jButtonImporterEnseignant = new javax.swing.JButton();
        jLabelFichierImportEnseignant = new javax.swing.JLabel();
        jButtonModifierCheminEnseignant = new javax.swing.JButton();
        jLabelCheminImportEnseignant = new javax.swing.JLabel();
        jPanelImportEtudiant = new javax.swing.JPanel();
        jLabelFichierImportEtudiant = new javax.swing.JLabel();
        jButtonModifierCheminEtudiant = new javax.swing.JButton();
        jLabelCheminImportEtudiant = new javax.swing.JLabel();
        jButtonImporterEtudiant = new javax.swing.JButton();
        jLabelPassword = new javax.swing.JLabel();
        TFIdent = new javax.swing.JTextField();
        PFPassword = new javax.swing.JPasswordField();
        jLabelIdent = new javax.swing.JLabel();
        LabelSvcW = new javax.swing.JLabel();
        jLabelAddrIp = new javax.swing.JLabel();
        jLabelAddrPort = new javax.swing.JLabel();
        jTFAddrIP = new javax.swing.JTextField();
        jTFAddrPort = new javax.swing.JTextField();
        jTFRacine = new javax.swing.JTextField();
        jLabelRacine = new javax.swing.JLabel();
        menuBar = new javax.swing.JMenuBar();
        javax.swing.JMenu fileMenu = new javax.swing.JMenu();
        jMenuItemExportCours = new javax.swing.JMenuItem();
        jMenuItemImportEnseignant = new javax.swing.JMenuItem();
        jMenuItemImportEtudiant = new javax.swing.JMenuItem();
        jSeparator2 = new javax.swing.JSeparator();
        jMenuItemEffacer = new javax.swing.JMenuItem();
        jSeparator1 = new javax.swing.JSeparator();
        javax.swing.JMenuItem exitMenuItem = new javax.swing.JMenuItem();
        javax.swing.JMenu helpMenu = new javax.swing.JMenu();
        javax.swing.JMenuItem aboutMenuItem = new javax.swing.JMenuItem();
        statusPanel = new javax.swing.JPanel();
        javax.swing.JSeparator statusPanelSeparator = new javax.swing.JSeparator();
        statusMessageLabel = new javax.swing.JLabel();
        statusAnimationLabel = new javax.swing.JLabel();
        progressBar = new javax.swing.JProgressBar();
        jFileChooser1 = new javax.swing.JFileChooser();

        mainPanel.setName("mainPanel"); // NOI18N

        jTabbedPaneOnglet.setName("jTabbedPaneOnglet"); // NOI18N

        jPanelExportCours.setName("jPanelExportCours"); // NOI18N

        org.jdesktop.application.ResourceMap resourceMap = org.jdesktop.application.Application.getInstance(java_exemplesvcwhp_application.Java_ExempleSvcWHP_Application.class).getContext().getResourceMap(Java_ExempleSvcWHP_View.class);
        jButtonExporterCours.setText(resourceMap.getString("jButtonExporterCours.text")); // NOI18N
        jButtonExporterCours.setName("jButtonExporterCours"); // NOI18N
        jButtonExporterCours.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                jButtonExporterCoursActionPerformed(evt);
            }
        });

        jLabelDateDebut.setText(resourceMap.getString("jLabelDateDebut.text")); // NOI18N
        jLabelDateDebut.setName("jLabelDateDebut"); // NOI18N

        jLabelDateFin.setText(resourceMap.getString("jLabelDateFin.text")); // NOI18N
        jLabelDateFin.setName("jLabelDateFin"); // NOI18N

        jLabelFichierExportCours.setText(resourceMap.getString("jLabelFichierExportCours.text")); // NOI18N
        jLabelFichierExportCours.setName("jLabelFichierExportCours"); // NOI18N

        jLabelCheminExportCours.setForeground(resourceMap.getColor("jLabelCheminExportCours.foreground")); // NOI18N
        jLabelCheminExportCours.setText(resourceMap.getString("jLabelCheminExportCours.text")); // NOI18N
        jLabelCheminExportCours.setToolTipText(jLabelCheminExportCours.getText());
        jLabelCheminExportCours.setName("jLabelCheminExportCours"); // NOI18N

        jButtonModifierCheminCours.setText(resourceMap.getString("jButtonModifierCheminCours.text")); // NOI18N
        jButtonModifierCheminCours.setToolTipText(resourceMap.getString("jButtonModifierCheminCours.toolTipText")); // NOI18N
        jButtonModifierCheminCours.setName("jButtonModifierCheminCours"); // NOI18N
        jButtonModifierCheminCours.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                jButtonModifierCheminCoursActionPerformed(evt);
            }
        });

        jTFSeparateur.setText(resourceMap.getString("jTFSeparateur.text")); // NOI18N
        jTFSeparateur.setName("jTFSeparateur"); // NOI18N

        jLabelSeparateur.setText(resourceMap.getString("jLabelSeparateur.text")); // NOI18N
        jLabelSeparateur.setName("jLabelSeparateur"); // NOI18N

        jDateChooserDebut.setDateFormatString(resourceMap.getString("jDateChooserDebut.dateFormatString")); // NOI18N
        jDateChooserDebut.setName("jDateChooserDebut"); // NOI18N

        jDateChooserFin.setDateFormatString(resourceMap.getString("jDateChooserFin.dateFormatString")); // NOI18N
        jDateChooserFin.setName("jDateChooserFin"); // NOI18N

        org.jdesktop.layout.GroupLayout jPanelExportCoursLayout = new org.jdesktop.layout.GroupLayout(jPanelExportCours);
        jPanelExportCours.setLayout(jPanelExportCoursLayout);
        jPanelExportCoursLayout.setHorizontalGroup(
            jPanelExportCoursLayout.createParallelGroup(org.jdesktop.layout.GroupLayout.LEADING)
            .add(jPanelExportCoursLayout.createSequentialGroup()
                .add(jPanelExportCoursLayout.createParallelGroup(org.jdesktop.layout.GroupLayout.LEADING)
                    .add(jPanelExportCoursLayout.createSequentialGroup()
                        .addContainerGap()
                        .add(jPanelExportCoursLayout.createParallelGroup(org.jdesktop.layout.GroupLayout.LEADING)
                            .add(jPanelExportCoursLayout.createSequentialGroup()
                                .add(131, 131, 131)
                                .add(jTFSeparateur, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE, 24, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE))
                            .add(jLabelSeparateur))
                        .addPreferredGap(org.jdesktop.layout.LayoutStyle.RELATED, org.jdesktop.layout.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                        .add(jButtonExporterCours, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE, 77, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE))
                    .add(jPanelExportCoursLayout.createSequentialGroup()
                        .add(10, 10, 10)
                        .add(jPanelExportCoursLayout.createParallelGroup(org.jdesktop.layout.GroupLayout.LEADING)
                            .add(jLabelDateDebut)
                            .add(jLabelDateFin))
                        .add(62, 62, 62)
                        .add(jPanelExportCoursLayout.createParallelGroup(org.jdesktop.layout.GroupLayout.LEADING, false)
                            .add(jDateChooserFin, org.jdesktop.layout.GroupLayout.DEFAULT_SIZE, org.jdesktop.layout.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                            .add(jDateChooserDebut, org.jdesktop.layout.GroupLayout.DEFAULT_SIZE, 124, Short.MAX_VALUE)))
                    .add(jPanelExportCoursLayout.createSequentialGroup()
                        .addContainerGap()
                        .add(jLabelFichierExportCours)
                        .add(46, 46, 46)
                        .add(jButtonModifierCheminCours, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE, 25, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE))
                    .add(jPanelExportCoursLayout.createSequentialGroup()
                        .addContainerGap()
                        .add(jLabelCheminExportCours, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE, 383, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE)))
                .add(20, 20, 20))
        );

        jPanelExportCoursLayout.linkSize(new java.awt.Component[] {jButtonModifierCheminCours, jTFSeparateur}, org.jdesktop.layout.GroupLayout.HORIZONTAL);

        jPanelExportCoursLayout.setVerticalGroup(
            jPanelExportCoursLayout.createParallelGroup(org.jdesktop.layout.GroupLayout.LEADING)
            .add(jPanelExportCoursLayout.createSequentialGroup()
                .addContainerGap()
                .add(jPanelExportCoursLayout.createParallelGroup(org.jdesktop.layout.GroupLayout.TRAILING)
                    .add(jLabelDateDebut)
                    .add(jDateChooserDebut, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE, org.jdesktop.layout.GroupLayout.DEFAULT_SIZE, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE))
                .addPreferredGap(org.jdesktop.layout.LayoutStyle.RELATED)
                .add(jPanelExportCoursLayout.createParallelGroup(org.jdesktop.layout.GroupLayout.TRAILING)
                    .add(jLabelDateFin)
                    .add(jDateChooserFin, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE, org.jdesktop.layout.GroupLayout.DEFAULT_SIZE, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE))
                .addPreferredGap(org.jdesktop.layout.LayoutStyle.RELATED)
                .add(jPanelExportCoursLayout.createParallelGroup(org.jdesktop.layout.GroupLayout.BASELINE)
                    .add(jLabelFichierExportCours)
                    .add(jButtonModifierCheminCours))
                .addPreferredGap(org.jdesktop.layout.LayoutStyle.RELATED)
                .add(jLabelCheminExportCours)
                .addPreferredGap(org.jdesktop.layout.LayoutStyle.RELATED)
                .add(jPanelExportCoursLayout.createParallelGroup(org.jdesktop.layout.GroupLayout.BASELINE)
                    .add(jLabelSeparateur)
                    .add(jTFSeparateur, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE, org.jdesktop.layout.GroupLayout.DEFAULT_SIZE, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE)
                    .add(jButtonExporterCours))
                .add(20, 20, 20))
        );

        jTabbedPaneOnglet.addTab(resourceMap.getString("jPanelExportCours.TabConstraints.tabTitle"), jPanelExportCours); // NOI18N

        jPanelImportEnseignant.setName("jPanelImportEnseignant"); // NOI18N

        jButtonImporterEnseignant.setText(resourceMap.getString("jButtonImporterEnseignant.text")); // NOI18N
        jButtonImporterEnseignant.setName("jButtonImporterEnseignant"); // NOI18N
        jButtonImporterEnseignant.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                jButtonImporterEnseignantActionPerformed(evt);
            }
        });

        jLabelFichierImportEnseignant.setText(resourceMap.getString("jLabelFichierImportEnseignant.text")); // NOI18N
        jLabelFichierImportEnseignant.setName("jLabelFichierImportEnseignant"); // NOI18N

        jButtonModifierCheminEnseignant.setText(resourceMap.getString("jButtonModifierCheminEnseignant.text")); // NOI18N
        jButtonModifierCheminEnseignant.setToolTipText(resourceMap.getString("jButtonModifierCheminEnseignant.toolTipText")); // NOI18N
        jButtonModifierCheminEnseignant.setName("jButtonModifierCheminEnseignant"); // NOI18N
        jButtonModifierCheminEnseignant.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                jButtonModifierCheminEnseignantActionPerformed(evt);
            }
        });

        jLabelCheminImportEnseignant.setForeground(resourceMap.getColor("jLabelCheminImportEnseignant.foreground")); // NOI18N
        jLabelCheminImportEnseignant.setText(resourceMap.getString("jLabelCheminImportEnseignant.text")); // NOI18N
        jLabelCheminImportEnseignant.setToolTipText(jLabelCheminImportEnseignant.getText());
        jLabelCheminImportEnseignant.setName("jLabelCheminImportEnseignant"); // NOI18N

        org.jdesktop.layout.GroupLayout jPanelImportEnseignantLayout = new org.jdesktop.layout.GroupLayout(jPanelImportEnseignant);
        jPanelImportEnseignant.setLayout(jPanelImportEnseignantLayout);
        jPanelImportEnseignantLayout.setHorizontalGroup(
            jPanelImportEnseignantLayout.createParallelGroup(org.jdesktop.layout.GroupLayout.LEADING)
            .add(jPanelImportEnseignantLayout.createSequentialGroup()
                .add(jPanelImportEnseignantLayout.createParallelGroup(org.jdesktop.layout.GroupLayout.LEADING)
                    .add(jPanelImportEnseignantLayout.createSequentialGroup()
                        .add(10, 10, 10)
                        .add(jLabelFichierImportEnseignant)
                        .add(46, 46, 46)
                        .add(jButtonModifierCheminEnseignant, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE, 25, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE))
                    .add(jPanelImportEnseignantLayout.createSequentialGroup()
                        .addContainerGap()
                        .add(jLabelCheminImportEnseignant, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE, 379, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE))
                    .add(org.jdesktop.layout.GroupLayout.TRAILING, jPanelImportEnseignantLayout.createSequentialGroup()
                        .addContainerGap(328, Short.MAX_VALUE)
                        .add(jButtonImporterEnseignant)))
                .addContainerGap())
        );
        jPanelImportEnseignantLayout.setVerticalGroup(
            jPanelImportEnseignantLayout.createParallelGroup(org.jdesktop.layout.GroupLayout.LEADING)
            .add(jPanelImportEnseignantLayout.createSequentialGroup()
                .add(11, 11, 11)
                .add(jPanelImportEnseignantLayout.createParallelGroup(org.jdesktop.layout.GroupLayout.BASELINE)
                    .add(jLabelFichierImportEnseignant)
                    .add(jButtonModifierCheminEnseignant))
                .addPreferredGap(org.jdesktop.layout.LayoutStyle.RELATED)
                .add(jLabelCheminImportEnseignant)
                .addPreferredGap(org.jdesktop.layout.LayoutStyle.RELATED, 50, Short.MAX_VALUE)
                .add(jButtonImporterEnseignant)
                .addContainerGap())
        );

        jTabbedPaneOnglet.addTab(resourceMap.getString("jPanelImportEnseignant.TabConstraints.tabTitle"), jPanelImportEnseignant); // NOI18N

        jPanelImportEtudiant.setName("jPanelImportEtudiant"); // NOI18N

        jLabelFichierImportEtudiant.setText(resourceMap.getString("jLabelFichierImportEtudiant.text")); // NOI18N
        jLabelFichierImportEtudiant.setName("jLabelFichierImportEtudiant"); // NOI18N

        jButtonModifierCheminEtudiant.setText(resourceMap.getString("jButtonModifierCheminEtudiant.text")); // NOI18N
        jButtonModifierCheminEtudiant.setToolTipText(resourceMap.getString("jButtonModifierCheminEtudiant.toolTipText")); // NOI18N
        jButtonModifierCheminEtudiant.setName("jButtonModifierCheminEtudiant"); // NOI18N
        jButtonModifierCheminEtudiant.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                jButtonModifierCheminEtudiantActionPerformed(evt);
            }
        });

        jLabelCheminImportEtudiant.setForeground(resourceMap.getColor("jLabelCheminImportEtudiant.foreground")); // NOI18N
        jLabelCheminImportEtudiant.setText(resourceMap.getString("jLabelCheminImportEtudiant.text")); // NOI18N
        jLabelCheminImportEtudiant.setToolTipText(jLabelCheminImportEtudiant.getText());
        jLabelCheminImportEtudiant.setName("jLabelCheminImportEtudiant"); // NOI18N

        jButtonImporterEtudiant.setText(resourceMap.getString("jButtonImporterEtudiant.text")); // NOI18N
        jButtonImporterEtudiant.setName("jButtonImporterEtudiant"); // NOI18N
        jButtonImporterEtudiant.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                jButtonImporterEtudiantActionPerformed(evt);
            }
        });

        org.jdesktop.layout.GroupLayout jPanelImportEtudiantLayout = new org.jdesktop.layout.GroupLayout(jPanelImportEtudiant);
        jPanelImportEtudiant.setLayout(jPanelImportEtudiantLayout);
        jPanelImportEtudiantLayout.setHorizontalGroup(
            jPanelImportEtudiantLayout.createParallelGroup(org.jdesktop.layout.GroupLayout.LEADING)
            .add(jPanelImportEtudiantLayout.createSequentialGroup()
                .add(jPanelImportEtudiantLayout.createParallelGroup(org.jdesktop.layout.GroupLayout.LEADING)
                    .add(jPanelImportEtudiantLayout.createSequentialGroup()
                        .add(10, 10, 10)
                        .add(jLabelFichierImportEtudiant)
                        .add(46, 46, 46)
                        .add(jButtonModifierCheminEtudiant, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE, 25, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE))
                    .add(jPanelImportEtudiantLayout.createSequentialGroup()
                        .addContainerGap()
                        .add(jLabelCheminImportEtudiant, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE, 379, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE))
                    .add(org.jdesktop.layout.GroupLayout.TRAILING, jPanelImportEtudiantLayout.createSequentialGroup()
                        .addContainerGap(328, Short.MAX_VALUE)
                        .add(jButtonImporterEtudiant)))
                .addContainerGap())
        );
        jPanelImportEtudiantLayout.setVerticalGroup(
            jPanelImportEtudiantLayout.createParallelGroup(org.jdesktop.layout.GroupLayout.LEADING)
            .add(jPanelImportEtudiantLayout.createSequentialGroup()
                .add(11, 11, 11)
                .add(jPanelImportEtudiantLayout.createParallelGroup(org.jdesktop.layout.GroupLayout.BASELINE)
                    .add(jLabelFichierImportEtudiant)
                    .add(jButtonModifierCheminEtudiant))
                .addPreferredGap(org.jdesktop.layout.LayoutStyle.RELATED)
                .add(jLabelCheminImportEtudiant)
                .addPreferredGap(org.jdesktop.layout.LayoutStyle.RELATED, 50, Short.MAX_VALUE)
                .add(jButtonImporterEtudiant)
                .addContainerGap())
        );

        jTabbedPaneOnglet.addTab(resourceMap.getString("jPanelImportEtudiant.TabConstraints.tabTitle"), jPanelImportEtudiant); // NOI18N

        jLabelPassword.setText(resourceMap.getString("labelMotDePasse.text")); // NOI18N
        jLabelPassword.setName("labelMotDePasse"); // NOI18N

        TFIdent.setHorizontalAlignment(javax.swing.JTextField.LEFT);
        TFIdent.setText(resourceMap.getString("TfIdent.text")); // NOI18N
        TFIdent.setMaximumSize(new java.awt.Dimension(11, 19));
        TFIdent.setName("TfIdent"); // NOI18N

        PFPassword.setHorizontalAlignment(javax.swing.JTextField.LEFT);
        PFPassword.setText(resourceMap.getString("tfPassword.text")); // NOI18N
        PFPassword.setAutoscrolls(false);
        PFPassword.setName("tfPassword"); // NOI18N

        jLabelIdent.setText(resourceMap.getString("jLabelIdent.text")); // NOI18N
        jLabelIdent.setName("jLabelIdent"); // NOI18N

        LabelSvcW.setBackground(resourceMap.getColor("LabelSvcW.background")); // NOI18N
        LabelSvcW.setText(resourceMap.getString("LabelSvcW.text")); // NOI18N
        LabelSvcW.setAlignmentX(0.5F);
        LabelSvcW.setBorder(javax.swing.BorderFactory.createEtchedBorder());
        LabelSvcW.setName("LabelSvcW"); // NOI18N

        jLabelAddrIp.setText(resourceMap.getString("jLabelAddrIp.text")); // NOI18N
        jLabelAddrIp.setName("jLabelAddrIp"); // NOI18N

        jLabelAddrPort.setText(resourceMap.getString("jLabelAddrPort.text")); // NOI18N
        jLabelAddrPort.setName("jLabelAddrPort"); // NOI18N

        jTFAddrIP.setHorizontalAlignment(javax.swing.JTextField.LEFT);
        jTFAddrIP.setText(resourceMap.getString("jTFAddrIP.text")); // NOI18N
        jTFAddrIP.setAutoscrolls(false);
        jTFAddrIP.setName("jTFAddrIP"); // NOI18N

        jTFAddrPort.setText(resourceMap.getString("jTFAddrPort.text")); // NOI18N
        jTFAddrPort.setAutoscrolls(false);
        jTFAddrPort.setName("jTFAddrPort"); // NOI18N

        jTFRacine.setText(resourceMap.getString("jTFRacine.text")); // NOI18N
        jTFRacine.setAutoscrolls(false);
        jTFRacine.setName("jTFRacine"); // NOI18N

        jLabelRacine.setText(resourceMap.getString("jLabelRacine.text")); // NOI18N
        jLabelRacine.setName("jLabelRacine"); // NOI18N

        org.jdesktop.layout.GroupLayout mainPanelLayout = new org.jdesktop.layout.GroupLayout(mainPanel);
        mainPanel.setLayout(mainPanelLayout);
        mainPanelLayout.setHorizontalGroup(
            mainPanelLayout.createParallelGroup(org.jdesktop.layout.GroupLayout.LEADING)
            .add(mainPanelLayout.createSequentialGroup()
                .addContainerGap()
                .add(mainPanelLayout.createParallelGroup(org.jdesktop.layout.GroupLayout.LEADING)
                    .add(mainPanelLayout.createParallelGroup(org.jdesktop.layout.GroupLayout.TRAILING, false)
                        .add(org.jdesktop.layout.GroupLayout.LEADING, LabelSvcW, org.jdesktop.layout.GroupLayout.DEFAULT_SIZE, org.jdesktop.layout.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                        .add(org.jdesktop.layout.GroupLayout.LEADING, jTabbedPaneOnglet))
                    .add(mainPanelLayout.createSequentialGroup()
                        .add(mainPanelLayout.createParallelGroup(org.jdesktop.layout.GroupLayout.LEADING)
                            .add(jLabelAddrIp)
                            .add(jLabelIdent, org.jdesktop.layout.GroupLayout.DEFAULT_SIZE, org.jdesktop.layout.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE))
                        .addPreferredGap(org.jdesktop.layout.LayoutStyle.RELATED)
                        .add(mainPanelLayout.createParallelGroup(org.jdesktop.layout.GroupLayout.LEADING)
                            .add(TFIdent, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE, 43, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE)
                            .add(jTFAddrIP, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE, org.jdesktop.layout.GroupLayout.DEFAULT_SIZE, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE))
                        .add(18, 18, 18)
                        .add(mainPanelLayout.createParallelGroup(org.jdesktop.layout.GroupLayout.LEADING)
                            .add(mainPanelLayout.createSequentialGroup()
                                .add(jLabelAddrPort)
                                .add(25, 25, 25))
                            .add(jLabelPassword, org.jdesktop.layout.GroupLayout.DEFAULT_SIZE, org.jdesktop.layout.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE))
                        .addPreferredGap(org.jdesktop.layout.LayoutStyle.RELATED)
                        .add(mainPanelLayout.createParallelGroup(org.jdesktop.layout.GroupLayout.LEADING)
                            .add(mainPanelLayout.createSequentialGroup()
                                .add(jTFAddrPort, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE, 49, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE)
                                .addPreferredGap(org.jdesktop.layout.LayoutStyle.UNRELATED)
                                .add(jLabelRacine)
                                .add(26, 26, 26)
                                .add(jTFRacine, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE, 49, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE))
                            .add(PFPassword, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE, 49, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE))))
                .addContainerGap())
        );
        mainPanelLayout.setVerticalGroup(
            mainPanelLayout.createParallelGroup(org.jdesktop.layout.GroupLayout.LEADING)
            .add(mainPanelLayout.createSequentialGroup()
                .addContainerGap()
                .add(mainPanelLayout.createParallelGroup(org.jdesktop.layout.GroupLayout.TRAILING)
                    .add(mainPanelLayout.createSequentialGroup()
                        .add(mainPanelLayout.createParallelGroup(org.jdesktop.layout.GroupLayout.BASELINE)
                            .add(jLabelAddrIp)
                            .add(jTFAddrIP, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE, org.jdesktop.layout.GroupLayout.DEFAULT_SIZE, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE))
                        .addPreferredGap(org.jdesktop.layout.LayoutStyle.RELATED)
                        .add(mainPanelLayout.createParallelGroup(org.jdesktop.layout.GroupLayout.BASELINE)
                            .add(jLabelIdent, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE, 17, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE)
                            .add(TFIdent, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE, org.jdesktop.layout.GroupLayout.DEFAULT_SIZE, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE)))
                    .add(mainPanelLayout.createSequentialGroup()
                        .add(jLabelAddrPort)
                        .add(25, 25, 25))
                    .add(mainPanelLayout.createSequentialGroup()
                        .add(mainPanelLayout.createParallelGroup(org.jdesktop.layout.GroupLayout.BASELINE)
                            .add(jTFAddrPort, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE, org.jdesktop.layout.GroupLayout.DEFAULT_SIZE, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE)
                            .add(jLabelRacine)
                            .add(jTFRacine, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE, org.jdesktop.layout.GroupLayout.DEFAULT_SIZE, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE))
                        .addPreferredGap(org.jdesktop.layout.LayoutStyle.RELATED)
                        .add(mainPanelLayout.createParallelGroup(org.jdesktop.layout.GroupLayout.BASELINE)
                            .add(PFPassword, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE, 21, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE)
                            .add(jLabelPassword))))
                .add(13, 13, 13)
                .add(jTabbedPaneOnglet, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE, 166, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE)
                .addPreferredGap(org.jdesktop.layout.LayoutStyle.RELATED)
                .add(LabelSvcW)
                .addContainerGap(org.jdesktop.layout.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE))
        );

        menuBar.setName("menuBar"); // NOI18N

        fileMenu.setText(resourceMap.getString("fileMenu.text")); // NOI18N
        fileMenu.setName("fileMenu"); // NOI18N

        jMenuItemExportCours.setText(resourceMap.getString("jMenuItemExportCours.text")); // NOI18N
        jMenuItemExportCours.setName("jMenuItemExportCours"); // NOI18N
        jMenuItemExportCours.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                jMenuItemExportCoursActionPerformed(evt);
            }
        });
        fileMenu.add(jMenuItemExportCours);

        jMenuItemImportEnseignant.setText(resourceMap.getString("jMenuItemImportEnseignant.text")); // NOI18N
        jMenuItemImportEnseignant.setName("jMenuItemImportEnseignant"); // NOI18N
        jMenuItemImportEnseignant.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                jMenuItemImportEnseignantActionPerformed(evt);
            }
        });
        fileMenu.add(jMenuItemImportEnseignant);

        jMenuItemImportEtudiant.setText(resourceMap.getString("jMenuItemImportEtudiant.text")); // NOI18N
        jMenuItemImportEtudiant.setName("jMenuItemImportEtudiant"); // NOI18N
        jMenuItemImportEtudiant.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                jMenuItemImportEtudiantActionPerformed(evt);
            }
        });
        fileMenu.add(jMenuItemImportEtudiant);

        jSeparator2.setName("jSeparator2"); // NOI18N
        fileMenu.add(jSeparator2);

        jMenuItemEffacer.setText(resourceMap.getString("jMenuItemEffacer.text")); // NOI18N
        jMenuItemEffacer.setName("jMenuItemEffacer"); // NOI18N
        jMenuItemEffacer.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                jMenuItemEffacerActionPerformed(evt);
            }
        });
        fileMenu.add(jMenuItemEffacer);

        jSeparator1.setName("jSeparator1"); // NOI18N
        fileMenu.add(jSeparator1);

        javax.swing.ActionMap actionMap = org.jdesktop.application.Application.getInstance(java_exemplesvcwhp_application.Java_ExempleSvcWHP_Application.class).getContext().getActionMap(Java_ExempleSvcWHP_View.class, this);
        exitMenuItem.setAction(actionMap.get("quit")); // NOI18N
        exitMenuItem.setText(resourceMap.getString("exitMenuItem.text")); // NOI18N
        exitMenuItem.setToolTipText(resourceMap.getString("exitMenuItem.toolTipText")); // NOI18N
        exitMenuItem.setName("exitMenuItem"); // NOI18N
        fileMenu.add(exitMenuItem);

        menuBar.add(fileMenu);

        helpMenu.setText(resourceMap.getString("helpMenu.text")); // NOI18N
        helpMenu.setName("helpMenu"); // NOI18N

        aboutMenuItem.setAction(actionMap.get("showAboutBox")); // NOI18N
        aboutMenuItem.setText(resourceMap.getString("aboutMenuItem.text")); // NOI18N
        aboutMenuItem.setToolTipText(resourceMap.getString("aboutMenuItem.toolTipText")); // NOI18N
        aboutMenuItem.setName("aboutMenuItem"); // NOI18N
        helpMenu.add(aboutMenuItem);

        menuBar.add(helpMenu);

        statusPanel.setName("statusPanel"); // NOI18N

        statusPanelSeparator.setName("statusPanelSeparator"); // NOI18N

        statusMessageLabel.setName("statusMessageLabel"); // NOI18N

        statusAnimationLabel.setHorizontalAlignment(javax.swing.SwingConstants.LEFT);
        statusAnimationLabel.setName("statusAnimationLabel"); // NOI18N

        progressBar.setName("progressBar"); // NOI18N

        org.jdesktop.layout.GroupLayout statusPanelLayout = new org.jdesktop.layout.GroupLayout(statusPanel);
        statusPanel.setLayout(statusPanelLayout);
        statusPanelLayout.setHorizontalGroup(
            statusPanelLayout.createParallelGroup(org.jdesktop.layout.GroupLayout.LEADING)
            .add(statusPanelSeparator, org.jdesktop.layout.GroupLayout.DEFAULT_SIZE, 438, Short.MAX_VALUE)
            .add(statusPanelLayout.createSequentialGroup()
                .addContainerGap()
                .add(statusMessageLabel)
                .addPreferredGap(org.jdesktop.layout.LayoutStyle.RELATED, 268, Short.MAX_VALUE)
                .add(progressBar, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE, org.jdesktop.layout.GroupLayout.DEFAULT_SIZE, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE)
                .addPreferredGap(org.jdesktop.layout.LayoutStyle.RELATED)
                .add(statusAnimationLabel)
                .addContainerGap())
        );
        statusPanelLayout.setVerticalGroup(
            statusPanelLayout.createParallelGroup(org.jdesktop.layout.GroupLayout.LEADING)
            .add(statusPanelLayout.createSequentialGroup()
                .add(statusPanelSeparator, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE, 2, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE)
                .addPreferredGap(org.jdesktop.layout.LayoutStyle.RELATED, org.jdesktop.layout.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                .add(statusPanelLayout.createParallelGroup(org.jdesktop.layout.GroupLayout.BASELINE)
                    .add(statusMessageLabel)
                    .add(statusAnimationLabel)
                    .add(progressBar, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE, org.jdesktop.layout.GroupLayout.DEFAULT_SIZE, org.jdesktop.layout.GroupLayout.PREFERRED_SIZE))
                .add(3, 3, 3))
        );

        jFileChooser1.setName("jFileChooser1"); // NOI18N

        setComponent(mainPanel);
        setMenuBar(menuBar);
        setStatusBar(statusPanel);
    }// </editor-fold>//GEN-END:initComponents

    private void jButtonModifierCheminCoursActionPerformed(java.awt.event.ActionEvent evt) {//GEN-FIRST:event_jButtonModifierCheminCoursActionPerformed
        jFileChooser1=new JFileChooser();
        jFileChooser1.setFileSelectionMode(JFileChooser.FILES_ONLY);
        jFileChooser1.setMultiSelectionEnabled(false);
        jFileChooser1.setDialogTitle("Selectionner le fichier d'export des cours");
        File file = new File(jLabelCheminExportCours.getText());
        if (file.exists())
            jFileChooser1.setSelectedFile(file);
        int result = jFileChooser1.showOpenDialog(null);
        if(result==JFileChooser.APPROVE_OPTION ) {
            jLabelCheminExportCours.setText(jFileChooser1.getSelectedFile().getAbsolutePath());
            jLabelCheminExportCours.setToolTipText(jLabelCheminExportCours.getText());
        }
}//GEN-LAST:event_jButtonModifierCheminCoursActionPerformed

    private void jButtonExporterCoursActionPerformed(java.awt.event.ActionEvent evt) {//GEN-FIRST:event_jButtonExporterCoursActionPerformed
        Thread t = new Thread() {
            public void run() {
                ImporterExporter(GenreImportExport.ExportCours);
            }
        };
        t.start();
}//GEN-LAST:event_jButtonExporterCoursActionPerformed

    private void jButtonImporterEnseignantActionPerformed(java.awt.event.ActionEvent evt) {//GEN-FIRST:event_jButtonImporterEnseignantActionPerformed
        Thread t = new Thread() {
            public void run() {
                ImporterExporter(GenreImportExport.ImportEnseignant);
            }
        };
        t.start();
}//GEN-LAST:event_jButtonImporterEnseignantActionPerformed

    private void jButtonModifierCheminEnseignantActionPerformed(java.awt.event.ActionEvent evt) {//GEN-FIRST:event_jButtonModifierCheminEnseignantActionPerformed
        jFileChooser1=new JFileChooser();
        jFileChooser1.setFileSelectionMode(JFileChooser.FILES_ONLY);
        jFileChooser1.setMultiSelectionEnabled(false);
        jFileChooser1.setDialogTitle("Selectionner le fichier d'import des enseignants");
        File file = new File(jLabelCheminImportEnseignant.getText());
        if (file.exists())
            jFileChooser1.setSelectedFile(file);
        int result = jFileChooser1.showOpenDialog(null);
        if(result==JFileChooser.APPROVE_OPTION ) {
            jLabelCheminImportEnseignant.setText(jFileChooser1.getSelectedFile().getAbsolutePath());
            jLabelCheminImportEnseignant.setToolTipText(jLabelCheminImportEnseignant.getText());
        }
}//GEN-LAST:event_jButtonModifierCheminEnseignantActionPerformed

    private void jButtonModifierCheminEtudiantActionPerformed(java.awt.event.ActionEvent evt) {//GEN-FIRST:event_jButtonModifierCheminEtudiantActionPerformed
        jFileChooser1=new JFileChooser();
        jFileChooser1.setFileSelectionMode(JFileChooser.FILES_ONLY);
        jFileChooser1.setMultiSelectionEnabled(false);
        jFileChooser1.setDialogTitle("Selectionner le fichier d'import des étudiants");
        File file = new File(jLabelCheminImportEtudiant.getText());
        if (file.exists())
            jFileChooser1.setSelectedFile(file);
        int result = jFileChooser1.showOpenDialog(null);
        if(result==JFileChooser.APPROVE_OPTION ) {
            jLabelCheminImportEtudiant.setText(jFileChooser1.getSelectedFile().getAbsolutePath());
            jLabelCheminImportEtudiant.setToolTipText(jLabelCheminImportEtudiant.getText());
        }
}//GEN-LAST:event_jButtonModifierCheminEtudiantActionPerformed

    private void jButtonImporterEtudiantActionPerformed(java.awt.event.ActionEvent evt) {//GEN-FIRST:event_jButtonImporterEtudiantActionPerformed
        Thread t = new Thread() {
            public void run() {
                ImporterExporter(GenreImportExport.ImportEtudiant);
            }
        };
        t.start();
}//GEN-LAST:event_jButtonImporterEtudiantActionPerformed

    private void jMenuItemExportCoursActionPerformed(java.awt.event.ActionEvent evt) {//GEN-FIRST:event_jMenuItemExportCoursActionPerformed
        jTabbedPaneOnglet.setSelectedIndex(0);
}//GEN-LAST:event_jMenuItemExportCoursActionPerformed

    private void jMenuItemImportEnseignantActionPerformed(java.awt.event.ActionEvent evt) {//GEN-FIRST:event_jMenuItemImportEnseignantActionPerformed
        jTabbedPaneOnglet.setSelectedIndex(1);
}//GEN-LAST:event_jMenuItemImportEnseignantActionPerformed

    private void jMenuItemImportEtudiantActionPerformed(java.awt.event.ActionEvent evt) {//GEN-FIRST:event_jMenuItemImportEtudiantActionPerformed
        jTabbedPaneOnglet.setSelectedIndex(2);
}//GEN-LAST:event_jMenuItemImportEtudiantActionPerformed

    private void jMenuItemEffacerActionPerformed(java.awt.event.ActionEvent evt) {//GEN-FIRST:event_jMenuItemEffacerActionPerformed
        LabelSvcW.setText("   ");
    }//GEN-LAST:event_jMenuItemEffacerActionPerformed

    @Action
    private void ImporterExporter(GenreImportExport aGenre) {
        EcrireDansZone ("Connexion en cours...");
        String user     = TFIdent.getText();
        String password = new String (PFPassword.getPassword());
        String addrIp   = jTFAddrIP.getText();
        String addrPort = jTFAddrPort.getText();
        String racine   = jTFRacine.getText();

        try {
            HpSvcWAdmin   lServiceAdmin  = new HpSvcWAdmin();
            HpSvcWDonnees lServiceDonnee = new HpSvcWDonnees();

            IHpSvcWAdmin       portAdmin      = lServiceAdmin.getPortAdmin();
            IHpSvcWMatieres    portMatiere    = lServiceDonnee.getPortMatieres();
            IHpSvcWEnseignants portEnseignant = lServiceDonnee.getPortEnseignants();
            IHpSvcWEtudiants   portEtudiant   = lServiceDonnee.getPortEtudiants();
            IHpSvcWPromotions  portPromotion  = lServiceDonnee.getPortPromotions();
            IHpSvcWTDOptions   portTDOption   = lServiceDonnee.getPortTDOptions();
            IHpSvcWCours       portCours      = lServiceDonnee.getPortCours();

            InitialiserSvcW ((BindingProvider)portAdmin,      addrIp, addrPort, racine, user, password);
            InitialiserSvcW ((BindingProvider)portMatiere,    addrIp, addrPort, racine, user, password);
            InitialiserSvcW ((BindingProvider)portEnseignant, addrIp, addrPort, racine, user, password);
            InitialiserSvcW ((BindingProvider)portEtudiant,   addrIp, addrPort, racine, user, password);
            InitialiserSvcW ((BindingProvider)portPromotion,  addrIp, addrPort, racine, user, password);
            InitialiserSvcW ((BindingProvider)portTDOption,   addrIp, addrPort, racine, user, password);
            InitialiserSvcW ((BindingProvider)portCours,      addrIp, addrPort, racine, user, password);

            EcrireDansZone (portAdmin.version() + " - connecté...");
            switch (aGenre){
                case ExportCours :
                    Date aDate1 = jDateChooserDebut.getDate();
                    Date aDate2 = jDateChooserFin.getDate();
                    if (aDate1 == null) {
                        EcrireDansZone("Export impossible : date de début incorrecte.");
                    } else {
                        if (aDate2 == null) {
                            EcrireDansZone("Export impossible : date de fin incorecte.");
                        } else { // les dates sont correctes. On peut exporter les cours.
                            Java_ExempleSvcWHP_ExportCours exportDesCours = new Java_ExempleSvcWHP_ExportCours (this,
                                                                                                                portCours,
                                                                                                                portMatiere,
                                                                                                                portEnseignant,
                                                                                                                portPromotion,
                                                                                                                aDate1,
                                                                                                                aDate2,
                                                                                                                jTFSeparateur.getText(),
                                                                                                                jLabelCheminExportCours.getText());
                            EcrireDansZone ("Export des cours terminé : " + exportDesCours.getExportCours() + " cours exportés");
                        }
                    }
                break;

                case ImportEnseignant :
                    if (new File(jLabelCheminImportEnseignant.getText()).exists()) {
                        Java_ExempleSvcWHP_ImportEnseignant importDesEnseignants = new Java_ExempleSvcWHP_ImportEnseignant(this,
                                                                                                                           portEnseignant,
                                                                                                                           jLabelCheminImportEnseignant.getText());
                        EcrireDansZone ("Import des enseignants terminé : " + importDesEnseignants.getImportEnseignants() + " lignes importés");
                    } else {
                        EcrireDansZone("Impossible d'ouvrir le fichier d'import des enseignants");
                    }
                break;

                case ImportEtudiant :
                    if (new File(jLabelCheminImportEtudiant.getText()).exists()) {
                        Java_ExempleSvcWHP_ImportEtudiant importDesEtudiants = new Java_ExempleSvcWHP_ImportEtudiant(this,
                                                                                                                     portEtudiant,
                                                                                                                     portPromotion,
                                                                                                                     portTDOption,
                                                                                                                     jLabelCheminImportEtudiant.getText());
                        EcrireDansZone ("Import des étudiants terminé : " + importDesEtudiants.getImportEtudiants() + " lignes importés");
                    } else {
                        EcrireDansZone("Impossible d'ouvrir le fichier d'import des étudiants");
                    }
                break;
            }
        } catch (Exception e) {
            e.printStackTrace();
            EcrireDansZone(e.getMessage());
        }
    }

    // Variables declaration - do not modify//GEN-BEGIN:variables
    private javax.swing.JLabel LabelSvcW;
    private javax.swing.JPasswordField PFPassword;
    private javax.swing.JTextField TFIdent;
    private javax.swing.JButton jButtonExporterCours;
    private javax.swing.JButton jButtonImporterEnseignant;
    private javax.swing.JButton jButtonImporterEtudiant;
    private javax.swing.JButton jButtonModifierCheminCours;
    private javax.swing.JButton jButtonModifierCheminEnseignant;
    private javax.swing.JButton jButtonModifierCheminEtudiant;
    private com.toedter.calendar.JDateChooser jDateChooserDebut;
    private com.toedter.calendar.JDateChooser jDateChooserFin;
    private javax.swing.JFileChooser jFileChooser1;
    private javax.swing.JLabel jLabelAddrIp;
    private javax.swing.JLabel jLabelAddrPort;
    private javax.swing.JLabel jLabelCheminExportCours;
    private javax.swing.JLabel jLabelCheminImportEnseignant;
    private javax.swing.JLabel jLabelCheminImportEtudiant;
    private javax.swing.JLabel jLabelDateDebut;
    private javax.swing.JLabel jLabelDateFin;
    private javax.swing.JLabel jLabelFichierExportCours;
    private javax.swing.JLabel jLabelFichierImportEnseignant;
    private javax.swing.JLabel jLabelFichierImportEtudiant;
    private javax.swing.JLabel jLabelIdent;
    private javax.swing.JLabel jLabelPassword;
    private javax.swing.JLabel jLabelRacine;
    private javax.swing.JLabel jLabelSeparateur;
    private javax.swing.JMenuItem jMenuItemEffacer;
    private javax.swing.JMenuItem jMenuItemExportCours;
    private javax.swing.JMenuItem jMenuItemImportEnseignant;
    private javax.swing.JMenuItem jMenuItemImportEtudiant;
    private javax.swing.JPanel jPanelExportCours;
    private javax.swing.JPanel jPanelImportEnseignant;
    private javax.swing.JPanel jPanelImportEtudiant;
    private javax.swing.JSeparator jSeparator1;
    private javax.swing.JSeparator jSeparator2;
    private javax.swing.JTextField jTFAddrIP;
    private javax.swing.JTextField jTFAddrPort;
    private javax.swing.JTextField jTFRacine;
    private javax.swing.JTextField jTFSeparateur;
    private javax.swing.JTabbedPane jTabbedPaneOnglet;
    private javax.swing.JPanel mainPanel;
    private javax.swing.JMenuBar menuBar;
    private javax.swing.JProgressBar progressBar;
    private javax.swing.JLabel statusAnimationLabel;
    private javax.swing.JLabel statusMessageLabel;
    private javax.swing.JPanel statusPanel;
    // End of variables declaration//GEN-END:variables

    private final Timer messageTimer;
    private final Timer busyIconTimer;
    private final Icon idleIcon;
    private final Icon[] busyIcons = new Icon[15];
    private int busyIconIndex = 0;

    private JDialog aboutBox;
}
