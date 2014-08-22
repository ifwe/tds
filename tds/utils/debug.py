'''
Debugging tools for TDS development
'''
import logging

__all__ = ['debug']

log = logging.getLogger('tds.utils.debug')


def debug(func):
    """Decorator method to handle debug-level logging of code flow
    (method entry and exit notifications)
    """

    do_depth = 1

    def wrapper(*a, **k):
        '''
        New function which outputs lots of debug info about `func`
        '''
        logger = k.get('logger', None) or log

        # pylint: disable=unused-variable
        name = func.func_name
        filename = func.func_code.co_filename
        line_number = func.func_code.co_firstlineno
        typ = 'function'
        exc = None
        spacer = do_depth * getattr(debug, 'depth', 0) * ' '
        # pylint: enable=unused-variable

        logger.log(
            5,
            '%(spacer)sEntering %(typ)s %(name)s '
            '(%(filename)s:%(line_number)s). args=%(a)r, '
            'kwargs=%(k)r', locals()
        )

        try:
            setattr(debug, 'depth', getattr(debug, 'depth', 0) + 1)
            return_val = func(*a, **k)
        except BaseException as exc:
            logger.log(
                5,
                '%(spacer)sLeaving %(typ)s %(name)s '
                '(%(filename)s:%(line_number)s). '
                'exception=%(exc)r', locals()
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
