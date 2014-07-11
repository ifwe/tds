import logging

__all__ = ['debug']

log = logging.getLogger('tds.utils.debug')


def debug(func):
    """Decorator method to handle debug-level logging of code flow
    (method entry and exit notifications)
    """

    do_depth = 1

    def wrapper(*a, **k):
        logger = k.get('logger', log)

        name = func.func_name
        filename = func.func_code.co_filename
        line_number = func.func_code.co_firstlineno
        typ = 'function'

        spacer = do_depth * getattr(debug, 'depth', 0) * ' '

        logger.log(
            5,
            '%(spacer)sEntering %(typ)s %(name)s '
            '(%(filename)s:%(line_number)s). args=%(a)r, '
            'kwargs=%(k)r', locals()
        )

        try:
            setattr(debug, 'depth', getattr(debug, 'depth', 0) + 1)
            return_val = func(*a, **k)
        except BaseException, e:
            logger.log(
                5,
                '%(spacer)sLeaving %(typ)s %(name)s '
                '(%(filename)s:%(line_number)s). '
                'exception=%(e)r', locals()
            )
            raise
        else:
            logger.log(
                5,
                '%(spacer)sLeaving %(typ)s %(name)s '
                '(%(filename)s:%(line_number)s). '
                'returning=%(return_val)r', locals()
            )
        finally:
            setattr(debug, 'depth', getattr(debug, 'depth', 1) - 1)

        return return_val

    return wrapper
