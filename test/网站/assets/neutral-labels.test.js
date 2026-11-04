const assert = require('node:assert/strict');
const { test } = require('node:test');
const labels = require('../../../网站/assets/neutral-labels.js');

test('neutral names cover course titles and site navigation', () => {
  const input = '行政职业能力测验 行测 申论 公安专业科目 公考 国考 省考 备考 考试 真题';
  const output = labels.text(input);
  assert.match(output, /A类/);
  assert.match(output, /B类/);
  assert.match(output, /C类/);
  assert.doesNotMatch(output, /行政职业能力测验|行测|申论|公安专业科目|公考|国考|省考|备考|考试|真题/);
  assert.equal(labels.text(output), output);
});

test('neutralization changes visible text but preserves source links and legal names', () => {
  const link = {
    nodeType: 1, tagName: 'A',
    attrs: { href: '/shenlun/申论.md', title: '申论真题' },
    childNodes: [{ nodeType: 3, nodeValue: '申论与行测' }],
    hasAttribute(name) { return name in this.attrs; },
    getAttribute(name) { return this.attrs[name]; },
    setAttribute(name, value) { this.attrs[name] = value; }
  };
  labels.tree(link);
  assert.equal(link.attrs.href, '/shenlun/申论.md');
  assert.equal(link.attrs.title, 'B类原题');
  assert.equal(link.childNodes[0].nodeValue, 'B类与A类');
  assert.equal(labels.text('中华人民共和国公务员法'), '中华人民共和国公务员法');
  assert.equal(labels.text('普通公务员岗位备考'), '普通公共事务岗位学习');
});

test('search snippets and attributes are neutralized without altering executable code', () => {
  const script = { nodeType: 1, tagName: 'SCRIPT', childNodes: [{ nodeType: 3, nodeValue: 'const value = "申论";' }] };
  labels.tree(script);
  assert.equal(script.childNodes[0].nodeValue, 'const value = "申论";');
  const snippet = { nodeType: 1, tagName: 'DIV', childNodes: [
    { nodeType: 3, nodeValue: '2027年度公务员考试：' },
    { nodeType: 1, tagName: 'EM', childNodes: [{ nodeType: 3, nodeValue: '行测' }] }
  ] };
  labels.tree(snippet);
  assert.doesNotMatch(snippet.childNodes[0].nodeValue, /考试|公务员/);
  assert.equal(snippet.childNodes[1].childNodes[0].nodeValue, 'A类');
});

test('search highlighting cannot split a hidden keyword across text nodes', () => {
  let flattened;
  const node = {
    nodeType: 1, tagName: 'P',
    matches(selector) { return selector.includes('.matching-post'); },
    childNodes: [
      { nodeType: 1, tagName: 'EM', childNodes: [{ nodeType: 3, nodeValue: '行' }] },
      { nodeType: 3, nodeValue: '测原题' }
    ],
    get textContent() { return flattened === undefined ? this.childNodes[0].childNodes[0].nodeValue + this.childNodes[1].nodeValue : flattened; },
    set textContent(value) { flattened = value; }
  };
  labels.tree(node);
  assert.equal(node.textContent, 'A类原题');
});
