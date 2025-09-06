package simulations;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.PriorityQueue;

public class Grid implements Iterable<Particle> {
    private static final double ENCLOSURE_LONG = 0.09;

    private final int N;
    private final double L;
    private final double channelBelow;
    private final List<Particle> particles = new ArrayList<>();

    public Grid(int N, double L, double r) {
        this.L = L;
        this.N = N;
        this.channelBelow = (ENCLOSURE_LONG - L) / 2;
        for (int i = 0; i < N; i++) {
            double x = 0, y = 0;
            boolean flag = false;
            while (!flag) {
                double cx = Math.random() * (ENCLOSURE_LONG - 2 * r) + r;
                double cy = Math.random() * (ENCLOSURE_LONG - 2 * r) + r;
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

    private boolean inBox(final Particle p) {
        return (p.getX() >= 0 && p.getX() <= ENCLOSURE_LONG)
                && (p.getY() >= 0 && p.getY() <= ENCLOSURE_LONG);
    }

    private boolean inChannel(final Particle p) {
        return p.getX() > ENCLOSURE_LONG && p.getX() < 2 * ENCLOSURE_LONG
                && p.getY() > channelBelow && p.getY() < channelBelow + L;
    }

    private Event timeToWallCollisionFromBox(final Particle p) {
        final double txRight = p.timeToXCoord(ENCLOSURE_LONG);
        final double txLeft = p.timeToXCoord(0);
        final double tyUp = p.timeToYCoord(ENCLOSURE_LONG);
        final double tyDown = p.timeToYCoord(0);
        final double minTy = Math.min(tyUp, tyDown);

        if (txRight == Double.POSITIVE_INFINITY) {
            // Nunca puedo ir en direccion al canal
            return txLeft < minTy
                    ? new WallCollisionEvent(txLeft, p, Wall.HORIZONTAL)
                    : new WallCollisionEvent(minTy, p, Wall.VERTICAL);
        }
        // Chequeo posicion en y para ver si cae en la apertura del canal
        if (minTy < txRight) {
            return new WallCollisionEvent(minTy, p, Wall.VERTICAL);
        }
        double yAfterTxRight = p.getYAfterDt(txRight);
        double yChannelBelow = channelBelow;
        double yChannelAbove = channelBelow + L;
        if ((yAfterTxRight + p.getR()) > yChannelAbove || (yAfterTxRight - p.getR()) < yChannelBelow) {
            // No cae en el canal
            return new WallCollisionEvent(txRight, p, Wall.HORIZONTAL);
        }
        // Hay que chequear el tiempo en el que llega a cada una de las paredes del
        // canal
        final double tyChannelMin = Math.min(p.timeToYCoord(yChannelAbove),
                p.timeToYCoord(yChannelBelow));
        final double txChannel = p.timeToXCoord(2 * ENCLOSURE_LONG);
        return txChannel < tyChannelMin
                ? new WallCollisionEvent(txChannel, p, Wall.HORIZONTAL)
                : new WallCollisionEvent(tyChannelMin, p, Wall.VERTICAL);
    }

    private Event timeToWallCollisionFromChannel(final Particle p) {
        final double txRight = p.timeToXCoord(2 * ENCLOSURE_LONG);
        final double txLeft = p.timeToXCoord(ENCLOSURE_LONG);
        final double tyUp = p.timeToYCoord(ENCLOSURE_LONG + L);
        final double tyDown = p.timeToYCoord(ENCLOSURE_LONG);

        if (txLeft == Double.POSITIVE_INFINITY) {
            // Nunca puedo ir en direccion a la box
            double minTy = Math.min(tyUp, tyDown);
            return txRight < minTy
                    ? new WallCollisionEvent(txRight, p, Wall.HORIZONTAL)
                    : new WallCollisionEvent(minTy, p, Wall.VERTICAL);
        }
        // Chequeo posicion en y para ver si cae en
        double yAfterTxLeft = p.getYAfterDt(txLeft);
        double yChannelBelow = channelBelow;
        double yChannelAbove = channelBelow + L;
        if ((yAfterTxLeft + p.getR()) > yChannelAbove || (yAfterTxLeft - p.getR()) < yChannelBelow) {
            // Se sale del canal
            double minTy = Math.min(tyUp, tyDown);
            return txLeft < minTy
                    ? new WallCollisionEvent(txLeft, p, Wall.HORIZONTAL)
                    : new WallCollisionEvent(minTy, p, Wall.VERTICAL);
        }
        // Hay que chequear el tiempo en el que llega a cada una de las paredes del
        // canal
        final double tyChannelMin = Math.min(p.timeToYCoord(yChannelAbove),
                p.timeToYCoord(yChannelBelow));
        final double txChannel = p.timeToXCoord(2 * ENCLOSURE_LONG);
        return txChannel < tyChannelMin
                ? new WallCollisionEvent(txChannel, p, Wall.HORIZONTAL)
                : new WallCollisionEvent(tyChannelMin, p, Wall.VERTICAL);
    }

    private Event timeToWallCollision(final Particle p) {
        if (inBox(p)) {
            System.out.println("Box");
            return timeToWallCollisionFromBox(p);
        }
        if (inChannel(p)) {
            System.out.println("Channel");
            return timeToWallCollisionFromChannel(p);
        }
        throw new IllegalStateException("Particle is out of bounds. x: " + p.getX() + ", y: " + p.getY() + ", vx: "
                + p.getVx() + ", vy: " + p.getVy());
    }

    public List<Event> getNextEvents() {
        PriorityQueue<Event> pq = new PriorityQueue<>();
        Map<Particle, Map<Particle, Boolean>> calculatedCollision = new HashMap<>();
        for (Particle p : this) {
            calculatedCollision.putIfAbsent(p, new HashMap<>());
            pq.add(timeToWallCollision(p));
            for (Particle other : this) {
                if (p != other && !calculatedCollision.getOrDefault(other, Map.of()).getOrDefault(p, false)) {
                    calculatedCollision.get(p).put(other, true);
                    pq.add(p.timeToCollision(other));
                }
            }
        }
        List<Event> nextEvents = List.of(pq.poll());
        while (!pq.isEmpty() && pq.peek().getTime() == nextEvents.get(0).getTime()) {
            nextEvents.add(pq.poll());
        }
        return nextEvents;
    }

    public void move(double dt) {
        for (Particle p : this) {
            p.move(dt);
        }
    }

    @Override
    public Iterator<Particle> iterator() {
        return particles.iterator();
    }
}
