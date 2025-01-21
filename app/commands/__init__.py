from app.crisalid_ikg import CrisalidIKG

ikg = CrisalidIKG()


def with_app_lifecycle(func):
    """
    Decorator to handle the startup and shutdown of the IKG application in command line functions.
    :param func: The decorated function
    :return:
    """

    async def wrapper(*args, **kwargs):
        await ikg.cli_startup()
        try:
            return await func(*args, **kwargs)
        finally:
            await ikg.cli_shutdown()

    return wrapper
