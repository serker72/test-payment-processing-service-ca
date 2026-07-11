LOCALE_DEFAULT = "ru_RU"

# SQLAlchemy
SA_FILTER_OPERATOR_AND = "and"
SA_FILTER_OPERATOR_OR = "or"
SA_SORT_ORDER_ASC = "ASC"
SA_SORT_ORDER_DESC = "DESC"

FORMAT_LOG_DEFAULT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)
FORMAT_LOG_APP = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<level>{extra[request_id]: <32}</level> | "
    "<level>{extra[user_ip]: <15}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)
FORMAT_LOG_CONSUMER = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<level>{extra[message_id]: <32}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)
