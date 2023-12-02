---
title: Detecting a sensor value out of expected range
---

Oftentimes, a user expects a sensor value to fall within a particular range. If a reading is outside the accepted limits, the user may want to determine what caused the anomaly and/or take action to reduce the impact. For instance, consider the following scenario.

Suppose a corn grower in the Midwestern United States would like to monitor the average temperature in his corn field using a sensor to improve his crop yield. The optimal temperatures for corn growth during daylight hours range between 77°F and 91°F. When the grower is alerted of a temperature value that is not in the optimal range, he may want to assess what can be done to mitigate the effect.

In this instance, we can use a filter to detect out-of-range temperature values.

## Setting up the application

We assume that the environment has been set up following the steps outlined in the [Getting started guide](../docs/edgent-getting-started). Let's begin by creating a `DirectProvider` and `Topology`. We also define the optimal temperature range.

```java
import static edgent.function.Functions.identity;

import java.util.concurrent.TimeUnit;

import org.apache.edgent.analytics.sensors.Filters;
import org.apache.edgent.analytics.sensors.Range;
import org.apache.edgent.analytics.sensors.Ranges;
import org.apache.edgent.providers.direct.DirectProvider;
import org.apache.edgent.samples.utils.sensor.SimulatedTemperatureSensor;
import org.apache.edgent.topology.TStream;
import org.apache.edgent.topology.Topology;

public class DetectValueOutOfRange {
    /**
     * Optimal temperature range (in Fahrenheit)
     */
    static double OPTIMAL_TEMP_LOW = 77.0;
    static double OPTIMAL_TEMP_HIGH = 91.0;
    static Range<Double> optimalTempRange = Ranges.closed(OPTIMAL_TEMP_LOW, OPTIMAL_TEMP_HIGH);

    public static void main(String[] args) throws Exception {

        DirectProvider dp = new DirectProvider();

        Topology top = dp.newTopology("TemperatureSensor");

        // The rest of the code pieces belong here
    }
}
```

## Generating temperature sensor readings

The next step is to simulate a stream of temperature readings using [`SimulatedTemperatureSensor`]({{ site.data.project.source_repository_mirror }}/blob/master/samples/utils/src/main/java/org/apache/{{ site.data.project.unix_name }}/samples/utils/sensor/SimulatedTemperatureSensor.java). By default, the sensor sets the initial temperature to 80°F and ensures that new readings are between 28°F and 112°F. In our `main()`, we use the `poll()` method to generate a flow of tuples, where a new tuple (temperature reading) arrives every second.

```java
// Generate a stream of temperature sensor readings
SimulatedTemperatureSensor tempSensor = new SimulatedTemperatureSensor();
TStream<Double> temp = top.poll(tempSensor, 1, TimeUnit.SECONDS);
```

## Simple filtering

If the corn grower is interested in determining when the temperature is strictly out of the optimal range of 77°F and 91°F, a simple filter can be used. The `filter` method can be applied to `TStream` objects, where a filter predicate determines which tuples to keep for further processing. For its method declaration, refer to the [Javadoc]({{ site.docsurl }}/org/apache/{{ site.data.project.unix_name }}/topology/TStream.html#filter-org.apache.{{ site.data.project.unix_name }}.function.Predicate-).

In this case, we want to keep temperatures below the lower range value *or* above the upper range value. This is expressed in the filter predicate, which follows Java's syntax for [lambda expressions](https://docs.oracle.com/javase/tutorial/java/javaOO/lambdaexpressions.html#syntax). Then, we terminate the stream (using `sink`) by printing out the warning to standard out. Note that `\u00b0` is the Unicode encoding for the degree (°) symbol.

```java
TStream<Double> simpleFiltered = temp.filter(tuple ->
        tuple < OPTIMAL_TEMP_LOW || tuple > OPTIMAL_TEMP_HIGH);
simpleFiltered.sink(tuple -> System.out.println("Temperature is out of range! "
        + "It is " + tuple + "\u00b0F!"));
```

## Deadband filter

Alternatively, a deadband filter can be used to glean more information about temperature changes, such as extracting the in-range temperature immediately after a reported out-of-range temperature. For example, large temperature fluctuations could be investigated more thoroughly.

The `deadband` filter is a part of the `edgent.analytics` package focused on handling sensor data. Let's look more closely at the method declaration below.

```java
deadband(TStream<T> stream, Function<T,V> value, Predicate<V> inBand)
```

The first parameter is the stream to the filtered, which is `temp` in our scenario. The second parameter is the value to examine. Here, we use the `identity()` method to return a tuple on the stream. The last parameter is the predicate that defines the optimal range, that is, between 77°F and 91°F. it is important to note that this differs from the `TStream` version of `filter` in which one must explicitly specify the values that are out of range. The code snippet below demonstrates how the method call is pieced together. The `deadbandFiltered` stream contains temperature readings that follow the rules as described in the [Javadoc]({{ site.docsurl }}/org/apache/{{ site.data.project.unix_name }}/analytics/sensors/Filters.html#deadband-org.apache.{{ site.data.project.unix_name }}.topology.TStream-org.apache.{{ site.data.project.unix_name }}.function.Function-org.apache.{{ site.data.project.unix_name }}.function.Predicate-):

* the value is outside of the optimal range (deadband)
* the first value inside the optimal range after a period being outside it
* the first tuple

As with the simple filter, the stream is terminated by printing out the warnings.

```java
TStream<Double> deadbandFiltered = Filters.deadband(temp,
        identity(), tuple -> tuple >= OPTIMAL_TEMP_LOW && tuple <= OPTIMAL_TEMP_HIGH);
deadbandFiltered.sink(tuple -> System.out.println("Temperature may not be "
        + "optimal! It is " + tuple + "\u00b0F!"));
```

We end our application by submitting the `Topology`.

## Observing the output

To see what the temperatures look like, we can print the stream to standard out.

```java
temp.print();
```

When the final application is run, the output looks something like the following:

```
Temperature may not be optimal! It is 79.1°F!
79.1
79.4
79.0
78.8
78.0
78.3
77.4
Temperature is out of range! It is 76.5°F!
Temperature may not be optimal! It is 76.5°F!
76.5
Temperature may not be optimal! It is 77.5°F!
77.5
77.1
...
```

Note that the deadband filter outputs a warning message for the very first temperature reading of 79.1°F. When the temperature falls to 76.5°F (which is outside the optimal range), both the simple filter and deadband filter print out a warning message. However, when the temperature returns to normal at 77.5°F, only the deadband filter prints out a message as it is the first value inside the optimal range after a period of being outside it.

## Range values

Filtering against a range of values is such a common analytic activity that the `edgent.analytics.sensors.Range` class is provided to assist with that.

Using a `Range` can simplify and clarify your application code and lessen mistakes that may occur when writing expressions to deal with ranges. Though not covered in this recipe, `Range`s offer additional conveniences for creating applications with external range specifications and adaptable filters.

In the above examples, a single `Range` can be used in place of the two different expressions for the same logical range:

```java
static double OPTIMAL_TEMP_LOW = 77.0;
static double OPTIMAL_TEMP_HIGH = 91.0;
static Range<Double> optimalTempRange = Ranges.closed(OPTIMAL_TEMP_LOW, OPTIMAL_TEMP_HIGH);
```

Using `optimalTempRange` in the Simple filter example code:

```java
TStream<Double> simpleFiltered = temp.filter(tuple ->
        !optimalTempRange.contains(tuple));
```

Using `optimalTempRange` in the Deadband filter example code:

```java
TStream<Double> deadbandFiltered = Filters.deadband(temp,
        identity(), optimalTempRange);
```

## The final application

```java
import static edgent.function.Functions.identity;

import java.util.concurrent.TimeUnit;

import org.apache.edgent.analytics.sensors.Filters;
import org.apache.edgent.analytics.sensors.Range;
import org.apache.edgent.analytics.sensors.Ranges;
import org.apache.edgent.providers.direct.DirectProvider;
import org.apache.edgent.samples.utils.sensor.SimulatedTemperatureSensor;
import org.apache.edgent.topology.TStream;
import org.apache.edgent.topology.Topology;

/**
 * Detect a sensor value out of expected range.
 */
public class DetectValueOutOfRange {
    /**
     * Optimal temperature range (in Fahrenheit)
     */
    static double OPTIMAL_TEMP_LOW = 77.0;
    static double OPTIMAL_TEMP_HIGH = 91.0;
    static Range<Double> optimalTempRange = Ranges.closed(OPTIMAL_TEMP_LOW, OPTIMAL_TEMP_HIGH);

    /**
     * Polls a simulated temperature sensor to periodically obtain
     * temperature readings (in Fahrenheit). Use a simple filter
     * and a deadband filter to determine when the temperature
     * is out of the optimal range.
     */
    public static void main(String[] args) throws Exception {

        DirectProvider dp = new DirectProvider();

        Topology top = dp.newTopology("TemperatureSensor");

        // Generate a stream of temperature sensor readings
        SimulatedTemperatureSensor tempSensor = new SimulatedTemperatureSensor();
        TStream<Double> temp = top.poll(tempSensor, 1, TimeUnit.SECONDS);

        // Simple filter: Perform analytics on sensor readings to
        // detect when the temperature is completely out of the
        // optimal range and generate warnings
        TStream<Double> simpleFiltered = temp.filter(tuple ->
                !optimalTempRange.contains(tuple));
        simpleFiltered.sink(tuple -> System.out.println("Temperature is out of range! "
                + "It is " + tuple + "\u00b0F!"));

        // Deadband filter: Perform analytics on sensor readings to
        // output the first temperature, and to generate warnings
        // when the temperature is out of the optimal range and
        // when it returns to normal
        TStream<Double> deadbandFiltered = Filters.deadband(temp,
                identity(), optimalTempRange);
        deadbandFiltered.sink(tuple -> System.out.println("Temperature may not be "
                + "optimal! It is " + tuple + "\u00b0F!"));

        // See what the temperatures look like
        temp.print();

        dp.submit(top);
    }
}
```
