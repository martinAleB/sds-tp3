package simulations;

public class WallCollisionEvent extends Event {
    private Wall wall;

    public WallCollisionEvent(double time, Particle particle, Wall wall) {
        super(time, particle, EventType.WALL_COLLISION);
        this.wall = wall;
    }

    @Override
    public void processEvent() {
        Particle p = getParticle();
        if (wall == Wall.VERTICAL) {
            p.invertVy();
        } else if (wall == Wall.HORIZONTAL) {
            p.invertVx();
        }
    }
}
