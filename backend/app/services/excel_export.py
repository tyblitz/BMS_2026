import io
from typing import Iterable
from openpyxl import Workbook
from app.models.bms_record import BMSRecord
from app.services.calculations import calculate_balances

EXPORT_HEADERS = [
    "PPAControl",
    "AppropriationType",
    "AllotmentPeriod",
    "AllotmentClass",
    "DateBMS",
    "AccountCode",
    "ObligationsIncurred",
    "Disbursement",
    "Appropriations",
    "Allotment",
    "TransferTo",
    "TransferFrom",
    "Particulars",
    "UACSPAPCODE",
    "DVAmount",
    "Region",
    "Division",
    "OperatingUnit",
    "OrgCodeUACS",
    "ApproAdjust",
    "Realignment",
    "FundSource",
    "Locality",
    "LegalBasis",
    "RC",
    "Reg",
    "CCETCode",
    "Ledger",
    "TOTAL ADJUSTED APPRO",
    "TOTAL ADJUSTED ALLOTMENT ", # Trailing space required by MS Access BMS
    "UNOBLIGATED",
    "UNPAID",
    "UNRELEASED"
]


class ExcelExportService:
    @staticmethod
    def export_to_stream(records: Iterable[BMSRecord], output_stream: io.BytesIO):
        """
        Generates an exact 33-column replica of 'Combine Sheet' in write-only streaming mode.
        Dynamically calculates columns 29-33 with zero memory bloat.
        """
        wb = Workbook(write_only=True)
        ws = wb.create_sheet(title="Combine Sheet")

        # Append headers
        ws.append(EXPORT_HEADERS)

        for rec in records:
            # Dynamically compute the 5 balance metrics
            balances = calculate_balances(
                appropriations=rec.appropriations,
                appro_adjust=rec.appro_adjust,
                allotment=rec.allotment,
                realignment=rec.realignment,
                transfer_from=rec.transfer_from,
                transfer_to=rec.transfer_to,
                obligations_incurred=rec.obligations_incurred,
                disbursement=rec.disbursement
            )

            row = [
                rec.ppa_control or "",
                rec.appropriation_type or "",
                rec.allotment_period or "",
                rec.allotment_class or "",
                rec.date_bms or "",
                rec.account_code or "",
                float(rec.obligations_incurred or 0),
                float(rec.disbursement or 0),
                float(rec.appropriations or 0),
                float(rec.allotment or 0),
                float(rec.transfer_to or 0),
                float(rec.transfer_from or 0),
                rec.particulars or "",
                rec.uacs_pap_code or "",
                float(rec.dv_amount or 0),
                rec.region or "",
                rec.division or "",
                rec.operating_unit or "",
                rec.org_code_uacs or "",
                float(rec.appro_adjust or 0),
                float(rec.realignment or 0),
                rec.fund_source or "",
                rec.locality or "",
                rec.legal_basis or "",
                rec.rc or "",
                rec.reg or "NA",
                rec.ccet_code or "NA",
                rec.ledger or "NA",
                # Calculated columns
                float(balances["total_adjusted_appro"]),
                float(balances["total_adjusted_allotment"]),
                float(balances["unobligated"]),
                float(balances["unpaid"]),
                float(balances["unreleased"])
            ]
            ws.append(row)

        wb.save(output_stream)
        output_stream.seek(0)
