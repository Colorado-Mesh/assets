import modules.logs as logging
from assets.meshcore_network_health_weights.math_utils import (
    cap_value,
    safe_log,
    safe_log2,
    double_sqrt_curve
)
from collections.abc import Callable
from typing import Optional, Any, List


class MeshCoreNetworkHealthCalculationRange:
    score: float
    min: Optional[float]
    max: Optional[float]

    def __init__(self, score: float, minimum: Optional[float] = None, maximum: Optional[float] = None):
        self.score = score
        self.min = minimum
        self.max = maximum

    def in_range(self, value: float) -> bool:
        if not value:
            return False
        if self.min is not None and value < self.min:
            return False
        if self.max is not None and value > self.max:
            return False
        return True


class MeshCoreNetworkHealthCalculation:
    id: str
    name: str
    description: str
    value_retrieval: Callable[[], Any]
    multiplier: int = 1
    ranges: Optional[List[MeshCoreNetworkHealthCalculationRange]] = None
    override_calculation: Optional[Callable[[Any], float]] = None

    def __init__(self,
                 _id: str,
                 name: str,
                 description: str,
                 value_retrieval: Callable[[], Any],
                 multiplier: int = 1,
                 ranges: Optional[list[MeshCoreNetworkHealthCalculationRange]] = None,
                 override_calculation: Optional[Callable[[Any], float]] = None):
        self.id = _id
        self.name = name
        self.description = description
        self.value_retrieval = value_retrieval
        self.multiplier = multiplier
        self.ranges = ranges
        self.override_calculation = override_calculation

    def calculate(self) -> float | None:
        if not self.ranges and not self.override_calculation:
            raise Exception("No calculation method")

        try:
            _input: Any = self.value_retrieval()
        except Exception:  # Data was not loaded/parsed properly, could not extract value properly
            _input = None  # Will trigger range failure and ultimately return None (will be ignored downstream)

        if self.override_calculation:
            return self.override_calculation(_input)

        for _range in self.ranges:  # type: ignore
            if _range.in_range(_input):
                return _range.score * self.multiplier

        logging.error(f"Input value out of range for calculation")
        return None


def prepare_calculations(value_lambdas: dict[str, Callable[[], Any]]) -> list[MeshCoreNetworkHealthCalculation]:
    """
        Max 10 points per category, but each can be weighed differently in final count (* multiplier), then percentage as max 100%

        # Node count - 0-25 = 0, 25-50 = 2, 50-100 = 4, 100-200 = 6, 200-400 = 8, 400+ = 10
        # Node active percentage - 0-30 = 0, 30-55 = 2, 55-75 = 4, 75-88 = 6, 88-95 = 8, 95+ = 10
        # Node with clock skew percentage -
        # Repeater/total ratio (room, sensor, companion) - target 1:2-1:1 (33% - 50%) - 0-5%,90-100% = 0, 5-10%,80-90% = 2, 10-20%,70-80% = 4, 20-25%,65-70% = 6, 25-30%,55-65% = 8, 30-55% = 10
        # Observer count (current) - 0-2 = 0, 2-5 = 2, 5-10 = 4, 10-25 = 6, 25-50 = 8, 50+ = 10
        # Observer active percentage -
        # Observer average noise floor (past 24h)
        Latency (observer?) average (past 24h) -
        # Signal (SNR) average (past 24h) - <5 = 0, 5-8 = 4, 8-12 = 6, 12-15 = 8, 15+ = 10
        # RSSI average (past 24h) -
        Most recent packet - <1 min = 10, <5 min = 8, <15 min = 6
        # Number of messages (past 24h) - log scale of messages (need 1000+ msg/day for max)
        # Message-to-non-message (advert) ratio (past 24h) - 0-5% = 0, 5-15% = 2, 15-25% = 4, 25-45% = 6, 45-70% = 8, 70-100% = 10
        # Number of unique users (past 24h) -
        # Top 10 senders is what percentage of all message senders -
        # Average hop count (past 24h) -
        # Largest hop count (past 24h) -
        # Average repeater-repeater (space between repeaters) distance (past 24h) -
        # Longest repeater-repeater (single hop) distance (past 24h) -
        # Unique route count (past 24h) -
        # Top 10 repeaters is what percentage of all paths - target 1:3 - 1:2 (25% - 33%) - 100-85% = 0, 85-75% = 2, 75-65% = 4, 65-50% = 6, 50-33% = 8, 33-25% = 10, 25-15% = 8, 15-10% = 6, 10-5% = 4, 5-0% = 2
        Analyzer scores -
        Neighbor graph average score (min 0.33 confidence) -
        Hash collision counts -
        2/3-byte packet percentage -
        2/3-byte node percentage -
    """

    return [
        MeshCoreNetworkHealthCalculation(
            _id="node_count",
            name="Node Count",
            description="We want a good number of nodes. This is not scaled as the mesh grows currently",
            multiplier=1,
            value_retrieval=value_lambdas["node_count"],
            ranges=[
                MeshCoreNetworkHealthCalculationRange(score=0, minimum=None, maximum=25),
                MeshCoreNetworkHealthCalculationRange(score=2, minimum=25, maximum=50),
                MeshCoreNetworkHealthCalculationRange(score=4, minimum=50, maximum=100),
                MeshCoreNetworkHealthCalculationRange(score=6, minimum=100, maximum=200),
                MeshCoreNetworkHealthCalculationRange(score=8, minimum=200, maximum=400),
                MeshCoreNetworkHealthCalculationRange(score=10, minimum=400, maximum=None),
            ]
        ),
        MeshCoreNetworkHealthCalculation(
            _id="node_active_percentage",
            name="Active Node Percentage",
            description="We want as many of our nodes on the mesh active as possible",
            multiplier=1,
            value_retrieval=value_lambdas["node_active_percentage"],
            ranges=[
                MeshCoreNetworkHealthCalculationRange(score=0, minimum=None, maximum=0.30),
                MeshCoreNetworkHealthCalculationRange(score=2, minimum=0.30, maximum=0.55),
                MeshCoreNetworkHealthCalculationRange(score=4, minimum=0.55, maximum=0.75),
                MeshCoreNetworkHealthCalculationRange(score=6, minimum=0.75, maximum=0.88),
                MeshCoreNetworkHealthCalculationRange(score=8, minimum=0.88, maximum=0.95),
                MeshCoreNetworkHealthCalculationRange(score=10, minimum=0.95, maximum=None),
            ]
        ),
        MeshCoreNetworkHealthCalculation(
            _id="node_with_skew_percentage",
            name="Node With Skew Percentage",
            description="We want no nodes with any clock skew",
            multiplier=1,
            value_retrieval=value_lambdas["node_with_skew_percentage"],
            ranges=[
                MeshCoreNetworkHealthCalculationRange(score=0, minimum=0.25, maximum=None),
                MeshCoreNetworkHealthCalculationRange(score=2, minimum=0.15, maximum=0.25),
                MeshCoreNetworkHealthCalculationRange(score=4, minimum=0.10, maximum=0.15),
                MeshCoreNetworkHealthCalculationRange(score=6, minimum=0.05, maximum=0.10),
                MeshCoreNetworkHealthCalculationRange(score=8, minimum=0.02, maximum=0.05),
                MeshCoreNetworkHealthCalculationRange(score=10, minimum=None, maximum=0.02),
            ]
        ),
        MeshCoreNetworkHealthCalculation(
            _id="observer_count",
            name="Observer Count",
            description="We want a good number of observers. This is not scaled as the mesh grows currently",
            multiplier=1,
            value_retrieval=value_lambdas["observer_count"],
            ranges=[
                MeshCoreNetworkHealthCalculationRange(score=0, minimum=None, maximum=2),
                MeshCoreNetworkHealthCalculationRange(score=2, minimum=2, maximum=5),
                MeshCoreNetworkHealthCalculationRange(score=4, minimum=5, maximum=10),
                MeshCoreNetworkHealthCalculationRange(score=6, minimum=10, maximum=25),
                MeshCoreNetworkHealthCalculationRange(score=8, minimum=25, maximum=50),
                MeshCoreNetworkHealthCalculationRange(score=10, minimum=50, maximum=None),
            ]
        ),
        MeshCoreNetworkHealthCalculation(
            _id="observer_active_percentage",
            name="Observer Active Percentage",
            description="We want as many of our registered observers up and running properly as possible",
            multiplier=1,
            value_retrieval=value_lambdas["observer_active_percentage"],
            ranges=[
                MeshCoreNetworkHealthCalculationRange(score=0, minimum=None, maximum=0.30),
                MeshCoreNetworkHealthCalculationRange(score=2, minimum=0.30, maximum=0.55),
                MeshCoreNetworkHealthCalculationRange(score=4, minimum=0.55, maximum=0.75),
                MeshCoreNetworkHealthCalculationRange(score=6, minimum=0.75, maximum=0.88),
                MeshCoreNetworkHealthCalculationRange(score=8, minimum=0.88, maximum=0.95),
                MeshCoreNetworkHealthCalculationRange(score=10, minimum=0.95, maximum=None),
            ]
        ),
        MeshCoreNetworkHealthCalculation(
            _id="average_observer_noise_floor",
            name="Average Observer Noise Floor",
            description="Noise floor across all observers should remain as low as possible",
            multiplier=1,
            value_retrieval=value_lambdas["average_observer_noise_floor"],
            ranges=[
                MeshCoreNetworkHealthCalculationRange(score=0, minimum=-90, maximum=None),
                MeshCoreNetworkHealthCalculationRange(score=2, minimum=-100, maximum=-90),
                MeshCoreNetworkHealthCalculationRange(score=4, minimum=-105, maximum=-100),
                MeshCoreNetworkHealthCalculationRange(score=6, minimum=-110, maximum=-105),
                MeshCoreNetworkHealthCalculationRange(score=8, minimum=-115, maximum=-110),
                MeshCoreNetworkHealthCalculationRange(score=10, minimum=None, maximum=-115),
            ]
        ),
        MeshCoreNetworkHealthCalculation(
            _id="repeater_to_total_node_ratio",
            name="Repeater-To-Total-Node Ratio",
            description="Repeaters should make up between 33% and 50% of all nodes on the network.",
            multiplier=1,
            value_retrieval=value_lambdas["repeater_to_total_node_ratio"],
            ranges=[
                MeshCoreNetworkHealthCalculationRange(score=0, minimum=None, maximum=0.05),
                MeshCoreNetworkHealthCalculationRange(score=2, minimum=0.05, maximum=0.10),
                MeshCoreNetworkHealthCalculationRange(score=4, minimum=0.10, maximum=0.20),
                MeshCoreNetworkHealthCalculationRange(score=6, minimum=0.20, maximum=0.25),
                MeshCoreNetworkHealthCalculationRange(score=8, minimum=0.25, maximum=0.30),
                MeshCoreNetworkHealthCalculationRange(score=10, minimum=0.30, maximum=0.55),
                MeshCoreNetworkHealthCalculationRange(score=8, minimum=0.55, maximum=0.65),
                MeshCoreNetworkHealthCalculationRange(score=6, minimum=0.65, maximum=0.70),
                MeshCoreNetworkHealthCalculationRange(score=4, minimum=0.70, maximum=0.80),
                MeshCoreNetworkHealthCalculationRange(score=2, minimum=0.80, maximum=0.90),
                MeshCoreNetworkHealthCalculationRange(score=0, minimum=0.90, maximum=None),
            ]
        ),
        MeshCoreNetworkHealthCalculation(
            _id="average_snr_past_24h",
            name="Average SNR (Past 24 Hours)",
            description="SNR across all observers should be as high as possible",
            multiplier=1,
            value_retrieval=value_lambdas["average_snr_past_24h"],
            ranges=[
                MeshCoreNetworkHealthCalculationRange(score=0, minimum=None, maximum=5),
                MeshCoreNetworkHealthCalculationRange(score=4, minimum=5, maximum=8),
                MeshCoreNetworkHealthCalculationRange(score=6, minimum=8, maximum=12),
                MeshCoreNetworkHealthCalculationRange(score=8, minimum=12, maximum=15),
                MeshCoreNetworkHealthCalculationRange(score=10, minimum=15, maximum=None),
            ]
        ),
        MeshCoreNetworkHealthCalculation(
            _id="average_rssi_past_24h",
            name="Average RSSI (Past 24 Hours)",
            description="RSSI across all observers should remain as close to 0 dBm as possible",
            multiplier=1,
            value_retrieval=value_lambdas["average_rssi_past_24h"],
            ranges=[
                MeshCoreNetworkHealthCalculationRange(score=0, minimum=None, maximum=-100),
                MeshCoreNetworkHealthCalculationRange(score=4, minimum=-100, maximum=-70),
                MeshCoreNetworkHealthCalculationRange(score=6, minimum=-70, maximum=-40),
                MeshCoreNetworkHealthCalculationRange(score=8, minimum=-40, maximum=-20),
                MeshCoreNetworkHealthCalculationRange(score=10, minimum=-20, maximum=None),
            ]
        ),
        MeshCoreNetworkHealthCalculation(
            _id="number_of_messages_past_24h",
            name="Number of Messages (Past 24 Hours)",
            description="Hopefully people are actually sending messages and using the mesh",
            multiplier=1,
            value_retrieval=value_lambdas["number_of_messages_past_24h"],
            # 1000 messages = ~9.9 for max score, 5 messages = ~2.3, 2 messages = 1, 1 (or 0 maxed to 1) message = 0
            override_calculation=lambda _input: cap_value(safe_log2(_input)),
        ),
        MeshCoreNetworkHealthCalculation(
            _id="message_percentage_of_all_traffic_past_24h",
            name="Message Percentage of Traffic (Past 24 Hours)",
            description="Adverts and non-messages are inevitable, but actual conversation should make up a plurality of traffic.",
            multiplier=1,
            value_retrieval=value_lambdas["message_percentage_of_all_traffic_past_24h"],
            ranges=[
                MeshCoreNetworkHealthCalculationRange(score=0, minimum=None, maximum=0.05),
                MeshCoreNetworkHealthCalculationRange(score=2, minimum=0.05, maximum=0.15),
                MeshCoreNetworkHealthCalculationRange(score=4, minimum=0.15, maximum=0.25),
                MeshCoreNetworkHealthCalculationRange(score=6, minimum=0.25, maximum=0.45),
                MeshCoreNetworkHealthCalculationRange(score=8, minimum=0.45, maximum=0.70),
                MeshCoreNetworkHealthCalculationRange(score=10, minimum=0.70, maximum=None),
            ]
        ),
        MeshCoreNetworkHealthCalculation(
            _id="average_hop_count_past_24h",
            name="Average Hop Count (Past 24 Hours)",
            description="As the mesh grows in geographical distance, we should start seeing completed routes with higher hop counts",
            multiplier=1,
            value_retrieval=value_lambdas["average_hop_count_past_24h"],
            # Want to encourage low number (good core repeaters)
            ranges=[
                MeshCoreNetworkHealthCalculationRange(score=0, minimum=None, maximum=4),
                MeshCoreNetworkHealthCalculationRange(score=2, minimum=4, maximum=8),
                MeshCoreNetworkHealthCalculationRange(score=4, minimum=8, maximum=12),
                MeshCoreNetworkHealthCalculationRange(score=6, minimum=12, maximum=16),
                MeshCoreNetworkHealthCalculationRange(score=8, minimum=16, maximum=32),
                MeshCoreNetworkHealthCalculationRange(score=10, minimum=32, maximum=None),
            ]
        ),
        MeshCoreNetworkHealthCalculation(
            _id="largest_hop_count_past_24h",
            name="Largest Hop Count (Past 24 Hours)",
            description="As the mesh grows in geographical distance, we should start seeing completed routes with higher hop counts",
            multiplier=1,
            value_retrieval=value_lambdas["largest_hop_count_past_24h"],
            # Want to encourage high number (interconnected repeaters)
            override_calculation=lambda _input: cap_value(
                double_sqrt_curve(_input=_input['_input'], _max=_input['_max'])),
        ),
        MeshCoreNetworkHealthCalculation(
            _id="unique_route_count",
            name="Unique Route Count",
            description="As the number of repeaters increases in the network, so should the number of permutations of possible routes.",
            multiplier=1,
            value_retrieval=value_lambdas["unique_route_count"],
            # Want to encourage high number (interconnected repeaters)
            override_calculation=lambda _input: cap_value(safe_log(_input) - 2),
        ),
        MeshCoreNetworkHealthCalculation(
            _id="top_path_nonreliance",
            name="Top Path Nonreliance",
            description="The most-used paths shouldn't handle more than 33% of traffic, to avoid over-reliance on specific routes/repeaters.",
            multiplier=1,
            value_retrieval=value_lambdas["top_path_nonreliance"],
            # Should make up approximately 25-33% of traffic
            ranges=[
                MeshCoreNetworkHealthCalculationRange(score=2, minimum=None, maximum=0.05),
                MeshCoreNetworkHealthCalculationRange(score=4, minimum=0.05, maximum=0.10),
                MeshCoreNetworkHealthCalculationRange(score=6, minimum=0.10, maximum=0.15),
                MeshCoreNetworkHealthCalculationRange(score=8, minimum=0.15, maximum=0.25),
                MeshCoreNetworkHealthCalculationRange(score=10, minimum=0.25, maximum=0.33),
                MeshCoreNetworkHealthCalculationRange(score=8, minimum=0.33, maximum=0.50),
                MeshCoreNetworkHealthCalculationRange(score=6, minimum=0.50, maximum=0.65),
                MeshCoreNetworkHealthCalculationRange(score=4, minimum=0.65, maximum=0.75),
                MeshCoreNetworkHealthCalculationRange(score=2, minimum=0.75, maximum=0.85),
                MeshCoreNetworkHealthCalculationRange(score=0, minimum=0.85, maximum=None),
            ]
        ),
        MeshCoreNetworkHealthCalculation(
            _id="unique_users_count",
            name="Unique Users Count",
            description="We don't want all the messages to just be coming from the same small group of users.",
            multiplier=1,
            value_retrieval=value_lambdas["unique_users_count"],
            override_calculation=lambda _input: cap_value(safe_log(_input * 10)),
        ),
        MeshCoreNetworkHealthCalculation(
            _id="top_senders_target_percentage",
            name="Top Senders Percentage",
            description="The most active users on the mesh shouldn't make up more than 33% of all traffic. We want everyone participating",
            multiplier=1,
            value_retrieval=value_lambdas["top_senders_target_percentage"],
            # Should make up approximately 25-33% of traffic
            ranges=[
                MeshCoreNetworkHealthCalculationRange(score=2, minimum=None, maximum=0.05),
                MeshCoreNetworkHealthCalculationRange(score=4, minimum=0.05, maximum=0.10),
                MeshCoreNetworkHealthCalculationRange(score=6, minimum=0.10, maximum=0.15),
                MeshCoreNetworkHealthCalculationRange(score=8, minimum=0.15, maximum=0.25),
                MeshCoreNetworkHealthCalculationRange(score=10, minimum=0.25, maximum=0.33),
                MeshCoreNetworkHealthCalculationRange(score=8, minimum=0.33, maximum=0.50),
                MeshCoreNetworkHealthCalculationRange(score=6, minimum=0.50, maximum=0.65),
                MeshCoreNetworkHealthCalculationRange(score=4, minimum=0.65, maximum=0.75),
                MeshCoreNetworkHealthCalculationRange(score=2, minimum=0.75, maximum=0.85),
                MeshCoreNetworkHealthCalculationRange(score=0, minimum=0.85, maximum=None),
            ]
        ),
        MeshCoreNetworkHealthCalculation(
            _id="average_single_hop_distance",
            name="Average Single Hop Distance",
            description="We'll likely never have a single hop across the diagonal length of Colorado. But we can try to get long hops nonetheless.",
            multiplier=1,
            value_retrieval=value_lambdas["average_single_hop_distance"],
            # Colorado is 280x380 mi, longest distance could be 472 mi (759 km) diagonal
            # Thanks Miho for the sqrt curve, still great after all these years
            # Double square root of max travel distance in Colorado, divided by 2-byte-hop-cap/2 (score 10 around 50 km)
            override_calculation=lambda _input: cap_value(double_sqrt_curve(_input=_input, _max=(759 / 15))),
        ),
        MeshCoreNetworkHealthCalculation(
            _id="longest_single_hop_distance",
            name="Longest Single Hop Distance",
            description="We'll likely never have a single hop across the diagonal length of Colorado. But we can try to get long hops nonetheless.",
            multiplier=1,
            value_retrieval=value_lambdas["longest_single_hop_distance"],
            # Colorado is 280x380 mi, longest distance could be 472 mi (759 km) diagonal
            # Thanks Miho for the sqrt curve, still great after all these years
            # Double square root (50 km = 5, 100 km = 6, 200 km = 7, 400 km = 8.5)
            override_calculation=lambda _input: cap_value(double_sqrt_curve(_input=_input, _max=759))
        ),
    ]
