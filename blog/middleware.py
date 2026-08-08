import time


class SimplePerformanceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        response = self.get_response(request)

        duration = time.time() - start_time


        response['X-Page-Generation-Time'] = f"{duration:.4f} seconds"

        print(f"⏰ [Middleware] Страница {request.path} загрузилась за {duration:.4f} сек.")

        return response
