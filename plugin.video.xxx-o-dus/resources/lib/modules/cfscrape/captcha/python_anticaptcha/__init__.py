from .base import AnticaptchaClient
try:
    from pkg_resources import get_distribution, DistributionNotFound
except ImportError:  # setuptools/pkg_resources is not shipped with Kodi's Python
    class DistributionNotFound(Exception): pass
    def get_distribution(name): raise DistributionNotFound(name)
from .tasks import (
    NoCaptchaTask,
    NoCaptchaTaskProxylessTask,
    FunCaptchaTask,
    FunCaptchaProxylessTask,
    RecaptchaV3TaskProxyless,
    HCaptchaTask,
    HCaptchaTaskProxyless,
    SquareNetTask,
    ImageToTextTask,
    CustomCaptchaTask,
)
from .exceptions import AnticaptchaException
from .fields import (
    SimpleText,
    Image,
    WebLink,
    TextInput,
    Textarea,
    Checkbox,
    Select,
    Radio,
    ImageUpload,
)

AnticatpchaException = AnticaptchaException

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    pass
