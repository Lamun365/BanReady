from pydantic import (
    BaseModel,
    Field,
    field_validator,
)


class ModeledStreetRequest(BaseModel):
    street_name: str
    segment_id: int | None = None

    parked_side: str
    restricted_side: str
    ban_type: str


class ModeledZoneRequest(BaseModel):
    latitude: float = Field(
        ge=-90,
        le=90,
    )

    longitude: float = Field(
        ge=-180,
        le=180,
    )

    origin_segment_id: int | None = None

    radius_meters: float = Field(
        default=500,
        ge=100,
        le=2000,
    )

    limit: int = Field(
        default=4,
        ge=1,
        le=10,
    )


class ModeledWalkingZonesRequest(BaseModel):
    latitude: float = Field(
        ge=-90,
        le=90,
    )

    longitude: float = Field(
        ge=-180,
        le=180,
    )

    origin_segment_id: int | None = None

    radii_meters: list[int] = Field(
        default_factory=lambda: [
            400,
            800,
        ]
    )

    @field_validator(
        "radii_meters"
    )
    @classmethod
    def validate_radii(
        cls,
        values: list[int],
    ) -> list[int]:
        if not values:
            raise ValueError(
                "At least one radius is required."
            )

        cleaned_values = sorted(
            set(values)
        )

        if any(
            value < 100
            or value > 5000
            for value in cleaned_values
        ):
            raise ValueError(
                "Each radius must be between "
                "100 and 5000 meters."
            )

        return cleaned_values