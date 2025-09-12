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
        // Caso 1: choque con obstáculo fijo (una sola partícula móvil)
        boolean pFixed = p.isFixed();
        boolean qFixed = q.isFixed();
        if ((pFixed && !qFixed) || (!pFixed && qFixed)) {
            // Tomo como móvil a 'm' y como fijo a 'f'
            final Particle m = pFixed ? q : p;
            final Particle f = pFixed ? p : q;

            // Vector normal en el punto de contacto (desde fijo hacia móvil)
            double dx = m.getX() - f.getX();
            double dy = m.getY() - f.getY();

            // Ángulo del versor normal con el eje x
            double alpha = Math.atan2(dy, dx);
            double c = Math.cos(alpha);
            double s = Math.sin(alpha);

            // Coeficientes de restitución (normal y tangencial)
            // Para choques elásticos sin disipación: cn = 1, ct = 1
            final double cn = 1.0;
            final double ct = 1.0;

            // Operador de colisión: v' = R(-α) S(cn,ct) R(α) v
            // Matriz resultante (diapo):
            // [ -cn c^2 + ct s^2      -(cn+ct) s c ]
            // [ -(cn+ct) s c          -cn s^2 + ct c^2 ]
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

        // Caso 2: ambas móviles (manejo existente con impulso para masas iguales)
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

        // Evitar divisiones por cero si hubiera solapamiento extremo o datos degenerados
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
