(function (root, factory) {
  'use strict';
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (!root || !root.document) return;

  root.$docsify = root.$docsify || {};
  const plugins = root.$docsify.plugins || [];
  plugins.push(function (hook) {
    // Change text after Markdown is parsed: hrefs, anchors and source URLs remain intact.
    hook.afterEach(function (html) {
      const container = root.document.createElement('div');
      container.innerHTML = html;
      api.tree(container);
      return container.innerHTML;
    });
    hook.doneEach(function () { api.tree(root.document.documentElement); });
  });
  root.$docsify.plugins = plugins;

  // Covers asynchronously rendered sidebar entries, search snippets, titles and tooltips.
  const observer = new root.MutationObserver(function (records) {
    records.forEach(function (record) {
      if (record.type === 'characterData') api.tree(record.target);
      else if (record.type === 'attributes') api.tree(record.target);
      else record.addedNodes.forEach(api.tree);
    });
  });
  api.tree(root.document.documentElement);
  observer.observe(root.document.documentElement, {
    childList: true, subtree: true, characterData: true, attributes: true,
    attributeFilter: ['title', 'aria-label', 'alt', 'placeholder']
  });
})(typeof window === 'object' ? window : null, function () {
  'use strict';
  const replacements = [
    ['行政职业能力测验', 'A类'], ['公安专业知识', 'C类'], ['公安专业科目', 'C类'],
    ['公务员录用考试', '综合练习'], ['公务员考试', '综合练习'],
    ['公务员招录', '岗位资料'], ['行政执法类', '专项类别'],
    ['心理素质测试', 'D类'], ['行测', 'A类'], ['申论', 'B类'],
    ['公考', '学习'], ['国考', '全国资料'], ['省考', '地方资料'],
    ['招警', '专项资料'], ['备考', '学习'], ['考试', '练习'],
    ['笔试', '书面练习'], ['面试', '交流练习'], ['真题', '原题'], ['冲刺', '集中学习']
  ];

  function text(value) {
    let result = value;
    replacements.forEach(function (pair) { result = result.split(pair[0]).join(pair[1]); });
    // Keep the exact legal title 公务员法 while neutralizing ordinary job labels.
    return result.replace(/公务员(?!法)(?:岗位|岗)?/g, '公共事务岗位');
  }

  function tree(node) {
    if (!node) return;
    if (node.nodeType === 3) {
      const parentTag = node.parentNode && node.parentNode.tagName;
      if (parentTag && /^(SCRIPT|STYLE|NOSCRIPT)$/.test(parentTag)) return;
      const value = text(node.nodeValue);
      if (value !== node.nodeValue) node.nodeValue = value;
      return;
    }
    if (node.nodeType !== 1 && node.nodeType !== 9 && node.nodeType !== 11) return;
    if (/^(SCRIPT|STYLE|NOSCRIPT)$/.test(node.tagName || '')) return;
    ['title', 'aria-label', 'alt', 'placeholder'].forEach(function (name) {
      if (!node.hasAttribute || !node.hasAttribute(name)) return;
      const value = node.getAttribute(name);
      const updated = text(value);
      if (updated !== value) node.setAttribute(name, updated);
    });
    Array.from(node.childNodes || []).forEach(tree);
    // Search highlights can split a keyword into e.g. <em>行</em>测.
    // Flatten only that snippet when needed; keep links and their destinations.
    if (node.matches && node.matches('.matching-post .title, .matching-post .content')) {
      const current = node.textContent;
      const updated = text(current);
      if (updated !== current) node.textContent = updated;
    }
  }
  return { text: text, tree: tree };
});
