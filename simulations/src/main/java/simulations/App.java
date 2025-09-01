package simulations;

import java.io.IOException;

/**
 * Hello world!
 */
public class App {
    public static void main(String[] args) throws IOException {
        FilesService filesService = new FilesService("../data");
        filesService.saveSimulation("simulation1");
    }
}
