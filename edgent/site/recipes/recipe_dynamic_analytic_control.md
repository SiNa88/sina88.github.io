---
title: Dynamically Enabling Analytic Flows
---

This recipe addresses the question: How can I dynamically enable or disable entire portions of my application's analytics?

Imagine a topology that has a variety of analytics that it can perform. Each analytic flow comes with certain costs in terms of demands on the CPU or memory and implications for power consumption. Hence an application may wish to dynamically control whether or not an analytic flow is currently enabled.

## Valve

A `edgent.topology.plumbing.Valve` is a simple construct that can be inserted in stream flows to dynamically enable or disable downstream processing. A valve is either open or closed. When used as a `Predicate` to `TStream.filter()`, `filter` passes tuples only when the valve is open. Hence downstream processing is enabled when the valve is open and effectively disabled when the valve is closed.

For example, consider a a topology consisting of 3 analytic processing flows that want to be dynamically enabled or disabled:

```java
Valve<Readings> flow1Valve = new Valve<>();  // default is open
Valve<Readings> flow2Valve = new Valve<>(false);  // closed
Valve<Readings> flow3Valve = new Valve<>(false);

TStream<Readings> readings = topology.poll(mySensor, 1, TimeUnit.SECONDS);
addAnalyticFlow1(readings.filter(flow1Valve));
addAnalyticFlow2(readings.filter(flow2Valve));
addAnalyticFlow3(readings.filter(flow3Valve));
```

Elsewhere in the application, perhaps as a result of processing some device command from an external service such as when using an `IotProvider` or `IotDevice`, valves may be opened and closed dynamically to achieve the desired effects. For example:

```java
TStream<JsonObject> cmds = simulatedValveCommands(topology);
cmds.sink(json -> {
    String valveId = json.getPrimitive("valve").getAsString();
    boolean isOpen = json.getPrimitive("isOpen").getAsBoolean();
    switch(valveId) {
        case "flow1": flow1Valve.setOpen(isOpen); break;
        case "flow2": flow2Valve.setOpen(isOpen); break;
        case "flow3": flow3Valve.setOpen(isOpen); break;
    }
});
```

## Loosely coupled Edgent applications

Another approach for achieving dynamic control over what analytics flows are running is to utilize loosely coupled applications.

In this approach, the overall application is partitioned into multiple applications (topologies). In the above example there could be four applications: one that publishes the sensor `readings` stream, and one for each of the analytic flows.

The separate applications can connect to each other's streams using the `edgent.connectors.pubsub.PublishSubscribe` connector.

Rather than having all of the analytic applications running all of the time, applications can be registered with a `edgent.topology.services.ApplicationService`. Registered applications can then be started and stopped dynamically.

The `edgent.providers.iot.IotProvider` is designed to facilitate this style of use.
