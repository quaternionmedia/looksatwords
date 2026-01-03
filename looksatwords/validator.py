from pandera import Column, String, DataFrameSchema, Index, Object, Float, Int


class BaseSchema:
    """
    Base class for defining schemas using pandera.

    Methods:
        generate_columns(prefix, suffixes, col_type):
            Dynamically generates a dictionary of column definitions with a given prefix and type.

        create_schema(columns_spec):
            Constructs a Pandera DataFrameSchema from a dictionary of column definitions.
    """

    @staticmethod
    def generate_columns(prefix, suffixes, col_type):
        return {
            f"{prefix}_{suffix}": Column(col_type, nullable=False)
            for suffix in suffixes
        }

    @staticmethod
    def create_schema(columns_spec):
        return DataFrameSchema(columns_spec, index=Index(int))


# Define the common suffixes for abstracted_headline and abstracted_description
sentiment_suffixes = ["sentiment", "positive", "negative", "neutral", "compound"]
wordcount_suffix = ["wordcount"]
pos_suffixes = [
    "noun",
    "verb",
    "adjective",
    "adverb",
    "pronoun",
    "conjunction",
    "preposition",
    "interjection",
]


class RawDataSchema(BaseSchema):
    """
    Schema definition for raw/unprocessed data. Currently empty, but acts as a placeholder for potential
    validation rules for unstructured or minimally processed datasets.

    Attributes:
        schema (DataFrameSchema): An empty schema object.
    """

    schema = BaseSchema.create_schema({})


class GNewsDataSchema(BaseSchema):
    """
    Schema for validating the structure of raw data fetched from the GNews API..

    Required Columns:
        - headline (str): The article headline.
        - description (str): The article description.
        - url (str): URL to the full article.
        - published date (str): Publication date in string format.
        - publisher (object): Metadata about the publisher (can be nested).

    Attributes:
        schema (DataFrameSchema): Schema object for GNews articles.
    """

    schema = BaseSchema.create_schema(
        {
            "headline": Column(String, nullable=False),
            "description": Column(String, nullable=False),
            "url": Column(String, nullable=False),
            "published date": Column(String, nullable=False),
            "publisher": Column(Object, nullable=False),
        }
    )


class AnalyzedDataSchema(BaseSchema):
    """
    Schema for validating the additional analyzed data columns produced in analyzer.py
    after processing GNews API data.

    Attributes:
        schema (DataFrameSchema): Schema object for validated, analyzed news articles.
    """

    columns_spec = {
        "headline": Column(String, nullable=False),
        "description": Column(String, nullable=False),
        "url": Column(String, nullable=False),
        "published date": Column(String, nullable=False),
        "publisher": Column(Object, nullable=False),
        "abstracted_headline": Column(String, nullable=False),
        **BaseSchema.generate_columns("abstracted_headline", sentiment_suffixes, Float),
        **BaseSchema.generate_columns("abstracted_headline", wordcount_suffix, Int),
        **BaseSchema.generate_columns("abstracted_headline", pos_suffixes, Int),
        "abstracted_description": Column(String, nullable=False),
        **BaseSchema.generate_columns(
            "abstracted_description", sentiment_suffixes, Float
        ),
        **BaseSchema.generate_columns("abstracted_description", wordcount_suffix, Int),
        **BaseSchema.generate_columns("abstracted_description", pos_suffixes, Int),
    }
    schema = BaseSchema.create_schema(columns_spec)


# Instantiate schemas
raw_data_schema = RawDataSchema.schema
gnews_data_schema = GNewsDataSchema.schema
analyzed_data_schema = AnalyzedDataSchema.schema
visualized_data_schema = AnalyzedDataSchema.schema
