package simulations;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

public class Grid implements Iterable<Particle> {
    private static final double enclosure_long = 0.09;

    private final int N;
    private final double L;
    private final List<Particle> particles = new ArrayList<>();

    public Grid(int N, double L) {
        this.L = L;
        this.N = N;
        for (int i = 0; i < N; i++) {
            double x = 0, y = 0;
            boolean flag = false;
            while (!flag) {
                double cx = Math.random() * (enclosure_long - 2 * Particle.r) + Particle.r;
                double cy = Math.random() * (enclosure_long - 2 * Particle.r) + Particle.r;
                flag = particles.stream().noneMatch(p -> p.isInside(cx, cy));
                if (flag) {
                    x = cx;
                    y = cy;
                }
            }
            double theta = Math.random() * 2 * Math.PI;
            particles.add(new Particle(x, y, theta));
        }
    }

    @Override
    public Iterator<Particle> iterator() {
        return particles.iterator();
    }

}
