---
title: Writing a source function
---

In the previous [Hello Edgent!](recipe_hello_edgent) example, we create a data source which generates two Java `String`s and prints them to output. Yet Edgent sources support the ability generate any data type as a source, not just Java types such as `String`s and `Double`s. Moreover, because the user supplies the code which generates the data, the user has complete flexibility for *how* the data is generated. This recipe demonstrates how a user could write such a custom data source.

## Custom source: reading the lines of a web page

{{site.data.alerts.note}} Edgent's API provides convenience methods for performing HTTP requests. For the sake of example we are writing a HTTP data source manually, but in principle there are easier methods. {{site.data.alerts.end}}

One example of a custom data source could be retrieving the contents of a web page and printing each line to output. For example, the user could be querying the Yahoo Finance website for the most recent stock price data of Bank of America, Cabot Oil & Gas, and Freeport-McMoRan Inc.:

``` java
public static void main(String[] args) throws Exception {
    DirectProvider dp = new DirectProvider();
    Topology top = dp.newTopology();

    final URL url = new URL("http://finance.yahoo.com/d/quotes.csv?s=BAC+COG+FCX&f=snabl");
}
```

Given the correctly formatted URL to request the data, we can use the *`Topology.source()`* method to generate each line of the page as a data item on the stream. `Topology.source()` takes a Java `Supplier` that returns an `Iterable`. The supplier is invoked once, and the items returned from the Iterable are used as the stream's data items. For example, the following `queryWebsite` method returns a supplier which queries a URL and returns an `Iterable` of its contents:

``` java
private static Supplier<Iterable<String> > queryWebsite(URL url) throws Exception{
    return () -> {
        List<String> lines = new LinkedList<>();
        try {
            InputStream is = url.openStream();
            BufferedReader br = new BufferedReader(
                    new InputStreamReader(is));

            for(String s = br.readLine(); s != null; s = br.readLine())
                lines.add(s);

        } catch (Exception e) {
            e.printStackTrace();
        }
        return lines;
    };
}
```

When invoking `Topology.source()`, we can use `queryWebsite` to return the required supplier, passing in the URL.

```java
public static void main(String[] args) throws Exception {
    DirectProvider dp = new DirectProvider();
    Topology top = dp.newTopology();

    final URL url = new URL("http://finance.yahoo.com/d/quotes.csv?s=BAC+COG+FCX&f=snabl");

    TStream<String> linesOfWebsite = top.source(queryWebsite(url));

    dp.submit(top);
}
```

Source methods such as `Topology.source()` and `Topology.strings()` return a `TStream`. If we print the `linesOfWebsite` stream to standard output and run the application, we can see that it correctly generates the data and feeds it into the Edgent runtime:

**Output**:

```java
"BAC","Bank of America Corporation Com",13.150,13.140,"12:00pm - <b>13.145</b>"
"COG","Cabot Oil & Gas Corporation Com",21.6800,21.6700,"12:00pm - <b>21.6775</b>"
"FCX","Freeport-McMoRan, Inc. Common S",8.8200,8.8100,"12:00pm - <b>8.8035</b>"
```

## Polling source: reading data periodically

A much more common scenario for a developer is the periodic generation of data from a source operator &mdash; a data source may need to be polled every 5 seconds, 3 hours, or any time frame. To this end, `Topology` exposes the `poll()` method which can be used to call a function at the frequency of the user's choosing. For example, a user might want to query Yahoo Finance every two seconds to retrieve the most up to date ticker price for a stock:

```java
public static void main(String[] args) throws Exception {
    DirectProvider dp = new DirectProvider();
    Topology top = dp.newTopology();

    final URL url = new URL("http://finance.yahoo.com/d/quotes.csv?s=BAC+COG+FCX&f=snabl");

    TStream<Iterable<String>> source = top.poll(queryWebsite(url), 2, TimeUnit.SECONDS);
    source.print();

    dp.submit(top);
}
```

**Output**:

<img src="images/pollingSource.gif">

It's important to note that calls to `DirectProvider.submit()` are non-blocking; the main thread will exit, and the threads executing the topology will continue to run. (Also, to see changing stock prices, the above example needs to be run during open trading hours. Otherwise, it will simply return the same results every time the website is polled).
