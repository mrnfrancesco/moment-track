'use strict';

(function (ns) {
    ns.ProgressBar = function (options) {
        this.$bar = $('#' + options.bar);
        if ('undefined' !== typeof options.text) {
            this.$text = $('#' + options.text);
        } else {
            this.$text = $(null);
        }
        this.infinite = options.infinite || false;
        this.infiniteAddValue = options.infiniteAddValue || 25;
        this.doneClass = options.doneClass || 'progress-bar-success';
        this.intervalIndex = null;
    };

    ns.ProgressBar.prototype.set = function (total, loaded) {
        if (total !== 0) {
            var percentage = Math.round((loaded / total) * 100);
            _update(this, percentage);
            _text(this, [
                formatBytes(loaded), ' / ', formatBytes(total),
                ' (', percentage, '%)'
            ].join(''));
        } else {
            _update(this, this.infiniteAddValue);
        }
    };

    ns.ProgressBar.prototype.empty = function (text) {
        _set(this, 0);
        _text(this, text);
    }

    ns.ProgressBar.prototype.intervalUpdate = function (interval) {
        if (this.infinite === true) {
            this.stopIntervalUpdate();
            var pbar = this;
            this.intervalIndex = setInterval(function () {
                _add(pbar, pbar.infiniteAddValue);
            }, interval);
        }
    };

    ns.ProgressBar.prototype.stopIntervalUpdate = function () {
        if (this.intervalIndex !== null) {
            clearInterval(this.intervalIndex);
        }
    };

    ns.ProgressBar.prototype.setDone = function (text) {
        this.stopIntervalUpdate();
        _set(this, 100);
        this.$bar.addClass(this.doneClass);
        _text(this, text);
    };

    function _text(pbar, text) {
        if ('undefined' !== typeof text) {
            pbar.$text.html(text);
        }
    }

    function _update(pbar, value) {
        pbar.$bar.attr('aria-valuenow', value);
        if (pbar.infinite === true) {
            _add(pbar, value);
        } else {
            _set(pbar, value);
        }
    }

    function _set(pbar, value) {
        pbar.$bar.attr('aria-valuenow', value);
        pbar.$bar.css('width', value + '%')
    }

    function _add(pbar, value) {
        var previousValue = Number(pbar.$bar.attr('aria-valuenow'));
        var nextValue = previousValue + value;
        if (nextValue > 100) {
            nextValue = 0;
        }
        _set(pbar, nextValue);
    }
}(window.ProgressBarNamespace || window));

