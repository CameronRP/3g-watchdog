# 3g-watchdog

This implements a simple service which if a 3G modem is in use it will
ensure that some internet hosts can be pinged. Generous retries and
timeouts are used.

If ping tests fail, the 3G modem is assumed to be dead and the system
is rebooted.
