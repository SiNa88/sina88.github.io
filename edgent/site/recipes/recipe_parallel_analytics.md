---
title: How can I run analytics on several tuples in parallel?
---

If the duration of your per-tuple analytic processing makes your application unable to keep up with the tuple ingest rate or result generation rate, you can often run analytics on several tuples in parallel to improve performance.

The overall proessing time for a single tuple is still the same but the processing for each tuple is overlapped. In the extreme your application may be able to process N tuples in the same time that it would have processed one.

This usage model is in contrast to what's been called _concurrent analytics_, where multiple different independent analytics for a single tuple are performed concurrently, as when using `PlumbingStreams.concurrent()`.

e.g., imagine your analytic pipeline has three stages to it: A1, A2, A3, and that A2 dominates the processing time. You want to change the serial processing flow graph from:

```
sensorReadings<T> -> A1 -> A2 -> A3 -> results<R>
```

to a flow where the A2 analytics run on several tuples in parallel in a flow like:

```
                           |-> A2-channel0 ->|
sensorReadings<T> -> A1 -> |-> A2-channel1 ->| -> A3 -> results<R>
                           |-> A2-channel2 ->|
                           |-> A2-channel3 ->|
                           |-> A2-channel4 ->|
                                  ...
```

The key to the above flow is to use a _splitter_ to distribute the tuples among the parallel channels. Each of the parallel channels also needs a thread to run its analytic pipeline.

`PlumbingStreams.parallel()` builds a parallel flow graph for you. Alternatively, you can use `TStream.split()`, `PlumbingStreams.isolate()`, and `TStream.union()` and build a parallel flow graph yourself.

More specifically `parallel()` generates a flow like:

```
                                   |-> isolate(10) -> pipeline-ch0 -> |
stream -> split(width,splitter) -> |-> isolate(10) -> pipeline-ch1 -> |-> union -> isolate(width) 
                                   |-> isolate(10) -> pipeline-ch2 -> |
                                       ...
```

It's easy to use `parallel()`!

## Define the splitter

The splitter function partitions the tuples among the parallel channels. `PlumbingStreams.roundRobinSplitter()` is a commonly used splitter that simply cycles among each channel in succession. The round robin strategy works great when the processing time of tuples is uniform. Other splitter functions may use information in the tuple to decide how to partition them.

This recipe just uses the round robin splitter for a `TStream<Double>`.

```java
int width = 5;  // number of parallel channels

ToIntFunction<Double> splitter = PlumbingStreams.roundRobinSplitter(width);
```

Another possibility is to use a "load balanced splitter" configuration.  That is covered below.

## Define the pipeline to run in parallel

Define a `BiFunction<TStream<T>, Integer, TStream<R>>` that builds the pipeline. That is, define a function that receives a `TStream<T>` and an integer `channel` and creates a pipeline for that channel that returns a `TStream<R>`.

Many pipelines don't care what channel they're being constructed for. While the pipeline function typically yields the same pipeline processing for each channel there is no requirement for it to do so.

In this simple recipe the pipeline receives a `TStream<Double>` as input and generates a `TStream<String>` as output.

```java
static BiFunction<TStream<Double>, Integer, TStream<String>> pipeline() {
    // a simple 4 stage pipeline simulating some amount of work by sleeping
    return (stream, channel) -> 
      { 
        String tagPrefix = "pipeline-ch"+channel;
        return stream.map(tuple -> {
            sleep(1000, TimeUnit.MILLISECONDS);
            return "This is the "+tagPrefix+" result for tuple "+tuple;
          }).tag(tagPrefix+".stage1")
          .map(Functions.identity()).tag(tagPrefix+".stage2")
          .map(Functions.identity()).tag(tagPrefix+".stage3");
          .map(Functions.identity()).tag(tagPrefix+".stage4");
      };
}
```

## Build the parallel flow

Given a width, splitter and pipeline function it just takes a single call:

```java
TStream<String> results = PlumbingStreams.parallel(readings, width, splitter, pipeline());
```

## Load balanced parallel flow

A load balanced parallel flow allocates an incoming tuple to the first available parallel channel. When tuple processing times are variable, using a load balanced parallel flow can result in greater overall throughput.

To create a load balanced parallel flow simply use the `parallelBalanced()` method instead of `parallel()`. Everything is the same except you don't supply a splitter: 

```java
TStream<String> results = PlumbingStreams.parallelBalanced(readings, width, pipeline());
```

## The final application

When the application is run it prints out 5 (width) tuples every second. Without the parallel channels, it would only print one tuple each second.

```java
package edgent.samples.topology;

import java.util.Date;
import java.util.concurrent.TimeUnit;

import org.apache.edgent.console.server.HttpServer;
import org.apache.edgent.function.BiFunction;
import org.apache.edgent.function.Functions;
import org.apache.edgent.providers.development.DevelopmentProvider;
import org.apache.edgent.providers.direct.DirectProvider;
import org.apache.edgent.samples.utils.sensor.SimpleSimulatedSensor;
import org.apache.edgent.topology.TStream;
import org.apache.edgent.topology.Topology;
import org.apache.edgent.topology.plumbing.PlumbingStreams;

/**
 * A recipe for parallel analytics.
 */
public class ParallelRecipe {

    /**
     * Process several tuples in parallel in a replicated pipeline.
     */
    public static void main(String[] args) throws Exception {

        DirectProvider dp = new DevelopmentProvider();
        System.out.println("development console url: "
                + dp.getServices().getService(HttpServer.class).getConsoleUrl());

        Topology top = dp.newTopology("ParallelRecipe");

        // The number of parallel processing channels to generate
        int width = 5;
        
        // Define the splitter
        ToIntFunction<Double> splitter = PlumbingStreams.roundRobinSplitter(width);
        
        // Generate a polled simulated sensor stream
        SimpleSimulatedSensor sensor = new SimpleSimulatedSensor();
        TStream<Double> readings = top.poll(sensor, 10, TimeUnit.MILLISECONDS)
                                      .tag("readings");
        
        // Build the parallel analytic pipelines flow
        TStream<String> results = 
            PlumbingStreams.parallel(readings, width, splitter, pipeline())
                .tag("results");
        
        // Print out the results.
        results.sink(tuple -> System.out.println(new Date().toString() + "   " + tuple));

        System.out.println("Notice that "+width+" results are generated every second - one from each parallel channel."
            + "\nOnly one result would be generated each second if performed serially.");
        dp.submit(top);
    }
    
    /** Function to create analytic pipeline and add it to a stream */
    private static BiFunction<TStream<Double>,Integer,TStream<String>> pipeline() {
        // a simple 3 stage pipeline simulating some amount of work by sleeping
        return (stream, channel) -> 
          { 
            String tagPrefix = "pipeline-ch"+channel;
            return stream.map(tuple -> {
                sleep(1000, TimeUnit.MILLISECONDS);
                return "This is the "+tagPrefix+" result for tuple "+tuple;
              }).tag(tagPrefix+".stage1")
              .map(Functions.identity()).tag(tagPrefix+".stage2")
              .map(Functions.identity()).tag(tagPrefix+".stage3");
          };
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
