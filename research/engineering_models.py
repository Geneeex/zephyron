"""Small analytical models, independent of plotting and file-system side effects."""
import math


def mission_duty_limit(usable_Wh, duration_h, auxiliary_W, drive_increment_W, solar_W):
    """Return an explicit infeasible state when stationary demand exceeds budget."""
    if usable_Wh < 0 or duration_h <= 0 or auxiliary_W < 0 or drive_increment_W <= 0 or solar_W < 0:
        raise ValueError('Invalid mission budget inputs')
    available_drive_W = usable_Wh / duration_h + solar_W - auxiliary_W
    feasible = available_drive_W >= 0
    return {
        'max_drive_duty_fraction': min(1.0, available_drive_W / drive_increment_W) if feasible else None,
        'stationary_feasible': feasible,
        'state': 'feasible_under_constant_scenario' if feasible else 'infeasible_even_stationary',
        'available_drive_power_W': available_drive_W,
    }


def energy_trajectory(initial_Wh, capacity_Wh, reserve_Wh, intervals):
    """Piecewise-constant, battery-side path audit; does not model real charger losses.

    Each interval has duration_s, load_W, and accepted_charge_W. Accepted charge
    must already satisfy the chosen charger/pack constraints. Capacity saturation
    is applied at every interval; feasibility records every reserve breach rather
    than allowing later charging to erase it. Constant interval powers make the
    endpoints sufficient to find that interval's minimum energy.
    """
    if not 0 <= initial_Wh <= capacity_Wh or not 0 <= reserve_Wh <= capacity_Wh:
        raise ValueError('Initial energy/reserve must lie within capacity')
    energy = initial_Wh
    minimum = initial_Wh
    curtailed = 0.0
    unserved = 0.0
    feasible = initial_Wh >= reserve_Wh
    path = [initial_Wh]
    for interval in intervals:
        seconds, load, charge = (interval[k] for k in ('duration_s', 'load_W', 'accepted_charge_W'))
        if seconds <= 0 or load < 0 or charge < 0 or not all(math.isfinite(x) for x in (seconds, load, charge)):
            raise ValueError('Invalid interval')
        raw = energy + (charge - load) * seconds / 3600
        curtailed += max(0.0, raw - capacity_Wh)
        unserved += max(0.0, -raw)
        energy = min(capacity_Wh, max(0.0, raw))
        minimum = min(minimum, energy)
        feasible = feasible and energy >= reserve_Wh and raw >= 0
        path.append(energy)
    return dict(final_Wh=energy, minimum_Wh=minimum, reserve_feasible=feasible,
                curtailed_Wh=curtailed, unserved_Wh=unserved, path_Wh=path)


def vision_timing(fps, frame_bytes, link_Mbps, inference_ms, other_ms, speed_m_s):
    if min(fps, frame_bytes, link_Mbps, inference_ms) <= 0 or other_ms < 0 or speed_m_s < 0:
        raise ValueError('Invalid vision scenario')
    transfer_s = 8 * frame_bytes / (link_Mbps * 1e6)
    offered_Mbps = fps * frame_bytes * 8 / 1e6
    total_s = 0.5 / fps + transfer_s + inference_ms / 1000 + other_ms / 1000
    return dict(acquisition_wait_mean_ms=500 / fps, transfer_ms=1000 * transfer_s,
                other_pipeline_ms=other_ms, total_event_to_display_ms=1000 * total_s,
                partial_capture_transfer_inference_upper_bound_fps=min(fps, 1 / transfer_s, 1000 / inference_ms),
                offered_stream_Mbps=offered_Mbps,
                network_can_carry_all_captured_frames_ideal=offered_Mbps <= link_Mbps,
                network_minimum_throttle_or_discard_fraction=max(0.0, 1 - link_Mbps / offered_Mbps),
                network_state='within_ideal_payload_capacity' if offered_Mbps <= link_Mbps else 'requires_throttling_or_discard',
                travel_during_latency_m=speed_m_s * total_s)
