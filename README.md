# Hexanonymity

Hexanonymity is a new algorithm for the anonymisation of geo-positioned data which introduces a limited amount of information loss while providing k-anonymity. Hexanonymity leverages the Uber H3 geo-indexing system, which subdivides the earth into hexagonal meshes. We take advantage of a property of hexagon meshes, where for any of them, the distance from its centre to the centre of the six surrounding hexagons is always the same. This property allows the algorithm to generate high-quality clusters of geo-positioned data points, introducing a limited information loss.

Hexanonymity therefore provides k-anonymity to datasets of geo-positioned datapoints. We use the Uber H3 library to group the set of locations into recursively larger areas so that, at the end of the process, locations belonging to the same cell in the hierarchy report the same final location, becoming indistinguishable and providing k-anonymity. 

### Requirements 

Install the requirements using pip: 

```
pip install -r ./requirements.txt
```

### Code example

You can easily apply Hexanonymity to a set of adding them into a Pandas Dataframe. The Hexanonymity class expects a DataFrame with the following columns: 

- A column with the geo-positioned data points (latitude and longitude) to be anonymized, as a comma-separated string ("lat,log")
- A column with the identifier of the user. To provide k-anonymity, the algorithm will try to make groups of at least k different individuals based on this identifier. 

The configuration of the Hexanonymity algorithm requires the following information: 

- `configuration`: `JSON` object with the following field: 
    - `k`: Minimum k (at least k=2 to provide privacy)
    - `min_p`: Minimum size to be applied in the hiearchy of Uber H3
    - `max_p`: Minimum size to be applied in the hiearchy of Uber H3
- `fields`: Column name which contains the geo-positioned data points
- `id_col`: Column name which contains the user identifier. 
- `sensitive_cols`: An (optional) list of column name(s) with other fields to write the anonymised position to. In some datasets, the gps data points appear in multiple columns. You can set the additional columns in this field of the configuration to anonymise all the columns at once. 


We provide a [Jupyter Notebook](Hexanonymity.ipynb) showcasing the anonymization of a symulated dataset of connected vehicles in near-real time. The dataset is available in the [INFINITECH H2020 project marketplace](https://marketplace.infinitech-h2020.eu/assets/sumo-vigo-vehicles-sample).

#### Initialize pandas dataframe with sample data
```
df = pd.DataFrame(
        {
            "locations": pd.Series(
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
            "other_locations": pd.Series(array(["a1", "b2", "c3", "d2"]), dtype=str),
        }
    )
```

#### Create an Hexanonymity class

```

operation = Hexanonimity(
    configuration={"k": 2, "min_p": 0, "max_p": 14},
    fields=["locations"],
    id_col="id",
    sensitive_cols=[
        "other_locations",
    ],
)
```

#### Apply the operation
```
result = operation.apply(df)
head(result)
```

## Authors
Please, refer to [AUTHORS](AUTHORS)

## Contributors
Please, refer to [CONTRIBUTORS](CONTRIBUTORS)

## License
BIC is licensed under the Mozilla Public License v2.0 - see the [LICENSE](LICENSE) file for details
