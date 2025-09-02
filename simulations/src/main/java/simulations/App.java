package simulations;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

public class App {
    private static final String SIMULATIONS_FOLDER = "simulations";
    private static final String BASE_PATH = "../data";

    public static void main(String[] args) throws IOException {
        final String simulationName = args[0];
        final int N = Integer.parseInt(args[1]);
        final double L = Double.parseDouble(args[2]);
        final Path simulationPath = Path.of(BASE_PATH, SIMULATIONS_FOLDER, simulationName);
        Files.createDirectories(simulationPath);
        final Path staticFile = simulationPath.resolve("static.txt");

        System.out.printf("%s %d %.2f%n", simulationName, N, L);
        try (var writer = Files.newBufferedWriter(staticFile)) {
            writer.write(String.valueOf(N));
            writer.newLine();
            writer.write(String.valueOf(L));
            writer.newLine();
            writer.write(String.valueOf(Particle.r));
            writer.newLine();
            writer.write(String.valueOf(Particle.m));
            writer.newLine();
            writer.write(String.valueOf(Particle.v));
            writer.newLine();
        }

        final Grid grid = new Grid(N, L);
        final Path dynamicFile = simulationPath.resolve("dynamic.txt");
        double t = 0;
        try (var writer = Files.newBufferedWriter(dynamicFile)) {
            writer.write(String.valueOf(t));
            writer.newLine();
            for (Particle p : grid) {
                writer.write(String.format("%f %f %f %f", p.getX(), p.getY(), p.getVx(), p.getVy()));
                writer.newLine();
            }
        }
    }
}
