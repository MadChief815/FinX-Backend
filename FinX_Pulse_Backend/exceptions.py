from rest_framework.views import exception_handler
from rest_framework.response import Response

def custom_exception_handler(exc, context):
    from finance.services import InsufficientBalanceError

    if isinstance(exc, InsufficientBalanceError):
        return Response(
            {
                'error': True,
                'status_code': 422,
                'message': str(exc),
            },
            status=422,
        )

    response = exception_handler(exc, context)
    if response is not None:
        response.data = {
            'error': True,
            'status_code': response.status_code,
            'message': response.data,
        }
    return response