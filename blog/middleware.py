import time


class SimplePerformanceMiddleware:
    def __init__(self, get_response):
        # Этот метод срабатывает один раз при запуске сервера Django
        self.get_response = get_response

    def __call__(self, request):
        # 1. ЗАСЕКАЕМ ВРЕМЯ (Срабатывает ДО того, как запрос попал во views.py)
        start_time = time.time()

        # Передаем запрос дальше по цепочке Django (в наши представления/views)
        response = self.get_response(request)

        # 2. СЧИТАЕМ РАЗНИЦУ (Срабатывает ПОСЛЕ того, как страница сгенерировалась)
        duration = time.time() - start_time

        # Добавляем кастомный HTTP-заголовок к ответу
        response['X-Page-Generation-Time'] = f"{duration:.4f} seconds"

        # Печатаем строчку в терминал PyCharm для контроля
        print(f"⏰ [Middleware] Страница {request.path} загрузилась за {duration:.4f} сек.")

        return response
