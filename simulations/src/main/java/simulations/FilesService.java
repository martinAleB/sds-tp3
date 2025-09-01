package simulations;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

public class FilesService {
    private static final String SIMULATIONS_FOLDER = "simulations";
    private final String basePath;

    public FilesService(String basePath) {
        this.basePath = basePath;
    }

    public void saveSimulation(String simulationName) throws IOException {
        Path simulationPath = Path.of(basePath, SIMULATIONS_FOLDER, simulationName);
        Files.createDirectories(simulationPath);
    }

}
