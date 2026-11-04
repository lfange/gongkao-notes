from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT

OUT = 'E:/public/output/annual-growth/年均增长率计算表.docx'
doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
sec.top_margin, sec.bottom_margin = Cm(1.8), Cm(1.8)
sec.left_margin, sec.right_margin = Cm(2), Cm(2)
for name in ['Normal', 'Title', 'Heading 1', 'Heading 2']:
    st = doc.styles[name]
    st.font.name = 'Microsoft YaHei'
    st._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'), 'Microsoft YaHei')
    st.font.color.rgb = RGBColor(0, 0, 0)
doc.styles['Normal'].font.size = Pt(10.5)
doc.styles['Normal'].paragraph_format.space_after = Pt(6)
doc.styles['Normal'].paragraph_format.line_spacing = 1.15
doc.styles['Title'].font.size = Pt(23)
doc.styles['Heading 1'].font.size = Pt(13)
doc.styles['Heading 1'].paragraph_format.space_before = Pt(12)
doc.styles['Heading 1'].paragraph_format.space_after = Pt(6)

def p(text, style=None):
    return doc.add_paragraph(text, style)

def table(headers, rows, widths):
    t = doc.add_table(rows=1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for c, w in zip(t.columns, widths): c.width = Cm(w)
    for c, v in zip(t.rows[0].cells, headers): c.text = v
    for row in rows:
        for c, v in zip(t.add_row().cells, row): c.text = str(v)
    borders = OxmlElement('w:tblBorders')
    for side in ['top','left','bottom','right','insideH','insideV']:
        e = OxmlElement('w:' + side)
        for key, value in [('val','single'),('sz','5'),('color','D9D9D9')]: e.set(qn('w:' + key), value)
        borders.append(e)
    t._tbl.tblPr.append(borders)
    for i, row in enumerate(t.rows):
        for j, cell in enumerate(row.cells):
            cell.width = Cm(widths[j])
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            tcpr = cell._tc.get_or_add_tcPr()
            margins = OxmlElement('w:tcMar')
            for side, val in [('top','90'),('bottom','90'),('left','100'),('right','100')]:
                e = OxmlElement('w:'+side); e.set(qn('w:w'),val); e.set(qn('w:type'),'dxa'); margins.append(e)
            tcpr.append(margins)
            sh = OxmlElement('w:shd'); sh.set(qn('w:fill'), 'DCE6F1' if i == 0 else ('F5F7FA' if i % 2 == 0 else 'FFFFFF')); tcpr.append(sh)
            for para in cell.paragraphs:
                para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                para.paragraph_format.space_after = Pt(0)
                for run in para.runs:
                    run.font.size = Pt(10)
                    run.bold = i == 0
    repeat = OxmlElement('w:tblHeader'); t.rows[0]._tr.get_or_add_trPr().append(repeat)
    p('') .paragraph_format.space_after = Pt(0)
    return t

p('年均增长率计算表', 'Title')
p('用于记录年度数据，并按复合年均增长率（CAGR）衡量一段时期内的平均增长水平。填写期初值、期末值和增长年数后，按公式计算并录入结果。')
p('一 计算口径', 'Heading 1')
p('年均增长率 = [(期末值 ÷ 期初值)^(1 ÷ n) − 1] × 100%')
p('n 为增长年数，按“期末年份 − 期初年份”计算。例如，2020 年至 2025 年的 n = 5，不能按 6 个年度数据点计算。公式中的 ^ 表示乘方。')
p('二 基本信息', 'Heading 1')
p('指标名称：________________    计量单位：________________')
p('统计期间：________年至________年    数据来源：________________')
p('三 年度数据填写表', 'Heading 1')
table(['年度', '指标数值', '较上年增长率', '备注'], [
    ['____年（期初）', '', '不适用', ''],
    *[['____年', '', '', ''] for _ in range(4)],
    ['____年（期末）', '', '', '']
], [3.4,4.1,4.4,5.1])
p('较上年增长率 =（本年值 ÷ 上年值 − 1）× 100%。行数可按统计期间增减。')
p('四 计算结果', 'Heading 1')
table(['期初值', '期末值', '增长年数 n', '年均增长率'], [['________','________','____年','________%']], [4.25,4.25,4.25,4.25])
p('计算过程：______________________________________________________')
p('填表人：________________    填表日期：________年____月____日')

doc.add_page_break()
p('年均增长率计算示例', 'Title')
p('以下为演示数据，用于说明计算步骤。假设某指标在 2020 年为 100，2025 年为 150，单位保持一致。')
p('一 年度数据示例', 'Heading 1')
values = [100,110,120,126,138,150]
rows = []
for i,v in enumerate(values):
    rows.append([str(2020+i), f'{v:.2f}', '不适用' if i==0 else f'{(v/values[i-1]-1)*100:.2f}%'])
table(['年度','指标数值','较上年增长率'], rows, [4,6.5,6.5])
p('二 计算过程与结果', 'Heading 1')
p('增长年数 n = 2025 − 2020 = 5 年。')
p('年均增长率 = [(150 ÷ 100)^(1 ÷ 5) − 1] × 100% ≈ 8.45%。')
table(['指标','结果','含义'], [
    ['年均增长率','8.45%','按复合增长口径折算的平均年度增长率'],
    ['累计增长率','50.00%','期末相对期初的总增长幅度']
], [3.7,3,10.3])
p('结论：该指标在 2020 年至 2025 年间累计增长 50.00%，复合年均增长率约为 8.45%。各年的实际增长率可以不同。')
p('三 填写与核对说明', 'Heading 1')
p('1. 各年度应使用相同的指标定义、单位和统计范围，并保持取数时点一致。')
p('2. 本表常规计算口径要求期初值大于 0、期末值大于 0，且 n 大于 0。零值、负值或正负跨越的数据，应另行说明适用口径，不能直接套用本表。')
p('3. 年均增长率不等于各年增长率的算术平均值，也不等于累计增长率除以增长年数。中间年份数据用于展示年度变化，CAGR 由期初值、期末值和 n 决定。')
p('4. 计算时保留完整精度，最终百分比通常保留两位小数。此 Word 表为填写模板，不会随输入值自动重新计算。')
doc.core_properties.title = '年均增长率计算表'
doc.core_properties.subject = '复合年均增长率填写模板与示例'
doc.core_properties.author = ''
doc.save(OUT)
print(OUT)
print('Example CAGR:', (1.5 ** .2 - 1) * 100)
