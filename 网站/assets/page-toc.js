(function () {
  'use strict';

  function pageTocPlugin(hook) {
    const desktop = window.matchMedia('(min-width: 1280px)');
    let dispose = function () {};

    hook.beforeEach(function (markdown) {
      dispose();
      document.body.classList.remove('has-page-toc');
      return markdown;
    });

    hook.doneEach(function () {
      dispose();
      const article = document.querySelector('#main');
      if (!article) return;
      const headings = Array.from(article.querySelectorAll('h2[id], h3[id]'));
      if (!headings.length) return;

      const aside = document.createElement('aside');
      aside.className = 'page-toc';
      const details = document.createElement('details');
      const summary = document.createElement('summary');
      summary.textContent = '本页目录';
      const nav = document.createElement('nav');
      nav.setAttribute('aria-label', '本页目录');
      const list = document.createElement('ul');
      nav.appendChild(list);
      details.append(summary, nav);
      aside.appendChild(details);

      let section = null;
      const entries = [];
      headings.forEach(function (heading) {
        const anchor = heading.querySelector('a.anchor');
        if (!anchor) return;
        const item = document.createElement('li');
        const link = document.createElement('a');
        link.textContent = heading.textContent.trim();
        link.setAttribute('href', anchor.getAttribute('href'));
        item.appendChild(link);
        if (heading.tagName === 'H3' && section) {
          let children = section.querySelector('ul');
          if (!children) {
            children = document.createElement('ul');
            section.appendChild(children);
          }
          children.appendChild(item);
        } else {
          list.appendChild(item);
          if (heading.tagName === 'H2') section = item;
        }
        entries.push({ heading: heading, link: link });
      });
      if (!entries.length) return;

      const title = article.querySelector('h1');
      if (title) title.after(aside);
      else article.prepend(aside);
      document.body.classList.add('has-page-toc');

      function setLayout() {
        details.open = desktop.matches;
        if (desktop.matches) summary.setAttribute('tabindex', '-1');
        else summary.removeAttribute('tabindex');
      }
      function keepDesktopOpen(event) {
        if (desktop.matches) event.preventDefault();
      }
      function collapseAfterNavigate(event) {
        if (!desktop.matches && event.target.closest('a')) details.open = false;
      }
      summary.addEventListener('click', keepDesktopOpen);
      nav.addEventListener('click', collapseAfterNavigate);
      desktop.addEventListener('change', setLayout);
      setLayout();

      let frame = 0;
      let active = null;
      function updateActive() {
        frame = 0;
        let current = entries[0];
        for (const entry of entries) {
          if (entry.heading.getBoundingClientRect().top > 120) break;
          current = entry;
        }
        if (active === current.link) return;
        if (active) {
          active.classList.remove('is-active');
          active.removeAttribute('aria-current');
        }
        active = current.link;
        active.classList.add('is-active');
        active.setAttribute('aria-current', 'location');
        if (desktop.matches) {
          const bounds = nav.getBoundingClientRect();
          const item = active.getBoundingClientRect();
          if (item.top < bounds.top) nav.scrollTop += item.top - bounds.top;
          else if (item.bottom > bounds.bottom) nav.scrollTop += item.bottom - bounds.bottom;
        }
      }
      function scheduleUpdate() {
        if (!frame) frame = window.requestAnimationFrame(updateActive);
      }
      window.addEventListener('scroll', scheduleUpdate, { passive: true });
      window.addEventListener('resize', scheduleUpdate);
      const observer = new ResizeObserver(scheduleUpdate);
      observer.observe(article);
      scheduleUpdate();

      dispose = function () {
        window.cancelAnimationFrame(frame);
        observer.disconnect();
        window.removeEventListener('scroll', scheduleUpdate);
        window.removeEventListener('resize', scheduleUpdate);
        desktop.removeEventListener('change', setLayout);
        aside.remove();
      };
    });
  }

  window.$docsify.plugins.push(pageTocPlugin);
})();
