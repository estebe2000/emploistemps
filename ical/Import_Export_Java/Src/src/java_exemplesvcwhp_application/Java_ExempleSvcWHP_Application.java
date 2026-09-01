/*
 * Java_ExempleSvcWHP_Application.java
 */

package java_exemplesvcwhp_application;

import org.jdesktop.application.Application;
import org.jdesktop.application.SingleFrameApplication;

/**
 * The main class of the application.
 */
public class Java_ExempleSvcWHP_Application extends SingleFrameApplication {

    /**
     * At startup create and show the main frame of the application.
     */
    @Override protected void startup() {
        show(new Java_ExempleSvcWHP_View(this));
    }

    /**
     * This method is to initialize the specified window by injecting resources.
     * Windows shown in our application come fully initialized from the GUI
     * builder, so this additional configuration is not needed.
     */
    @Override protected void configureWindow(java.awt.Window root) {
    }

    /**
     * A convenient static getter for the application instance.
     * @return the instance of Java_ExempleSvcWHP_Application
     */
    public static Java_ExempleSvcWHP_Application getApplication() {
        return Application.getInstance(Java_ExempleSvcWHP_Application.class);
    }

    /**
     * Main method launching the application.
     */
    public static void main(String[] args) {
        launch(Java_ExempleSvcWHP_Application.class, args);
    }
}
