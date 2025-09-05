package simulations;

public abstract class Event implements Comparable<Event> {
    private double time;
    private Particle particle;
    private EventType eventType;

    public Event(double time, Particle particle, EventType eventType) {
        this.time = time;
        this.particle = particle;
        this.eventType = eventType;
    }

    public double getTime() {
        return time;
    }

    public EventType getEventType() {
        return eventType;
    }

    public Particle getParticle() {
        return particle;
    }

    public abstract void processEvent();

    @Override
    public int compareTo(Event other) {
        return Double.compare(this.time, other.time);
    }
}
