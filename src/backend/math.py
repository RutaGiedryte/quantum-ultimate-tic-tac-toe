from backend.enums import Axis
import numpy as np


def rotate_vec(vec: list[int], angle: float, axis: Axis) -> list[int]:
    """Rotate `vec` `angle` radians along `axis`.

    Args:
        vec: 3d vector to rotate
        angle: angle to rotate by
        axis: axis to rotate along

    Returns:
        rotated vector
    """

    assert len(vec) == 3, "Vector must be 3-dimensional"

    sin = np.sin(angle)
    cos = np.cos(angle)

    match axis:
        case Axis.X:
            mat = np.array([[1, 0, 0], [0, cos, -sin], [0, sin, cos]])
        case Axis.Y:
            mat = np.array([[cos, 0, sin], [0, 1, 0], [-sin, 0, cos]])
        case Axis.Z:
            mat = np.array([[cos, -sin, 0], [sin, cos, 0], [0, 0, 1]])

    return mat.dot(vec)
