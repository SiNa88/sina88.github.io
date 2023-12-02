---
title: Using an external configuration file for filter ranges
---

The [Detecting a sensor value out of range](recipe_value_out_of_range.html) recipe introduced the basics of filtering as well as the use of a [Range]({{ site.docsurl }}/index.html?org/apache/{{ site.data.project.unix_name }}/analytics/sensors/Range.html).

Oftentimes, a user wants to initialize a range specification from an external configuration file so the application code is more easily configured and reusable.

The string form of a `Range` is natural, consise, and easy to use. As such it's a convenient form to use in configuration files or for users to enter. The range string can easily be converted back into a `Range`.

We're going to assume familiarity with that earlier recipe and those concepts and focus on just the "external range specification" aspect of this recipe.

## Create a configuration file

The file's syntax is that for a `java.util.Properties` object. See the `Range` [documentation]({{ site.data.project.source_repository_mirror }}/blob/master/analytics/sensors/src/main/java/org/apache/{{ site.data.project.unix_name }}/analytics/sensors/Range.java) for its string syntax.

Put this into a file:

```
# the Range string for the temperature sensor optimal range
optimalTempRange=[77.0..91.0]
```

Supply the pathname to this file as an argument to the application when you run it.

## Loading the configuration file

A `java.util.Properties` object is often used for configuration parameters and it is easy to load the properties from a file.

```java
// Load the configuration file with the path string in configFilePath
Properties props = new Properties();
props.load(Files.newBufferedReader(new File(configFilePath).toPath()));
```

## Initializing the `Range`

```java
// initialize the range from a Range string in the properties.
// Use a default value if a range isn't present.
static String DEFAULT_TEMP_RANGE_STR = "[60.0..100.0]";
static Range<Double> optimalTempRange = Ranges.valueOfDouble(
        props.getProperty("optimalTempRange", defaultRange));
```

## The final application

```java
import java.io.File;
import java.nio.file.Files;
import java.util.Properties;
import java.util.concurrent.TimeUnit;

import org.apache.edgent.analytics.sensors.Range;
import org.apache.edgent.analytics.sensors.Ranges;
import org.apache.edgent.providers.direct.DirectProvider;
import org.apache.edgent.samples.utils.sensor.SimulatedTemperatureSensor;
import org.apache.edgent.topology.TStream;
import org.apache.edgent.topology.Topology;

/**
 * Detect a sensor value out of expected range.
 * Get the range specification from a configuration file.
 */
public class ExternalFilterRange {
    /**
     * Optimal temperatures (in Fahrenheit)
     */
    static String DEFAULT_TEMP_RANGE_STR = "[60.0..100.0]";
    static Range<Double> optimalTempRange;

    /** Initialize the application's configuration */
    static void initializeConfiguration(String configFilePath) throws Exception {
        // Load the configuration file
        Properties props = new Properties();
        props.load(Files.newBufferedReader(new File(configFilePath).toPath()));

        // initialize the range from a Range string in the properties.
        // Use a default value if a range isn't present in the properties.
        optimalTempRange = Ranges.valueOfDouble(
                props.getProperty("optimalTempRange", DEFAULT_TEMP_RANGE_STR));
        System.out.println("Using optimal temperature range: " + optimalTempRange);
    }

    /**
     * Polls a simulated temperature sensor to periodically obtain
     * temperature readings (in Fahrenheit). Use a simple filter
     * to determine when the temperature is out of the optimal range.
     */
    public static void main(String[] args) throws Exception {
        if (args.length != 1)
            throw new Exception("missing pathname to configuration file");
        String configFilePath = args[0];

        DirectProvider dp = new DirectProvider();

        Topology top = dp.newTopology("TemperatureSensor");

        // Initialize the configuration
        initializeConfiguration(configFilePath);

        // Generate a stream of temperature sensor readings
        SimulatedTemperatureSensor tempSensor = new SimulatedTemperatureSensor();
        TStream<Double> temp = top.poll(tempSensor, 1, TimeUnit.SECONDS);

        // Simple filter: Perform analytics on sensor readings to detect when
        // the temperature is out of the optimal range and generate warnings
        TStream<Double> simpleFiltered = temp.filter(tuple ->
                !optimalTempRange.contains(tuple));
        simpleFiltered.sink(tuple -> System.out.println("Temperature is out of range! "
                + "It is " + tuple + "\u00b0F!"));

        // See what the temperatures look like
        temp.print();

        dp.submit(top);
    }
}
```
