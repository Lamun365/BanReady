from dataclasses import asdict, dataclass
from typing import Optional


# ============================================================
# Evidence-status constants
# ============================================================

OBSERVED = "OBSERVED"

ESTIMATED = "ESTIMATED"

UNKNOWN = "UNKNOWN"


# ============================================================
# Collection-method constants
# ============================================================

MANUAL_FIELD_COUNT = "MANUAL_FIELD_COUNT"

CAMERA_COUNT = "CAMERA_COUNT"

CITY_DATA = "CITY_DATA"

SYNTHETIC_SCENARIO = "SYNTHETIC_SCENARIO"


# ============================================================
# Weather constants
# ============================================================

CLEAR = "CLEAR"

RAIN = "RAIN"

SNOW = "SNOW"

ICE = "ICE"

CLOUDY = "CLOUDY"

UNKNOWN_WEATHER = "UNKNOWN"


# ============================================================
# Parking-demand observation model
# ============================================================

@dataclass
class ParkingDemandObservation:
    observation_id: str

    street_name: str

    segment_id: int

    observation_date: str

    observation_time: str

    # --------------------------------------------------------
    # Observed on-street vehicles
    #
    # These two fields represent BanReady's actual
    # block-level parking demand.
    # --------------------------------------------------------

    parked_odd: int

    parked_even: int

    # --------------------------------------------------------
    # Optional off-street contextual counts
    #
    # These values are retained for research context.
    # They are NOT included in total_on_street_demand.
    # --------------------------------------------------------

    driveway_vehicles: Optional[int] = None

    private_lot_vehicles: Optional[int] = None

    # --------------------------------------------------------
    # Observation location and context
    # --------------------------------------------------------

    observer_id: Optional[str] = None

    weather: str = UNKNOWN_WEATHER

    snow_on_ground: Optional[bool] = None

    winter_ban_active: Optional[bool] = None

    unusual_event: Optional[bool] = None

    # --------------------------------------------------------
    # Evidence information
    # --------------------------------------------------------

    evidence_status: str = OBSERVED

    collection_method: str = MANUAL_FIELD_COUNT

    notes: Optional[str] = None

    # --------------------------------------------------------
    # Calculated demand
    # --------------------------------------------------------

    @property
    def total_on_street_demand(
        self,
    ) -> int:
        """
        Return the total number of vehicles observed
        parked on the street.

        Vehicles in private driveways or private lots
        are intentionally excluded.
        """

        return (
            self.parked_odd
            + self.parked_even
        )

    # --------------------------------------------------------
    # Side-specific contextual values
    # --------------------------------------------------------

    @property
    def total_contextual_off_street_vehicles(
        self,
    ) -> int:
        """
        Return the optional observed off-street vehicle
        total.

        This value is contextual and must not be used as
        on-street parking demand.
        """

        driveway_count = (
            self.driveway_vehicles
            if self.driveway_vehicles
            is not None
            else 0
        )

        private_lot_count = (
            self.private_lot_vehicles
            if self.private_lot_vehicles
            is not None
            else 0
        )

        return (
            driveway_count
            + private_lot_count
        )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    def validate(
        self,
    ):
        """
        Validate the observation before it is used in
        BanReady demand or shortfall calculations.

        Returns a list of validation-error messages.
        An empty list means the observation is valid.
        """

        errors = []

        # ----------------------------------------------------
        # Observation ID
        # ----------------------------------------------------

        if not isinstance(
            self.observation_id,
            str,
        ):
            errors.append(
                "observation_id must be a string."
            )

        elif (
            self.observation_id.strip()
            == ""
        ):
            errors.append(
                "observation_id cannot be empty."
            )

        # ----------------------------------------------------
        # Street name
        # ----------------------------------------------------

        if not isinstance(
            self.street_name,
            str,
        ):
            errors.append(
                "street_name must be a string."
            )

        elif (
            self.street_name.strip()
            == ""
        ):
            errors.append(
                "street_name cannot be empty."
            )

        # ----------------------------------------------------
        # Segment ID
        # ----------------------------------------------------

        if (
            not isinstance(
                self.segment_id,
                int,
            )
            or isinstance(
                self.segment_id,
                bool,
            )
        ):
            errors.append(
                "segment_id must be an integer."
            )

        elif self.segment_id <= 0:
            errors.append(
                "segment_id must be positive."
            )

        # ----------------------------------------------------
        # Date and time
        #
        # Format validation is deliberately lightweight for
        # the MVP. The expected formats are:
        #
        # observation_date: YYYY-MM-DD
        # observation_time: HH:MM
        # ----------------------------------------------------

        if not isinstance(
            self.observation_date,
            str,
        ):
            errors.append(
                "observation_date must be a string."
            )

        elif (
            self.observation_date.strip()
            == ""
        ):
            errors.append(
                "observation_date cannot be empty."
            )

        if not isinstance(
            self.observation_time,
            str,
        ):
            errors.append(
                "observation_time must be a string."
            )

        elif (
            self.observation_time.strip()
            == ""
        ):
            errors.append(
                "observation_time cannot be empty."
            )

        # ----------------------------------------------------
        # On-street counts
        # ----------------------------------------------------

        if (
            not isinstance(
                self.parked_odd,
                int,
            )
            or isinstance(
                self.parked_odd,
                bool,
            )
        ):
            errors.append(
                "parked_odd must be an integer."
            )

        elif self.parked_odd < 0:
            errors.append(
                "parked_odd cannot be negative."
            )

        if (
            not isinstance(
                self.parked_even,
                int,
            )
            or isinstance(
                self.parked_even,
                bool,
            )
        ):
            errors.append(
                "parked_even must be an integer."
            )

        elif self.parked_even < 0:
            errors.append(
                "parked_even cannot be negative."
            )

        # ----------------------------------------------------
        # Optional contextual counts
        # ----------------------------------------------------

        if (
            self.driveway_vehicles
            is not None
        ):
            if (
                not isinstance(
                    self.driveway_vehicles,
                    int,
                )
                or isinstance(
                    self.driveway_vehicles,
                    bool,
                )
            ):
                errors.append(
                    "driveway_vehicles must be an "
                    "integer or null."
                )

            elif (
                self.driveway_vehicles
                < 0
            ):
                errors.append(
                    "driveway_vehicles cannot be "
                    "negative."
                )

        if (
            self.private_lot_vehicles
            is not None
        ):
            if (
                not isinstance(
                    self.private_lot_vehicles,
                    int,
                )
                or isinstance(
                    self.private_lot_vehicles,
                    bool,
                )
            ):
                errors.append(
                    "private_lot_vehicles must be an "
                    "integer or null."
                )

            elif (
                self.private_lot_vehicles
                < 0
            ):
                errors.append(
                    "private_lot_vehicles cannot be "
                    "negative."
                )

        # ----------------------------------------------------
        # Evidence status
        # ----------------------------------------------------

        allowed_evidence_statuses = {
            OBSERVED,
            ESTIMATED,
            UNKNOWN,
        }

        if (
            self.evidence_status
            not in allowed_evidence_statuses
        ):
            errors.append(
                "evidence_status must be OBSERVED, "
                "ESTIMATED or UNKNOWN."
            )

        # ----------------------------------------------------
        # Collection method
        # ----------------------------------------------------

        allowed_collection_methods = {
            MANUAL_FIELD_COUNT,
            CAMERA_COUNT,
            CITY_DATA,
            SYNTHETIC_SCENARIO,
        }

        if (
            self.collection_method
            not in allowed_collection_methods
        ):
            errors.append(
                "collection_method is invalid."
            )

        # ----------------------------------------------------
        # Synthetic-data protection
        # ----------------------------------------------------

        if (
            self.collection_method
            == SYNTHETIC_SCENARIO
            and self.evidence_status
            == OBSERVED
        ):
            errors.append(
                "Synthetic scenario data cannot be "
                "labeled OBSERVED."
            )

        return errors

    # --------------------------------------------------------
    # Dictionary conversion
    # --------------------------------------------------------

    def to_dict(
        self,
    ):
        """
        Convert the observation into a serializable
        dictionary and include calculated totals.
        """

        data = asdict(
            self
        )

        data[
            "total_on_street_demand"
        ] = (
            self.total_on_street_demand
        )

        data[
            "total_contextual_off_street_vehicles"
        ] = (
            self.total_contextual_off_street_vehicles
        )

        return data