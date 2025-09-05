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
        if (wall == Wall.X_AXIS_WALL) {
            p.invertVy();
        } else if (wall == Wall.Y_AXIS_WALL) {
            p.invertVx();
        }
    }
}
