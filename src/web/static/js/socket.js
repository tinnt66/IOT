/* global io, jQuery */

(function (window, $) {
  'use strict';

  window.WebDashboard = window.WebDashboard || {};

  function setStatus(text, kind) {
    var $badge = $('#connStatusBadge');
    $badge.removeClass(
      'bg-gray-100 text-gray-700 bg-green-100 text-green-700 bg-red-100 text-red-700 ' +
      'dark:bg-gray-800 dark:text-gray-200 dark:bg-green-900/40 dark:text-green-200 dark:bg-red-900/40 dark:text-red-200'
    );
    if (kind === 'ok') $badge.addClass('bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-200');
    else if (kind === 'bad') $badge.addClass('bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-200');
    else $badge.addClass('bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-200');
    $badge.text(text);
  }

  window.WebDashboard.socket = {
    start: function () {
      // Force long-polling to avoid Werkzeug WebSocket issues in development.
      var socket = io({ transports: ['polling'], upgrade: false });

      setStatus('Connecting', 'neutral');

      // Refresh DB stats periodically (counts update after DB worker commits).
      setInterval(function () {
        if (socket.connected) socket.emit('request_stats');
      }, 10000);

      socket.on('connect', function () {
        setStatus('Connected', 'ok');
        $(document).trigger('ws:connect');
        socket.emit('request_stats');
      });

      socket.on('disconnect', function () {
        setStatus('Disconnected', 'bad');
        $(document).trigger('ws:disconnect');
      });

      socket.on('stats_update', function (data) {
        $(document).trigger('ws:stats', [data || {}]);
      });

      socket.on('rs485_data', function (payload) {
        $(document).trigger('ws:rs485', [payload || {}]);
      });

      socket.on('adxl_data', function (payload) {
        $(document).trigger('ws:adxl', [payload || {}]);
      });

      socket.on('error', function (data) {
        $(document).trigger('ws:error', [data || {}]);
      });

      window.WebDashboard._socket = socket;
      return socket;
    }
  };
})(window, jQuery);
