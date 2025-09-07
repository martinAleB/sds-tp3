package simulations;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

public class App {
    private static final String SIMULATIONS_FOLDER = "simulations";
    private static final String BASE_PATH = "../data";

    public static void main(String[] args) throws IOException {
        final String simulationName = args[0];
        final int N = Integer.parseInt(args[1]);
        final double L = Double.parseDouble(args[2]);
        final int T = Integer.parseInt(args[3]);
        final Path simulationPath = Path.of(BASE_PATH, SIMULATIONS_FOLDER, simulationName);
        Files.createDirectories(simulationPath);
        final Path staticFile = simulationPath.resolve("static.txt");

        System.out.printf("%s %d %.2f%n", simulationName, N, L);
        try (var writer = Files.newBufferedWriter(staticFile)) {
            writer.write(String.valueOf(N));
            writer.newLine();
            writer.write(String.valueOf(L));
            writer.newLine();
            writer.write(String.valueOf(Particle.R_DEFAULT));
            writer.newLine();
            writer.write(String.valueOf(Particle.M_DEFAULT));
            writer.newLine();
            writer.write(String.valueOf(Particle.V_DEFAULT));
            writer.newLine();
            writer.write(String.valueOf(T));
            writer.newLine();
        }

        final Grid grid = new Grid(N, L, Particle.R_DEFAULT);
        final Path dynamicFile = simulationPath.resolve("dynamic.txt");
        double tAccum = 0;
        try (var writer = Files.newBufferedWriter(dynamicFile)) {
            writer.write(String.valueOf(tAccum));
            writer.newLine();
            for (Particle p : grid) {
                writer.write(String.format("%f %f %f %f", p.getX(), p.getY(), p.getVx(), p.getVy()));
                writer.newLine();
            }
            for (int i = 1; i < T; i++) {
                List<Event> events = grid.getNextEvents();
                double dt = events.get(0).getTime();
                grid.move(dt);
                for (Event event : events) {
                    event.processEvent();
                }
                // Guard against FP drift pushing particles slightly out of bounds
                grid.clampAll();
                tAccum += dt;
                writer.write(String.valueOf(tAccum));
                writer.newLine();
                for (Particle p : grid) {
                    writer.write(String.format("%f %f %f %f", p.getX(), p.getY(), p.getVx(), p.getVy()));
                    writer.newLine();
                }
            }
        }
        System.out.printf("Simulacion %s generada con éxito.%nN = %d, L = %.2f, T = %d%n", simulationName, N, L, T);
    }
}
