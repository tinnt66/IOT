/* global jQuery */

(function (window, $) {
  'use strict';

  function smoothScroll(target) {
    var $el = $(target);
    if (!$el.length) return;
    $('html, body').animate({ scrollTop: $el.offset().top - 72 }, 200);
  }

  $(function () {
    window.WebDashboard = window.WebDashboard || {};

    if (window.WebDashboard.theme && window.WebDashboard.theme.init) {
      window.WebDashboard.theme.init();
    }

    window.WebDashboard.realtime.init();
    window.WebDashboard.database.init();
    window.WebDashboard.socket.start();

    // Navbar smooth scroll (jQuery 100%)
    $('a.nav-link[href^="#"]').on('click', function (e) {
      e.preventDefault();
      var href = $(this).attr('href');
      smoothScroll(href);
    });
  });
})(window, jQuery);
