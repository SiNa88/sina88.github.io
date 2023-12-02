---
title: Changing a filter's range
---

The [Detecting a sensor value out of range](recipe_value_out_of_range.html) recipe introduced the basics of filtering as well as the use of a [Range]({{ site.docsurl }}/index.html?org/apache/{{ site.data.project.unix_name }}/analytics/sensors/Range.html).

Oftentimes, a user wants a filter's behavior to be adaptable rather than static. A filter's range can be made changeable via commands from some external source or just changed as a result of some other local analytics.

An Edgent `IotProvider` and `IoTDevice` with its command streams would be a natural way to control the application. In this recipe we will just simulate a "set optimal temp range" command stream.

The string form of a `Range` is natural, consise, and easy to use. As such it's a convenient form to use as external range format. The range string can easily be converted back into a `Range`.

We're going to assume familiarity with that earlier recipe and those concepts and focus on just the "adaptable range specification" aspect of this recipe.

## Define the range

A `java.util.concurrent.atomic.AtomicReference` is used to provide the necessary thread synchronization.

```java
static Range<Double> DEFAULT_TEMP_RANGE = Ranges.valueOfDouble("[77.0..91.0]");
static AtomicReference<Range<Double>> optimalTempRangeRef =
        new AtomicReference<>(DEFAULT_TEMP_RANGE);
```

## Define a method to change the range

```java
static void setOptimalTempRange(Range<Double> range) {
    System.out.println("Using optimal temperature range: " + range);
    optimalTempRangeRef.set(range);
}
```

The filter just uses `optimalTempRangeRef.get()` to use the current range setting.

## Simulate a command stream

A `TStream<Range<Double>> setRangeCmds` stream is created and a new range specification tuple is generated every 10 seconds.  A `sink()` on the stream calls `setOptimalTempRange()` to change the range and hence the filter's bahavior.

```java
// Simulate a command stream to change the optimal range.
// Such a stream might be from an IotDevice command.
String[] ranges = new String[] {
    "[70.0..120.0]", "[80.0..130.0]", "[90.0..140.0]",
};
AtomicInteger count = new AtomicInteger(0);
TStream<Range<Double>> setRangeCmds = top.poll(()
        -> Ranges.valueOfDouble(ranges[count.incrementAndGet() % ranges.length]),
        10, TimeUnit.SECONDS);

setRangeCmds.sink(tuple -> setOptimalTempRange(tuple));
```

## The final application

```java
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;

import org.apache.edgent.analytics.sensors.Range;
import org.apache.edgent.analytics.sensors.Ranges;
import org.apache.edgent.providers.direct.DirectProvider;
import org.apache.edgent.samples.utils.sensor.SimulatedTemperatureSensor;
import org.apache.edgent.topology.TStream;
import org.apache.edgent.topology.Topology;

/**
 * Detect a sensor value out of expected range.
 * Simulate an adaptable range changed by external commands.
 */
public class AdaptableFilterRange {
    /**
     * Optimal temperatures (in Fahrenheit)
     */
    static Range<Double> DEFAULT_TEMP_RANGE = Ranges.valueOfDouble("[77.0..91.0]");
    static AtomicReference<Range<Double>> optimalTempRangeRef =
            new AtomicReference<>(DEFAULT_TEMP_RANGE);

    static void setOptimalTempRange(Range<Double> range) {
        System.out.println("Using optimal temperature range: " + range);
        optimalTempRangeRef.set(range);
    }

    /**
     * Polls a simulated temperature sensor to periodically obtain
     * temperature readings (in Fahrenheit). Use a simple filter
     * to determine when the temperature is out of the optimal range.
     */
    public static void main(String[] args) throws Exception {

        DirectProvider dp = new DirectProvider();

        Topology top = dp.newTopology("TemperatureSensor");

        // Generate a stream of temperature sensor readings
        SimulatedTemperatureSensor tempSensor = new SimulatedTemperatureSensor();
        TStream<Double> temp = top.poll(tempSensor, 1, TimeUnit.SECONDS);

        // Simple filter: Perform analytics on sensor readings to detect when
        // the temperature is out of the optimal range and generate warnings
        TStream<Double> simpleFiltered = temp.filter(tuple ->
                !optimalTempRangeRef.get().contains(tuple));
        simpleFiltered.sink(tuple -> System.out.println("Temperature is out of range! "
                + "It is " + tuple + "\u00b0F!"));

        // See what the temperatures look like
        temp.print();

        // Simulate a command stream to change the optimal range.
        // Such a stream might be from an IotDevice command.
        String[] ranges = new String[] {
            "[70.0..120.0]", "[80.0..130.0]", "[90.0..140.0]",
        };
        AtomicInteger count = new AtomicInteger(0);
        TStream<Range<Double>> setRangeCmds = top.poll(
                () -> Ranges.valueOfDouble(ranges[count.incrementAndGet() % ranges.length]),
                10, TimeUnit.SECONDS);

        setRangeCmds.sink(tuple -> setOptimalTempRange(tuple));

        dp.submit(top);
    }
}
```
