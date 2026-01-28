/* global jQuery */

(function (window, $) {
  'use strict';

  window.WebDashboard = window.WebDashboard || {};

  function prefersDark() {
    return !!(window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches);
  }

  function applyTheme(theme) {
    var root = document.documentElement;
    var shouldDark = theme === 'dark' || (theme === 'device' && prefersDark());
    root.classList.toggle('dark', shouldDark);
    root.dataset.theme = theme;
    $(document).trigger('theme:changed', [theme, shouldDark]);
  }

  function setActive(theme) {
    $('.theme-btn').each(function () {
      var $btn = $(this);
      var isActive = String($btn.data('theme')) === String(theme);
      $btn.attr('aria-pressed', isActive ? 'true' : 'false');
      $btn.toggleClass('bg-gray-900 text-white shadow-sm dark:bg-white dark:text-gray-900', isActive);
      $btn.toggleClass('text-gray-700 hover:bg-gray-100 dark:text-gray-200 dark:hover:bg-gray-800', !isActive);
    });
  }

  function getTheme() {
    try {
      return localStorage.getItem('theme') || document.documentElement.dataset.theme || 'device';
    } catch (e) {
      return document.documentElement.dataset.theme || 'device';
    }
  }

  function setTheme(theme) {
    try {
      localStorage.setItem('theme', theme);
    } catch (e) {
      // ignore
    }
    setActive(theme);
    applyTheme(theme);
  }

  window.WebDashboard.theme = {
    init: function () {
      if (!$('.theme-btn').length) return;

      var initial = getTheme();
      setActive(initial);
      applyTheme(initial);

      $('.theme-btn').on('click', function () {
        var theme = String($(this).data('theme') || 'device');
        setTheme(theme);
      });

      if (window.matchMedia) {
        var mql = window.matchMedia('(prefers-color-scheme: dark)');
        var handler = function () {
          var current = getTheme();
          if (current === 'device') applyTheme('device');
        };

        if (mql.addEventListener) mql.addEventListener('change', handler);
        else if (mql.addListener) mql.addListener(handler);
      }
    }
  };
})(window, jQuery);
