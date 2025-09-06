package simulations;

public class ParticleCollisionEvent extends Event {
    private final Particle other;

    public ParticleCollisionEvent(double time, Particle p, Particle other) {
        super(time, p, EventType.PARTICLE_COLLISION);
        this.other = other;
    }

    public Particle getP() {
        return this.getP();
    }

    public Particle getOther() {
        return other;
    }

    @Override
    public void processEvent() {
        Particle p = this.getParticle();
        Particle q = this.getOther();

        // Vectores relativos
        double dx = q.getX() - p.getX();
        double dy = q.getY() - p.getY();
        double dvx = q.getVx() - p.getVx();
        double dvy = q.getVy() - p.getVy();

        // Escalares útiles
        double rv = dx * dvx + dy * dvy; // Δr · Δv
        double mTotal = p.getM() + q.getM(); // m1 + m2
        double J = (2 * p.getM() * q.getM() * rv) / (mTotal); // Impulso escalar

        // Actualizar velocidades
        p.setVx(p.getVx() + J * dx / (p.getM() * Math.sqrt(dx * dx + dy * dy)));
        p.setVy(p.getVy() + J * dy / (p.getM() * Math.sqrt(dx * dx + dy * dy)));
        q.setVx(q.getVx() - J * dx / (q.getM() * Math.sqrt(dx * dx + dy * dy)));
        q.setVy(q.getVy() - J * dy / (q.getM() * Math.sqrt(dx * dx + dy * dy)));
    }
}
