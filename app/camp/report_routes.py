"""
Camp report routes.

Kept in its own module and blueprint: `routes.py` is already very large, and a separate
blueprint avoids importing `camp_bp` from it (and the circular import that would risk).
"""

from apiflask import APIBlueprint
from flask import current_app, g

from .._shared.auth import token_required
from .report_schemas import CampReportResponseWrapperSchema
from .report_service import ReportService

report_bp = APIBlueprint('report', __name__, url_prefix='/camps')

report_service = ReportService()

# Volunteers holding this page permission may also view the report.
REPORT_PERMISSION = 'financials'


def _may_view_report(user) -> bool:
    """Camp managers always; volunteers need the financials page permission."""
    if user is None:
        return False
    if user.role == 'camp_manager':
        return True
    return REPORT_PERMISSION in (user.permissions or [])


@report_bp.get('/<camp_id>/report')
@report_bp.output(CampReportResponseWrapperSchema)
@report_bp.doc(
    summary='Get full camp report',
    description=(
        'Comprehensive end-of-camp analytics: registration and check-in, demographics, '
        'categories, church spread, payments, accommodation, pledges, financials, '
        'inventory and food.'
    )
)
@token_required
def get_camp_report(camp_id):
    """Get the full analytics report for a camp"""
    try:
        if not _may_view_report(getattr(g, 'current_user', None)):
            return {
                'data': {
                    'code': 'PERMISSION_DENIED',
                    'message': 'You do not have permission to view this report',
                    'details': None
                }
            }, 403

        report = report_service.get_camp_report(camp_id)

        if not report:
            return {
                'data': {
                    'code': 'CAMP_NOT_FOUND',
                    'message': 'Camp not found',
                    'details': None
                }
            }, 404

        return {
            'data': report
        }, 200

    except Exception as e:
        current_app.logger.error(f"Get camp report error: {str(e)}")
        return {
            'data': {
                'code': 'GET_REPORT_ERROR',
                'message': 'Failed to generate camp report',
                'details': {'error': str(e)}
            }
        }, 500
