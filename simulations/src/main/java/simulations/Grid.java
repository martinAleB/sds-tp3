package simulations;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.PriorityQueue;

public class Grid implements Iterable<Particle> {
    private static final double ENCLOSURE_LONG = 0.09;
    private static final double EPS = 1e-12;

    private final int N;
    private final double L;
    private final double channelBelow;
    private final double channelAbove;
    private final List<Particle> particles = new ArrayList<>();

    public Grid(int N, double L, double r) {
        this.L = L;
        this.N = N;
        this.channelBelow = (ENCLOSURE_LONG - L) / 2;
        this.channelAbove = channelBelow + L;
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
        // Agrego los obstaculos
        particles.add(new Particle(ENCLOSURE_LONG, channelBelow));
        particles.add(new Particle(ENCLOSURE_LONG, channelAbove));
    }

    private boolean inBox(final Particle p) {
        return (p.getX() >= 0 - EPS && p.getX() <= ENCLOSURE_LONG + EPS)
                && (p.getY() >= 0 - EPS && p.getY() <= ENCLOSURE_LONG + EPS);
    }

    private boolean inChannel(final Particle p) {
        return p.getX() >= ENCLOSURE_LONG - EPS && p.getX() <= 2 * ENCLOSURE_LONG + EPS
                && p.getY() >= channelBelow - EPS && p.getY() <= channelBelow + L + EPS;
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
                    ? new WallCollisionEvent(txLeft, p, Wall.VERTICAL)
                    : new WallCollisionEvent(minTy, p, Wall.HORIZONTAL);
        }
        if (minTy < txRight) {
            return new WallCollisionEvent(minTy, p, Wall.HORIZONTAL);
        }
        // Chequeo posicion en y para ver si cae en la apertura del canal
        double txCenterToEnclosure = p.timeToXCoord(ENCLOSURE_LONG + p.getR());
        double yAfterTxCenterToEnclosure = p.getYAfterDt(txCenterToEnclosure);
        if ((yAfterTxCenterToEnclosure + p.getR()) > channelAbove
                || (yAfterTxCenterToEnclosure - p.getR()) < channelBelow) {
            // No cae en el canal
            return new WallCollisionEvent(txRight, p, Wall.VERTICAL);
        }
        // Hay que chequear el tiempo en el que llega a cada una de las paredes del
        // canal
        final double vMagEnter = Math.hypot(p.getVx(), p.getVy());
        final Particle pAfterEnteringChannel = new Particle(
                p.getR(),
                p.getM(),
                vMagEnter,
                ENCLOSURE_LONG,
                yAfterTxCenterToEnclosure,
                Math.atan2(p.getVy(), p.getVx()));
        final double tyChannelMin = Math.min(pAfterEnteringChannel.timeToYCoord(channelAbove),
                pAfterEnteringChannel.timeToYCoord(channelBelow));
        final double txChannel = pAfterEnteringChannel.timeToXCoord(2 * ENCLOSURE_LONG);
        return txChannel < tyChannelMin
                ? new WallCollisionEvent(txCenterToEnclosure + txChannel, p, Wall.VERTICAL)
                : new WallCollisionEvent(txCenterToEnclosure + tyChannelMin, p, Wall.HORIZONTAL);
    }

    private Event timeToWallCollisionFromChannel(final Particle p) {
        final double txRight = p.timeToXCoord(2 * ENCLOSURE_LONG);
        final double tyUp = p.timeToYCoord(channelAbove);
        final double tyDown = p.timeToYCoord(channelBelow);
        final double minTy = Math.min(tyUp, tyDown);

        if (txRight != Double.POSITIVE_INFINITY) {
            // Nunca puedo ir en direccion a la box
            return txRight < minTy
                    ? new WallCollisionEvent(txRight, p, Wall.VERTICAL)
                    : new WallCollisionEvent(minTy, p, Wall.HORIZONTAL);
        }
        // Chequeo posicion en y para ver si sale del canal
        double txCenterToEnclosure = p.timeToXCoord(ENCLOSURE_LONG - p.getR());
        double yAfterTxCenterToEnclosure = p.getYAfterDt(txCenterToEnclosure);
        if ((yAfterTxCenterToEnclosure + p.getR()) > channelAbove
                || (yAfterTxCenterToEnclosure - p.getR()) < channelBelow) {
            // Todavia no sale del canal
            return new WallCollisionEvent(minTy, p, Wall.HORIZONTAL);
        }
        // Sale del canal
        final double vMagLeave = Math.hypot(p.getVx(), p.getVy());
        final Particle pAfterLeavingChannel = new Particle(
                p.getR(),
                p.getM(),
                vMagLeave,
                ENCLOSURE_LONG,
                yAfterTxCenterToEnclosure,
                Math.atan2(p.getVy(), p.getVx()));
        final double tyChannelMin = Math.min(pAfterLeavingChannel.timeToYCoord(0),
                pAfterLeavingChannel.timeToYCoord(ENCLOSURE_LONG));
        final double txChannel = pAfterLeavingChannel.timeToXCoord(0);
        return txChannel < tyChannelMin
                ? new WallCollisionEvent(txCenterToEnclosure + txChannel, p, Wall.VERTICAL)
                : new WallCollisionEvent(txCenterToEnclosure + tyChannelMin, p, Wall.HORIZONTAL);
    }

    private Event timeToWallCollision(final Particle p) {
        if (inBox(p)) {
            return timeToWallCollisionFromBox(p);
        }
        if (inChannel(p)) {
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
            Event wallCollisionEvent = timeToWallCollision(p);
            pq.add(wallCollisionEvent);
            for (Particle other : this) {
                if (p != other && !calculatedCollision.getOrDefault(other, Map.of()).getOrDefault(p, false)) {
                    calculatedCollision.get(p).put(other, true);
                    Event particleCollisionEvent = p.timeToCollision(other);
                    pq.add(particleCollisionEvent);
                }
            }
        }
        List<Event> nextEvents = new ArrayList<>();
        if (pq.isEmpty())
            return nextEvents;
        Event first = pq.poll();
        nextEvents.add(first);
        double t0 = first.getTime();
        while (!pq.isEmpty()) {
            double ti = pq.peek().getTime();
            double scale = Math.max(1.0, Math.max(Math.abs(t0), Math.abs(ti)));
            if (Math.abs(ti - t0) > EPS * scale)
                break;
            nextEvents.add(pq.poll());
        }
        return nextEvents;
    }

    public void move(double dt) {
        for (Particle p : this) {
            p.move(dt);
        }
    }

    public List<Particle> getParticlesInBorder() {
        List<Particle> borderParticles = new ArrayList<>();
        for (Particle p : this) {
            double x = p.getX();
            double y = p.getY();
            double r = p.getR();

            boolean onBorder = false;

            if (inBox(p)) {
                if (x - r <= 0 + EPS)
                    onBorder = true;
                if (!onBorder && (y - r <= 0 + EPS))
                    onBorder = true;
                if (!onBorder && (y + r >= ENCLOSURE_LONG - EPS))
                    onBorder = true;

                if (!onBorder && (x + r >= ENCLOSURE_LONG - EPS)) {
                    boolean fullyInsideOpening = (y - r >= channelBelow - EPS) && (y + r <= channelAbove + EPS);
                    if (!fullyInsideOpening) {
                        onBorder = true;
                    }
                }
            } else if (inChannel(p)) {
                if (y - r <= channelBelow + EPS)
                    onBorder = true;
                if (!onBorder && (y + r >= channelAbove - EPS))
                    onBorder = true;
                if (!onBorder && (x + r >= 2 * ENCLOSURE_LONG - EPS))
                    onBorder = true;
            }

            if (onBorder)
                borderParticles.add(p);
        }
        return borderParticles;
    }

    public void clampAll() {
        for (Particle p : this) {
            double x = p.getX();
            if (x < p.getR() - EPS)
                x = p.getR();
            if (x > 2 * ENCLOSURE_LONG - p.getR() + EPS)
                x = 2 * ENCLOSURE_LONG - p.getR();

            double y = p.getY();
            if (x < ENCLOSURE_LONG) {
                double ymin = p.getR();
                double ymax = ENCLOSURE_LONG - p.getR();
                if (y < ymin - EPS)
                    y = ymin;
                if (y > ymax + EPS)
                    y = ymax;
            } else if (x < 2 * ENCLOSURE_LONG) {
                double ymin = channelBelow + p.getR();
                double ymax = channelAbove - p.getR();
                if (y < ymin - EPS)
                    y = ymin;
                if (y > ymax + EPS)
                    y = ymax;
            } else {
                double ymin = p.getR();
                double ymax = ENCLOSURE_LONG - p.getR();
                if (y < ymin - EPS)
                    y = ymin;
                if (y > ymax + EPS)
                    y = ymax;
            }

            p.setX(x);
            p.setY(y);
        }
    }

    @Override
    public Iterator<Particle> iterator() {
        return particles.iterator();
    }

    @Override
    public String toString() {
        return particles.toString();
    }
}
