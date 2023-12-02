---
title: Apache Edgent community
---
<!--
{% comment %}
Licensed to the Apache Software Foundation (ASF) under one or more
contributor license agreements.  See the NOTICE file distributed with
this work for additional information regarding copyright ownership.
The ASF licenses this file to you under the Apache License, Version 2.0
(the "License"); you may not use this file except in compliance with
the License.  You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
{% endcomment %}
-->

Every volunteer project obtains its strength from the people involved in it. We invite you to participate as much or as little as you choose.

You can:

* Use our project and provide a feedback.
* Provide us with the use-cases.
* Report bugs and submit patches.
* Contribute code, javadocs, documentation.

Visit the [Contributing](http://www.apache.org/foundation/getinvolved.html) page for general Apache contribution information. If you plan to make any significant contribution, you will need to have an Individual Contributor License Agreement [\(ICLA\)](https://www.apache.org/licenses/icla.txt) on file with Apache.

## Mailing list

Get help using {{ site.data.project.short_name }} or contribute to the project on our mailing lists:

{% if site.data.project.user_list %}
* [site.data.project.user_list](mailto:{{ site.data.project.user_list }}) is for usage questions, help, and announcements. [subscribe](mailto:{{ site.data.project.user_list_subscribe }}?subject=send this email to subscribe), [unsubscribe](mailto:{{ site.data.project.dev_list_unsubscribe }}?subject=send this email to unsubscribe), [archives]({{ site.data.project.user_list_archive_mailarchive }})
{% endif %}
* [{{ site.data.project.dev_list }}](mailto:{{ site.data.project.dev_list }}) is for people who want to contribute code to {{ site.data.project.short_name }}. [subscribe](mailto:{{ site.data.project.dev_list_subscribe }}?subject=send this email to subscribe), [unsubscribe](mailto:{{ site.data.project.dev_list_unsubscribe }}?subject=send this email to unsubscribe), [Apache archives]({{ site.data.project.dev_list_archive }}), [mail-archive.com archives]({{ site.data.project.dev_list_archive_mailarchive }})
* [{{ site.data.project.commits_list }}](mailto:{{ site.data.project.commits_list }}) is for commit messages and patches to {{ site.data.project.short_name }}. [subscribe](mailto:{{ site.data.project.commits_list_subscribe }}?subject=send this email to subscribe), [unsubscribe](mailto:{{ site.data.project.commits_list_unsubscribe }}?subject=send this email to unsubscribe), [Apache archives]({{ site.data.project.commits_list_archive }}), [mail-archive.com archives]({{ site.data.project.commits_list_archive_mailarchive }})

## Issue tracker

We use JIRA here: [https://issues.apache.org/jira/browse/{{ site.data.project.jira }}](https://issues.apache.org/jira/browse/{{ site.data.project.jira }})

### Bug reports

Found a bug? Create an issue in [JIRA](https://issues.apache.org/jira/browse/{{ site.data.project.jira }}).

Before submitting an issue, please:

* Verify that the bug does in fact exist
* Search the issue tracker to verify there is no existing issue reporting the bug you've found
* Consider tracking down the bug yourself in the {{ site.data.project.short_name }} source and submitting a pull request along with your bug report. This is a great time saver for the {{ site.data.project.short_name }} developers and helps ensure the bug will be fixed quickly.

### Feature requests

Enhancement requests for new features are also welcome. The more concrete the request is and the better rationale you provide, the greater the chance it will incorporated into future releases. To make a request, create an issue in [JIRA](https://issues.apache.org/jira/browse/{{ site.data.project.jira }}).

## Source code

The project sources are accessible via the [source code repository]({{ site.data.project.source_repository }}) which is also mirrored in [GitHub]({{ site.data.project.source_repository_mirror }}).

When you are considering a code contribution, make sure there is a [JIRA issue](https://issues.apache.org/jira/browse/{{ site.data.project.jira }}) that describes your work or the bug you are fixing. For significant contributions, please discuss your proposed changes in the issue so that others can comment on your plans. Someone else may be working on the same functionality, so it's good to communicate early and often. A committer is more likely to accept your change if there is clear information in the issue.

To contribute, [fork](https://help.github.com/articles/fork-a-repo/) the [mirror]({{ site.data.project.source_repository_mirror }}) and issue a [pull request](https://help.github.com/articles/using-pull-requests/). Put the JIRA issue number, e.g. {{ site.data.project.jira }}-100 in the pull request title. The tag [WIP] can also be used in the title of pull requests to indicate that you are not ready to merge but want feedback. Remove [WIP] when you are ready for merge. Make sure you document your code and contribute tests along with the code.

Read [DEVELOPMENT.md]({{ site.data.project.source_repository_mirror }}/blob/master/DEVELOPMENT.md) at the top of the code tree for details on setting up your development environment.

## Website and documentation source code

The project website and documentation sources are accessible via the [website source code repository]({{ site.data.project.website_repository }}) which is also mirrored in [GitHub]({{ site.data.project.website_repository_mirror }}). Contributing changes to the website and documentation is similar to contributing code. Follow the instructions in the *Source Code* section above, but fork and issue a pull request against the [website mirror]({{ site.data.project.website_repository_mirror }}). Follow the instructions in the top-level [README.md]({{ site.data.project.website_repository_mirror }}/blob/master/README.md) for details on contributing to the website and documentation.

You will need to use [Markdown](https://daringfireball.net/projects/markdown/) and [Jekyll](http://jekyllrb.com) to develop pages. See:

* [Markdown Cheat Sheet](https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet)
* [Jekyll on Linux and Mac](https://jekyllrb.com/)
* [Jekyll on Windows](https://jekyllrb.com/docs/windows/) is not officially supported but people have gotten it to work
