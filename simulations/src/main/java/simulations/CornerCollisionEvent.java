package simulations;

/**
 * Corner (point-obstacle) collision with a fixed vertex.
 * Updates particle velocity using normal/tangential decomposition:
 *   vn' = -c_n * vn,   vt' = c_t * vt
 * where n is the unit vector from the corner to the particle center at impact
 * and t = (-ny, nx).
 */
public class CornerCollisionEvent extends Event {
    private final double cx; // corner X
    private final double cy; // corner Y
    private final double cn; // normal restitution coefficient
    private final double ct; // tangential restitution coefficient

    public CornerCollisionEvent(double time, Particle particle, double cx, double cy) {
        this(time, particle, cx, cy, 1.0, 1.0);
    }

    public CornerCollisionEvent(double time, Particle particle, double cx, double cy, double cn, double ct) {
        super(time, particle, EventType.CORNER_COLLISION);
        this.cx = cx;
        this.cy = cy;
        this.cn = cn;
        this.ct = ct;
    }

    @Override
    public void processEvent() {
        Particle p = getParticle();
        // Unit normal from corner to particle center (at collision time)
        double nx = p.getX() - cx;
        double ny = p.getY() - cy;
        double norm = Math.hypot(nx, ny);
        if (norm == 0.0) {
            // Degenerate; nothing to do
            return;
        }
        nx /= norm;
        ny /= norm;
        // Tangent: rotate normal by +90°
        double tx = -ny;
        double ty = nx;

        // Project velocity onto n and t
        double vx = p.getVx();
        double vy = p.getVy();
        double vn = vx * nx + vy * ny;
        double vt = vx * tx + vy * ty;

        // Apply restitution
        double vnAfter = -cn * vn;
        double vtAfter = ct * vt;

        // Recompose
        double vxAfter = vnAfter * nx + vtAfter * tx;
        double vyAfter = vnAfter * ny + vtAfter * ty;
        p.setVx(vxAfter);
        p.setVy(vyAfter);
    }
}

