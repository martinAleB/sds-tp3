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

        // Δr y Δv (en el instante del choque)
        double dx = q.getX() - p.getX();
        double dy = q.getY() - p.getY();
        double dvx = q.getVx() - p.getVx();
        double dvy = q.getVy() - p.getVy();

        // Productos escalares
        double rv = dx * dvx + dy * dvy; // Δv · Δr

        // Masas
        double mi = p.getM();
        double mj = q.getM();

        // σ = Ri + Rj (en el contacto también vale |Δr| ≈ σ)
        double sigma = (p.getR() + q.getR());

        // Evitar divisiones por cero si hubiera solapamiento extremo o datos
        // degenerados
        if (sigma == 0.0)
            return;

        // J escalar (diapo)
        double J = (2.0 * mi * mj * rv) / (sigma * (mi + mj));

        // Componentes del impulso
        double Jx = J * dx / sigma;
        double Jy = J * dy / sigma;

        // Actualización de velocidades (antes -> después)
        p.setVx(p.getVx() + Jx / mi);
        p.setVy(p.getVy() + Jy / mi);

        q.setVx(q.getVx() - Jx / mj);
        q.setVy(q.getVy() - Jy / mj);
    }
}
