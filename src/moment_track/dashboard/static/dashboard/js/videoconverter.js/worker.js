importScripts('./ffmpeg-all-codecs.js');

var _createMessageFn = function (type) {
    return function (data) {
        return {
            type: type,
            data: data || {}
        }
    }
};

var Message = {
    ready: _createMessageFn('ready'),
    start: _createMessageFn('start'),
    done: _createMessageFn('done'),
    print: _createMessageFn('print'),
    error: _createMessageFn('error')
};

onmessage = function (event) {
    var message = event.data;

    if ('command' !== message.type) {
        return;
    }

    var Command = {
        print: function (data) { postMessage(Message.print(data))},
        printErr: function (data) { postMessage(Message.error(data))},
        files: message.files || [],
        arguments: message.arguments,
        TOTAL_MEMORY: message.TOTAL_MEMORY || false
    };

    postMessage(Message.start(Command.arguments.join(" ")));

    var startTime = Date.now();
    var results = ffmpeg_run(Command);
    var endTime = Date.now();

    postMessage(
        Message.done({
            results: results,
            elapsedTime: endTime - startTime
        })
    );
};

postMessage(Message.ready());