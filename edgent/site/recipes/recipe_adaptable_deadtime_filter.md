---
title: Using an adaptable deadtime filter
---

Oftentimes, an application wants to control the frequency that continuously generated analytic results are made available to other parts of the application or published to other applications or an event hub.

For example, an application polls an engine temperature sensor every second and performs various analytics on each reading &mdash; an analytic result is generated every second. By default, the application only wants to publish a (healthy) analytic result every 30 minutes. However, under certain conditions, the desire is to publish every per-second analytic result.

Such a condition may be locally detected, such as detecting a sudden rise in the engine temperature or it may be as a result of receiving some external command to change the publishing frequency.

Note this is a different case than simply changing the polling frequency for the sensor as doing that would disable local continuous monitoring and analysis of the engine temperature.

This case needs a *deadtime filter* and Edgent provides one for your use! In contrast to a *deadband filter*, which skips tuples based on a deadband value range, a deadtime filter skips tuples based on a *deadtime period* following a tuple that is allowed to pass through. For example, if the deadtime period is 30 minutes, after allowing a tuple to pass, the filter skips any tuples received for the next 30 minutes. The next tuple received after that is allowed to pass through, and a new deadtime period is begun.

See `edgent.analytics.sensors.Filters.deadtime()` (on [GitHub]({{ site.data.project.source_repository_mirror }}/blob/master/analytics/sensors/src/main/java/org/apache/{{ site.data.project.unix_name }}/analytics/sensors/Filters.java)) and `edgent.analytics.sensors.Deadtime` (on [GitHub]({{ site.data.project.source_repository_mirror }}/blob/master/analytics/sensors/src/main/java/org/apache/{{ site.data.project.unix_name }}/analytics/sensors/Deadtime.java)).

This recipe demonstrates how to use an adaptable deadtime filter.

An Edgent `IotProvider` ad `IoTDevice` with its command streams would be a natural way to control the application. In this recipe we will just simulate a "set deadtime period" command stream.

## Create a polled sensor readings stream

```java
Topology top = ...;
SimulatedTemperatureSensor tempSensor = new SimulatedTemperatureSensor();
TStream<Double> engineTemp = top.poll(tempSensor, 1, TimeUnit.SECONDS)
                              .tag("engineTemp");
```

It's also a good practice to add tags to streams to improve the usability of the development mode Edgent console.

## Create a deadtime filtered stream&mdash;initially no deadtime

In this recipe we'll just filter the direct ``engineTemp`` sensor reading stream. In practice this filtering would be performed after some analytics stages and used as the input to ``IotDevice.event()`` or some other connector publish operation.

```java
Deadtime<Double> deadtime = new Deadtime<>();
TStream<Double> deadtimeFilteredEngineTemp = engineTemp.filter(deadtime)
                              .tag("deadtimeFilteredEngineTemp");
```

## Define a "set deadtime period" method

```java
static <T> void setDeadtimePeriod(Deadtime<T> deadtime, long period, TimeUnit unit) {
    System.out.println("Setting deadtime period="+period+" "+unit);
    deadtime.setPeriod(period, unit);
}
```

## Process the "set deadtime period" command stream

Our commands are on the ``TStream<JsonObject> cmds`` stream. Each ``JsonObject`` tuple is a command with the properties "period" and "unit".

```java
cmds.sink(json -> setDeadtimePeriod(deadtimeFilteredEngineTemp,
    json.getAsJsonPrimitive("period").getAsLong(),
    TimeUnit.valueOf(json.getAsJsonPrimitive("unit").getAsString())));
```

## The final application

When the application is run it will initially print out temperature sensor readings every second for 15 seconds&mdash;the deadtime period is 0. Then every 15 seconds the application will toggle the deadtime period between 5 seconds and 0 seconds, resulting in a reduction in tuples being printed during the 5 second deadtime period.

```java
import java.util.Date;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

import com.google.gson.JsonObject;

import org.apache.edgent.analytics.sensors.Deadtime;
import org.apache.edgent.console.server.HttpServer;
import org.apache.edgent.providers.development.DevelopmentProvider;
import org.apache.edgent.providers.direct.DirectProvider;
import org.apache.edgent.samples.utils.sensor.SimulatedTemperatureSensor;
import org.apache.edgent.topology.TStream;
import org.apache.edgent.topology.Topology;

/**
 * A recipe for using an Adaptable Deadtime Filter.
 */
public class AdaptableDeadtimeFilterRecipe {

    /**
     * Poll a temperature sensor to periodically obtain temperature readings.
     * Create a "deadtime" filtered stream: after passing a tuple,
     * any tuples received during the "deadtime" are filtered out.
     * Then the next tuple is passed through and a new deadtime period begun.
     *
     * Respond to a simulated command stream to change the deadtime window
     * duration.
     */
    public static void main(String[] args) throws Exception {

        DirectProvider dp = new DevelopmentProvider();
        System.out.println("development console url: "
                + dp.getServices().getService(HttpServer.class).getConsoleUrl());

        Topology top = dp.newTopology("TemperatureSensor");

        // Generate a polled temperature sensor stream and set it alias
        SimulatedTemperatureSensor tempSensor = new SimulatedTemperatureSensor();
        TStream<Double> engineTemp = top.poll(tempSensor, 1, TimeUnit.SECONDS)
                                      .tag("engineTemp");

        // Filter out tuples during the specified "deadtime window"
        // Initially no filtering.
        Deadtime<Double> deadtime = new Deadtime<>();
        TStream<Double> deadtimeFilteredEngineTemp =
                engineTemp.filter(deadtime)
                    .tag("deadtimeFilteredEngineTemp");

        // Report the time each temperature reading arrives and the value
        deadtimeFilteredEngineTemp.peek(tuple -> System.out.println(new Date() + " temp=" + tuple));

        // Generate a simulated "set deadtime period" command stream
        TStream<JsonObject> cmds = simulatedSetDeadtimePeriodCmds(top);

        // Process the commands to change the deadtime window period
        cmds.sink(json -> setDeadtimePeriod(deadtime,
            json.getAsJsonPrimitive("period").getAsLong(),
            TimeUnit.valueOf(json.getAsJsonPrimitive("unit").getAsString())));

        dp.submit(top);
    }

    static <T> void setDeadtimePeriod(Deadtime<T> deadtime, long period, TimeUnit unit) {
        System.out.println("Setting deadtime period="+period+" "+unit);
        deadtime.setPeriod(period, unit);
    }

    static TStream<JsonObject> simulatedSetDeadtimePeriodCmds(Topology top) {
        AtomicInteger lastPeriod = new AtomicInteger(-1);
        TStream<JsonObject> cmds = top.poll(() -> {
                // don't change on first invocation
                if (lastPeriod.get() == -1) {
                    lastPeriod.incrementAndGet();
                    return null;
                }
                // toggle between 0 and 5 sec deadtime period
                int newPeriod = lastPeriod.get() == 5 ? 0 : 5;
                lastPeriod.set(newPeriod);
                JsonObject jo = new JsonObject();
                jo.addProperty("period", newPeriod);
                jo.addProperty("unit", TimeUnit.SECONDS.toString());
                return jo;
            }, 15, TimeUnit.SECONDS)
            .tag("cmds");
        return cmds;
    }

}
```
