# Leapp-inspector

Leapp-inspector is supposed to help with (post-mortem) debugging working just
with the leapp.db database, which contains all information about the execution
of leapp and processed actors, including:
- logs from leapp itself about the progress
- logs from actors
- executed commands on the system using the run function from the leapp
  standard library (with ecode, stderr, stdout)
- errors
- Messages produced by actor

and all metada round. Basically it contains currently most important data
we usually need to be able to investigate what happens. But it can be used
for debug purposes during the development as well.

The whole script can be used as the tool itself, but it can be used just as
library, that can be extended by other people (teams) for their own purposes.


## Generic Use-cases for the default tool

Here is expected set of generic use-cases for the tool:

- just get generic info about repository:
  - what actors have been detected
  - what phases have been detected,
  - what repositores exists

- get info about progress of the workflow
  - what actors have been processed
  - what phases have been processed (finished)
  - the status of the workflow: in-progress/checkpoint, finished: ok, error (inhibit?..)

- print information related to specific actor:
  - produced messages
  - logs,
  - errors
  - called cmds, with outputs, ...

- print basic info about the system:
  - OS version, sys arch, subscriptions, installed version of "*leapp*" rpms,
    storage,...

- print info related to messages:
  - what type of messages have been produced (by who, in which phase...)
  - print content of a speciffied message type (print list of all messages
    of the specified type)
  - or print messages with specified tags (groups), resources...
  - get number of produced messages?
  - print errors
  - print/regenerate report
  - print inhibitors

- reconstruct terminal-like output
  - it's possible to reconstruct the terminal output as user could see it, just
    with small difference, e.g.: output of called cmds is sorted: stdout/stderr.
    In reality, lines/msgs are usually mixed during the execution of commands.
    - additionally, msgs outside of leapp are missing as well - e.g. booting,
      errors that happens inside initrd but still outside of leapp
  - ??be able to switch between various levels of verbosity??


## Other possible extensions

These use-cases are not already so generic as they are connected to specific
leapp workflow or repositories. So it's more expected that it will be
developed by substems for their own purposes probably.

- do an automatic basic investigation based on the collected data
  - the most common problems (or better to say reports from people)
    can be many times discoveredd automatically, e.g.
    - system is not subscribed
    - content of the target system is not available
    - wrong setup (hw?)..
    - used devel switches without proper setup changes
    - old data files
    - unsupported upgrade-path
    - ...and many other pebkac... :/
    - known issues
    - broken rpm transaction
    and other casual cases that are reported by people and many times even
    have same hints - which could be printed per each problem..
