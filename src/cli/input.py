def get_int(min: int, max: int, prompt: str, error: str) -> int:
    """Get integer from stdin in range [`min`, `max`].

    Args:
        min: min. value
        max: max. value
        prompt: text to display when asking for input
        error: text to display when invalid input

    Returns:
        integer in range [`min`, `max`]
    """

    while True:
        try:
            val = int(input(prompt))
            if val < min or val > max:
                raise ValueError
            return val
        except ValueError:
            print(error)


def get_float(min: float, max: float, prompt: str, error: str) -> float:
    """Get float from stdin in range [`min`, `max`].

    Args:
        min: min. value
        max: max. value
        prompt: text to display when asking for input
        error: text to display when invalid input

    Returns:
        float in range [`min`, `max`]
    """

    while True:
        try:
            val = float(input(prompt))
            if val < min or val > max:
                raise ValueError
            return val
        except ValueError:
            print(error)


def get_int_from_list(list: list[int], prompt: str, error: str) -> int:
    """Get int from stdin that is in `list`.

    Args:
        list: list of allowed values
        prompt: text to display when asking for input
        error: text to display when invalid input

    Returns:
        int in `list`
    """

    while True:
        try:
            i = int(input(prompt))

            if i in list:
                return i

            raise ValueError

        except ValueError:
            print(error)
