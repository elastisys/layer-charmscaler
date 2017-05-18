# Overview

The Elastisys CharmScaler is an autoscaler for Juju applications. It
automatically scales your charm by adding units at times of high load and by
removing units at times of low load.

The initial edition of the CharmScaler features a simplified version of
[Elastisys](https://elastisys.com)' autoscaling engine (described below),
without its
[_predictive capabilities_](https://elastisys.com/cloud-platform-features/predictive-auto-scaling/)
and with limited scaling metric support. Work is underway on a more
fully-featured CharmScaler, but no release date has been set yet.

The initial CharmScaler edition scales the number of units of your applications
based on the observed CPU usage. These CPU metrics are collected from your
application by a [telegraf](https://jujucharms.com/telegraf/) agent, which
pushes the metrics into an
[InfluxDB](https://jujucharms.com/u/chris.macnaughton/influxdb/) backend, from
where they are consumed by the CharmScaler.

The CharmScaler is available both free-of-charge and as a subscription service.
The free version comes with a size restriction which currently limits the size
of the scaled application to four units. Subscription users will see no such
size restrictions. For more details refer to the [Subscription](#subscription)
section below.

If you are eager to try out the CharmScaler, head directly to the
[Quickstart](#quickstart) section. If you want to learn more about the
Elastisys autoscaler, read on ...

# Introducing the Elastisys Autoscaler

User experience is king. You want to offer your users a smooth ride. From a
performance perspective, this translates into providing them with a responsive
service. As response times increase you will see more and more users leaving,
perhaps for competing services.

An application can be tuned in many ways, but one critical aspect is to make
sure that it runs on sufficient hardware, capable of bearing the weight that is
placed on your system. However, resource planning is notoriously hard and
involves a lot of guesswork. A fixed "peak-dimensioned" infrastructure is
certain to have you overspending most of the time and, what's worse, you can
never be sure that it actually will be able to handle the next load surge.
Ideally, you want to run with just the right amount of resources at all times.
It is plain to see that such a process involves a lot of planning and manual
labor.

Elastisys automates this process with a sophisticated autoscaler. The Elastisys
autoscaler uses proactive scaling algorithms based on state-of-the-art
research, which, predictively offers _just in time capacity_. That is, it can
provision servers in advance so that the right amount of capacity is available
_when it is needed_, not when you _realize_ that it's needed (by then your
application may already be suffering). Research has shown that there is no
single scaling algorithm to rule them all. Different workload patterns require
different algorithms. The Elastisys autoscaler is armed with a growing
collection of such algorithms.

The Elastisys autoscaler already supports a
[wide range of clouds and platforms](https://github.com/elastisys/scale.cloudpool).
With the addition of the Juju CharmScaler, which can scale any Juju application
Charm, integration with your application has never been easier. Whether it’s a
Wordpress site, a Hadoop cluster, a Kubernetes cluster, or even OpenStack
compute nodes, or your own custom-made application charm, hooking it up to be
scaled by the Elastisys autoscaler is really easy.

Read more about Elastisys' cloud automation platform at
[https://elastisys.com](https://elastisys.com).

# Subscription

The free edition places a constraint on the size of the scaled application to
four units. To remove this restriction you need to become a paying subscription
user. Juju is currently in beta, and does not yet support commercial charms.
Once Juju is officially released, the CharmScaler will be available as a
subscription service. Until then, you can contact us and we will help you set
up a temporary subscription arrangement.

For upgrading to a premium subscription, for a customized solution, or for
general questions or feature requests, feel free to contact Elastisys at
[contact@elastisys.com](mailto:contact@elastisys.com).

# Quickstart

If you can't wait to get started, the following minimal example (relying on
configuration defaults) will let you start scaling your charm right away. For a
description of the CharmScaler and further details on its configuration, refer
to the sections below.

#### Juju credentials

At the time of writing there is no easy way to give a charm special Juju access
levels. Therefore, for the CharmScaler to be able to scale units you need to
give it the necessary credentials via the charm config.

Create a user and grant it model write access

    juju add-user [username] && juju grant [username] write [model]

*To set the password, execute the `juju register` command line given to you*

Get the Juju API address and model UUID

    juju show-controller

Minimal config.yaml example

    charmscaler:
      juju_api_endpoint: "[API address]:17070"
      juju_model_uuid: "[uuid]"
      juju_username: "[username]"
      juju_password: "[password]"

#### Deploy

Deploy and relate the charms

    juju deploy charmscaler --config=config.yaml
    juju deploy cs:~chris.macnaughton/influxdb-7
    juju deploy telegraf-2
    juju deploy [charm]

    juju relate charmscaler:db-api influxdb:query
    juju relate telegraf:influxdb-api influxdb:query
    juju relate telegraf:juju-info [charm]:juju-info
    juju relate charmscaler:juju-info [charm]:juju-info

# How the CharmScaler operates

![CharmScaler flow](https://cdn.rawgit.com/elastisys/layer-charmscaler/master/charmscaler.svg)

The image above illustrates the flow of the CharmScaler when scaling a
Wordpress application. Scaling decisions executed by the CharmScaler are
dependent on a load metric. In this case it looks at the CPU usage of machines
where Wordpress instances are deployed.

Metrics are collected by the Telegraf agent which is deployed as a subordinate
charm attached to the Wordpress application. This means that whenever the
Wordpress application is scaled out, another Telegraf collector will be
deployed as well and automatically start pushing new metrics to InfluxDB.

The CharmScaler will ask InfluxDB for new metric datapoints at every poll
interval (configured using the `metric_poll_interval` option). From these load
metrics the CharmScaler decides how many units are needed by your application.

In the case of Wordpress it is necessary to distribute the load on all of the
units using a load balancer. If you haven't already, checkout the Juju
documentation page on
[charm scaling](https://jujucharms.com/docs/2.0/charms-scaling).

# Configuration explained

The CharmScaler's configuration is comprised of three main parts:
`juju`, `scaling` and `alerts`.

#### Juju

The CharmScaler manages the number of units of the scaled charm via the Juju
controller. To be able to do that it needs to authenticate with the controller.
Controller authentication credentials are passed to the CharmScaler through
options prefixed with `juju_`.

Note that in a foreseeable future, passing this kind of credentials to the
CharmScaler may no longer be necessary. Instead of requiring you to manually
type in the authentication details one could envision Juju giving the charm
access through relations or something similar.

#### Scaling

The CharmScaler has a number of config options that control the autoscaler's
behavior. Those options are prefixed with either `scaling_` or `metric_`.
`metric_` options control the way metrics are fetched and processed while the
`scaling_` options control when and how the charm units are scaled.

The scaling algorithm available in this edition of the CharmScaler is a
rule-based one that looks at CPU usage. At each iteration (configured using the
`scaling_interval` option) the following rules are considered by the autoscaler
before making a scaling decision:

1. `scaling_cooldown` - Has enough time passed since the last scale-event
    (scale in or out) occured?
2. `scaling_cpu_[max/min]` - Is the CPU usage above/below the set limit?
3. `scaling_period_[up/down]scale` - Has the CPU usage been above/below
    `scaling_cpu_[max/min]` for a long enough period of time?

If all three rules above are satisifed either a scale-out or a scale-in occurs
and the scaled charm will automatically add or remove a unit.

Note that configuring the scaling algorithm is a balancing act -- one always
needs to balance the need to scale "quickly enough" against the need to avoid
"jumpy behavior". Too frequent scale-ups/scale-downs could have a negative
impact on overall performance/system stability.

The default behavior adds a new unit when the average CPU usage (over all charm
units) has exceeded 80% for at least one minute. If you want to make the
CharmScaler quicker to respond to changes, you can, for example, lower the
threshold to 60% and the evaluation period to 30 seconds:

    juju config charmscaler scaling_cpu_max=60
    juju config charmscaler scaling_period_upscale=30

Similarly, the default behavior removes a new unit when the average CPU usage
has been under 20% (`scaling_cpu_min`) for at least two minutes
(`scaling_period_downscale`). Typically, it is preferable to allow the
application to be overprovisioned for some time to prevent situations where we
are too quick to scale down, only to realize that the load dip was only
temporary and that we need to scale back up again. We can, for instance, set
the evaluation period preceding scale-downs a bit longer (five minutes) via:

    juju config charmscaler scaling_period_downscale=300

Finally, changing the amount of time required between two scaling decisions can
be done via:

    juju config charmscaler scaling_cooldown=300

This parameter should, however, be kept long enough to give scaling decisions a
chance to take effect, before a new scaling decision is triggered.

#### Alerts

Lastly, the options with the `alert_` prefix are used to enable CharmScaler
alerts (these are turned off by default).

Alerts are used to notify the outside world (such as the charm owner) of
noteable scaling events or error conditions. Alerts are, for example, sent
(with severity-level `ERROR`) if there are problems to reach the Juju
controller. Alerts are also sent (with severity-level `INFO`) when a scaling
decision has been made.

This edition of the CharmScaler includes email alerts which are configured by
entering the SMTP server details which the autoscaler is supposed to send the
alert email messages to.

## Known limitations

#### When deploying on LXD provider

Due to missing support for the Docker LXC profile in Juju you need to apply it
manually.

See: https://bugs.launchpad.net/juju/+bug/1552815

-----------------------

By using the Elastisys CharmScaler, you agree to its
[license](https://elastisys.com/documents/legal/documents/legal/elastisys-software-license/)
and [privacy statement](https://elastisys.com/documents/legal/privacy-policy/).
