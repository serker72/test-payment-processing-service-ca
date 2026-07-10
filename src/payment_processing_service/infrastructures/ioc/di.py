from dishka import Provider

from payment_processing_service.infrastructures.ioc.provides import (
    AsyncRedisProvider,
    BrokerProvider,
    DatabaseProvider,
    HTTPClientProvider,
    MapperProvider,
    RepositoryProvider,
    ServiceProvider,
    SettingsProvider,
    UnitOfWorkProvider,
    UseCaseProvider,
)


def get_providers() -> list[Provider]:
    """Получение списка провайдеров Dishka для инъекции зависимостей"""
    return [
        SettingsProvider(),
        HTTPClientProvider(),
        BrokerProvider(),
        DatabaseProvider(),
        AsyncRedisProvider(),
        RepositoryProvider(),
        UnitOfWorkProvider(),
        ServiceProvider(),
        MapperProvider(),
        UseCaseProvider(),
    ]
