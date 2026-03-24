from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_CENTER

styles = getSampleStyleSheet()
H2   = ParagraphStyle('H2',   fontSize=14, textColor=colors.HexColor('#283593'), spaceAfter=4,  spaceBefore=12, fontName='Helvetica-Bold')
H3   = ParagraphStyle('H3',   fontSize=11, textColor=colors.HexColor('#3949ab'), spaceAfter=3,  spaceBefore=8,  fontName='Helvetica-Bold')
BD   = ParagraphStyle('BD',   fontSize=10, leading=16, spaceAfter=4, fontName='Helvetica',      textColor=colors.HexColor('#212121'))
BL   = ParagraphStyle('BL',   fontSize=10, leading=15, spaceAfter=2, leftIndent=14, fontName='Helvetica', textColor=colors.HexColor('#212121'))
TTL  = ParagraphStyle('TTL',  fontSize=26, textColor=colors.HexColor('#0d1b6e'), alignment=TA_CENTER, fontName='Helvetica-Bold', spaceAfter=4)
SUB  = ParagraphStyle('SUB',  fontSize=12, textColor=colors.HexColor('#5c6bc0'), alignment=TA_CENTER, fontName='Helvetica', spaceAfter=6)
CONF = ParagraphStyle('CONF', fontSize=8,  textColor=colors.HexColor('#9e9e9e'), alignment=TA_CENTER, fontName='Helvetica')

# ─── DOC 1: FINANCE GUIDE ────────────────────────────────────────
story = []
story.append(Spacer(1, 0.8*cm))
story.append(Paragraph('Personal &amp; Corporate Finance Guide 2024', TTL))
story.append(Paragraph('Comprehensive Reference for Financial Literacy and Decision Making', SUB))
story.append(Paragraph('Updated March 2024 | For educational purposes', CONF))
story.append(HRFlowable(width='100%', thickness=2, color=colors.HexColor('#3949ab'), spaceAfter=14, spaceBefore=8))

data = [
    ('1. Introduction to Finance',
     'Finance is the discipline of managing money, assets, investments, and liabilities across individuals, businesses, and governments. Financial literacy enables better decision-making at every stage of life.',
     [
         ('Types of Finance', [
             'Personal Finance: budgeting, saving, insurance, investing for individuals.',
             'Corporate Finance: capital structure, funding, profitability for businesses.',
             'Public Finance: government revenue, expenditure, and debt management.',
         ])
     ]
    ),
    ('2. Personal Finance Fundamentals',
     'Building a strong personal financial foundation starts with living within your means, saving consistently, and protecting against risk.',
     [
         ('The 50/30/20 Budgeting Rule', [
             '50% of take-home income for Needs: rent, groceries, utilities, loan EMIs.',
             '30% for Wants: dining, entertainment, subscriptions, travel.',
             '20% for Savings and Debt Repayment: emergency fund, investments, extra payments.',
         ]),
         ('Emergency Fund', [
             'Target: 3 to 6 months of total monthly living expenses.',
             'Keep in a liquid instrument: savings account or liquid mutual fund.',
             'Do NOT invest emergency funds in equity or locked instruments.',
         ]),
         ('Net Worth Formula', [
             'Net Worth = Total Assets minus Total Liabilities.',
             'Example: Assets Rs.45L (property Rs.30L + investments Rs.15L), Liabilities Rs.18L (home loan Rs.15L + car loan Rs.3L) = Net Worth Rs.27L.',
         ]),
     ]
    ),
    ('3. Investment Options in India',
     'Diversification across asset classes reduces risk and improves long-term returns.',
     [
         ('Asset Class Comparison', [
             'Equity / Stocks: High risk, high return. Average Sensex return approx 12% per annum long term.',
             'Fixed Deposits (FD): Low risk, fixed return. Typical rates 6.5% to 7.5% per annum.',
             'Mutual Funds via SIP: Diversified; minimum SIP Rs.500 per month; professional management.',
             'Real Estate: Illiquid asset; rental yield 2% to 4% in India; long-term appreciation.',
             'Gold: Inflation hedge; 10-year CAGR approximately 9.8%.',
             'PPF (Public Provident Fund): Government-backed; 7.1% per annum tax-free; 15-year lock-in.',
             'NPS (National Pension System): Retirement corpus; tax benefit up to Rs.2L under Sec 80C + 80CCD(1B).',
         ]),
     ]
    ),
    ('4. Corporate Finance Concepts',
     'Corporate finance focuses on maximizing shareholder value through financial planning, capital allocation, and strategy.',
     [
         ('Key Ratios and Formulas', [
             'Capital Structure: Debt-to-Equity ratio. Healthy range: 1:1 to 2:1.',
             'Working Capital = Current Assets minus Current Liabilities.',
             'EBITDA: Earnings Before Interest, Tax, Depreciation and Amortisation.',
             'ROI = (Net Profit / Cost of Investment) x 100.',
             'P/E Ratio = Price per Share / Earnings per Share. Indian market average: 20 to 25x.',
             'Current Ratio: Current Assets / Current Liabilities. Healthy value is above 2.',
             'Quick Ratio: (Current Assets minus Inventory) / Current Liabilities. Healthy = above 1.',
         ]),
     ]
    ),
    ('5. Taxation in India (FY2024-25)',
     'Understanding tax slabs helps optimize take-home pay and investment planning under the new tax regime.',
     [
         ('New Tax Regime Income Slabs', [
             'Up to Rs.3 lakh: Nil (0%)',
             'Rs.3 lakh to Rs.7 lakh: 5%',
             'Rs.7 lakh to Rs.10 lakh: 10%',
             'Rs.10 lakh to Rs.12 lakh: 15%',
             'Rs.12 lakh to Rs.15 lakh: 20%',
             'Above Rs.15 lakh: 30%',
         ]),
         ('Key Deductions and Rates', [
             'Section 80C deduction limit: Rs.1.5 lakh per financial year.',
             'HRA exemption: Minimum of actual HRA, 50% salary (metro) or 40% (non-metro), rent paid minus 10% of salary.',
             'GST rates: 0%, 5%, 12%, 18%, 28% depending on goods or services category.',
             'LTCG on equity: 10% on gains above Rs.1 lakh; asset held more than 1 year.',
             'STCG on equity: 15% flat rate; asset held less than 1 year.',
         ]),
     ]
    ),
    ('6. Risk Management and Insurance',
     'Insurance is financial protection, not an investment. Skipping it to save premiums creates dangerous financial gaps.',
     [
         ('Coverage Guidelines', [
             'Life Insurance: Pure term plan; coverage = 10 to 15 times annual income.',
             'Health Insurance: Minimum Rs.5 lakh individual; family floater for households.',
             'Premium Budget: Total insurance premium should not exceed 5% of annual income.',
             'Risk Types: Market risk, credit risk, liquidity risk, inflation risk, operational risk.',
         ]),
     ]
    ),
    ('7. Financial Planning by Life Stage',
     'Priorities shift as you age. Align your investments and protection strategy to your current life stage.',
     [
         ('Stage-wise Milestones', [
             'Age 20s: Build emergency fund; start SIP Rs.2000+/month; buy term insurance early.',
             'Age 30s: Increase SIP; home loan if needed (EMI max 40% of income); maximise 80C.',
             'Age 40s: Reduce debt aggressively; boost retirement corpus; diversify across assets.',
             'Age 50s: Shift to low-risk assets; maximise NPS; plan estate and succession.',
             'Retirement Target: 25 times annual expenses (based on the 4% safe withdrawal rule).',
         ]),
     ]
    ),
    ('8. Key Financial Terms Glossary',
     '',
     [
         ('Important Terms', [
             'Inflation: RBI CPI target is 4% plus or minus 2%.',
             'Repo Rate: RBI benchmark lending rate; as of 2024 it is 6.5%.',
             'SIP: Systematic Investment Plan; fixed monthly mutual fund contribution.',
             'NAV: Net Asset Value; price per unit of a mutual fund.',
             'CAGR: Compound Annual Growth Rate; measures annualised investment return.',
             'FII: Foreign Institutional Investor; large overseas fund investing in Indian markets.',
             'NFO: New Fund Offer; like an IPO but for a new mutual fund scheme.',
             'Diversification: Spreading investments to reduce concentration risk.',
         ]),
     ]
    ),
    ('9. Common Financial Mistakes to Avoid',
     'Awareness of common pitfalls helps build wealth faster and avoids costly errors.',
     [
         ('Avoid These Mistakes', [
             'No emergency fund: even one medical emergency can derail all finances.',
             'Delaying insurance: premiums rise sharply with age; health issues may cause rejection.',
             'Chasing past mutual fund returns: past performance does not guarantee future results.',
             'Over-borrowing: EMI above 40% of income is financially dangerous and stressful.',
             'Ignoring inflation: Rs.10,000 today will buy far less in 20 years without investment growth.',
         ]),
     ]
    ),
]

for title, intro, subs in data:
    story.append(Paragraph(title, H2))
    if intro:
        story.append(Paragraph(intro, BD))
    for stitle, bullets in subs:
        story.append(Paragraph(stitle, H3))
        for b in bullets:
            story.append(Paragraph(b, BL))
        story.append(Spacer(1, 0.15*cm))
    story.append(Spacer(1, 0.25*cm))

story.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#9e9e9e'), spaceBefore=10))
story.append(Paragraph('Finance Guide 2024 | For educational purposes only | Not financial advice', CONF))

doc1 = SimpleDocTemplate('finance_guide_2024.pdf', pagesize=A4,
    leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
doc1.build(story)
print('finance_guide_2024.pdf created OK')

# ─── DOC 2: CREDIBILITY QUESTIONS ────────────────────────────────
QH = ParagraphStyle('QH', fontSize=11, textColor=colors.HexColor('#b71c1c'), spaceAfter=2, spaceBefore=10, fontName='Helvetica-Bold')
ANS= ParagraphStyle('ANS', fontSize=10, textColor=colors.HexColor('#1b5e20'), spaceAfter=2, leftIndent=10, fontName='Helvetica', leading=15)
INF= ParagraphStyle('INF', fontSize=9,  textColor=colors.HexColor('#616161'), spaceAfter=2, leftIndent=10, fontName='Helvetica', leading=13)
TTL2=ParagraphStyle('TTL2', fontSize=22, textColor=colors.HexColor('#0d1b6e'), alignment=TA_CENTER, fontName='Helvetica-Bold', spaceAfter=6)
SUB2=ParagraphStyle('SUB2', fontSize=11, textColor=colors.HexColor('#5c6bc0'), alignment=TA_CENTER, fontName='Helvetica', spaceAfter=4)

qs = [
    ('Q1. What is the 50/30/20 budgeting rule?',
     'Answer: 50% of income for needs, 30% for wants, and 20% for savings or debt repayment.',
     'Tests: Section 2 - Personal Finance Fundamentals'),
    ('Q2. How many months of expenses should an emergency fund cover?',
     'Answer: 3 to 6 months of living expenses.',
     'Tests: Section 2 - Emergency Fund'),
    ('Q3. What is the formula for calculating Net Worth?',
     'Answer: Net Worth = Total Assets minus Total Liabilities.',
     'Tests: Section 2 - Net Worth Formula'),
    ('Q4. In the example given, assets are Rs.45L and liabilities are Rs.18L. What is the net worth?',
     'Answer: Rs.27 lakh (Rs.45L - Rs.18L).',
     'Tests: Numerical reasoning from Section 2'),
    ('Q5. What is the approximate average annual Sensex return mentioned?',
     'Answer: Approximately 12% per annum over the long term.',
     'Tests: Section 3 - Equity / Stocks'),
    ('Q6. What is the typical FD interest rate range?',
     'Answer: 6.5% to 7.5% per annum.',
     'Tests: Section 3 - Fixed Deposits'),
    ('Q7. What is the minimum SIP amount for mutual funds?',
     'Answer: Rs.500 per month.',
     'Tests: Section 3 - Mutual Funds via SIP'),
    ('Q8. What is the interest rate for PPF and its lock-in period?',
     'Answer: 7.1% per annum, tax-free, with a 15-year lock-in period.',
     'Tests: Section 3 - PPF'),
    ('Q9. What is a healthy Debt-to-Equity ratio for a company?',
     'Answer: 1:1 to 2:1.',
     'Tests: Section 4 - Capital Structure'),
    ('Q10. What is the Working Capital formula?',
     'Answer: Working Capital = Current Assets minus Current Liabilities.',
     'Tests: Section 4 - Corporate Finance'),
    ('Q11. Under the new tax regime, what is the tax rate for income between Rs.7L and Rs.10L?',
     'Answer: 10%.',
     'Tests: Section 5 - Tax Slabs (exact slab lookup)'),
    ('Q12. What is the Section 80C deduction limit per year?',
     'Answer: Rs.1.5 lakh per financial year.',
     'Tests: Section 5 - Key Deductions'),
    ('Q13. What is the LTCG tax rate on equity, and what holding period qualifies?',
     'Answer: 10% on gains above Rs.1 lakh, for holdings of more than 1 year.',
     'Tests: Section 5 - LTCG'),
    ('Q14. What is the STCG tax rate on equity?',
     'Answer: 15% flat rate for equity held less than 1 year.',
     'Tests: Section 5 - STCG'),
    ('Q15. How much life insurance coverage is recommended relative to income?',
     'Answer: 10 to 15 times the annual income as a pure term plan.',
     'Tests: Section 6 - Risk Management'),
    ('Q16. What is the RBI repo rate as of 2024?',
     'Answer: 6.5%.',
     'Tests: Section 8 - Glossary'),
    ('Q17. What is the RBI CPI inflation target?',
     'Answer: 4% with a tolerance band of plus or minus 2%.',
     'Tests: Section 8 - Glossary'),
    ('Q18. What is the 4% withdrawal rule used for?',
     'Answer: Estimating retirement corpus needed. Target = 25 times annual expenses.',
     'Tests: Section 7 - Retirement Planning'),
    ('Q19. What is the minimum recommended health insurance coverage?',
     'Answer: Minimum Rs.5 lakh individual coverage.',
     'Tests: Section 6 - Insurance'),
    ('Q20. What does CAGR stand for and what is it used for?',
     'Answer: Compound Annual Growth Rate. Used to measure the annualised rate of return on an investment over time.',
     'Tests: Section 8 - Glossary'),
]

story2 = []
story2.append(Spacer(1, 0.8*cm))
story2.append(Paragraph('Finance Chatbot Credibility Test', TTL2))
story2.append(Paragraph('20 Questions to Verify AI Accuracy Against finance_guide_2024.pdf', SUB2))
story2.append(Paragraph('Upload finance_guide_2024.pdf to DocuVault, then ask the chatbot each question below.', CONF))
story2.append(Paragraph('Compare chatbot answers to the expected answers provided here.', CONF))
story2.append(HRFlowable(width='100%', thickness=2, color=colors.HexColor('#b71c1c'), spaceAfter=12, spaceBefore=8))

for q, a, info in qs:
    story2.append(Paragraph(q, QH))
    story2.append(Paragraph(a, ANS))
    story2.append(Paragraph(info, INF))

story2.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#9e9e9e'), spaceBefore=12))
story2.append(Paragraph('DocuVault Credibility Test Sheet | finance_guide_2024.pdf | March 2024', CONF))

doc2 = SimpleDocTemplate('finance_questions.pdf', pagesize=A4,
    leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
doc2.build(story2)
print('finance_questions.pdf created OK')
