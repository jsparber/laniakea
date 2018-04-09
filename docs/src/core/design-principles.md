# Design Principles

Laniakea is developed with a couple of fundamental design principles in mind, that guide the way design
decisions are made in the project, and are helpful for developing new modules.
This page contains a list of them, as well as a rationale for them.

If you make a change to Laniakea, please ensure you followed these principles.


### The database is the one and only source for information

In previous solutions, a lot of components of the technical infrastructure had their own configuration files.
This basically required configuration management solutions, and required values to be changed across
a large amount of modules, even if it was the same value. For example, changing the current development suite
had to be done in at least 5 configuration files additionally to the main database.
Adding fine grained permissions on which user could change what value was made basically impossible.
Additionally, we were constantly syncing data across machines and duplicating it in order to satisfy the requirement
for each tool, resulting in tools working with outdated information quite frequently.

To avoid this complexity, Laniakea enforces all modules to publish their data and configuration in the database,
even if it is only ever consumed by the module itself. This ensures that we can have modules reuse data generated
by other modules and create nice synergy effects (e.g. the Debcheck data is consumed by the package-sync module as
well as the website and build scheduling), as well as having a central place to modify configuration.
There are only two exceptions to this rule:

 * If data is specific to the current machine, it has to be placed in a configuration file in `/etc/laniakea/` (e.g. database connection, ZMQ ports, executable locations, ...)
 * If the data is not suitable for database storage (e.g. build artifacts, large binaries) it should be stored in a well-known location and only have a reference in the database

Do add an external tool to Laniakea, usually a wrapper module is written that generates the tool-specific configuration from
Laniakea database data and imports its output data back into the database.


### No specialized workers

If you want to extend the speed at which Laniakea performs long-running task, you only ever should have to add
new machines to a cluster running a wide array of tasks already. This ensures we don't have machines which
build disk images being under heavy load while package builders are currently idling, and similar issues.
Therefore, if possible, Laniakea modules should add dedicated code they need for performing a long-running
task to the *laniakea-spark* generic job runner, and have the jobs scheduled by the global job scheduling
built into the system already.


### Modular, but highly integrated

With the exception of some core modules, every module in Laniakea should be optional, and users should be
able not to use it. E.g. if people don't want the package migration support, they can just decide to disable
or even not install the *spears* module.
At the same time, modules should be highly integrated and are allowed to have dependencies on each other.
All modules should be managed via the same interface (web, or `lk-admin`), and are located in the same
repository to easily share code and make global changes on the system.


### Avoid timed triggers

Modules are able to receive messages on events from the *Lighthouse* messaging hub. These messages should
always be preferred as triggers for actions over any time-based (cron-job) action.


### Get rid of humans

If Laniakea has enough information to automatically and reliably perform a certain action,
it should always do so automatically, without needing a human to look at the changes again
(with, depending on the action, an option to turn the automatism off).
This is true for, for example, transition job scheduling.


### Avoid shell scripts

This is basically the result of looking too much at the code of DAK: If you start with a very simple shell
script for a very simple task (and call it "configuration"), chances are that over time it might grow into a large and
complex monstrosity. Don't let it get to that. Extend the code of Laniakea directly if it does not yet do exactly what
you want - adding tiny but helpful commands is encouraged over working around that with scripting.


### Laniakea is written in D and Python

It's tempting to write code in a different programming language that might be more suited to the job, but each new programming
language a project is written in creates a higher entry barrier for new people to join and modify the code. It also
makes maintenance much harder and increases the difficulty for users to set up the project.
Therefore, Laniakea is written in D, with a few parts being done in Python, and no new programming language will be added.