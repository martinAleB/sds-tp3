package simulations;

public class Particle {
    private static int idCounter = 1;

    public static final double R_DEFAULT = 0.0015;
    public static final double M_DEFAULT = 1;
    public static final double V_DEFAULT = 0.01;

    private int id;
    private double r, m, vx, vy, x, y;
    private boolean fixed = false;

    public Particle(double x, double y, double theta) {
        this(R_DEFAULT, M_DEFAULT, V_DEFAULT, x, y, theta);
    }

    public Particle(double r, double m, double v, double x, double y, double theta) {
        this.id = idCounter++;
        this.r = r;
        this.m = m;
        this.x = x;
        this.y = y;
        this.vx = v * Math.cos(theta);
        this.vy = v * Math.sin(theta);
    }

    public Particle(double x, double y) {
        // Para los obstaculos
        this(0, 0, 0, x, y, 0);
        this.fixed = true;
    }

    public boolean isInside(double x, double y) {
        double dx = x - this.x;
        double dy = y - this.y;
        return dx * dx + dy * dy < r * r;
    }

    public double timeToXCoord(double xcoord) {
        if (vx > 0 && xcoord >= (this.x + r))
            return (xcoord - (this.x + r)) / vx;
        if (vx < 0 && xcoord <= (this.x - r))
            return (xcoord - (this.x - r)) / vx;
        return Double.POSITIVE_INFINITY;
    }

    public double timeToYCoord(double ycoord) {
        if (vy > 0 && ycoord >= (this.y + r))
            return (ycoord - (this.y + r)) / vy;
        if (vy < 0 && ycoord <= (this.y - r))
            return (ycoord - (this.y - r)) / vy;
        return Double.POSITIVE_INFINITY;
    }

    public Event timeToCollision(Particle other) {
        double dx = other.x - this.x;
        double dy = other.y - this.y;
        double dvx = other.vx - this.vx;
        double dvy = other.vy - this.vy;

        double rv = dx * dvx + dy * dvy;
        double vv = dvx * dvx + dvy * dvy;
        double rr = dx * dx + dy * dy;
        double sigma = this.r + other.r;

        if (vv == 0.0) {
            return new ParticleCollisionEvent((rr <= sigma * sigma) ? 0.0 : Double.POSITIVE_INFINITY, this, other);
        }

        if (rv >= 0.0)
            return new ParticleCollisionEvent(Double.POSITIVE_INFINITY, this, other);

        double d = rv * rv - vv * (rr - sigma * sigma);
        if (d < 0.0)
            return new ParticleCollisionEvent(Double.POSITIVE_INFINITY, this, other);

        double t = -(rv + Math.sqrt(d)) / vv;
        return new ParticleCollisionEvent((t >= 0.0) ? t : Double.POSITIVE_INFINITY, this, other);
    }

    public double getXAfterDt(double dt) {
        return x + vx * dt;
    }

    public double getYAfterDt(double dt) {
        return y + vy * dt;
    }

    public void move(double dt) {
        x = getXAfterDt(dt);
        y = getYAfterDt(dt);
    }

    public boolean isFixed() {
        return fixed;
    }

    public int getId() {
        return id;
    }

    public double getR() {
        return r;
    }

    public double getM() {
        return m;
    }

    public double getVx() {
        return vx;
    }

    public double getVy() {
        return vy;
    }

    public double getX() {
        return x;
    }

    public double getY() {
        return y;
    }

    public void setX(double x) {
        this.x = x;
    }

    public void setY(double y) {
        this.y = y;
    }

    public void invertVx() {
        setVx(-vx);
    }

    public void invertVy() {
        setVy(-vy);
    }

    public void setVx(double vx) {
        this.vx = vx;
    }

    public void setVy(double vy) {
        this.vy = vy;
    }

    @Override
    public String toString() {
        return String.format("Particle[id = %d, X = %f, Y = %f, vx = %f, vy = %f]", id, x, y, vx, vy);
    }

    @Override
    public boolean equals(Object obj) {
        return this == obj || (obj instanceof Particle other &&
                Double.compare(x, other.x) == 0 &&
                Double.compare(y, other.y) == 0 &&
                Double.compare(r, other.r) == 0 &&
                Double.compare(m, other.m) == 0 &&
                Double.compare(vx, other.vx) == 0 &&
                Double.compare(vy, other.vy) == 0);
    }

    @Override
    public int hashCode() {
        return java.util.Objects.hash(x, y, r, m, vx, vy);
    }
}
