# De-obfuscated replacement for the original lover.py (5.00.028).
#
# The original checkupdates() downloaded the Stream Army repo index on every
# scraper call, compared it with the installed version, and quit the add-on with
# "None Supported Version Of XXX-O-DUS" if they differed. It is now a no-op so a
# patched or different version keeps working. The scrapers still call it, so the
# function itself is kept.


def checkupdates():
    return
