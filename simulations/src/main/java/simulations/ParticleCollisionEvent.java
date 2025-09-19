package simulations;

public class ParticleCollisionEvent extends Event {
    private final Particle other;

    public ParticleCollisionEvent(double time, Particle p, Particle other) {
        super(time, p, EventType.PARTICLE_COLLISION);
        this.other = other;
    }

    public Particle getP() {
        return super.getParticle();
    }

    public Particle getOther() {
        return other;
    }

    @Override
    public void processEvent() {
        Particle p = this.getParticle();
        Particle q = this.getOther();
        boolean pFixed = p.isFixed();
        boolean qFixed = q.isFixed();
        if ((pFixed && !qFixed) || (!pFixed && qFixed)) {
            final Particle m = pFixed ? q : p;
            final Particle f = pFixed ? p : q;

            double dx = m.getX() - f.getX();
            double dy = m.getY() - f.getY();

            double alpha = Math.atan2(dy, dx);
            double c = Math.cos(alpha);
            double s = Math.sin(alpha);

            final double cn = 1.0;
            final double ct = 1.0;

            double m11 = (-cn * c * c) + (ct * s * s);
            double m12 = (-(cn + ct) * s * c);
            double m21 = m12;
            double m22 = (-cn * s * s) + (ct * c * c);

            double vx = m.getVx();
            double vy = m.getVy();
            double vxp = m11 * vx + m12 * vy;
            double vyp = m21 * vx + m22 * vy;

            m.setVx(vxp);
            m.setVy(vyp);
            return;
        }

        double dx = q.getX() - p.getX();
        double dy = q.getY() - p.getY();
        double dvx = q.getVx() - p.getVx();
        double dvy = q.getVy() - p.getVy();

        double rv = dx * dvx + dy * dvy;

        double mi = p.getM();
        double mj = q.getM();

        double sigma = (p.getR() + q.getR());

        if (sigma == 0.0)
            return;

        double J = (2.0 * mi * mj * rv) / (sigma * (mi + mj));

        double Jx = J * dx / sigma;
        double Jy = J * dy / sigma;

        p.setVx(p.getVx() + Jx / mi);
        p.setVy(p.getVy() + Jy / mi);

        q.setVx(q.getVx() - Jx / mj);
        q.setVy(q.getVy() - Jy / mj);
    }
}
