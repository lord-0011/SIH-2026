"""Generate synthetic Flash Report PDF fixture for non-skipping CI testing.

Constructs tests/fixtures/sample_flash_report.pdf containing:
1. Table 1 (Ministry-wise summary with grand totals and MoRTH count)
2. Table 6 (All Ongoing Projects with paired cells, '-' tokens, garbage cost 0.1)
3. Table 3 (Completed projects during month)
4. Table 4 (Newly added projects during month)
"""

import os
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Table, TableStyle


def build_fixture_pdf(output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=landscape(letter),
        leftMargin=20,
        rightMargin=20,
        topMargin=20,
        bottomMargin=20,
    )
    styles = getSampleStyleSheet()
    story = []

    # ----------------------------------------------------
    # Page 1: Table 1: Ministry-wise Ongoing Projects
    # ----------------------------------------------------
    story.append(Paragraph("Table 1: Ministry-wise Ongoing Projects", styles["Heading1"]))
    t1_data = [
        [
            "S.No",
            "Ministry / Department",
            "Sector",
            "No. of Ongoing Projects",
            "Original Cost (Rs. Cr.)",
            "Cumulative Expenditure (Rs. Cr.)",
        ],
        [
            "16",
            "Ministry of Road Transport & Highways",
            "Roads & Highways",
            "1137",
            "1054522.87",
            "369902.00",
        ],
        [
            "1",
            "Ministry of Civil Aviation",
            "Civil Aviation",
            "50",
            "50000.00",
            "25000.00",
        ],
        ["Total", "1981", "3712662.01", "2036107.69", "", ""],
    ]
    t1 = Table(t1_data)
    t1.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ]
        )
    )
    story.append(t1)
    story.append(PageBreak())

    # ----------------------------------------------------
    # Page 2: Table 6: All Ongoing Projects
    # ----------------------------------------------------
    story.append(Paragraph("Table 6: All Ongoing Projects", styles["Heading1"]))
    t6_data = [
        [
            "Sl.No",
            "Project Name\n(Agency)\n(Project Code)\n(Legacy OCMS Code) (PMGID)",
            "State",
            "Date of Approval\n(Start Date)\nMM/YYYY",
            "Orignal/Target DoC\n(Revised DoC)\nMM/YYYY",
            "Orignal Cost\n(Revised Cost)\nin Rs. Crore",
            "Cumulative\nExpenditure\nin Rs. Crore",
            "Physical\nProgress\n(%)",
        ],
        ["", "Ministry of Civil Aviation", "", "", "", "", "", ""],
        ["", "Civil Aviation", "", "", "", "", "", ""],
        # Project 1: Standard multi-line name, paired cost, paired date, regular codes
        [
            "1",
            "Construction of New Domestic Terminal Building\nand miscellaneous airside works\n(AAI)\n(612786)\n(N04000106) (PMG12345)",
            "Andhra Pradesh",
            "03/2023\n(01/2024)",
            "01/2026\n(07/2026)",
            "265.91\n(280.50)",
            "129.07",
            "65.0",
        ],
        # Project 2: '-' for Legacy OCMS Code and PMGID, and garbage low revised cost (0.1)
        [
            "2",
            "Four Laning of Highway Section From Km 100 to Km 150\n(NHAI)\n(618886)\n(-) (-)",
            "Maharashtra",
            "05/2021\n(10/2021)",
            "12/2024\n(03/2025)",
            "238.66\n(0.1)",
            "185.20",
            "82.5",
        ],
        # Project 3: Single unrevised cost (fallback), '-' start date, '-' rev DoC
        [
            "3",
            "Gauge Conversion Project Line B\n(RVNL)\n(619999)\n(LEG999) (-)",
            "Assam",
            "08/2022\n(-)",
            "06/2025\n(-)",
            "500.00",
            "50.00",
            "10.0",
        ],
    ]
    t6 = Table(t6_data)
    t6.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ]
        )
    )
    story.append(t6)
    story.append(PageBreak())

    # ----------------------------------------------------
    # Page 3: Table 3: Completed Projects During Month
    # ----------------------------------------------------
    story.append(Paragraph("Table 3: Completed Projects During Month", styles["Heading1"]))
    t3_data = [
        [
            "Sl.No",
            "Project Name\n(Agency)\n(Project Code)",
            "State",
            "Date of Approval\n(Start Date)\nMM/YYYY",
            "Actual Date of Completion\n(Original DoC)\nMM/YYYY",
            "Orignal Cost\n(Revised Cost)\nin Rs. Crore",
            "Cumulative\nExpenditure\nin Rs. Crore",
        ],
        ["", "Ministry of Civil Aviation", "", "", "", "", ""],
        ["", "Civil Aviation", "", "", "", "", ""],
        [
            "1",
            "Runway Resurfacing and Modernization\n(AAI)\n(701001)",
            "Karnataka",
            "01/2021\n(05/2021)",
            "04/2026\n(12/2025)",
            "150.00\n(165.00)",
            "165.00",
        ],
    ]
    t3 = Table(t3_data)
    t3.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ]
        )
    )
    story.append(t3)
    story.append(PageBreak())

    # ----------------------------------------------------
    # Page 4: Table 4: Newly Added Projects
    # ----------------------------------------------------
    story.append(Paragraph("Table 4: Newly Added Projects", styles["Heading1"]))
    t4_data = [
        [
            "Sl.No",
            "Project Name\n(Agency)\n(Project Code)",
            "State",
            "Date of Approval\n(Start Date)\nMM/YYYY",
            "Orignal/Target DoC\n(Revised DoC)\nMM/YYYY",
            "Orignal Cost\n(Revised Cost)\nin Rs. Crore",
        ],
        ["", "Ministry of Civil Aviation", "", "", "", ""],
        ["", "Civil Aviation", "", "", "", ""],
        [
            "1",
            "New Heliport Development Project\n(AAI)\n(801001)",
            "Sikkim",
            "02/2026\n(04/2026)",
            "10/2027\n(10/2027)",
            "85.00\n(85.00)",
        ],
    ]
    t4 = Table(t4_data)
    t4.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ]
        )
    )
    story.append(t4)

    doc.build(story)
    print(
        f"Generated synthetic fixture at {output_path} (size: {os.path.getsize(output_path)} bytes)"
    )


if __name__ == "__main__":
    build_fixture_pdf(Path("tests/fixtures/sample_flash_report.pdf"))
