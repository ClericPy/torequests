import logging

dummy_logger = logging.getLogger('torequests.dummy')
main_logger = logging.getLogger('torequests.main')


def init_logger(name='unnamed', handler_path_levels=None,
                level=logging.INFO, formatter=None,
                formatter_str=None, datefmt="%Y-%m-%d %H:%M:%S"):
    '''Args:
    name = 'unnamed' or logger obj.
    handler_path_levels = [['loggerfile.log',13],['','DEBUG'],['','info'],['','notSet']] # [[path,level]]
    level : the least level for the logger.
    formatter = logging.Formatter(
            '%(levelname)-8s  [%(asctime)s]  %(name)s (%(funcName)s: %(lineno)s): %(message)s',
             "%Y-%m-%d %H:%M:%S")
    formatter_str = '%(levelname)-6s  [%(asctime)s]  %(name)s (%(funcName)s: %(lineno)s): %(message)s'

    custom formatter:
        %(asctime)s  %(created)f  %(filename)s  %(funcName)s  %(levelname)s  %(levelno)s  %(lineno)s   %(message)s   %(module)s    %(name)s   %(pathname)s   %(process)s   %(relativeCreated)s   %(thread)s  %(threadName)s  
    '''
    levels = {'NOTSET': logging.NOTSET, 'DEBUG': logging.DEBUG, 'INFO': logging.INFO,
              'WARNING': logging.WARNING, 'ERROR': logging.ERROR, 'CRITICAL': logging.CRITICAL}
    if not formatter:
        if formatter_str:
            formatter_str = formatter_str
        else:
            formatter_str = '%(levelname)-6s  [%(asctime)s]  %(name)s (%(funcName)s: %(lineno)s): %(message)s'
        formatter = logging.Formatter(formatter_str, datefmt=datefmt)
    logger = name if isinstance(
        name, logging.Logger) else logging.getLogger(str(name))
    logger.setLevel(level)
    handler_path_levels = handler_path_levels or [['', 'INFO']]
    # ---------------------------------------
    for each_handler in handler_path_levels:
        path, handler_level = each_handler
        handler = logging.FileHandler(
            path) if path else logging.StreamHandler()
        handler.setLevel(levels.get(handler_level.upper(), 1) if isinstance(
            handler_level, str) else handler_level)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger
