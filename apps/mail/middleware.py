import traceback

class VerboseErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        print(f"[DJANGO EXCEPTION] {request.method} {request.path}", flush=True)
        print(f"[DJANGO EXCEPTION] {type(exception).__name__}: {str(exception)}", flush=True)
        print(traceback.format_exc(), flush=True)
        return None
