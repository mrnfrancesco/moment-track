#!/bin/bash
## Automatically build Sphinx documentation upon file change
## Copyright (c) 2011-2012 Samuele ~redShadow~ Santi - Under GPL

if ! which inotifywait &>/dev/null; then
    echo "ERROR: Program 'inotifywait' is not installed"
    exit 1
fi

## Gray out the output
fade() {
    sed 's/^\(.*\)$/\x1b[1;30m\1\x1b[0m/'
}

while :; do
    ## Wait for changes in current directory
    inotifywait \
        -e modify,close_write,moved_to,moved_from,move,create,delete \
         ./src/*.rst 2>&1 | fade

    ## Run the command and retrieve return code
    "$@"
    RET="$?"
    ARGS="$@"

    ## Try to send a notification using libnotify
    if which notify-send &>/dev/null; then
        if [ "$RET" == "0" ]; then
            ICO="dialog-information"
            TITLE="Make execution successful"
        else
            ICO="dialog-error"
            TITLE="Make execution failed"
        fi
        notify-send "$TITLE" \
            "Command was: '$ARGS'\n\nPWD: $(pwd)\n\nReturn code: $RET" \
            --icon="$ICO" \
            2>&1 | fade
    fi
done
