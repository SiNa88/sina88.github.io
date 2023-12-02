---
title: How can I run several analytics on a tuple concurrently?
---

If you have several independent lengthy analytics to perform on each tuple, you may determine that it would be advantageous to perform the analytics concurrently and then combine their results.

The overall proessing time for a single tuple is then roughly that of the slowest analytic pipeline instead of the aggregate of each analytic pipeline.

This usage model is in contrast to what's often referred to as _parallel_ tuple processing where several tuples are processed in parallel in replicated pipeline channels.

e.g., for independent analytic pipelines A1, A2, and A3, you want to change the serial processing flow graph from:

```
sensorReadings<T> -> A1 -> A2 -> A3 -> results<R>
```

to a flow where the analytics run concurrently in a flow like:

```
                     |-> A1 ->|
sensorReadings<T> -> |-> A2 ->| -> results<R>
                     |-> A3 ->|
```

The key to the above flow is to use a _barrier_ to synchronize the results from each of the pipelines so they can be combined into a single result tuple.  Each of the concurrent channels also needs a thread to run its analytic pipeline.

`PlumbingStreams.concurrent()` builds a concurrent flow graph for you.  Alternatively, you can use `PlumbingStreams.barrier()` and `PlumbingStreams.isolate()` and build a concurrent flow graph yourself.

More specifically `concurrent()` generates a flow like:

```
          |-> isolate(1) -> pipeline1 -> |
stream -> |-> isolate(1) -> pipeline2 -> |-> barrier(10) -> combiner 
          |-> isolate(1) -> pipeline3 -> |
```

It's easy to use `concurrent()`!

## Define the collection of analytic pipelines to run

For the moment assume we have defined methods to create each pipeline: `a1pipeline()`, `a2pipeline()` and `a3pipeline()`. In this simple recipe each pipeline receives a `TStream<Double>` as input and generates a `TStream<String>` as output.

```java
List<Function<TStream<Double>, TStream<String>>> pipelines = new ArrayList<>();
pipelines.add(a1pipeline());
pipelines.add(a2pipeline());
pipelines.add(a3pipeline());
```

## Define the result combiner

Each pipeline creates one result tuple for each input tuple.  The `barrier` collects one tuple from each pipeline and then creates a list of those tuples. The combiner is invoked with that list to generate the final aggregate result tuple.

In this recipe the combiner is a simple lambda function that returns the input list:

```java
Function<List<String>, List<String>> combiner = list -> list;
```

## Build the concurrent flow

```java
TStream<List<String>> results = PlumbingStreams.concurrent(readings, pipelines, combiner);
```

## Define your analytic pipelines

For each analytic pipeline, define a `Function<TStream<T>, TStream<U>>` that will create the pipeline.  That is, define a function that takes a `TStream<T>` as its input and yields a `TStream<U>` as its result.  Of course, `U` can be the same type as `T`.

In this recipe we'll just define some very simple pipelines and use sleep to simulate some long processing times.

Here's the A3 pipeline builder:

```java
static Function<TStream<Double>,TStream<String>> a3pipeline() {
    // simple 3 stage pipeline simulating some amount of work by sleeping
    return stream -> stream.map(tuple -> {
        sleep(800, TimeUnit.MILLISECONDS);
        return "This is the a3pipeline result for tuple "+tuple;
      }).tag("a3.stage1")
      .map(Functions.identity()).tag("a3.stage2")
      .map(Functions.identity()).tag("a3.stage3");
}
```

## The final application

When the application is run it prints out an aggregate result (a list of one tuple from each pipeline) every second. If the three pipelines were run serially, it would take on the order of 2.4 seconds to generate each aggregate result.

```java
package edgent.samples.topology;

import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.concurrent.TimeUnit;

import org.apache.edgent.console.server.HttpServer;
import org.apache.edgent.function.Function;
import org.apache.edgent.function.Functions;
import org.apache.edgent.providers.development.DevelopmentProvider;
import org.apache.edgent.providers.direct.DirectProvider;
import org.apache.edgent.samples.utils.sensor.SimpleSimulatedSensor;
import org.apache.edgent.topology.TStream;
import org.apache.edgent.topology.Topology;
import org.apache.edgent.topology.plumbing.PlumbingStreams;

/**
 * A recipe for concurrent analytics.
 */
public class ConcurrentRecipe {

    /**
     * Concurrently run a collection of long running independent
     * analytic pipelines on each tuple.
     */
    public static void main(String[] args) throws Exception {

        DirectProvider dp = new DevelopmentProvider();
        System.out.println("development console url: "
                + dp.getServices().getService(HttpServer.class).getConsoleUrl());

        Topology top = dp.newTopology("ConcurrentRecipe");
        
        // Define the list of independent unique analytic pipelines to include
        List<Function<TStream<Double>,TStream<String>>> pipelines = new ArrayList<>();
        pipelines.add(a1pipeline());
        pipelines.add(a2pipeline());
        pipelines.add(a3pipeline());
        
        // Define the result combiner function.  The combiner receives 
        // a tuple containing a list of tuples, one from each pipeline, 
        // and returns a result tuple of any type from them.
        // In this recipe we'll just return the list.
        Function<List<String>,List<String>> combiner = list -> list;
        
        // Generate a polled simulated sensor stream
        SimpleSimulatedSensor sensor = new SimpleSimulatedSensor();
        TStream<Double> readings = top.poll(sensor, 1, TimeUnit.SECONDS)
                                      .tag("readings");
        
        // Build the concurrent analytic pipeline flow
        TStream<List<String>> results = 
            PlumbingStreams.concurrent(readings, pipelines, combiner)
            .tag("results");
        
        // Print out the results.
        results.sink(list -> System.out.println(new Date().toString() + " results tuple: " + list));

        System.out.println("Notice how an aggregate result is generated every second."
            + "\nEach aggregate result would take 2.4sec if performed serially.");
        dp.submit(top);
    }
    
    /** Function to create analytic pipeline a1 and add it to a stream */
    private static Function<TStream<Double>,TStream<String>> a1pipeline() {
        // a simple 1 stage pipeline simulating some amount of work by sleeping
        return stream -> stream.map(tuple -> {
            sleep(800, TimeUnit.MILLISECONDS);
            return "This is the a1pipeline result for tuple "+tuple;
          }).tag("a1.stage1");
    }
    
    /** Function to create analytic pipeline a2 and add it to a stream */
    private static Function<TStream<Double>,TStream<String>> a2pipeline() {
        // a simple 2 stage pipeline simulating some amount of work by sleeping
        return stream -> stream.map(tuple -> {
            sleep(800, TimeUnit.MILLISECONDS);
            return "This is the a2pipeline result for tuple "+tuple;
          }).tag("a2.stage1")
          .map(Functions.identity()).tag("a2.stage2");
    }
    
    /** Function to create analytic pipeline a3 and add it to a stream */
    private static Function<TStream<Double>,TStream<String>> a3pipeline() {
        // a simple 3 stage pipeline simulating some amount of work by sleeping
        return stream -> stream.map(tuple -> {
            sleep(800, TimeUnit.MILLISECONDS);
            return "This is the a3pipeline result for tuple "+tuple;
          }).tag("a3.stage1")
          .map(Functions.identity()).tag("a3.stage2")
          .map(Functions.identity()).tag("a3.stage3");
    }

    private static void sleep(long period, TimeUnit unit) throws RuntimeException {
        try {
            Thread.sleep(unit.toMillis(period));
        } catch (InterruptedException e) {
            throw new RuntimeException("Interrupted", e);
        }
    }

}

```
