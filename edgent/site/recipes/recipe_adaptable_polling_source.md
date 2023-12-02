---
title: Changing a polled source stream's period
---

The [Writing a source function](recipe_source_function.html) recipe introduced the basics of creating a source stream by polling a data source periodically.

Oftentimes, a user wants the poll frequency to be adaptable rather than static. For example, an event such as a sudden rise in a temperature sensor may motivate more frequent polling of the sensor and analysis of the data until the condition subsides. A change in the poll frequency may be driven by locally performed analytics or via a command from an external source.

An Edgent `IotProvider` and `IoTDevice` with its command streams would be a natural way to control the application. In this recipe we will just simulate a "set poll period" command stream.

The `Topology.poll()` [documentation]({{ site.docsurl }}/org/apache/{{ site.data.project.unix_name }}/topology/Topology.html#poll-org.apache.{{ site.data.project.unix_name }}.function.Supplier-long-java.util.concurrent.TimeUnit-) describes how the poll period may be changed at runtime.

The mechanism is based on a more general Edgent runtime `edgent.execution.services.ControlService` service. The runtime registers "control beans" for entities that are controllable. These controls can be retrieved at runtime via the service.

At runtime, `Topology.poll()` registers a `edgent.execution.mbeans.PeriodMXBean` control. __Retrieving the control at runtime requires setting an alias on the poll generated stream using `TStream.alias()`.__

## Create the polled stream and set its alias

```java
Topology top = ...;
SimulatedTemperatureSensor tempSensor = new SimulatedTemperatureSensor();
TStream<Double> engineTemp = top.poll(tempSensor, 1, TimeUnit.SECONDS)
                              .alias("engineTemp")
                              .tag("engineTemp");
```

It's also a good practice to add tags to streams to improve the usability of the development mode Edgent console.

## Define a "set poll period" method

```java
static <T> void setPollPeriod(TStream<T> pollStream, long period, TimeUnit unit) {
    // get the topology's runtime ControlService service
    ControlService cs = pollStream.topology().getRuntimeServiceSupplier()
                                .get().getService(ControlService.class);

    // using the the stream's alias, get its PeriodMXBean control
    PeriodMXBean control = cs.getControl(TStream.TYPE, pollStream.getAlias(), PeriodMXBean.class);

    // change the poll period using the control
    System.out.println("Setting period="+period+" "+unit+" stream="+pollStream);
    control.setPeriod(period, unit);
}
```

## Process the "set poll period" command stream

Our commands are on the `TStream<JsonObject> cmds` stream. Each `JsonObject` tuple is a command with the properties "period" and "unit".

```java
cmds.sink(json -> setPollPeriod(engineTemp,
    json.getAsJsonPrimitive("period").getAsLong(),
    TimeUnit.valueOf(json.getAsJsonPrimitive("unit").getAsString())));
```

## The final application

```java
import java.util.Date;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

import com.google.gson.JsonObject;

import org.apache.edgent.execution.mbeans.PeriodMXBean;
import org.apache.edgent.execution.services.ControlService;
import org.apache.edgent.providers.development.DevelopmentProvider;
import org.apache.edgent.providers.direct.DirectProvider;
import org.apache.edgent.samples.utils.sensor.SimulatedTemperatureSensor;
import org.apache.edgent.topology.TStream;
import org.apache.edgent.topology.Topology;

/**
 * A recipe for a polled source stream with an adaptable poll period.
 */
public class AdaptablePolledSource {

    /**
     * Poll a temperature sensor to periodically obtain temperature readings.
     * Respond to a simulated command stream to change the poll period.
     */
    public static void main(String[] args) throws Exception {

        DirectProvider dp = new DirectProvider();

        Topology top = dp.newTopology("TemperatureSensor");

        // Generate a polled temperature sensor stream and set its alias
        SimulatedTemperatureSensor tempSensor = new SimulatedTemperatureSensor();
        TStream<Double> engineTemp = top.poll(tempSensor, 1, TimeUnit.SECONDS)
                                      .alias("engineTemp")
                                      .tag("engineTemp");

        // Report the time each temperature reading arrives and the value
        engineTemp.peek(tuple -> System.out.println(new Date() + " temp=" + tuple));

        // Generate a simulated "set poll period" command stream
        TStream<JsonObject> cmds = simulatedSetPollPeriodCmds(top);

        // Process the commands to change the poll period
        cmds.sink(json -> setPollPeriod(engineTemp,
            json.getAsJsonPrimitive("period").getAsLong(),
            TimeUnit.valueOf(json.getAsJsonPrimitive("unit").getAsString())));

        dp.submit(top);
    }

    static <T> void setPollPeriod(TStream<T> pollStream, long period, TimeUnit unit) {
        // get the topology's runtime ControlService service
        ControlService cs = pollStream.topology().getRuntimeServiceSupplier()
                                    .get().getService(ControlService.class);

        // using the the stream's alias, get its PeriodMXBean control
        PeriodMXBean control = cs.getControl(TStream.TYPE, pollStream.getAlias(), PeriodMXBean.class);

        // change the poll period using the control
        System.out.println("Setting period="+period+" "+unit+" stream="+pollStream);
        control.setPeriod(period, unit);
    }

    static TStream<JsonObject> simulatedSetPollPeriodCmds(Topology top) {
        AtomicInteger lastPeriod = new AtomicInteger(1);
        TStream<JsonObject> cmds = top.poll(() -> {
                // toggle between 1 and 2 sec period
                int newPeriod = lastPeriod.get() == 1 ? 2 : 1;
                lastPeriod.set(newPeriod);
                JsonObject jo = new JsonObject();
                jo.addProperty("period", newPeriod);
                jo.addProperty("unit", TimeUnit.SECONDS.toString());
                return jo;
            }, 5, TimeUnit.SECONDS)
            .tag("cmds");
        return cmds;
    }

}
```
