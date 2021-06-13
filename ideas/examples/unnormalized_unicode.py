"""Python does 'normalization' of unicode names by default.
As a result, some different unicode names can end up representing
the same object.

This example demonstrates how different names can be prevented
from being 'normalized'.

Original idea from Sergey B. Kirpichev.
See https://github.com/aroberge/ideas/issues/13 for a reference.
"""
import io
import tokenize
import unicodedata
import uuid

from ideas import import_hook

__NAMES_MAP = {}


def transform_names(source, **kwargs):
    """Transform names that would normally be 'normalized' by
    Python into different and unique variable names.
    """
    result = []
    g = tokenize.tokenize(io.BytesIO(source.encode()).readline)
    for toknum, tokval, _, _, _ in g:
        if toknum == tokenize.NAME:
            normalized_name = unicodedata.normalize("NFKC", tokval)
            if normalized_name != tokval:
                if tokval not in __NAMES_MAP:
                    __NAMES_MAP[tokval] = f"{normalized_name}_{uuid.uuid4().hex!s}"
                tokval = __NAMES_MAP[tokval]
        result.append((toknum, tokval))
    return tokenize.untokenize(result).decode()


def ndir(obj=None):
    """Similar to Python's dir, but shows the original name
    entered, not the transformed one."""
    import inspect
    if obj is not None:
        names = dir(obj)
    else:
        names = list(inspect.currentframe().f_back.f_locals)
    for k, v in __NAMES_MAP.items():
        names = [_.replace(v, k) for _ in names]
    if obj is None:
        # The following usually would not show in Python's dir()
        if 'dir' in names:
            names.remove('dir')
        if 'true_dir' in names:  # Purposely hide this one as well. :-)
            names.remove('true_dir')
    return sorted(names)


def source_init():
    return """
dir, true_dir = ndir, dir
del ndir
"""


import_hook.create_hook(
    source_init=source_init,
    transform_source=transform_names,
    console_dict={"__NAMES_MAP": __NAMES_MAP, "ndir": ndir},
)
