import io
import tempfile
from typing import Any

import biotite.structure as struct
import biotite.structure.io as structio
import numpy as np


def load_structure_from_buffer(
    buffer: str | io.StringIO, format: str, **load_kwargs: Any
) -> struct.AtomArray:
    """
    Loads a molecular structure from a string buffer into a Biotite AtomArray.

    Args:
        - buffer (Union[str, io.StringIO]): String or StringIO buffer containing the structure data in the specified format.
        - format (str): File format of the structure data (e.g., 'pdb', 'mmcif').
        - **load_kwargs: Additional keyword arguments passed to biotite.structure.io.load_structure.

    Returns:
        - struct.AtomArray: The loaded structure as a Biotite AtomArray.
    """
    # ... read the string buffer
    if isinstance(buffer, io.StringIO):
        buffer = buffer.getvalue()

    # ... write to temporary file and load
    with tempfile.NamedTemporaryFile(suffix=f".{format}", delete=True) as tmp:
        with open(tmp.name, "w") as f:
            f.write(buffer)
        return structio.load_structure(tmp.name, **load_kwargs)


def assert_same_atom_array(
    atom_array_1: struct.AtomArray,
    atom_array_2: struct.AtomArray,
    annotations_to_check: list[str] | None = None,
):
    """
    Asserts that two Biotite AtomArrays are equivalent within specified tolerances, comparing coordinates and annotations.

    Args:
        - atom_array_1 (struct.AtomArray): First AtomArray to compare.
        - atom_array_2 (struct.AtomArray): Second AtomArray to compare.
        - annotations_to_check (Optional[list[str]]): List of annotation categories to compare. If None, compares all
            annotations present in both arrays.

    Raises:
        - AssertionError: If arrays differ in shape, coordinates (beyond tolerance of 1e-3), or annotation values.
    """
    # Check shapes
    if atom_array_1.shape != atom_array_2.shape:
        raise AssertionError(
            f"Shape mismatch:\n"
            f"  Array 1: {atom_array_1.shape}\n"
            f"  Array 2: {atom_array_2.shape}"
        )

    # Check coordinates
    coord_diff = np.abs(atom_array_1.coord - atom_array_2.coord)
    if not np.allclose(
        atom_array_1.coord, atom_array_2.coord, equal_nan=True, atol=1e-3, rtol=1e-3
    ):
        max_diff_idx = np.unravel_index(np.argmax(coord_diff), coord_diff.shape)
        raise AssertionError(
            f"Coordinate mismatch:\n"
            f"  Maximum difference at index {max_diff_idx}:\n"
            f"    Array 1: {atom_array_1.coord[max_diff_idx]}\n"
            f"    Array 2: {atom_array_2.coord[max_diff_idx]}\n"
            f"    Difference: {coord_diff[max_diff_idx]:.6f}"
        )

    # Check annotation categories
    annots_1 = set(atom_array_1.get_annotation_categories())
    annots_2 = set(atom_array_2.get_annotation_categories())
    if annotations_to_check is not None:
        annots_1 = {annot for annot in annots_1 if annot in annotations_to_check}
        annots_2 = {annot for annot in annots_2 if annot in annotations_to_check}
    if annots_1 != annots_2:
        raise AssertionError(
            f"Annotation category mismatch:\n"
            f"  Only in array 1: {annots_1 - annots_2}\n"
            f"  Only in array 2: {annots_2 - annots_1}"
        )

    # Check annotation values
    if annotations_to_check is None:
        annotations_to_check = list(annots_1)
    for annot in annotations_to_check:
        values_1 = atom_array_1.get_annotation(annot)
        values_2 = atom_array_2.get_annotation(annot)
        if not np.all(values_1 == values_2):
            mismatch_idx = np.where(values_1 != values_2)[0]
            first_mismatch = mismatch_idx[0]
            raise AssertionError(
                f"Annotation '{annot}' mismatch:\n"
                f"  First difference at index {first_mismatch}:\n"
                f"    Array 1: {values_1[first_mismatch]}\n"
                f"    Array 2: {values_2[first_mismatch]}"
            )
