window.VideoConverterJsApp = (function () {

    var _worker = null;

    var _isWorkerLoaded = false;
    var _isWorkerRunning = false;

    var callbacks = {
        onStartRunning: false,
        onStopRunning: false,
        onReady: false,
        onPrint: false,
        onError: false,
        onDone: false
    };

    function _doNothing() {}
    function _getCallback(name) {
        if ('function' === typeof callbacks[name]) {
            return callbacks[name];
        } else {
            return _doNothing;
        }
    }

    function _isWorkerReady() {
        return (_isWorkerLoaded && (!_isWorkerRunning))
    }

    function _startRunning() {
        _isWorkerRunning = true;
        _getCallback('onStartRunning')();
    }

    function _stopRunning() {
        _isWorkerRunning = false;
        _getCallback('onStopRunning')();
    }

    function _parseArguments(text) {
        text = text.replace(/\s+/g, ' ');
        var args = [];
        // Allow double quotes to not split args.
        text.split('"').forEach(function (t, i) {
            t = t.trim();
            if ((i % 2) === 1) {
                args.push(t);
            } else {
                args = args.concat(t.split(" "));
            }
        });
        return args;
    }

    function run(command, file) {
        if (_isWorkerReady()) {
            _startRunning();
            var args = _parseArguments(command);
            _worker.postMessage({
                type: "command",
                arguments: args,
                files: (('undefined' !== typeof file) ? [file] : [])
            });
            return true;
        } else {
            _isWorkerRunning = false;
            return false;
        }
    }

    function initWorker(scriptURL) {
        _worker = new Worker(scriptURL);
        _worker.onmessage = function (event) {
            var message = event.data;
            if (message.type === 'ready') {
                _isWorkerLoaded = true;
                _getCallback('onReady')();
            } else if (message.type === 'print') {
                _getCallback('onPrint')(message.data);
            } else if (message.type === 'error') {
                _getCallback('onError')(message.data);
            } else if (message.type === 'done') {
                _stopRunning();
                _getCallback('onDone')(message.data);
            }
        }
    }

    function File(name, data) {
        return {
            'name': name || '',
            'data': new Uint8Array(data)
        }
    }

    return {
        init: initWorker,
        run: run,
        callbacks: callbacks,
        File: File
    }
})();