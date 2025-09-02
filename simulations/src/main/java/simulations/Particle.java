package simulations;

public class Particle {
    public static final double r = 0.0015;
    public static final double m = 1;
    public static final double v = 0.01;

    private double vx, vy, x, y;

    public Particle(double x, double y, double theta) {
        this.x = x;
        this.y = y;
        this.vx = v * Math.cos(theta);
        this.vy = v * Math.sin(theta);
    }

    public boolean isInside(double x, double y) {
        double dx = x - this.x;
        double dy = y - this.y;
        return dx * dx + dy * dy < r * r;
    }

    public double getR() {
        return r;
    }

    public double getM() {
        return m;
    }

    public double getV() {
        return v;
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

    @Override
    public String toString() {
        return String.format("X = %f, Y = %f, vx = %f, vy = %f", x, y, vx, vy);
    }
}
