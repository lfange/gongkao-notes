(function () {
  'use strict';

  function sidebarGroupsPlugin(hook) {
    const storageKey = 'gongkao-sidebar-groups-v1';
    let states = {};
    let renderedRoot = null;
    let groups = [];
    try {
      const saved = JSON.parse(localStorage.getItem(storageKey));
      if (saved && typeof saved === 'object' && !Array.isArray(saved)) states = saved;
    } catch (error) {
      // Navigation still works when browser storage is unavailable.
    }

    function save() {
      try {
        localStorage.setItem(storageKey, JSON.stringify(states));
      } catch (error) {
        // Keep the current state in memory for this visit.
      }
    }

    function setExpanded(group, expanded) {
      group.list.hidden = !expanded;
      group.button.setAttribute('aria-expanded', String(expanded));
      group.button.title = (expanded ? '收起' : '展开') + group.name;
    }

    function currentLink(nav) {
      function pageKey(url) {
        return decodeURIComponent(new URL(url, location.href).hash.split('?')[0] || '#/')
          .replace(/\.md$/, '')
          .replace(/\/$/, '');
      }
      const current = pageKey(location.href);
      return Array.from(nav.querySelectorAll('a')).find(function (link) {
        return pageKey(link.href) === current;
      });
    }

    hook.doneEach(function () {
      const nav = document.querySelector('.sidebar-nav');
      const root = nav && Array.from(nav.children).find(function (child) {
        return child.tagName === 'UL';
      });
      if (!root) return;
      const active = currentLink(nav);
      if (root === renderedRoot) {
        groups.forEach(function (group) {
          if (active && group.item.contains(active)) setExpanded(group, true);
        });
        return;
      }
      renderedRoot = root;
      const oldActions = nav.querySelector('.sidebar-menu-actions');
      if (oldActions) oldActions.remove();

      groups = Array.from(root.querySelectorAll('li')).map(function (item) {
        const list = Array.from(item.children).find(function (child) {
          return child.tagName === 'UL';
        });
        if (!list) return null;
        const caption = Array.from(item.childNodes).filter(function (node) {
          return node !== list;
        });
        const label = caption.map(function (node) { return node.textContent; }).join(' ')
          .replace(/\s+/g, ' ').trim();
        return { item: item, list: list, caption: caption, label: label };
      }).filter(Boolean);

      const labels = new Map(groups.map(function (group) { return [group.item, group.label]; }));
      groups.forEach(function (group, index) {
        const path = [group.label];
        let parent = group.item.parentElement;
        while (parent && parent !== root) {
          if (labels.has(parent)) path.unshift(labels.get(parent));
          parent = parent.parentElement;
        }
        group.key = path.join('/');
        group.name = group.label.replace(/^[^\p{L}\p{N}]+/u, '');
        group.item.classList.add('sidebar-group');
        group.list.id = 'site-sidebar-submenu-' + index;

        const row = document.createElement('div');
        row.className = 'sidebar-group-heading';
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'sidebar-group-toggle';
        button.setAttribute('aria-label', group.name);
        button.setAttribute('aria-controls', group.list.id);
        group.button = button;
        row.appendChild(button);

        const hasLink = group.caption.some(function (node) {
          return node.nodeType === 1 && (node.tagName === 'A' || node.querySelector('a'));
        });
        if (hasLink) {
          button.classList.add('is-link-toggle');
          const label = document.createElement('span');
          label.className = 'sidebar-group-label';
          group.caption.forEach(function (node) { label.appendChild(node); });
          row.appendChild(label);
        } else {
          button.textContent = group.label;
          group.caption.forEach(function (node) { node.remove(); });
        }
        group.item.insertBefore(row, group.list);
        setExpanded(group, Boolean(active && group.item.contains(active)) || states[group.key] === true);
        button.addEventListener('click', function () {
          const expanded = button.getAttribute('aria-expanded') !== 'true';
          setExpanded(group, expanded);
          states[group.key] = expanded;
          save();
        });
      });

      if (!groups.length) return;
      const actions = document.createElement('div');
      actions.className = 'sidebar-menu-actions';
      [true, false].forEach(function (expanded) {
        const button = document.createElement('button');
        button.type = 'button';
        button.textContent = expanded ? '全部展开' : '全部收起';
        button.addEventListener('click', function () {
          groups.forEach(function (group) {
            setExpanded(group, expanded);
            states[group.key] = expanded;
          });
          save();
        });
        actions.appendChild(button);
      });
      nav.insertBefore(actions, root);
    });
  }

  window.$docsify.plugins.push(sidebarGroupsPlugin);
})();
