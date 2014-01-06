# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt
import logging

logger = logging.getLogger(__name__)


class TracebackLoggingMiddleware(object):
    """Middleware that logs exceptions. Copied from lizard-ui

    See http://djangosnippets.org/snippets/421/.
    """

    def process_exception(self, request, exception):
        logger.exception("Error 500 in %s", request.path)
