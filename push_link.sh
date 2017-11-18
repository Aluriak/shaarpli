DIR=$(dirname $(realpath $0))
TOSEND="${DIR}/tosend"

HOST_PORT=22
HOST_NAME=example.net
HOST_DIR=~/links


# do not reuse empty or only-space file
touch "${TOSEND}"
CONTENT=$(cat ${TOSEND})
if [[ "x`printf '%s' "$CONTENT" | tr -d "$IFS"`" = x ]]
then
    echo "delete empty tosend"
    rm "${TOSEND}"
fi
# make it empty at start
touch "${TOSEND}"


# reuse file if available and not avoided by user
if [[ -e "${TOSEND}".sav && "$1" != "-b" ]]
then
    echo "reuse non-sent link. Use -b to avoid this behavior."
    mv "${TOSEND}".sav "${TOSEND}"
else

    # make use of the clipboard content if any
    CLIP=$(xclip -o)
    if ! [[ "x`printf '%s' "${CLIP}" | tr -d "$IFS"`" = x ]]
    then
        if [[ $(echo "${CLIP}" | grep "http") ]]
        then
            echo "" > "${TOSEND}"
        fi
        echo "${CLIP}" >> "${TOSEND}"
    fi

fi



# finally edit the file
$EDITOR "${TOSEND}"


function validate() {
    if [[ -e ${TOSEND} ]]
    then
        first_line=$(sed "1q;d" "${TOSEND}")
        second_line=$(sed "2q;d" "${TOSEND}")
        last_lines=$(tail -n +3 ${TOSEND})

        echo -ne '\033[0;33m'
        if [[ ! "$first_line" ]]
        then
            echo "WARNING: empty title"
        elif [[ $(echo "$first_line" | grep "https://") ]]
        then
            echo "WARNING: title contains a link"
        # else
            # echo "INFO: title is ok ($first_line)"
        fi

        if [[ ! "$second_line" ]]
        then
            echo "WARNING: no link sent"
        elif [[ $(echo "$second_line" | grep -ve "^https:\/\/") ]]
        then
            echo "WARNING: link line contains no https link"
        # else
            # echo "INFO: link is ok ($second_line)"
        fi

        # if [[ ! "$third_line" ]]
        # then
            # echo "WARNING: no tags given"
        # elif [[ $(echo "$third_line" | grep "http") ]]
        # then
            # echo "WARNING: tags contains a link"
        # elif [[ ! $(echo "$third_line" | grep ",") ]]
        # then
            # echo "WARNING: tags do not contains comma (tag separator)"
        # # else
            # # echo "INFO: title is ok ($first_line)"
        # fi

        if [[ ! "$last_lines" ]]
        then
            echo "WARNING: empty body"
        # else
            # echo "INFO: body is ok ($last_lines)"
        fi
        echo -ne '\033[0m'
    fi
}

function push_to_send() {
    # source /home/lucas/scripts/add-bom.sh
    # add_bom "${TOSEND}"
    echo "pushing…"
    scp -P ${HOST_PORT} "${TOSEND}" "${HOST_NAME}:${HOST_DIR}/toadd"
    ssh -p ${HOST_PORT} ${HOST_NAME} -t "cd ${HOST_DIR} && ./addlink.sh"
    echo "done !"
    mv "${TOSEND}" "${TOSEND}.last_sent"
}


while [[ 1 ]]
do
    echo ""
    echo -ne '\033[1;30m'
    echo " ——————— PAYLOAD ——————— "
    echo -ne '\033[0m'
    cat "${TOSEND}"
    echo -ne '\033[1;30m'
    echo " ——————————————————————— "
    echo -ne '\033[0m'
    echo ""
    validate
    read -p "[y/n/e/s/a/?]" USER_INPUT
    case "${USER_INPUT}" in

    [aA]* )
        # additional behavior
        RESTART=1
        push_to_send
        break
        ;;

    [yY]* )
        push_to_send
        break
        ;;

    [nN]* )
        echo "delete and forget…"
        rm "${TOSEND}"
        echo "done !"
        break
        ;;

    [sS]* )
        echo "save…"
        mv "${TOSEND}" "${TOSEND}".sav
        echo "done !"
        break
        ;;

    [eE]* )
        ${EDITOR} ${TOSEND}
        ;;

    \? )
        echo -ne '\033[0;31m'
        echo "
y -- push to remote the current data
n -- do not push, delete current data
s -- do not push, save current data for next call
e -- edit current data, then prompt again
a -- same as y + restart to send another link
? -- print this help
"
        echo -ne '\033[0m'
        ;;

    * )
        ;;

    esac
done


if [[ $RESTART ]]
then
    exec "${0}"
fi
