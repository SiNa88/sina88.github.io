---
title: Writing a Connector
---

Edgent applications interface with other entities by way of a connector.  The other entity may be an IO device, an IoT messaging hub, a file, process, database, another Edgent application/topology, etc.  

Edgent includes several connectors -- see the "Edgent Connectors" package group in the [javadoc](https://edgent.incubator.apache.org/javadoc/latest). The [CommandStreams](https://edgent.incubator.apache.org/javadoc/latest/org/apache/edgent/connectors/command/CommandStreams) connector can be particularly useful if commands already exist for getting data to or from an entity.  

When your application needs something new or special [Writing Connectors for Edgent Applications](https://cwiki.apache.org/confluence/display/EDGENT/Writing+Connectors+For+Edgent+Applications) tells you what you need to know!
