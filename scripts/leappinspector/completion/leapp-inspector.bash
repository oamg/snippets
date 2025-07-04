_get_subcommands() {
    # if the leapp-inspector command is not available, return predefined
    # set of subcommands
    command -v leapp-inspector >/dev/null || {
        echo help actors messages executions interactive inspecion
        return
    }
    leapp-inspector help \
        | grep -A1 -m1 "^Subcommands:" \
        | tail -n1 \
        | tr "{}," "   "
}

_get_dbfile() {
    # print existing leapp db file or nothing + return
    # return 0 if discovered, otherwise 1
    local use_next=0
    for word in "${COMP_WORDS[@]}"; do
       if [[ "$use_next" == "1" ]]; then
           # Check if file exists, but still return the path
           echo "$word"
           return 0
       fi
       if [[ "$word" == "--db" ]]; then
           use_next=1
       fi
    done

    # try to find the defaults if present..
    [[ -e "leapp.db" ]] && echo "leapp.db" && return 0
    [[ -e "/var/lib/leapp/leapp.db" ]] && echo "/var/lib/leapp/leapp.db" && return 0

    # no leapp.db file discovered
    return 1
}

_get_context() {
    # if an existing context is set in cmdline already, print it
    # return 0 if context set, otherwise 1
    local use_next=0
    for word in "${COMP_WORDS[@]}"; do
       if [[ "$use_next" == "1" ]]; then
           # Check if file exists, but still return the path
           echo "$word"
           return 0
       fi
       if [[ "$word" == "--context" ]]; then
           use_next=1
       fi
    done

    return 1
}

in_array() {
    local i
    for i in $2; do
        [[ $i = $1 ]] && return 0
    done
    return 1
}

_gen_leapp_inspector_cmd() {
    # gen leapp-inspector command if the leapp db file exists
    dbfile="$(_get_dbfile)"
    [[ -z "$dbfile" ]] && return 1
    context="$(_get_context)"
    [[ -z "$context" ]] || context="--context $context"
    echo "leapp-inspector --db $dbfile $context"
    return 0
}

_handle_subcmd_actors() {
    local cur="${COMP_WORDS[COMP_CWORD]}"
    local prev="${COMP_WORDS[COMP_CWORD-1]}"
    local opts="--help --list-executed --list--producers --actor --terminal-like --log-level"
    if [[ "$cur" == -* ]]; then
        COMPREPLY=( $(compgen -W "$opts" -- "$cur") )
        return 0
    fi

    case "$prev" in
        --actor)
            cmd="$(_gen_leapp_inspector_cmd)"
            [[ -z "$cmd" ]] && return 0
            actors=$($cmd actors --list-executed)
            COMPREPLY=( $(compgen -W "$actors" -- "$cur") )
            ;;
        --log-level)
            COMPREPLY=( $(compgen -W "ERROR WARNING INFO DEBUG" -- "$cur") )
            ;;
        *)
            COMPREPLY=( $(compgen -W "$opts" -- "$cur") )
            ;;
    esac
}

_handle_subcmd_messages() {
    local cur="${COMP_WORDS[COMP_CWORD]}"
    local prev="${COMP_WORDS[COMP_CWORD-1]}"
    local opts="--help --list --actor --type --phase --recursive-expand"
    if [[ "$cur" == -* ]]; then
        COMPREPLY=( $(compgen -W "$opts" -- "$cur") )
        return 0
    fi

    case "$prev" in
        --actor)
            cmd="$(_gen_leapp_inspector_cmd)"
            [[ -z "$cmd" ]] && return 1
            actors=$($cmd actors --list-executed)
            COMPREPLY=( $(compgen -W "$actors" -- "$cur") )
            ;;
        --type)
            cmd="$(_gen_leapp_inspector_cmd)"
            [[ -z "$cmd" ]] && return 1
            msg_types=$($cmd messages --list)
            COMPREPLY=( $(compgen -W "$msg_types" -- "$cur") )
            ;;
        --phase)
            cmd="$(_gen_leapp_inspector_cmd)"
            [[ -z "$cmd" ]] && return 1
            phases=$($cmd messages | grep "^Phase" | cut -f 2 -d ":" | sort | uniq)
            COMPREPLY=( $(compgen -W "$phases" -- "$cur") )
            ;;
        *)
            COMPREPLY=( $(compgen -W "$opts" -- "$cur") )
            ;;
    esac
}

_handle_subcmd_inspection() {
    local cur="${COMP_WORDS[COMP_CWORD]}"
    local prev="${COMP_WORDS[COMP_CWORD-1]}"
    local opts="--help --paranoid"
    if [[ "$cur" == -* ]]; then
        COMPREPLY=( $(compgen -W "$opts" -- "$cur") )
        return 0
    fi

    case "$prev" in
        *)
            COMPREPLY=( $(compgen -W "$opts" -- "$cur") )
            ;;
    esac
}

_leapp_inspector_complete () {
    COMPREPLY=()
    local cur="${COMP_WORDS[COMP_CWORD]}"
    local prev="${COMP_WORDS[COMP_CWORD-1]}"
    local gen_opts="--help --context --db"
    local subcmds="$(_get_subcommands)"
    local subcmd=
    local word=

    for word in "${COMP_WORDS[@]}"; do
       if in_array "$word" "$subcmds"; then
           subcmd="$word"
           break
       fi
    done

    if  [[ -z "$subcmd" ]]; then
        if [[ "$cur" == -* ]]; then
           # suggest generic options
           COMPREPLY=( $(compgen -W "$gen_opts" -- "$cur") )
           return 0
        fi

        case "$prev" in
            --context)
                dbfile="$(_get_dbfile)"
                [[ -z "$dbfile" ]] && return 1
                words=$(leapp-inspector --db "$dbfile" executions | grep -o "^[0-9a-f][^ ]*")
                COMPREPLY=( $(compgen -W "$words" -- "$cur") )
                ;;
            --db)
                _filedir
                ;;
            *)
                COMPREPLY=( $(compgen -W "$subcmds" -- "$cur") )
                ;;
        esac
    else
        if [[ "$cur" == "$subcmd" ]]; then
           # subcmd is discovered but maybe unfinished, case like:
           #    'hello' is written but 'hello' and 'hello-kitty' subcmds exist
           # or 'hello' is written and cursor is in the end of the 'hello'
           # in such case, to be able to move on when <TAB> is pressed, add
           # even 'hello ' to possible options...
           COMPREPLY=( $(compgen -W "$gen_opts '$subcmd '" -- "$cur") )
           return 0
        fi

        # and now handle options for specific subcommands..
        case "$subcmd" in
            actors)
                _handle_subcmd_actors
                ;;
            messages)
                _handle_subcmd_messages
                ;;
            inspection)
                _handle_subcmd_inspection
                ;;
            *)
                COMPREPLY=( $(compgen -W "-h --help" -- "$cur") )
                ;;
        esac
    fi

    return 0
}
complete -F _leapp_inspector_complete leapp-inspector
