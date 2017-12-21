# 3g-watchdog

This implements a simple check to be used with the watchdog daemon. If
a 3G modem is in use it will ensure that some internet hosts can be
pinged. Generous retries and timeouts are used.

The watchdog daemon will call the check quite often so the check
tracks when it last performed its tests. The ping tests are only run
every 5 mins.
