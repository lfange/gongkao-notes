"""Import supplied DOCX notes into the site's neutral reference collection."""
from pathlib import Path
from zipfile import ZipFile
import html
import json
import posixpath
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
      'v': 'urn:schemas-microsoft-com:vml'}
W = '{' + NS['w'] + '}'


def neutral(text):
    for old, new in [('行政职业能力测验', 'A类'), ('公安专业科目', 'C类'),
                     ('公安专业考试', 'C类练习'), ('申论', 'B类'), ('行测', 'A类'),
                     ('国考', '综合练习'), ('省考', '区域练习'), ('招警', 'C类'),
                     ('公务员考试', '综合练习'), ('考试', '练习')]:
        text = text.replace(old, new)
    return text


def convert(source, code, label):
    target = ROOT / '文档' / code
    target.mkdir(parents=True, exist_ok=True)
    with ZipFile(source) as archive:
        body = ET.fromstring(archive.read('word/document.xml')).find('w:body', NS)
        rels = {r.attrib['Id']: r.attrib for r in
                ET.fromstring(archive.read('word/_rels/document.xml.rels'))}
        images = {}
        stats = {'paragraphs': 0, 'tables': 0, 'images': 0, 'characters': 0}

        def paragraph(node):
            parts = []
            for el in node.iter():
                if el.tag == W + 't':
                    parts.append(html.escape(neutral(el.text or '')))
                    stats['characters'] += len(el.text or '')
                elif el.tag == W + 'tab':
                    parts.append('　')
                elif el.tag in (W + 'br', W + 'cr'):
                    parts.append('<br>')
                elif el.tag in ('{' + NS['a'] + '}blip', '{' + NS['v'] + '}imagedata'):
                    rid = el.get('{' + NS['r'] + '}embed') or el.get('{' + NS['r'] + '}id')
                    rel = rels.get(rid, {})
                    if not rel or rel.get('TargetMode') == 'External':
                        raise ValueError('Unsupported external or missing image relationship')
                    member = posixpath.normpath(posixpath.join('word', rel['Target']))
                    if member not in images:
                        filename = f'figure-{len(images) + 1:03d}{Path(member).suffix.lower()}'
                        (target / 'images').mkdir(exist_ok=True)
                        (target / 'images' / filename).write_bytes(archive.read(member))
                        images[member] = filename
                    stats['images'] += 1
                    parts.append(f'<img src="文档/{code}/images/{images[member]}" alt="资料配图" loading="lazy">')
            stats['paragraphs'] += 1
            content = ''.join(parts).strip()
            if not content:
                return ''
            style = node.find('w:pPr/w:pStyle', NS)
            name = style.get(W + 'val', '') if style is not None else ''
            levels = {'全文一级大标题': 2, '正文一级标题': 3, '正文二级标题': 4, '正文三级标题': 5}
            if name in levels:
                return '#' * levels[name] + ' ' + content
            if '列表' in name:
                return '- ' + content
            return content

        def table(node):
            stats['tables'] += 1
            rows = []
            for row in node.findall('w:tr', NS):
                cells = []
                for cell in row.findall('w:tc', NS):
                    span = cell.find('w:tcPr/w:gridSpan', NS)
                    attrs = f' colspan="{int(span.get(W + "val"))}"' if span is not None else ''
                    values = []
                    for child in cell:
                        if child.tag == W + 'p':
                            value = paragraph(child)
                            if value:
                                values.append('<p>' + re.sub(r'^#{2,5} |^- ', '', value) + '</p>')
                        elif child.tag == W + 'tbl':
                            values.append(table(child))
                    cells.append(f'<td{attrs}>' + ''.join(values) + '</td>')
                rows.append('<tr>' + ''.join(cells) + '</tr>')
            return '<div style="overflow-x:auto"><table>' + ''.join(rows) + '</table></div>'

        output = [f'# 资料{code[2:]} · {label}',
                  '[返回文档目录](文档/README.md)',
                  '> 根据用户提供的 AI 总结原文整理，保留原有内容、表格和配图。原文观点及法律条文时效尚未逐条核验。']
        for node in body:
            if node.tag == W + 'p':
                output.append(paragraph(node))
            elif node.tag == W + 'tbl':
                output.append(table(node))
        (target / 'README.md').write_text('\n\n'.join(x for x in output if x) + '\n', encoding='utf-8')
        stats['unique_images'] = len(images)
        (target / 'import-summary.json').write_text(json.dumps(stats, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        return stats


if __name__ == '__main__':
    for prefix, code, label in [('07.', '资料C02', '单元13—14'),
                                 ('10.', '资料C03', '单元19—20'),
                                 ('11.', '资料C04', '单元21—22')]:
        candidates = list(Path('H:/Downloads').glob(prefix + '*AI总结.docx'))
        if len(candidates) != 1:
            raise ValueError(f'Expected one source for {prefix}')
        print(code, convert(candidates[0], code, label))
