"""
Generate two finance-related PDF files using reportlab.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import Table, TableStyle


# ---------------------------------------------------------------------------
# Helper: page number canvas
# ---------------------------------------------------------------------------

def add_page_number(canvas, doc):
    """Draw page number at bottom center of every page."""
    canvas.saveState()
    canvas.setFont("Helvetica", 9)
    page_num = canvas.getPageNumber()
    text = f"Page {page_num}"
    canvas.drawCentredString(A4[0] / 2, 1.5 * cm, text)
    canvas.restoreState()


# ---------------------------------------------------------------------------
# FILE 1 — Personal & Corporate Finance Guide 2024
# ---------------------------------------------------------------------------

def build_finance_guide(path: str):
    doc = SimpleDocTemplate(
        path,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        fontName="Helvetica-Bold",
        fontSize=22,
        textColor=colors.HexColor("#1a3a5c"),
        spaceAfter=6,
        alignment=TA_CENTER,
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        fontName="Helvetica",
        fontSize=13,
        textColor=colors.HexColor("#4a6fa5"),
        spaceAfter=20,
        alignment=TA_CENTER,
    )
    section_style = ParagraphStyle(
        "SectionHead",
        fontName="Helvetica-Bold",
        fontSize=14,
        textColor=colors.HexColor("#1a3a5c"),
        spaceBefore=16,
        spaceAfter=6,
        borderPad=4,
    )
    sub_style = ParagraphStyle(
        "SubHead",
        fontName="Helvetica-Bold",
        fontSize=11,
        textColor=colors.HexColor("#2c5f8a"),
        spaceBefore=8,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "Body",
        fontName="Helvetica",
        fontSize=10,
        leading=15,
        spaceBefore=2,
        spaceAfter=2,
        alignment=TA_JUSTIFY,
    )
    bullet_style = ParagraphStyle(
        "Bullet",
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        leftIndent=18,
        spaceBefore=2,
        spaceAfter=2,
    )
    note_style = ParagraphStyle(
        "Note",
        fontName="Helvetica",
        fontSize=9,
        textColor=colors.HexColor("#555555"),
        leading=13,
        leftIndent=18,
        spaceBefore=2,
        spaceAfter=2,
        alignment=TA_JUSTIFY,
    )

    story = []

    # Title block
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("Personal &amp; Corporate Finance Guide 2024", title_style))
    story.append(Paragraph("A Comprehensive Reference for Individual and Business Finance", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1a3a5c")))
    story.append(Spacer(1, 0.4 * cm))

    # ---- SECTION 1 ----
    story.append(Paragraph("1. Introduction to Finance", section_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#aaaaaa")))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "Finance is the discipline concerned with the management of money, investments, and other financial instruments. "
        "It encompasses the study of how individuals, businesses, and governments allocate resources over time.",
        body_style))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("<b>Definition and Scope of Finance:</b>", sub_style))
    story.append(Paragraph(
        "Finance studies the allocation of assets and liabilities over space and time, often under conditions of risk and uncertainty.",
        body_style))
    story.append(Paragraph("<b>Importance of Financial Literacy:</b>", sub_style))
    story.append(Paragraph(
        "Financial literacy equips individuals to make informed decisions about saving, investing, borrowing, and planning for the future. "
        "A financially literate population drives economic stability and personal well-being.",
        body_style))
    story.append(Paragraph("<b>Types of Finance:</b>", sub_style))
    for item in [
        "<b>Personal Finance:</b> Managing individual or household financial decisions — budgeting, saving, investing, and insurance.",
        "<b>Corporate Finance:</b> Financial activities of businesses — capital structure, funding, and maximising shareholder value.",
        "<b>Public Finance:</b> Government revenue, expenditure, and debt management at local, state, and national levels.",
    ]:
        story.append(Paragraph(f"&bull; {item}", bullet_style))

    # ---- SECTION 2 ----
    story.append(Paragraph("2. Personal Finance Fundamentals", section_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#aaaaaa")))
    story.append(Spacer(1, 0.2 * cm))

    story.append(Paragraph("<b>Budgeting: The 50/30/20 Rule</b>", sub_style))
    for item in [
        "<b>50%</b> of after-tax income for <b>Needs</b> (rent, utilities, groceries, transport)",
        "<b>30%</b> for <b>Wants</b> (dining, entertainment, travel, hobbies)",
        "<b>20%</b> for <b>Savings and Debt Repayment</b> (emergency fund, investments, loan EMIs)",
    ]:
        story.append(Paragraph(f"&bull; {item}", bullet_style))

    story.append(Paragraph("<b>Emergency Fund</b>", sub_style))
    story.append(Paragraph(
        "Financial planners recommend maintaining an emergency fund equivalent to <b>3 to 6 months</b> of total living expenses. "
        "Keep this in a liquid account such as a savings account or liquid mutual fund.",
        body_style))

    story.append(Paragraph("<b>Net Worth Formula</b>", sub_style))
    story.append(Paragraph("<b>Net Worth = Assets &minus; Liabilities</b>", body_style))
    story.append(Paragraph(
        "<i>Example:</i> Assets = Rs.45L (Property Rs.30L + Investments Rs.15L), "
        "Liabilities = Rs.18L (Home Loan Rs.15L + Car Loan Rs.3L). "
        "Net Worth = Rs.45L &minus; Rs.18L = <b>Rs.27 lakh</b>.",
        note_style))

    # ---- SECTION 3 ----
    story.append(Paragraph("3. Investment Basics", section_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#aaaaaa")))
    story.append(Spacer(1, 0.2 * cm))

    investments = [
        ("<b>Equity (Stocks)</b>",
         "High risk, high return. Average market return approximately 12% annually (Sensex). "
         "Suitable for long-term goals (5+ years)."),
        ("<b>Debt (Bonds / Fixed Deposits)</b>",
         "Low risk, fixed return. FD rates typically 6.5 to 7.5% per annum. "
         "Ideal for capital preservation and short-to-medium term goals."),
        ("<b>Mutual Funds</b>",
         "Professionally managed, diversified portfolio. "
         "Systematic Investment Plan (SIP) minimum: Rs.500 per month."),
        ("<b>Real Estate</b>",
         "Illiquid asset. Rental yield typically 2 to 4% in India. "
         "Suitable for long-term wealth building; consider liquidity constraints."),
        ("<b>Gold</b>",
         "Hedge against inflation and currency risk. 10-year CAGR approximately 9.8%. "
         "Can be held via Sovereign Gold Bonds (SGB) for additional interest."),
        ("<b>PPF (Public Provident Fund)</b>",
         "Government-backed, 7.1% per annum tax-free return. Lock-in period of 15 years. "
         "Eligible for Section 80C deduction."),
        ("<b>NPS (National Pension System)</b>",
         "Retirement corpus builder. Tax benefit up to Rs.2L under Section 80C + 80CCD(1B). "
         "Regulated by PFRDA; partially annuitised at retirement."),
    ]
    for head, detail in investments:
        story.append(Paragraph(head, sub_style))
        story.append(Paragraph(detail, body_style))

    # ---- SECTION 4 ----
    story.append(Paragraph("4. Corporate Finance", section_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#aaaaaa")))
    story.append(Spacer(1, 0.2 * cm))

    corp = [
        ("<b>Capital Structure</b>",
         "The mix of debt and equity financing. Healthy Debt-to-Equity ratio range: 1:1 to 2:1. "
         "Excessive debt increases financial risk."),
        ("<b>Working Capital</b>",
         "Working Capital = Current Assets &minus; Current Liabilities. "
         "Positive working capital indicates short-term financial health."),
        ("<b>EBITDA</b>",
         "Earnings Before Interest, Tax, Depreciation, and Amortisation. "
         "A proxy for operating cash flow used widely in business valuation."),
        ("<b>ROI (Return on Investment)</b>",
         "ROI = (Net Profit / Cost of Investment) &times; 100. "
         "Measures the efficiency and profitability of an investment."),
        ("<b>P/E Ratio (Price-to-Earnings)</b>",
         "P/E = Price per Share / Earnings per Share. "
         "Indian market average: 20 to 25x. Higher P/E may indicate overvaluation."),
        ("<b>Liquidity Ratios</b>",
         "Current Ratio (Current Assets / Current Liabilities) &gt;2 is considered healthy. "
         "Quick Ratio &gt;1 is preferred, indicating ability to meet short-term obligations without inventory."),
    ]
    for head, detail in corp:
        story.append(Paragraph(head, sub_style))
        story.append(Paragraph(detail, body_style))

    # ---- SECTION 5 ----
    story.append(Paragraph("5. Taxation in India (FY 2024-25)", section_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#aaaaaa")))
    story.append(Spacer(1, 0.2 * cm))

    story.append(Paragraph("<b>New Tax Regime — Income Tax Slabs:</b>", sub_style))
    tax_data = [
        ["Income Slab", "Tax Rate"],
        ["Up to Rs.3 lakh", "Nil"],
        ["Rs.3 lakh to Rs.7 lakh", "5%"],
        ["Rs.7 lakh to Rs.10 lakh", "10%"],
        ["Rs.10 lakh to Rs.12 lakh", "15%"],
        ["Rs.12 lakh to Rs.15 lakh", "20%"],
        ["Above Rs.15 lakh", "30%"],
    ]
    tax_table = Table(tax_data, colWidths=[9 * cm, 5 * cm])
    tax_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f0f4f8"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#aaaaaa")),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(tax_table)
    story.append(Spacer(1, 0.3 * cm))

    tax_points = [
        "<b>Section 80C</b> deduction limit: Rs.1.5 lakh (covers ELSS, PPF, life insurance premium, home loan principal, etc.)",
        "<b>HRA Exemption:</b> Minimum of (actual HRA received, 50% of salary for metro / 40% for non-metro cities, "
        "rent paid minus 10% of salary).",
        "<b>GST Rates:</b> 0%, 5%, 12%, 18%, and 28% depending on goods/services category.",
        "<b>LTCG on Equity:</b> 10% on gains above Rs.1 lakh for holdings longer than 1 year.",
        "<b>STCG on Equity:</b> 15% for equity held less than 1 year.",
    ]
    for pt in tax_points:
        story.append(Paragraph(f"&bull; {pt}", bullet_style))

    # ---- SECTION 6 ----
    story.append(Paragraph("6. Risk Management &amp; Insurance", section_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#aaaaaa")))
    story.append(Spacer(1, 0.2 * cm))

    risk_items = [
        ("<b>Life Insurance (Term Plan)</b>",
         "Recommended coverage: 10 to 15 times annual income. "
         "Pure term plans offer high coverage at low premiums. Avoid mixing insurance with investment."),
        ("<b>Health Insurance</b>",
         "Minimum Rs.5 lakh individual coverage. Family floater plan recommended for households. "
         "Covers hospitalisation, daycare procedures, and pre/post-hospitalisation expenses."),
        ("<b>Premium Ratio</b>",
         "Total insurance premiums should not exceed 5% of annual income to maintain healthy financial balance."),
        ("<b>Risk Types</b>",
         "Market risk (price fluctuation), Credit risk (counterparty default), "
         "Liquidity risk (inability to sell quickly), Operational risk (internal process failures)."),
    ]
    for head, detail in risk_items:
        story.append(Paragraph(head, sub_style))
        story.append(Paragraph(detail, body_style))

    # ---- SECTION 7 ----
    story.append(Paragraph("7. Financial Ratios Quick Reference", section_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#aaaaaa")))
    story.append(Spacer(1, 0.2 * cm))

    ratio_data = [
        ["Ratio", "Formula"],
        ["Debt-to-Equity", "Total Debt / Shareholders Equity"],
        ["Return on Equity (ROE)", "Net Income / Shareholders Equity x 100"],
        ["Gross Profit Margin", "(Revenue - COGS) / Revenue x 100"],
        ["Current Ratio", "Current Assets / Current Liabilities"],
        ["Interest Coverage", "EBIT / Interest Expense"],
    ]
    ratio_table = Table(ratio_data, colWidths=[6 * cm, 10 * cm])
    ratio_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c5f8a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f0f4f8"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#aaaaaa")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(ratio_table)

    # ---- SECTION 8 ----
    story.append(Paragraph("8. Key Financial Terms Glossary", section_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#aaaaaa")))
    story.append(Spacer(1, 0.2 * cm))

    glossary = [
        ("Inflation", "India's CPI target 4% (+/-2%) set by the Reserve Bank of India (RBI)."),
        ("Repo Rate", "As of 2024 -- 6.5%. The benchmark rate at which RBI lends to commercial banks."),
        ("SIP", "Systematic Investment Plan -- fixed monthly investment into a mutual fund scheme."),
        ("NAV", "Net Asset Value -- market value of mutual fund assets per unit, calculated daily."),
        ("CAGR", "Compound Annual Growth Rate -- measures the rate of return on investment over multiple years."),
        ("FII", "Foreign Institutional Investor -- overseas entities investing in Indian financial markets."),
        ("NFO", "New Fund Offer -- launch of a new mutual fund scheme, similar to an IPO for stocks."),
    ]
    for term, definition in glossary:
        story.append(Paragraph(f"<b>{term}:</b>  {definition}", bullet_style))

    # ---- SECTION 9 ----
    story.append(Paragraph("9. Financial Planning Milestones", section_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#aaaaaa")))
    story.append(Spacer(1, 0.2 * cm))

    milestones = [
        ("<b>Age 20s</b>",
         "Build emergency fund (3-6 months expenses). Start SIP of Rs.2,000 or more per month. "
         "Buy a pure term life insurance policy. Avoid high-interest debt."),
        ("<b>Age 30s</b>",
         "Increase SIP contributions as income grows. Consider buying a home if financially feasible. "
         "Maximise Section 80C benefits. Review and increase health insurance coverage."),
        ("<b>Age 40s</b>",
         "Aggressively reduce outstanding debt. Boost retirement corpus with higher NPS / mutual fund contributions. "
         "Diversify investments across asset classes."),
        ("<b>Age 50s</b>",
         "Gradually shift to lower-risk assets (debt funds, FDs, SGBs). "
         "Plan estate and succession. Maximise NPS contributions for tax benefits."),
        ("<b>Retirement Target</b>",
         "Accumulate 25 times your annual expenses as retirement corpus (based on the 4% withdrawal rule). "
         "Example: Annual expenses Rs.6L -- target corpus Rs.1.5 crore."),
    ]
    for head, detail in milestones:
        story.append(Paragraph(head, sub_style))
        story.append(Paragraph(detail, body_style))

    # ---- SECTION 10 ----
    story.append(Paragraph("10. Common Financial Mistakes to Avoid", section_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#aaaaaa")))
    story.append(Spacer(1, 0.2 * cm))

    mistakes = [
        "Not building an emergency fund before investing.",
        "Delaying or ignoring life and health insurance.",
        "Chasing past returns in mutual funds without assessing risk profile.",
        "Taking excessive home loan (EMI exceeding 40% of monthly income is high-risk).",
        "Not accounting for inflation when planning retirement corpus.",
        "Withdrawing from long-term investments (ELSS, PPF, NPS) prematurely.",
        "Neglecting to review and rebalance the investment portfolio annually.",
        "Using credit cards for lifestyle spending beyond repayment capacity.",
    ]
    for m in mistakes:
        story.append(Paragraph(f"&bull; {m}", bullet_style))

    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1a3a5c")))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "<i>This guide is for educational purposes only. Consult a SEBI-registered financial advisor "
        "before making investment or tax decisions.</i>",
        ParagraphStyle("Disclaimer", fontName="Helvetica", fontSize=9,
                       textColor=colors.HexColor("#777777"), alignment=TA_CENTER)))

    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    print(f"FILE 1 saved: {path}")


# ---------------------------------------------------------------------------
# FILE 2 — Finance Knowledge Test / Credibility Questions
# ---------------------------------------------------------------------------

def build_finance_questions(path: str):
    doc = SimpleDocTemplate(
        path,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "QTitle",
        fontName="Helvetica-Bold",
        fontSize=20,
        textColor=colors.HexColor("#1a3a5c"),
        spaceAfter=6,
        alignment=TA_CENTER,
    )
    subtitle_style = ParagraphStyle(
        "QSubtitle",
        fontName="Helvetica",
        fontSize=12,
        textColor=colors.HexColor("#4a6fa5"),
        spaceAfter=8,
        alignment=TA_CENTER,
    )
    instruction_style = ParagraphStyle(
        "Instruction",
        fontName="Helvetica",
        fontSize=10,
        textColor=colors.HexColor("#333333"),
        spaceAfter=16,
        alignment=TA_CENTER,
        leading=14,
    )
    q_style = ParagraphStyle(
        "Question",
        fontName="Helvetica-Bold",
        fontSize=11,
        textColor=colors.HexColor("#1a3a5c"),
        spaceBefore=12,
        spaceAfter=4,
    )
    a_style = ParagraphStyle(
        "Answer",
        fontName="Helvetica",
        fontSize=10,
        textColor=colors.HexColor("#1e5631"),
        leftIndent=20,
        spaceAfter=4,
        leading=14,
    )

    story = []

    # Title block
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("Finance Document Credibility Test Sheet", title_style))
    story.append(Paragraph("Finance Knowledge Test -- Credibility Questions", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1a3a5c")))
    story.append(Spacer(1, 0.25 * cm))
    story.append(Paragraph(
        "Ask these questions to the AI assistant after uploading finance_guide_2024.pdf to verify "
        "that the document has been correctly indexed and the AI can accurately retrieve information from it.",
        instruction_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#aaaaaa")))
    story.append(Spacer(1, 0.2 * cm))

    qa_pairs = [
        ("Q1. What is the 50/30/20 budgeting rule?",
         "A: 50% of income for needs, 30% for wants, and 20% for savings or debt repayment."),

        ("Q2. How many months of expenses should an emergency fund cover?",
         "A: 3 to 6 months of living expenses."),

        ("Q3. What is the formula for calculating Net Worth?",
         "A: Net Worth = Assets minus Liabilities."),

        ("Q4. In the example given, what is the net worth if assets are Rs.45L and liabilities are Rs.18L?",
         "A: Rs.27 lakh."),

        ("Q5. What is the average annual market return mentioned for the Sensex?",
         "A: Approximately 12% annually."),

        ("Q6. What is the typical FD interest rate range mentioned in the document?",
         "A: 6.5% to 7.5% per annum."),

        ("Q7. What is the minimum SIP amount for mutual funds?",
         "A: Rs.500 per month."),

        ("Q8. What is the interest rate for PPF and how long is the lock-in period?",
         "A: 7.1% per annum, tax-free, with a 15-year lock-in period."),

        ("Q9. What is a healthy Debt-to-Equity ratio range for a company?",
         "A: 1:1 to 2:1."),

        ("Q10. What is the Working Capital formula?",
         "A: Working Capital = Current Assets minus Current Liabilities."),

        ("Q11. Under the new tax regime, what is the tax rate for income between Rs.7L and Rs.10L?",
         "A: 10%."),

        ("Q12. What is the Section 80C deduction limit?",
         "A: Rs.1.5 lakh."),

        ("Q13. What is the LTCG tax rate on equity and what holding period qualifies?",
         "A: 10% on gains above Rs.1 lakh, for holdings longer than 1 year."),

        ("Q14. How much life insurance coverage is recommended relative to annual income?",
         "A: 10 to 15 times the annual income as a term plan."),

        ("Q15. What is India's RBI repo rate as of 2024?",
         "A: 6.5%."),

        ("Q16. What is the RBI's CPI inflation target?",
         "A: 4% with a tolerance band of +/-2%."),

        ("Q17. What is the 4% withdrawal rule used for?",
         "A: It is used to estimate the retirement corpus needed -- 25 times your annual expenses."),

        ("Q18. What is the STCG tax rate on equity investments?",
         "A: 15% for equity held less than 1 year."),

        ("Q19. What is the minimum health insurance coverage recommended?",
         "A: Minimum Rs.5 lakh coverage."),

        ("Q20. What does CAGR stand for and what is it used for?",
         "A: Compound Annual Growth Rate -- used to measure the rate of return on investment over time."),
    ]

    for question, answer in qa_pairs:
        story.append(Paragraph(question, q_style))
        story.append(Paragraph(answer, a_style))

    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1a3a5c")))
    story.append(Spacer(1, 0.2 * cm))
    footer_style = ParagraphStyle(
        "Footer",
        fontName="Helvetica",
        fontSize=9,
        textColor=colors.HexColor("#777777"),
        alignment=TA_CENTER,
    )
    story.append(Paragraph(
        "This test sheet corresponds to finance_guide_2024.pdf -- Use it to validate AI document retrieval accuracy.",
        footer_style))

    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    print(f"FILE 2 saved: {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    guide_path = (
        r"D:\AI_Model_Renata\Document-management\Group\V2\DocuVault"
        r"\media\uploads\finance_guide_2024.pdf"
    )
    questions_path = (
        r"D:\AI_Model_Renata\Document-management\Group\V2\DocuVault"
        r"\media\uploads\finance_questions.pdf"
    )

    build_finance_guide(guide_path)
    build_finance_questions(questions_path)
    print("Both PDF files created successfully.")
