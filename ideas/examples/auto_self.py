"""auto_self.py

Helps to reduce the amount of typing required and increases readability
when assigning attributes in a class's ``__init__()`` method.
"""
from functools import partial

from ideas import import_hook, token_utils


def print_info(kind, source):
    """Prints the source code.

    ``kind`` is usually either ``"Original"`` or ``"Transformed"``
    """
    print(f"==========={kind}============")
    print(source)
    print("-----------------------------")


def transform_source(source, callback_params=None, **kwargs):
    """This function is called by the import hook loader and is used as a
    wrapper for the function where the real transformation is performed.
    """
    if callback_params is not None:
        if callback_params["show_original"]:
            print_info("Original", source)

    source = automatic_self(source)

    if callback_params is not None:
        if callback_params["show_transformed"]:
            print_info("Transformed", source)

    return source


def automatic_self(source):
    """Replaces code like::

        self .= :
            a
            b
            c = this if __ == that else ___

    by::

        self.a = a
        self.b = b
        self.c = this if c == that else c
    """
    new_tokens = []
    auto_self_block = False
    self_name = ""
    indentation = 0

    get_nb = partial(token_utils.get_number, ignore_comments=True)
    get_first = token_utils.get_first
    get_first_index = token_utils.get_first_index

    for tokens in token_utils.get_lines_of_tokens(source):
        if auto_self_block:
            variable = get_first(tokens)
            if variable is not None:  # None would mean an empty line
                var_name = variable.string
                block_indent = variable.start_col
                if block_indent > indentation:
                    if get_nb(tokens) == 1:
                        new_string = f"{self_name}.{var_name} = {var_name}\n"
                        new_line = " " * indentation + new_string
                        tokens = [new_line]
                    else:
                        new_line = token_utils.untokenize(tokens)
                        rest = new_line[variable.end_col :]
                        new_line = " " * indentation + f"{self_name}.{var_name}" + rest
                        new_line = new_line.replace("__", var_name)
                        tokens = [new_line]
                else:
                    auto_self_block = False
        elif get_nb(tokens) == 4:
            index = get_first_index(tokens)
            if (
                tokens[index].is_identifier()
                and tokens[index + 1] == "."
                and tokens[index + 2] == "="
                and tokens[index + 1].end_col == tokens[index + 2].start_col
                and tokens[index + 3] == ":"
            ):
                self_name = tokens[index].string
                indentation = tokens[index].start_col
                auto_self_block = True
                continue
        new_tokens.extend(tokens)
    return token_utils.untokenize(new_tokens)


def add_hook(show_original=False, show_transformed=False, verbose_finder=False):
    """Creates and adds the import hook in sys.meta_path"""
    callback_params = {
        "show_original": show_original,
        "show_transformed": show_transformed,
    }
    hook = import_hook.create_hook(
        transform_source=transform_source,
        callback_params=callback_params,
        name=__name__,
        verbose_finder=verbose_finder,
    )
    return hook
