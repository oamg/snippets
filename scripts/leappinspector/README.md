# Leapp-inspector

The leapp-inspector script can be used as library for python scripts or as a tool
when it is executed directy.

The main purpose of Leapp-inspector is to help with investigation / debugging
of the Leapp execution based on data in the leapp db. E.g. what actors have
been executed, what meesages have been produced, what happened during
the execution of leapp, ...

## DISCLAIMER

The code is not stabilized yet! It's under heavy development!
You should expect that output format, CLI, and classes/functions in the script
can be significantly changed without notification and without sorry.

## Requirements
The script is Python2 & Python3 compatible. By default, when execute the tool,
Python3 is required. In case you want to use the tool with Python2, invoke it
directly with python2 (`python2 ./leapp-inspector`) or change the shebang.

Only required dependcies to use the script are Python2 or Python3 standard
libraries. So having installed Python, nothing else is needed.

## How to install the tooling
You can just download the script into your system e.g. store it into the
`~/bin/leapp-inspector`:
```bash
leapp_inspector_url=https://raw.githubusercontent.com/oamg/snippets/master/scripts/leappinspector/leapp-inspector
mkdir -p ~/bin
curl -kL $leapp_inspector_url > ~/bin/leapp-inspector
chmod +x ~/bin/leapp-inspector
```

By default, the script expects to use Python3. But in case you are using a system
where Python2 is still present as default, change the shebang (the first line
of the script) from python3 to python2 to make the tool working for you. The tooling
is now Python2 & Python3 compatible.

### Install the bash-completion for leapp-inspector
For convenient use, the bash-completion file is located under the bash-completion
directory. To install it, just copy it under your bash-completion. If you want
to specify bash-completion on the user level, do somethin like that:
1. create ~/.bash-completion.d directory
1. copy the script inside
1. create user's ~/.bash\_completion configuration script:
```
for bcfile in $(find ~/.bash_completion.d/ -type f -exec grep -Iq . {} \; -print) ; do
  . $bcfile
done
```

## How to use the tool

The most simple use of the tool is execute it in the direcotry with the leapp
db file (usually `leapp.db`) and use a subcommand you wish to get some data.
E.g.
```
 # to print all messages produced by actors
 leapp-inspector messages

 # to list all executed actors
 leapp-inspector actors --list-executed

 # print help to see more..
 leapp-inspector help
```

If the leapp db file is located in different than current working directory
or has a different name, use th `--db` option (prior a subcommand) to specify
location of the leapp db file.

