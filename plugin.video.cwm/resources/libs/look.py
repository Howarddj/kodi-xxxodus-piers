# One text colour everywhere: strip the [COLOR], [B] and [I] tags that Cum With Me and its
# scrapers put on list rows, labels, text boxes, chat lines and dialogs, so all text is drawn in
# the window's single text colour. (Same rule as the XXX-O-DUS build.)
import re

import xbmcgui
import pyxbmct

TEXT_COLOUR = '0xFFFFFFFF'
FOCUS_COLOUR = '0xFFFFFFFF'

_TAGS = re.compile(r'\[/?(?:COLOR[^\]]*|B|I|UPPERCASE|LOWERCASE|CAPITALIZE|LIGHT)\]', re.I)


def plain(text):
    if isinstance(text, str):
        return _TAGS.sub('', text)
    return text


def _wrap_method(cls, name, base):
    orig = getattr(base, name)

    def method(self, text, *args, **kwargs):
        return orig(self, plain(text), *args, **kwargs)
    setattr(cls, name, method)


if not getattr(pyxbmct, '_cwm_plain', False):
    pyxbmct._cwm_plain = True
    _wrap_method(pyxbmct.Label, 'setLabel', xbmcgui.ControlLabel)
    _wrap_method(pyxbmct.TextBox, 'setText', xbmcgui.ControlTextBox)
    _wrap_method(pyxbmct.FadeLabel, 'addLabel', xbmcgui.ControlFadeLabel)
    _wrap_method(pyxbmct.List, 'addItem', xbmcgui.ControlList)

    _orig_label_new = pyxbmct.Label.__new__

    def _label_new(cls, label='', *args, **kwargs):
        return _orig_label_new(cls, plain(label), *args, **kwargs)
    pyxbmct.Label.__new__ = staticmethod(_label_new)


def button(label):
    """A plain text button: pyxbmct's own rounded button textures, the window's text colour."""
    return pyxbmct.Button(label, textColor=TEXT_COLOUR, focusedColor=FOCUS_COLOUR, font='font13')


class PlainDialog(object):
    """xbmcgui.Dialog with formatting tags removed from headings, messages and list rows."""

    def __init__(self):
        self._d = xbmcgui.Dialog()

    def notification(self, heading, message, *args, **kwargs):
        return self._d.notification(plain(heading), plain(message), *args, **kwargs)

    def ok(self, heading, message, *args, **kwargs):
        return self._d.ok(plain(heading), plain(message), *args, **kwargs)

    def yesno(self, heading, message, *args, **kwargs):
        return self._d.yesno(plain(heading), plain(message), *args, **kwargs)

    def yesnocustom(self, heading, message, *args, **kwargs):
        return self._d.yesnocustom(plain(heading), plain(message), *args, **kwargs)

    def select(self, heading, options, *args, **kwargs):
        return self._d.select(plain(heading), [plain(o) for o in options], *args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._d, name)
