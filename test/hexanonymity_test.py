import pandas as pd
import numpy as np
from numpy import array
from src.application.Hexanonymity.Hexanonymity import Hexanonimity

def test_hexanonimity():
    df = pd.DataFrame(
        {
            "a": pd.Series(
                array(
                    [
                        "-8.7354573,42.2239522",
                        "-8.7357169,42.224499",
                        "-8.8932563,42.1011589",
                        "-8.8910411,42.08599",
                    ]
                ),
                dtype=str,
            ),
            "id": pd.Series(array(["1", "2", "1", "2"]), dtype=str),
            "b": pd.Series(array(["a1", "b2", "c3", "d2"]), dtype=str),
        }
    )

    configuration = {"k": 2, "min_p": 0, "max_p": 14}
    operation = Hexanonimity(
        configuration=configuration,
        fields=["a"],
        id_col="id",
        sensitive_cols=[
            "b",
        ],
    )
    np.random.seed(1)

    result = operation.apply(df)
    expected = array(
        [
            "-8.7354573,42.2239522",
            "-8.7354573,42.2239522",
            "-8.8932563,42.1011589",
            "-8.8932563,42.1011589",
        ],
        dtype=str,
    )
    assert (result["a"].values == expected).all()
    expected = array(["a1", "a1", "c3", "c3"], dtype=str)
    assert (result["b"].values == expected).all()


def test_hexanonimity_k():
    df = pd.DataFrame(
        {
            "a": pd.Series(
                array(
                    [
                        "-8.7354573,42.2239522",
                        "-8.7357169,42.224499",
                        "-8.8932563,42.1011589",
                        "-8.8910411,42.08599",
                    ]
                ),
                dtype=str,
            ),
            "id": pd.Series(array(["1", "2", "1", "2"]), dtype=str),
        }
    )
    configuration = {"k": 3, "min_p": 0, "max_p": 14}
    operation = Hexanonimity(
        configuration=configuration, fields=["a"], id_col="id", sensitive_cols=[]
    )
    np.random.seed(1)
    
    result = operation.apply(df)
    expected = array(
        [
            "-8.7354573,42.2239522",
            "-8.7354573,42.2239522",
            "-8.7354573,42.2239522",
            "-8.7354573,42.2239522",
        ],
        dtype=str,
    )
    assert (result["a"].values == expected).all()


def test_hexanonimity_idcol():
    df = pd.DataFrame(
        {
            "a": pd.Series(
                array(
                    [
                        "-8.7354573,42.2239522",
                        "-8.7357169,42.224499",
                        "-8.8932563,42.1011589",
                        "-8.8910411,42.08599",
                    ]
                ),
                dtype=str,
            ),
            "id": pd.Series(array(["1", "1", "2", "2"]), dtype=str),
            "b": pd.Series(array(["a1", "b2", "c3", "d2"]), dtype=str),
        }
    )

    configuration = {"k": 2, "min_p": 0, "max_p": 14}
    operation = Hexanonimity(
        configuration=configuration,
        fields=["a"],
        id_col="id",
        sensitive_cols=[
            "b",
        ],
    )

    result = operation.apply(df)
    expected = array(
        [
            "-8.8932563,42.1011589",
            "-8.8932563,42.1011589",
            "-8.8932563,42.1011589",
            "-8.8932563,42.1011589",
        ],
        dtype=str,
    )
    assert (result["a"].values == expected).all()
