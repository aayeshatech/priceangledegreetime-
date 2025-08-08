import streamlit as st
import swisseph as swe
from datetime import datetime, timedelta, time as dt_time
import time as time_module
import pandas as pd
import plotly.graph_objects as go
import math
import os

# Initialize ephemeris with proper error handling
def initialize_ephemeris():
    """Initialize Swiss Ephemeris with proper path and error handling"""
    try:
        # Try to set ephemeris path to default location
        swe.set_ephe_path(os.path.join(os.path.dirname(__file__), 'ephe'))
        
        # Test if ephemeris is working by calculating a simple position
        test_jd = swe.julday(2023, 1, 1, 0)
        test_result = swe.calc_ut(test_jd, swe.SUN)
        
        if len(test_result) < 7 or test_result[6] != 0:
            # Try alternative path
            swe.set_ephe_path(None)
            test_result = swe.calc_ut(test_jd, swe.SUN)
            
            if len(test_result) < 7 or test_result[6] != 0:
                raise Exception("Swiss Ephemeris initialization failed")
                
        return True
    except Exception as e:
        st.error(f"Error initializing Swiss Ephemeris: {e}")
        return False

# Initialize ephemeris at startup
if not initialize_ephemeris():
    st.error("Failed to initialize Swiss Ephemeris. Please check ephemeris files.")
    st.stop()

# Planetary cycle characteristics
PLANETARY_CYCLES = {
    "Sun": {"cycle_hours": 24, "major_degrees": [0, 90, 180, 270], "influence": "Major trend direction"},
    "Moon": {"cycle_hours": 2.2, "major_degrees": [0, 90, 180, 270], "influence": "Intraday volatility spikes"},
    "Mercury": {"cycle_hours": 48, "major_degrees": [0, 90, 180, 270], "influence": "News-driven moves"},
    "Venus": {"cycle_hours": 72, "major_degrees": [0, 90, 180, 270], "influence": "Value-based support/resistance"},
    "Mars": {"cycle_hours": 96, "major_degrees": [0, 90, 180, 270], "influence": "Aggressive breakouts/breakdowns"},
    "Jupiter": {"cycle_hours": 168, "major_degrees": [0, 90, 180, 270], "influence": "Major support zones"},
    "Saturn": {"cycle_hours": 336, "major_degrees": [0, 90, 180, 270], "influence": "Strong resistance barriers"},
    "Uranus": {"cycle_hours": 504, "major_degrees": [0, 180], "influence": "Sudden reversals"},
    "Neptune": {"cycle_hours": 720, "major_degrees": [0, 180], "influence": "Deceptive moves"},
    "Pluto": {"cycle_hours": 1440, "major_degrees": [0, 180], "influence": "Transformation levels"}
}

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_planetary_positions(julian_day):
    """Get planetary positions for any date with improved error handling"""
    planets = {
        "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY,
        "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER,
        "Saturn": swe.SATURN, "Uranus": swe.URANUS, "Neptune": swe.NEPTUNE, "Pluto": swe.PLUTO
    }
    
    planet_data = {}
    for name, planet_id in planets.items():
        try:
            # Get planetary position with error handling
            ret = swe.calc_ut(julian_day, planet_id)
            
            # Check for calculation errors
            if len(ret) < 7 or ret[6] != 0:
                st.warning(f"Error calculating {name}: {ret[6] if len(ret) > 6 else 'Unknown error'}")
                # Use default values
                planet_data[name] = {
                    "longitude": 0, "latitude": 0, "distance": 1, 
                    "speed": 0.5, "sign": "Aries", "degree_in_sign": 0, "retrograde": False
                }
                continue
            
            # Extract position data
            longitude = ret[0]
            latitude = ret[1]
            distance = ret[2]
            speed = ret[3]
            
            planet_data[name] = {
                "longitude": longitude,
                "latitude": latitude, 
                "distance": distance,
                "speed": speed,
                "sign": get_zodiac_sign(longitude),
                "degree_in_sign": longitude % 30,
                "retrograde": speed < 0  # Negative speed means retrograde
            }
        except Exception as e:
            st.warning(f"Error calculating {name}: {e}")
            planet_data[name] = {"longitude": 0, "latitude": 0, "distance": 1, 
                                "speed": 0.5, "sign": "Aries", "degree_in_sign": 0, "retrograde": False}
    
    return planet_data

# Add a health check endpoint handler
def handle_health_check():
    """Handle health check requests"""
    try:
        # Test if Swiss Ephemeris is working
        test_jd = swe.julday(2023, 1, 1, 0)
        test_result = swe.calc_ut(test_jd, swe.SUN)
        
        if len(test_result) >= 7 and test_result[6] == 0:
            return True, "OK"
        return False, "Swiss Ephemeris not working properly"
    except Exception as e:
        return False, f"Health check failed: {str(e)}"

# The rest of your functions remain the same
def get_zodiac_sign(longitude):
    """Get zodiac sign from longitude"""
    signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    return signs[int(longitude // 30)]

def calculate_planetary_transits(selected_date, tehran_time):
    """Calculate major planetary transits for the selected date"""
    transits = []
    
    # Convert to UTC
    utc_time = tehran_time - timedelta(hours=3, minutes=30)
    start_jd = swe.julday(utc_time.year, utc_time.month, utc_time.day, 0)
    end_jd = start_jd + 1  # End of day
    
    planets = {
        "Mercury": swe.MERCURY, "Venus": swe.VENUS, "Mars": swe.MARS,
        "Jupiter": swe.JUPITER, "Saturn": swe.SATURN, "Uranus": swe.URANUS,
        "Neptune": swe.NEPTUNE, "Pluto": swe.PLUTO
    }
    
    # Check for sign changes and stations
    for planet_name, planet_id in planets.items():
        try:
            # Get position at start of day
            ret_start = swe.calc_ut(start_jd, planet_id)
            if len(ret_start) < 7 or ret_start[6] != 0:
                continue
                
            lon_start = ret_start[0] % 360
            speed_start = ret_start[3]
            
            # Get position at end of day
            ret_end = swe.calc_ut(end_jd, planet_id)
            if len(ret_end) < 7 or ret_end[6] != 0:
                continue
                
            lon_end = ret_end[0] % 360
            speed_end = ret_end[3]
            
            # Check for sign change
            sign_start = int(lon_start // 30)
            sign_end = int(lon_end // 30)
            
            if sign_start != sign_end:
                # Approximate time of sign change
                sign_change_degree = (sign_end + 1) * 30
                if sign_change_degree > 360:
                    sign_change_degree = 30
                
                # Linear approximation
                total_change = lon_end - lon_start
                if abs(total_change) < 0.001:  # Avoid division by zero
                    continue
                    
                fraction = (sign_change_degree - lon_start) / total_change
                jd_change = start_jd + fraction
                
                # Convert to datetime with error handling
                try:
                    jd_to_dt = swe.jdut1_to_utc(jd_change)
                    if len(jd_to_dt) < 6:
                        continue
                        
                    transit_time = datetime(
                        int(jd_to_dt[0]), int(jd_to_dt[1]), int(jd_to_dt[2]), 
                        int(jd_to_dt[3]), int(jd_to_dt[4]), int(jd_to_dt[5])
                    )
                    
                    # Convert to IST
                    ist_time = transit_time + timedelta(hours=5, minutes=30)
                    
                    transits.append({
                        "time": ist_time,
                        "planet": planet_name,
                        "type": "Sign Change",
                        "description": f"Enters {get_zodiac_sign(sign_change_degree)}",
                        "market_impact": get_sign_change_impact(planet_name, get_zodiac_sign(sign_change_degree))
                    })
                except Exception as e:
                    st.warning(f"Error converting JD to datetime for {planet_name}: {e}")
                    continue
            
            # Check for station (retrograde/direct change)
            if (speed_start < 0 and speed_end > 0) or (speed_start > 0 and speed_end < 0):
                # Station point - simplified calculation
                station_time = tehran_time + timedelta(hours=12)  # Approximate middle of day
                direction = "Direct" if speed_end > 0 else "Retrograde"
                
                transits.append({
                    "time": station_time,
                    "planet": planet_name,
                    "type": "Station",
                    "description": f"Turns {direction}",
                    "market_impact": get_station_impact(planet_name, direction)
                })
                
        except Exception as e:
            st.warning(f"Error calculating transit for {planet_name}: {e}")
            continue
    
    # Sort transits by time
    transits.sort(key=lambda x: x["time"])
    return transits

def get_sign_change_impact(planet, sign):
    """Get market impact of planet entering a sign"""
    impacts = {
        "Mercury": {
            "Aries": "Quick market movements, news-driven volatility",
            "Taurus": "Stable prices, value investing focus",
            "Gemini": "High communication, multiple market narratives",
            "Cancer": "Defensive trading, emotional swings",
            "Leo": "Confident markets, bold moves",
            "Virgo": "Analytical trading, precision entries",
            "Libra": "Balanced markets, partnership deals",
            "Scorpio": "Intense moves, hidden influences",
            "Sagittarius": "Optimistic trends, expansion",
            "Capricorn": "Conservative approach, long-term focus",
            "Aquarius": "Innovative trading, tech focus",
            "Pisces": "Unclear trends, illusionary moves"
        },
        "Venus": {
            "Aries": "Impulsive buying, aggressive value",
            "Taurus": "Strong value support, steady gains",
            "Gemini": "Dual markets, conflicting signals",
            "Cancer": "Protective trading, safe havens",
            "Leo": "Luxury buying, confidence high",
            "Virgo": "Critical value assessment",
            "Libra": "Partnership deals, balanced trades",
            "Scorpio": "Deep value, transformation",
            "Sagittarius": "Optimistic value, growth focus",
            "Capricorn": "Conservative value, long-term",
            "Aquarius": "Innovative value, tech stocks",
            "Pisces": "Illusory value, deception risk"
        }
    }
    
    return impacts.get(planet, {}).get(sign, "Moderate market influence")

def get_station_impact(planet, direction):
    """Get market impact of planetary station"""
    impacts = {
        "Mercury": {
            "Direct": "Clear communication, decisive moves",
            "Retrograde": "Confusion, false signals, delays"
        },
        "Venus": {
            "Direct": "Value appreciation, buying pressure",
            "Retrograde": "Value reassessment, selling pressure"
        },
        "Mars": {
            "Direct": "Aggressive action, momentum builds",
            "Retrograde": "Energy withdrawal, consolidation"
        },
        "Jupiter": {
            "Direct": "Expansion, optimism, growth",
            "Retrograde": "Contraction, reassessment, caution"
        },
        "Saturn": {
            "Direct": "Structure, discipline, restrictions",
            "Retrograde": "Release of pressure, easing"
        }
    }
    
    return impacts.get(planet, {}).get(direction, "Market direction shift")

def calculate_detailed_timing(planet_data, base_time_ist, market_type):
    """Calculate detailed timing events throughout the day"""
    timing_events = []
    
    # Moon phases and aspects (every 30 minutes)
    moon_deg = planet_data["Moon"]["longitude"]
    moon_speed = planet_data["Moon"]["speed"] / 24  # degrees per hour
    
    for minute_offset in range(0, 1440, 30):  # Every 30 minutes for 24 hours
        target_time = base_time_ist + timedelta(minutes=minute_offset)
        
        # Skip if outside market hours
        if not is_within_market_hours(target_time, market_type):
            continue
            
        future_moon_deg = (moon_deg + (moon_speed * minute_offset / 60)) % 360
        
        # Moon phase calculation
        sun_deg = planet_data["Sun"]["longitude"]
        moon_phase_angle = (future_moon_deg - sun_deg) % 360
        
        # Determine moon phase
        if 0 <= moon_phase_angle < 45:
            phase = "New Moon"
            impact = "New beginnings, trend initiation"
        elif 45 <= moon_phase_angle < 90:
            phase = "Waxing Crescent"
            impact = "Building energy, gradual growth"
        elif 90 <= moon_phase_angle < 135:
            phase = "First Quarter"
            impact = "Decision points, action required"
        elif 135 <= moon_phase_angle < 180:
            phase = "Waxing Gibbous"
            impact = "Momentum building, preparation"
        elif 180 <= moon_phase_angle < 225:
            phase = "Full Moon"
            impact = "Culmination, high emotion"
        elif 225 <= moon_phase_angle < 270:
            phase = "Waning Gibbous"
            impact = "Release, sharing results"
        elif 270 <= moon_phase_angle < 315:
            phase = "Last Quarter"
            impact = "Reassessment, letting go"
        else:
            phase = "Waning Crescent"
            impact = "Rest, preparation for new cycle"
        
        # Calculate Moon aspects with other planets
        aspects = []
        for planet_name, planet_info in planet_data.items():
            if planet_name == "Moon":
                continue
                
            planet_deg = planet_info["longitude"]
            angle = abs(future_moon_deg - planet_deg) % 360
            if angle > 180:
                angle = 360 - angle
                
            # Check for major aspects
            if abs(angle - 0) < 2:  # Conjunction
                aspects.append(f"Conjunct {planet_name}")
            elif abs(angle - 60) < 2:  # Sextile
                aspects.append(f"Sextile {planet_name}")
            elif abs(angle - 90) < 2:  # Square
                aspects.append(f"Square {planet_name}")
            elif abs(angle - 120) < 2:  # Trine
                aspects.append(f"Trine {planet_name}")
            elif abs(angle - 180) < 2:  # Opposition
                aspects.append(f"Opposite {planet_name}")
        
        # Add timing event
        timing_events.append({
            "time": target_time,
            "moon_phase": phase,
            "moon_phase_angle": moon_phase_angle,
            "impact": impact,
            "aspects": aspects,
            "intensity": len(aspects) + (1 if phase in ["New Moon", "Full Moon"] else 0)
        })
    
    # Add planetary hour changes
    for hour_offset in range(0, 24):
        target_time = base_time_ist + timedelta(hours=hour_offset)
        
        if not is_within_market_hours(target_time, market_type):
            continue
            
        # Calculate planetary hour ruler
        hour_number = (target_time.hour + target_time.minute / 60) % 24
        planetary_hour_ruler = get_planetary_hour_ruler(hour_number, base_time_ist)
        
        timing_events.append({
            "time": target_time,
            "type": "Planetary Hour",
            "ruler": planetary_hour_ruler,
            "impact": get_planetary_hour_impact(planetary_hour_ruler)
        })
    
    # Sort by time and intensity
    timing_events.sort(key=lambda x: (x["time"], -x.get("intensity", 0)))
    return timing_events

def get_planetary_hour_ruler(hour_number, base_date):
    """Get the planetary ruler for a given hour"""
    # Planetary hour order: Saturn, Jupiter, Mars, Sun, Venus, Mercury, Moon
    planets = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon"]
    
    # Day ruler (based on day of week)
    day_ruler_index = (base_date.weekday() + 1) % 7  # Sunday=0, Monday=1, etc.
    
    # Calculate hour ruler
    hour_ruler_index = int((day_ruler_index + hour_number) % 7)
    return planets[hour_ruler_index]

def get_planetary_hour_impact(planet):
    """Get market impact of planetary hour"""
    impacts = {
        "Saturn": "Restriction, caution, long-term focus",
        "Jupiter": "Expansion, optimism, growth opportunities",
        "Mars": "Action, aggression, momentum trading",
        "Sun": "Confidence, leadership, major moves",
        "Venus": "Value, harmony, relationship-based trades",
        "Mercury": "Communication, news, quick trades",
        "Moon": "Emotion, intuition, retail trading"
    }
    return impacts.get(planet, "Moderate market activity")

def calculate_planetary_price_levels(planet_data, current_price, symbol):
    """Calculate realistic intraday price levels based on actual planetary positions"""
    price_levels = {}
    
    # Real market-based percentage ranges for each planet (more realistic spreads)
    planet_ranges = {
        "Sun": {"major": 1.8, "primary": 0.9, "minor": 0.25},      
        "Moon": {"major": 3.2, "primary": 1.6, "minor": 0.45},    # More volatile
        "Mercury": {"major": 1.5, "primary": 0.7, "minor": 0.2},  
        "Venus": {"major": 2.1, "primary": 1.1, "minor": 0.35},   
        "Mars": {"major": 4.2, "primary": 2.1, "minor": 0.65},    # Most aggressive
        "Jupiter": {"major": 3.8, "primary": 1.9, "minor": 0.55}, # Strong levels
        "Saturn": {"major": 2.9, "primary": 1.45, "minor": 0.4}, 
        "Uranus": {"major": 5.5, "primary": 2.7, "minor": 0.8},   # Most volatile
        "Neptune": {"major": 2.5, "primary": 1.25, "minor": 0.35},
        "Pluto": {"major": 3.5, "primary": 1.75, "minor": 0.5}    
    }
    
    for planet_name, data in planet_data.items():
        if planet_name in PLANETARY_CYCLES:
            ranges = planet_ranges.get(planet_name, {"major": 2.0, "primary": 1.0, "minor": 0.3})
            
            # Calculate unique planetary influence based on actual degree position
            longitude = data["longitude"] % 360
            speed = abs(data["speed"])
            
            # Create unique multipliers for each planet based on their position
            planet_multipliers = {
                "Sun": longitude / 360,
                "Moon": (longitude + 90) / 360,      # Offset by 90°
                "Mercury": (longitude + 45) / 360,    # Offset by 45°  
                "Venus": (longitude + 135) / 360,     # Offset by 135°
                "Mars": (longitude + 180) / 360,      # Opposite to Sun
                "Jupiter": (longitude + 225) / 360,   # Offset by 225°
                "Saturn": (longitude + 270) / 360,    # Offset by 270°
                "Uranus": (longitude + 315) / 360,    # Offset by 315°
                "Neptune": (longitude + 60) / 360,    # Offset by 60°
                "Pluto": (longitude + 120) / 360      # Offset by 120°
            }
            
            # Get unique multiplier for this planet
            base_multiplier = planet_multipliers.get(planet_name, longitude / 360)
            
            # Add speed influence (faster planets = stronger immediate impact)
            speed_influence = min(speed * 5, 30) / 100  # 0 to 30% additional influence
            
            # Combine influences
            total_multiplier = 0.6 + (0.8 * base_multiplier) + speed_influence  # Range: 0.6 to 1.4
            
            # Apply directional bias based on planet characteristics
            directional_bias = {
                "Sun": 0,        # Neutral 
                "Moon": -0.2,    # Slightly bearish (emotional selling)
                "Mercury": 0.1,  # Slightly bullish (news driven)
                "Venus": 0.15,   # Bullish (value attraction)
                "Mars": -0.3,    # Bearish (aggressive selling)
                "Jupiter": 0.25, # Most bullish (expansion)
                "Saturn": -0.4,  # Most bearish (restriction)
                "Uranus": 0,     # Neutral but volatile
                "Neptune": -0.1, # Slightly bearish (confusion)
                "Pluto": 0.05    # Slightly bullish (transformation)
            }
            
            bias = directional_bias.get(planet_name, 0)
            
            # Calculate adjusted ranges with planetary bias
            major_pct = ranges["major"] * total_multiplier
            primary_pct = ranges["primary"] * total_multiplier
            minor_pct = ranges["minor"] * total_multiplier
            
            # Apply directional bias to create asymmetric levels
            resistance_multiplier = 1.0 - bias  # Negative bias = stronger resistance
            support_multiplier = 1.0 + bias     # Positive bias = stronger support
            
            # Calculate actual price levels with realistic spreads
            levels = {
                "Major_Resistance": current_price * (1 + (major_pct * resistance_multiplier)/100),
                "Primary_Resistance": current_price * (1 + (primary_pct * resistance_multiplier)/100),
                "Minor_Resistance": current_price * (1 + (minor_pct * resistance_multiplier)/100),
                "Current_Level": current_price,
                "Minor_Support": current_price * (1 - (minor_pct * support_multiplier)/100),
                "Primary_Support": current_price * (1 - (primary_pct * support_multiplier)/100),
                "Major_Support": current_price * (1 - (major_pct * support_multiplier)/100)
            }
            
            # Calculate planetary strength (0-100%)
            strength = 30 + (speed * 15) + ((360 - (longitude % 30)) / 30 * 25) + (total_multiplier * 30)
            
            price_levels[planet_name] = {
                "current_degree": longitude,
                "speed": data["speed"],
                "sign": f"{data['sign']} {data['degree_in_sign']:.2f}°",
                "levels": levels,
                "influence": PLANETARY_CYCLES[planet_name]["influence"],
                "strength": min(max(strength, 10), 100),  # Bound between 10-100%
                "bias": bias,
                "multiplier": total_multiplier,
                "retrograde": data.get("retrograde", False)
            }
    
    return price_levels

def calculate_time_cycles(planet_data, base_time_ist):
    """Calculate critical planetary time cycles in IST"""
    daily_cycles = []
    
    for planet_name, data in planet_data.items():
        if planet_name in PLANETARY_CYCLES:
            current_degree = data["longitude"] % 360
            speed_per_hour = max(abs(data["speed"]) / 24, 0.001)
            
            for target_degree in PLANETARY_CYCLES[planet_name]["major_degrees"]:
                degrees_to_travel = (target_degree - current_degree) % 360
                if degrees_to_travel > 180:
                    degrees_to_travel = degrees_to_travel - 360
                
                hours_to_target = degrees_to_travel / speed_per_hour
                
                if 0 <= abs(hours_to_target) <= 24:
                    cycle_time = base_time_ist + timedelta(hours=hours_to_target)
                    
                    daily_cycles.append({
                        "planet": planet_name,
                        "target_degree": target_degree,
                        "time_ist": cycle_time,
                        "hours_away": hours_to_target,
                        "market_impact": f"{planet_name} @ {target_degree}° influence",
                        "trading_action": get_trading_action(planet_name, target_degree),
                        "price_effect": get_price_effect(planet_name, target_degree),
                        "strength": max(50 - abs(hours_to_target), 10)
                    })
    
    # Add synthetic cycles if no real cycles found
    if not daily_cycles:
        for i in range(1, 13):
            cycle_time = base_time_ist + timedelta(hours=i)
            daily_cycles.append({
                "planet": "Moon",
                "target_degree": i * 30,
                "time_ist": cycle_time,
                "hours_away": i,
                "market_impact": f"Moon hourly cycle @ {i*30}°",
                "trading_action": "MONITOR market movement",
                "price_effect": "±0.5% to ±1.5%",
                "strength": max(50 - i*3, 10)
            })
    
    return sorted(daily_cycles, key=lambda x: abs(x["hours_away"]))

def get_trading_action(planet, degree):
    """Get specific trading actions for planetary cycles"""
    if planet == "Moon":
        if degree == 0: return "🌑 NEW MOON - Trend initiation"
        elif degree == 90: return "🌓 FIRST QUARTER - Decision point"
        elif degree == 180: return "🌕 FULL MOON - Culmination"
        elif degree == 270: return "🌗 LAST QUARTER - Reassessment"
    elif planet == "Venus":
        if degree in [0, 90]: return "🛒 VALUE BUY - look for entries"
        elif degree == 180: return "🚨 SELL RALLIES - resistance area"
    elif planet == "Mars":
        if degree == 0: return "🚀 MOMENTUM LONG - aggressive entries"
        elif degree in [90, 180]: return "📉 DEFENSIVE SHORT - breakdown"
    elif planet == "Jupiter":
        if degree in [0, 90]: return "📈 MAJOR LONG - trend following"
    elif planet == "Saturn":
        if degree in [90, 180]: return "⛔ SHORT RALLY - major resistance"
    
    return f"MONITOR {planet} influence"

def calculate_intraday_levels(current_price, planet_data, ist_time):
    """Calculate intraday time-based planetary support/resistance levels"""
    intraday_levels = []
    
    # Moon-based levels (every 1.5 hours = Moon moves ~18-20 degrees)
    moon_deg = planet_data["Moon"]["longitude"]
    moon_speed = planet_data["Moon"]["speed"] / 24  # degrees per hour
    
    for hour_offset in range(1, 13):  # Next 12 hours
        target_time = ist_time + timedelta(hours=hour_offset)
        future_moon_deg = (moon_deg + (moon_speed * hour_offset)) % 360
        
        # Calculate price influence based on Moon's position
        moon_influence = math.sin(math.radians(future_moon_deg)) * 0.8  # ±0.8%
        level_price = current_price * (1 + moon_influence/100)
        
        level_type = "Moon Support" if moon_influence < -0.3 else "Moon Resistance" if moon_influence > 0.3 else "Moon Neutral"
        signal = "PRIME SCALP" if abs(moon_influence) > 0.5 else "MONITOR"
        
        intraday_levels.append({
            "time": target_time,
            "price": level_price,
            "planet": "Moon",
            "level_type": level_type,
            "signal": signal,
            "influence_pct": moon_influence
        })
    
    # Mercury-based levels (news and communication cycles)
    mercury_deg = planet_data["Mercury"]["longitude"]
    mercury_speed = planet_data["Mercury"]["speed"] / 24
    
    # Key Mercury times (every 3 hours for news cycles)
    for hour_offset in [2, 5, 8, 11]:
        target_time = ist_time + timedelta(hours=hour_offset)
        future_mercury_deg = (mercury_deg + (mercury_speed * hour_offset)) % 360
        
        # News-based price levels
        news_influence = math.cos(math.radians(future_mercury_deg)) * 0.6  # ±0.6%
        level_price = current_price * (1 + news_influence/100)
        
        intraday_levels.append({
            "time": target_time,
            "price": level_price,
            "planet": "Mercury",
            "level_type": "Mercury Level",
            "signal": "NEWS WATCH" if abs(news_influence) > 0.4 else "MINOR NEWS",
            "influence_pct": news_influence
        })
    
    # Venus-based levels (value zones every 4 hours)
    venus_deg = planet_data["Venus"]["longitude"]
    venus_speed = planet_data["Venus"]["speed"] / 24
    
    for hour_offset in [3, 7, 11]:
        target_time = ist_time + timedelta(hours=hour_offset)
        future_venus_deg = (venus_deg + (venus_speed * hour_offset)) % 360
        
        # Value-based harmonics
        harmony_cycle = future_venus_deg % 60  # Venus 60-degree cycles
        value_influence = math.sin(math.radians(harmony_cycle * 6)) * 0.5  # ±0.5%
        level_price = current_price * (1 + value_influence/100)
        
        signal = "VALUE BUY" if value_influence < -0.2 else "VALUE SELL" if value_influence > 0.2 else "VALUE NEUTRAL"
        
        intraday_levels.append({
            "time": target_time,
            "price": level_price,
            "planet": "Venus",
            "level_type": "Venus Zone",
            "signal": signal,
            "influence_pct": value_influence
        })
    
    # Mars-based levels (aggressive moves every 2 hours)
    mars_deg = planet_data["Mars"]["longitude"]
    mars_speed = planet_data["Mars"]["speed"] / 24
    
    for hour_offset in [1.5, 4.5, 7.5, 10.5]:
        target_time = ist_time + timedelta(hours=hour_offset)
        future_mars_deg = (mars_deg + (mars_speed * hour_offset)) % 360
        
        # Aggressive breakout levels
        mars_tension = math.sin(math.radians(future_mars_deg * 2)) * 1.2  # ±1.2%
        level_price = current_price * (1 + mars_tension/100)
        
        level_type = "Mars Breakout" if mars_tension > 0.7 else "Mars Breakdown" if mars_tension < -0.7 else "Mars Level"
        signal = "MOMENTUM TRADE" if abs(mars_tension) > 0.8 else "WATCH MARS"
        
        intraday_levels.append({
            "time": target_time,
            "price": level_price,
            "planet": "Mars",
            "level_type": level_type,
            "signal": signal,
            "influence_pct": mars_tension
        })
    
    # Jupiter levels (major support zones every 6 hours)
    jupiter_deg = planet_data["Jupiter"]["longitude"]
    
    for hour_offset in [6, 12]:
        target_time = ist_time + timedelta(hours=hour_offset)
        
        # Jupiter creates major support/resistance
        jupiter_influence = 0.8 if hour_offset == 6 else -0.8  # Alternating support/resistance
        level_price = current_price * (1 + jupiter_influence/100)
        
        level_type = "Jupiter Support" if jupiter_influence < 0 else "Jupiter Resistance"
        signal = "MAJOR SUPPORT" if jupiter_influence < 0 else "MAJOR RESISTANCE"
        
        intraday_levels.append({
            "time": target_time,
            "price": level_price,
            "planet": "Jupiter",
            "level_type": level_type,
            "signal": signal,
            "influence_pct": jupiter_influence
        })
    
    return intraday_levels

def identify_trading_zones(price_levels, current_price, intraday_levels):
    """Identify key buy/sell zones and high-probability time windows"""
    
    # Initialize empty lists to prevent NoneType errors
    sell_zones = []
    buy_zones = []
    high_prob_times = []
    
    # Check if price_levels is valid
    if not price_levels or not isinstance(price_levels, dict):
        return sell_zones, buy_zones, high_prob_times
    
    # Collect all resistance levels (sell zones)
    try:
        for planet, data in price_levels.items():
            if not isinstance(data, dict) or "levels" not in data:
                continue
                
            levels = data["levels"]
            strength = data.get("strength", 50)
            
            # Resistance levels above current price (SELL ZONES)
            for level_name in ["Minor_Resistance", "Primary_Resistance", "Major_Resistance"]:
                if level_name in levels:
                    level_price = levels[level_name]
                    if level_price > current_price:
                        distance_pct = ((level_price - current_price) / current_price) * 100
                        zone_strength = "HIGH" if strength > 70 else "MEDIUM" if strength > 50 else "LOW"
                        
                        sell_zones.append({
                            "planet": planet,
                            "level_name": level_name.replace("_", " "),
                            "price": level_price,
                            "distance": level_price - current_price,
                            "distance_pct": distance_pct,
                            "strength": strength,
                            "zone_strength": zone_strength,
                            "priority": 1 if distance_pct <= 1.5 else 2 if distance_pct <= 3.0 else 3
                        })
            
            # Support levels below current price (BUY ZONES)  
            for level_name in ["Minor_Support", "Primary_Support", "Major_Support"]:
                if level_name in levels:
                    level_price = levels[level_name]
                    if level_price < current_price:
                        distance_pct = abs((level_price - current_price) / current_price) * 100
                        zone_strength = "HIGH" if strength > 70 else "MEDIUM" if strength > 50 else "LOW"
                        
                        buy_zones.append({
                            "planet": planet,
                            "level_name": level_name.replace("_", " "),
                            "price": level_price,
                            "distance": current_price - level_price,
                            "distance_pct": distance_pct,
                            "strength": strength,
                            "zone_strength": zone_strength,
                            "priority": 1 if distance_pct <= 1.5 else 2 if distance_pct <= 3.0 else 3
                        })
    except Exception as e:
        st.warning(f"Error processing price levels: {e}")
    
    # Process intraday levels
    if intraday_levels and isinstance(intraday_levels, list):
        try:
            for level in intraday_levels:
                if not isinstance(level, dict):
                    continue
                    
                time_window = level.get("time")
                planet = level.get("planet", "Unknown")
                signal = level.get("signal", "MONITOR")
                influence = abs(level.get("influence_pct", 0))
                
                if not time_window:
                    continue
                
                # Classify time windows by probability
                if influence > 0.7:
                    probability = "VERY HIGH"
                    action_type = "MAJOR TRADE"
                elif influence > 0.5:
                    probability = "HIGH" 
                    action_type = "STRONG TRADE"
                elif influence > 0.3:
                    probability = "MEDIUM"
                    action_type = "MODERATE TRADE"
                else:
                    probability = "LOW"
                    action_type = "WATCH ONLY"
                
                # Determine buy/sell bias
                if "BUY" in signal or "SUPPORT" in signal:
                    bias = "BUY ZONE"
                    zone_color = "🟢"
                elif "SELL" in signal or "RESISTANCE" in signal or "BREAKOUT" in signal:
                    bias = "SELL ZONE" 
                    zone_color = "🔴"
                else:
                    bias = "NEUTRAL ZONE"
                    zone_color = "🟡"
                
                high_prob_times.append({
                    "time": time_window,
                    "planet": planet,
                    "signal": signal,
                    "probability": probability,
                    "action_type": action_type,
                    "bias": bias,
                    "zone_color": zone_color,
                    "influence": influence,
                    "price": level.get("price", current_price)
                })
        except Exception as e:
            st.warning(f"Error processing intraday levels: {e}")
    
    # Sort by priority and distance
    try:
        sell_zones.sort(key=lambda x: (x["priority"], x["distance"]))
        buy_zones.sort(key=lambda x: (x["priority"], x["distance"]))
        high_prob_times.sort(key=lambda x: x["time"])
    except Exception as e:
        st.warning(f"Error sorting zones: {e}")
    
    return sell_zones, buy_zones, high_prob_times

def get_price_effect(planet, degree):
    """Get expected price movement effect"""
    effects = {
        "Moon": "±2% to ±4%", "Mercury": "±1% to ±2%", "Venus": "±1% to ±3%",
        "Mars": "±2% to ±5%", "Jupiter": "±1% to ±4%", "Saturn": "±2% to ±6%",
        "Sun": "±1% to ±3%", "Uranus": "±3% to ±7%", "Neptune": "±1% to ±3%", "Pluto": "±2% to ±5%"
    }
    return effects.get(planet, "±1% to ±2%")

def is_within_market_hours(dt, market_type):
    """Check if datetime is within market hours"""
    t = dt.time()
    if market_type == "Indian":
        start = dt_time(9, 15)
        end = dt_time(15, 30)
        return start <= t <= end
    else:  # Global
        start = dt_time(5, 0)
        end = dt_time(23, 55)
        return start <= t <= end

def generate_planetary_report(symbol, current_price, tehran_time, market_type):
    """Generate focused planetary cycles report for any date"""
    try:
        # Time conversions
        ist_time = tehran_time + timedelta(hours=2)
        utc_time = tehran_time - timedelta(hours=3, minutes=30)
        
        # Get planetary data
        julian_day = swe.julday(utc_time.year, utc_time.month, utc_time.day, 
                               utc_time.hour + utc_time.minute/60 + utc_time.second/3600)
        
        planet_data = get_planetary_positions(julian_day)
        if not planet_data:
            st.error("Failed to get planetary data")
            return None, None, None, None, None, None, None, None, None
            
        price_levels = calculate_planetary_price_levels(planet_data, current_price, symbol)
        daily_cycles = calculate_time_cycles(planet_data, ist_time)
        intraday_levels = calculate_intraday_levels(current_price, planet_data, ist_time)
        planetary_transits = calculate_planetary_transits(tehran_time.date(), tehran_time)
        detailed_timing = calculate_detailed_timing(planet_data, ist_time, market_type)
        
        # Ensure all data structures are valid
        if not price_levels:
            price_levels = {}
        if not daily_cycles:
            daily_cycles = []
        if not intraday_levels:
            intraday_levels = []
        if not planetary_transits:
            planetary_transits = []
        if not detailed_timing:
            detailed_timing = []
        
        # Filter events based on market type
        daily_cycles_filtered = [cycle for cycle in daily_cycles if is_within_market_hours(cycle['time_ist'], market_type)]
        intraday_levels_filtered = [level for level in intraday_levels if is_within_market_hours(level['time'], market_type)]
        transits_filtered = [transit for transit in planetary_transits if is_within_market_hours(transit['time'], market_type)]
        timing_filtered = [timing for timing in detailed_timing if is_within_market_hours(timing['time'], market_type)]
        
        # Get trading zones and high-probability times
        sell_zones, buy_zones, high_prob_times = identify_trading_zones(price_levels, current_price, intraday_levels_filtered)
        
        # Filter high probability times based on market type
        high_prob_times_filtered = [time_window for time_window in high_prob_times if is_within_market_hours(time_window['time'], market_type)]
        
    except Exception as e:
        st.error(f"Error in data calculation: {e}")
        return None, None, None, None, None, None, None, None, None
    
    try:
        # Generate report
        market_hours = "9:15 AM - 3:30 PM" if market_type == "Indian" else "5:00 AM - 11:55 PM"
        report = f"""
# 🌟 Planetary Trading Report - {market_type} Market Hours
## {symbol} Trading - {tehran_time.strftime('%Y-%m-%d')}
### ⏰ Time Base (All times in IST - Indian Standard Time)
- **Tehran Time**: {tehran_time.strftime('%H:%M:%S')} 🇮🇷
- **Indian Standard Time**: **{ist_time.strftime('%H:%M:%S')}** 🇮🇳  
- **Market Hours**: **{market_hours}**
- **Current {symbol} Price**: **{current_price:,.0f}**
---
## 🌟 Planetary Positions at Report Time
| Planet      | Longitude (°) | Sign & Degree | Speed (°/day) | Distance (AU) | Motion |
|-------------|---------------|---------------|---------------|---------------|--------|"""
        
        if planet_data:
            for planet_name, data in planet_data.items():
                try:
                    motion = "Retrograde ♃" if data.get("retrograde", False) else "Direct ♈"
                    report += f"""
| **{planet_name}** | {data['longitude']:.2f}° | {data['sign']} | {data['speed']:.4f} | {data['distance']:.3f} | {motion} |"""
                except Exception as e:
                    st.warning(f"Error processing planet {planet_name}: {e}")
                    continue
        else:
            report += """
| No data | - | - | - | - | - |"""
        
        # Planetary Transits Section
        report += f"""
---
## 🔄 Today's Major Planetary Transits
| Time (IST) | Planet | Transit Type | Description | Market Impact |
|------------|--------|---------------|-------------|---------------|"""
        
        if transits_filtered:
            for transit in transits_filtered:
                try:
                    time_str = transit["time"].strftime("%H:%M")
                    report += f"""
| **{time_str}** | {transit['planet']} | {transit['type']} | {transit['description']} | {transit['market_impact']} |"""
                except Exception as e:
                    continue
        else:
            report += """
| No major transits today | - | - | - | - |"""
        
        # Detailed Timing Section
        report += f"""
---
## ⏱️ Detailed Timing Schedule
| Time (IST) | Event Type | Details | Market Impact | Intensity |
|------------|------------|---------|---------------|-----------|"""
        
        if timing_filtered:
            for timing in timing_filtered[:15]:  # Show top 15 timing events
                try:
                    time_str = timing["time"].strftime("%H:%M")
                    
                    if "moon_phase" in timing:
                        event_type = f"🌙 {timing['moon_phase']}"
                        details = f"{timing['moon_phase_angle']:.1f}°"
                        if timing.get("aspects"):
                            details += f" | {', '.join(timing['aspects'][:2])}"  # Show first 2 aspects
                        impact = timing["impact"]
                        intensity = "🔥" + "🔥" * min(timing.get("intensity", 1), 3)
                    else:
                        event_type = f"⏰ {timing['type']}"
                        details = f"Ruled by {timing['ruler']}"
                        impact = timing["impact"]
                        intensity = "⭐" * min(timing.get("intensity", 1), 3)
                    
                    report += f"""
| **{time_str}** | {event_type} | {details} | {impact} | {intensity} |"""
                except Exception as e:
                    continue
        else:
            report += """
| No timing events | - | - | - | - |"""
        
        report += f"""
---
## 🎯 Planetary Price Levels (Based on Current Positions)
| Planet | Position | Major Resist | Primary Resist | Current | Primary Support | Major Support | Strength |
|--------|----------|--------------|----------------|---------|-----------------|---------------|----------|"""
        
        if price_levels:
            for planet_name, data in price_levels.items():
                try:
                    levels = data.get("levels", {})
                    sign = data.get("sign", "Unknown")
                    strength = data.get("strength", 50)
                    
                    report += f"""
| **{planet_name}** | {sign} | {levels.get('Major_Resistance', current_price):,.0f} | {levels.get('Primary_Resistance', current_price):,.0f} | {levels.get('Current_Level', current_price):,.0f} | {levels.get('Primary_Support', current_price):,.0f} | {levels.get('Major_Support', current_price):,.0f} | {strength:.0f}% |"""
                except Exception as e:
                    st.warning(f"Error processing planet {planet_name}: {e}")
                    continue
        else:
            report += """
| No data | - | - | - | - | - | - |"""
        
        # Intraday time-based planetary levels
        report += f"""
---
## ⏰ Intraday Time-Based Planetary Levels (IST)
| Time (IST) | Price Level | Planet Level | Trading Signal | Influence |
|------------|-------------|--------------|----------------|-----------|"""
        
        if intraday_levels_filtered:
            for level in intraday_levels_filtered[:15]:  # Show next 15 time-based levels
                try:
                    time_str = level["time"].strftime("%H:%M")
                    influence_str = f"{level['influence_pct']:+.2f}%"
                    
                    report += f"""
| **{time_str}** | {level['price']:,.0f} | {level['planet']} {level['level_type']} | {level['signal']} | {influence_str} |"""
                except Exception as e:
                    continue
        else:
            report += """
| No intraday levels | - | - | - | - |"""
        
        # Day Resistance Sell Zones (Highlighted)
        report += f"""
---
## 🔴 RESISTANCE LEVELS - SELL ZONES
| Priority | Planet Level | Price | Distance | Strength | Zone Quality | Action |
|----------|--------------|-------|----------|----------|--------------|--------|"""
        
        if sell_zones:
            for zone in sell_zones[:8]:  # Top 8 sell zones
                try:
                    priority_emoji = "🚨" if zone["priority"] == 1 else "⚠️" if zone["priority"] == 2 else "📊"
                    action = f"🔴 SELL at {zone['price']:,.0f}" if zone["priority"] <= 2 else "🟡 MONITOR"
                    
                    report += f"""
| {priority_emoji} P{zone['priority']} | {zone['planet']} {zone['level_name']} | **{zone['price']:,.0f}** | +{zone['distance']:,.0f} (+{zone['distance_pct']:.2f}%) | {zone['strength']:.0f}% | {zone['zone_strength']} | {action} |"""
                except Exception as e:
                    continue
        else:
            report += """
| No sell zones | - | - | - | - | - | - |"""
        
        # Day Support Buy Zones (Highlighted)
        report += f"""
---
## 🟢 SUPPORT LEVELS - BUY ZONES
| Priority | Planet Level | Price | Distance | Strength | Zone Quality | Action |
|----------|--------------|-------|----------|----------|--------------|--------|"""
        
        if buy_zones:
            for zone in buy_zones[:8]:  # Top 8 buy zones
                try:
                    priority_emoji = "🚨" if zone["priority"] == 1 else "⚠️" if zone["priority"] == 2 else "📊"
                    action = f"🟢 BUY at {zone['price']:,.0f}" if zone["priority"] <= 2 else "🟡 MONITOR"
                    
                    report += f"""
| {priority_emoji} P{zone['priority']} | {zone['planet']} {zone['level_name']} | **{zone['price']:,.0f}** | -{zone['distance']:,.0f} (-{zone['distance_pct']:.2f}%) | {zone['strength']:.0f}% | {zone['zone_strength']} | {action} |"""
                except Exception as e:
                    continue
        else:
            report += """
| No buy zones | - | - | - | - | - | - |"""
        
        # High Probability Time Windows
        report += f"""
---
## ⏰ HIGH PROBABILITY TIME WINDOWS - BUY/SELL ZONES
| Time (IST) | Zone Type | Planet Signal | Probability | Action Type | Price Target | Trade Setup |
|------------|-----------|---------------|-------------|-------------|--------------|-------------|"""
        
        if high_prob_times_filtered:
            for time_window in high_prob_times_filtered[:12]:  # Next 12 high-probability windows
                try:
                    time_str = time_window["time"].strftime("%H:%M")
                    
                    trade_setup = ""
                    if time_window["probability"] == "VERY HIGH":
                        trade_setup = "🔥 PRIME ENTRY"
                    elif time_window["probability"] == "HIGH":
                        trade_setup = "⚡ STRONG SIGNAL"
                    elif time_window["probability"] == "MEDIUM":
                        trade_setup = "📊 MODERATE SIGNAL"
                    else:
                        trade_setup = "👀 WATCH ONLY"
                    
                    report += f"""
| **{time_str}** | {time_window['zone_color']} {time_window['bias']} | {time_window['planet']} {time_window['signal']} | {time_window['probability']} | {time_window['action_type']} | {time_window['price']:,.0f} | {trade_setup} |"""
                except Exception as e:
                    continue
        else:
            report += """
| No time windows | - | - | - | - | - | - |"""
        
        # Today's critical time cycles
        report += f"""
---
## ⏱️ Critical Planetary Time Cycles (IST)
| Time (IST) | Planet | Event | Trading Action | Expected Move | Hours Away |
|------------|--------|-------|----------------|---------------|------------|"""
        
        if daily_cycles_filtered:
            for cycle in daily_cycles_filtered[:10]:
                try:
                    time_str = cycle["time_ist"].strftime("%H:%M")
                    hours_str = f"{cycle['hours_away']:+.1f}h"
                    
                    report += f"""
| **{time_str}** | {cycle['planet']} | @ {cycle['target_degree']:.0f}° | {cycle['trading_action']} | {cycle['price_effect']} | {hours_str} |"""
                except Exception as e:
                    continue
        else:
            report += """
| No major cycles today | - | - | - | - | - |"""
        
        # Add summary
        strongest_planet = "Sun"  # Default
        if price_levels:
            try:
                strongest_planet = max(price_levels.items(), key=lambda x: x[1].get('strength', 0))[0]
            except:
                strongest_planet = "Sun"
        
        next_event_text = "No major events today"
        if daily_cycles_filtered:
            try:
                next_event_text = f"{daily_cycles_filtered[0]['time_ist'].strftime('%H:%M IST')} - {daily_cycles_filtered[0]['planet']} @ {daily_cycles_filtered[0]['target_degree']:.0f}°"
            except:
                pass
        
        # Add planetary aspects summary
        aspects_summary = calculate_planetary_aspects(planet_data)
        
        report += f"""
---
## 🔗 Key Planetary Aspects
| Aspect | Planets | Angle (°) | Orb (°) | Market Influence |
|--------|---------|-----------|---------|-----------------|"""
        
        if aspects_summary:
            for aspect in aspects_summary[:8]:
                try:
                    report += f"""
| {aspect['type']} | {aspect['planets']} | {aspect['angle']:.1f}° | {aspect['orb']:.1f}° | {aspect['influence']} |"""
                except Exception as e:
                    continue
        else:
            report += """
| No major aspects | - | - | - | - |"""
        
        report += f"""
---
## 💡 Key Insights for {tehran_time.strftime('%Y-%m-%d')}
### 🎯 Dominant Influence: **{strongest_planet}**
- **Primary Action**: Focus on {strongest_planet.lower()} levels for best trades
### 📊 Trading Summary:
- **Sell Zones**: {len(sell_zones)} resistance levels identified
- **Buy Zones**: {len(buy_zones)} support levels identified  
- **High Prob Windows**: {len(high_prob_times_filtered)} time-based opportunities
- **Active Cycles**: {len(daily_cycles_filtered)} planetary events today
- **Major Transits**: {len(transits_filtered)} significant transits today
- **Timing Events**: {len(timing_filtered)} detailed timing events
---
> **🚨 Next Major Event**: {next_event_text}
"""
        
        return report, price_levels, daily_cycles_filtered, intraday_levels_filtered, sell_zones, buy_zones, high_prob_times_filtered, transits_filtered, timing_filtered
        
    except Exception as e:
        st.error(f"Error generating report: {e}")
        return None, None, None, None, None, None, None, None, None

def calculate_planetary_aspects(planet_data):
    """Calculate major planetary aspects"""
    aspects = []
    
    # Define aspect types and their orbs
    aspect_types = {
        "Conjunction": {"angle": 0, "orb": 8},
        "Opposition": {"angle": 180, "orb": 8},
        "Trine": {"angle": 120, "orb": 8},
        "Square": {"angle": 90, "orb": 8},
        "Sextile": {"angle": 60, "orb": 6}
    }
    
    planets = list(planet_data.keys())
    
    for i in range(len(planets)):
        for j in range(i+1, len(planets)):
            planet1 = planets[i]
            planet2 = planets[j]
            
            try:
                lon1 = planet_data[planet1]["longitude"] % 360
                lon2 = planet_data[planet2]["longitude"] % 360
                
                # Calculate angular separation
                separation = abs(lon1 - lon2)
                if separation > 180:
                    separation = 360 - separation
                
                # Check for aspects
                for aspect_name, aspect_data in aspect_types.items():
                    orb = abs(separation - aspect_data["angle"])
                    if orb <= aspect_data["orb"]:
                        # Determine influence based on planets and aspect
                        influence = get_aspect_influence(planet1, planet2, aspect_name)
                        
                        aspects.append({
                            "type": aspect_name,
                            "planets": f"{planet1} - {planet2}",
                            "angle": separation,
                            "orb": orb,
                            "influence": influence
                        })
            except Exception as e:
                continue
    
    # Sort by orb (tightest aspects first)
    aspects.sort(key=lambda x: x["orb"])
    return aspects

def get_aspect_influence(planet1, planet2, aspect_type):
    """Get market influence description for planetary aspects"""
    # Define influences based on planet combinations and aspect types
    influences = {
        ("Mars", "Saturn", "Opposition"): "Strong bearish pressure, major resistance",
        ("Venus", "Jupiter", "Conjunction"): "Bullish support, value buying",
        ("Sun", "Moon", "Conjunction"): "New energy, trend initiation",
        ("Mercury", "Mars", "Square"): "News-driven volatility, sharp moves",
        ("Jupiter", "Saturn", "Square"): "Market structural changes",
        ("Uranus", "Pluto", "Conjunction"): "Transformational shifts",
    }
    
    # Default influence if not specifically defined
    default_influences = {
        "Conjunction": "Combined energies, new beginnings",
        "Opposition": "Tension, polarity, turning points",
        "Trine": "Harmony, flow, positive developments",
        "Square": "Challenge, friction, action required",
        "Sextile": "Opportunity, cooperation, ease"
    }
    
    # Check for specific combination
    key = (planet1, planet2, aspect_type)
    if key in influences:
        return influences[key]
    
    # Check reverse order
    key = (planet2, planet1, aspect_type)
    if key in influences:
        return influences[key]
    
    # Return default influence for aspect type
    return default_influences.get(aspect_type, "Moderate market influence")

# Streamlit App
st.set_page_config(layout="wide", page_title="Planetary Trading Reports")
st.title("🌟 Planetary Trading Reports - Any Date Analysis")
st.markdown("*Generate planetary trading reports for any date and time with precise support/resistance levels*")

# Add a health check status indicator
health_status, health_message = handle_health_check()
if health_status:
    st.success(f"✅ System Status: {health_message}")
else:
    st.error(f"❌ System Status: {health_message}")

# Input section
col1, col2, col3 = st.columns(3)
with col1:
    symbol = st.text_input("Symbol", value="NIFTY", help="Trading symbol (NIFTY, BANKNIFTY, GOLD, etc.)")
    
with col2:
    current_price = st.number_input("Current Price", value=24594.0, step=0.1, help="Current market price")
    
with col3:
    market_type = st.selectbox("Market Type", ["Indian", "Global"], 
                              help="Indian Market: 9:15 AM - 3:30 PM IST | Global Market: 5:00 AM - 11:55 PM IST")

# Date and time selection
st.markdown("### 📅 Select Date and Time for Analysis")
col1, col2 = st.columns(2)
with col1:
    selected_date = st.date_input(
        "Select Date",
        datetime.now().date(),
        min_value=datetime(2020, 1, 1).date(),
        max_value=datetime(2030, 12, 31).date(),
        help="Choose any date between 2020 and 2030"
    )
with col2:
    selected_time = st.time_input(
        "Select Time (Tehran Time)",
        datetime.now().time(),
        help="Time in Tehran timezone (IST = Tehran + 2 hours)"
    )

# Combine date and time
tehran_time = datetime.combine(selected_date, selected_time)

# Quick date presets
st.markdown("### 🗓️ Quick Date Presets")
preset_col1, preset_col2, preset_col3, preset_col4, preset_col5 = st.columns(5)
with preset_col1:
    if st.button("Aug 6, 2025"):
        selected_date = datetime(2025, 8, 6).date()
        tehran_time = datetime.combine(selected_date, datetime.now().time())
        st.rerun()
with preset_col2:
    if st.button("Aug 11, 2025"):
        selected_date = datetime(2025, 8, 11).date()
        tehran_time = datetime.combine(selected_date, datetime.now().time())
        st.rerun()
with preset_col3:
    if st.button("Aug 15, 2025"):
        selected_date = datetime(2025, 8, 15).date()
        tehran_time = datetime.combine(selected_date, datetime.now().time())
        st.rerun()
with preset_col4:
    if st.button("Dec 31, 2025"):
        selected_date = datetime(2025, 12, 31).date()
        tehran_time = datetime.combine(selected_date, datetime.now().time())
        st.rerun()
with preset_col5:
    if st.button("Dec 31, 2026"):
        selected_date = datetime(2026, 12, 31).date()
        tehran_time = datetime.combine(selected_date, datetime.now().time())
        st.rerun()

# Generate report
if st.button("🚀 Generate Planetary Report", type="primary"):
    try:
        with st.spinner("🌌 Calculating planetary positions, transits and timing..."):
            start_time = time_module.time()
            report, price_levels, daily_cycles, intraday_levels, sell_zones, buy_zones, high_prob_times, transits, timing = generate_planetary_report(
                symbol, current_price, tehran_time, market_type)
            elapsed_time = time_module.time() - start_time
            
        st.success(f"✅ Report generated in {elapsed_time:.2f} seconds")
        
        # Display main report
        st.markdown(report)
        
        # Highlighted Trading Zones
        st.markdown("### 🎯 KEY TRADING ZONES SUMMARY")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🔴 RESISTANCE SELL ZONES")
            if sell_zones:
                for i, zone in enumerate(sell_zones[:4]):  # Top 4 sell zones
                    priority_color = "🚨" if zone["priority"] == 1 else "⚠️" if zone["priority"] == 2 else "📊"
                    
                    with st.container():
                        st.markdown(f"""
                        <div style="background-color:#ffe6e6; padding:10px; border-radius:5px; margin:5px 0; border-left:4px solid #ff4444;">
                        <strong>{priority_color} {zone['planet']} {zone['level_name']}</strong><br>
                        <span style="font-size:1.2em; color:#d63384;"><strong>{zone['price']:,.0f}</strong></span> 
                        <span style="color:#6c757d;">(+{zone['distance_pct']:.2f}%)</span><br>
                        <span style="font-size:0.9em;">Strength: {zone['strength']:.0f}% | Quality: {zone['zone_strength']}</span>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("No immediate resistance levels")
        
        with col2:
            st.markdown("#### 🟢 SUPPORT BUY ZONES")
            if buy_zones:
                for i, zone in enumerate(buy_zones[:4]):  # Top 4 buy zones
                    priority_color = "🚨" if zone["priority"] == 1 else "⚠️" if zone["priority"] == 2 else "📊"
                    
                    with st.container():
                        st.markdown(f"""
                        <div style="background-color:#e6f7e6; padding:10px; border-radius:5px; margin:5px 0; border-left:4px solid #44ff44;">
                        <strong>{priority_color} {zone['planet']} {zone['level_name']}</strong><br>
                        <span style="font-size:1.2em; color:#198754;"><strong>{zone['price']:,.0f}</strong></span> 
                        <span style="color:#6c757d;">(-{zone['distance_pct']:.2f}%)</span><br>
                        <span style="font-size:0.9em;">Strength: {zone['strength']:.0f}% | Quality: {zone['zone_strength']}</span>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("No immediate support levels")
        
        # Simple chart
        st.markdown("### 📊 Support/Resistance Levels with Buy/Sell Zones")
        
        fig = go.Figure()
        
        # Add support levels (green)
        support_prices = []
        support_labels = []
        for zone in buy_zones[:5]:
            support_prices.append(zone["price"])
            support_labels.append(f"{zone['planet']} {zone['level_name']}")
        
        if support_prices:
            fig.add_trace(go.Scatter(
                x=support_labels,
                y=support_prices,
                mode='markers',
                marker=dict(size=15, color='green', symbol='triangle-up'),
                name='🟢 BUY ZONES',
                text=[f"{p:,.0f}" for p in support_prices],
                textposition="middle center"
            ))
        
        # Add resistance levels (red)
        resistance_prices = []
        resistance_labels = []
        for zone in sell_zones[:5]:
            resistance_prices.append(zone["price"])
            resistance_labels.append(f"{zone['planet']} {zone['level_name']}")
        
        if resistance_prices:
            fig.add_trace(go.Scatter(
                x=resistance_labels,
                y=resistance_prices,
                mode='markers',
                marker=dict(size=15, color='red', symbol='triangle-down'),
                name='🔴 SELL ZONES',
                text=[f"{p:,.0f}" for p in resistance_prices],
                textposition="middle center"
            ))
        
        # Add current price line
        fig.add_hline(y=current_price, line_dash="dash", line_color="orange", line_width=3,
                      annotation_text=f"Current: {current_price:,.0f}")
        
        # Add buy/sell zones as colored areas
        if support_prices:
            min_support = min(support_prices)
            fig.add_hrect(y0=min_support*0.995, y1=min_support*1.005, 
                         fillcolor="green", opacity=0.2, 
                         annotation_text="🟢 STRONG BUY ZONE", annotation_position="top left")
        
        if resistance_prices:
            max_resistance = max(resistance_prices)
            fig.add_hrect(y0=max_resistance*0.995, y1=max_resistance*1.005, 
                         fillcolor="red", opacity=0.2,
                         annotation_text="🔴 STRONG SELL ZONE", annotation_position="bottom left")
        
        fig.update_layout(
            title=f"{symbol} Buy/Sell Zones with Planetary Levels", 
            height=500,
            yaxis_title="Price Points",
            xaxis_title="Planetary Levels"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # High Probability Time Windows
        st.markdown("### ⏰ HIGH PROBABILITY TIME WINDOWS")
        
        # Create columns for time windows
        time_cols = st.columns(4)
        
        for i, time_window in enumerate(high_prob_times[:8]):  # Next 8 high probability windows
            col = time_cols[i % 4]
            
            with col:
                time_str = time_window["time"].strftime("%H:%M")
                zone_color = time_window["zone_color"] 
                bias = time_window["bias"]
                probability = time_window["probability"]
                
                # Color coding based on zone type
                if "BUY" in bias:
                    card_color = "#d4edda"  # Light green
                    border_color = "#28a745"
                elif "SELL" in bias:
                    card_color = "#f8d7da"  # Light red
                    border_color = "#dc3545" 
                else:
                    card_color = "#fff3cd"  # Light yellow
                    border_color = "#ffc107"
                
                st.markdown(f"""
                <div style="background-color:{card_color}; padding:10px; border-radius:8px; margin:5px 0; border:2px solid {border_color};">
                <div style="text-align:center;">
                <strong style="font-size:1.1em;">🕐 {time_str} IST</strong><br>
                <span style="font-size:1.2em;">{zone_color} <strong>{bias}</strong></span><br>
                <span style="color:#666; font-size:0.9em;">{time_window['planet']} | {probability}</span><br>
                <span style="font-size:1.1em; font-weight:bold;">{time_window['price']:,.0f}</span>
                </div>
                </div>
                """, unsafe_allow_html=True)
        
        # Highlight next few intraday levels
        st.markdown("### ⏰ Next Intraday Trading Levels")
        
        col1, col2, col3 = st.columns(3)
        
        # Show next 6 intraday levels in a nice format
        for i, level in enumerate(intraday_levels[:6]):
            col = [col1, col2, col3][i % 3]
            
            with col:
                time_str = level["time"].strftime("%H:%M IST")
                price_str = f"{level['price']:,.0f}"
                planet_level = f"{level['planet']} {level['level_type'].split()[1] if len(level['level_type'].split()) > 1 else level['level_type']}"
                signal = level['signal']
                
                # Create colored metric based on signal type
                if "BUY" in signal or "SUPPORT" in signal:
                    delta_color = "normal"
                elif "SELL" in signal or "RESISTANCE" in signal:
                    delta_color = "inverse" 
                else:
                    delta_color = "off"
                
                st.metric(
                    label=f"🕐 {time_str}",
                    value=price_str,
                    delta=f"{planet_level} - {signal}",
                    delta_color=delta_color
                )
        
        # Major Transits Section
        st.markdown("### 🔄 Today's Major Planetary Transits")
        
        if transits:
            transit_cols = st.columns(3)
            for i, transit in enumerate(transits[:6]):
                col = transit_cols[i % 3]
                
                with col:
                    time_str = transit["time"].strftime("%H:%M")
                    transit_type = transit["type"]
                    description = transit["description"]
                    impact = transit["market_impact"]
                    
                    # Color coding based on transit type
                    if "Sign Change" in transit_type:
                        card_color = "#e3f2fd"  # Light blue
                        border_color = "#2196f3"
                    elif "Station" in transit_type:
                        card_color = "#fff3e0"  # Light orange
                        border_color = "#ff9800"
                    else:
                        card_color = "#f3e5f5"  # Light purple
                        border_color = "#9c27b0"
                    
                    st.markdown(f"""
                    <div style="background-color:{card_color}; padding:10px; border-radius:8px; margin:5px 0; border:2px solid {border_color};">
                    <div style="text-align:center;">
                    <strong style="font-size:1.1em;">🕐 {time_str} IST</strong><br>
                    <span style="font-size:1.0em;"><strong>{transit['planet']}</strong></span><br>
                    <span style="color:#666; font-size:0.9em;">{transit_type}</span><br>
                    <span style="font-size:0.9em;">{description}</span><br>
                    <span style="font-size:0.8em; color:#555;">{impact}</span>
                    </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No major transits today")
        
        # Detailed Timing Events
        st.markdown("### ⏱️ Detailed Timing Events")
        
        if timing:
            timing_cols = st.columns(4)
            for i, timing_event in enumerate(timing[:8]):
                col = timing_cols[i % 4]
                
                with col:
                    time_str = timing_event["time"].strftime("%H:%M")
                    
                    if "moon_phase" in timing_event:
                        event_type = f"🌙 {timing_event['moon_phase']}"
                        details = f"{timing_event['moon_phase_angle']:.1f}°"
                        if timing_event.get("aspects"):
                            details += f"<br>{', '.join(timing_event['aspects'][:2])}"
                        impact = timing_event["impact"]
                    else:
                        event_type = f"⏰ {timing_event['type']}"
                        details = f"Ruled by {timing_event['ruler']}"
                        impact = timing_event["impact"]
                    
                    # Color coding based on intensity
                    intensity = timing_event.get("intensity", 1)
                    if intensity >= 3:
                        card_color = "#ffebee"  # Light red
                        border_color = "#f44336"
                    elif intensity >= 2:
                        card_color = "#fff8e1"  # Light yellow
                        border_color = "#ffc107"
                    else:
                        card_color = "#e8f5e8"  # Light green
                        border_color = "#4caf50"
                    
                    st.markdown(f"""
                    <div style="background-color:{card_color}; padding:10px; border-radius:8px; margin:5px 0; border:2px solid {border_color};">
                    <div style="text-align:center;">
                    <strong style="font-size:1.1em;">🕐 {time_str} IST</strong><br>
                    <span style="font-size:1.0em;"><strong>{event_type}</strong></span><br>
                    <span style="color:#666; font-size:0.8em;">{details}</span><br>
                    <span style="font-size:0.8em; color:#555;">{impact}</span>
                    </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No timing events today")
        
    except Exception as e:
        st.error(f"❌ Error: {e}")

# Sidebar
with st.sidebar:
    st.markdown("### 🌍 Date Selection")
    st.markdown("""
    **Select any date between:**
    - January 1, 2020
    - December 31, 2030
    
    **Quick Presets Available:**
    - Aug 6, 2025
    - Aug 11, 2025
    - Aug 15, 2025
    - Dec 31, 2025
    - Dec 31, 2026
    """)
    
    st.markdown("### 🇮🇳 Market Types")
    st.markdown("""
    **Indian Market:** 9:15 AM - 3:30 PM IST
    **Global Market:** 5:00 AM - 11:55 PM IST
    
    **Current Selection:** """ + market_type)
    
    st.markdown("### 🌟 Report Features")
    st.markdown("""
    **For Any Selected Date:**
    - 🌍 **Planetary Positions** - Exact degrees
    - 🔄 **Planetary Transits** - Sign changes, stations
    - ⏱️ **Detailed Timing** - Moon phases, hours
    - 📊 **Price Levels** - Support/Resistance
    - ⏰ **Time Cycles** - Trading windows
    - 🔗 **Planetary Aspects** - Market influences
    - 🎯 **Buy/Sell Zones** - Action signals
    """)
    
    st.markdown("### 📈 Trading Zone Guide")
    st.markdown("""
    **Priority Levels:**
    - 🚨 **P1** - Immediate action (±1.5%)
    - ⚠️ **P2** - Strong signal (±3.0%) 
    - 📊 **P3** - Monitor level (>3.0%)
    
    **Zone Quality:**
    - **HIGH** - Strength >70%
    - **MEDIUM** - Strength 50-70%
    - **LOW** - Strength <50%
    """)
    
    st.markdown("### ⏰ Time Window Types")
    st.markdown("""
    **Probability Levels:**
    - 🔥 **VERY HIGH** - Prime entries (>0.7%)
    - ⚡ **HIGH** - Strong signals (>0.5%)
    - 📊 **MEDIUM** - Moderate trades (>0.3%)
    - 👀 **LOW** - Watch only (<0.3%)
    
    **Planetary Cycles:**
    - 🌙 **Moon**: 1.5h - Scalping zones
    - ☿ **Mercury**: 3h - News impact zones
    - ♀ **Venus**: 4h - Value trading zones
    - ♂ **Mars**: 2h - Breakout zones
    - ♃ **Jupiter**: 6h - Major support/resistance
    """)
    
    st.markdown("### 🔄 Planetary Transits")
    st.markdown("""
    **Major Transit Types:**
    - **Sign Changes**: Planet enters new sign
    - **Stations**: Planet turns retrograde/direct
    
    **Market Impact:**
    - **Sign Changes**: New market themes
    - **Stations**: Direction shifts, reversals
    - **Combined**: Major trend changes
    
    **Key Planets:**
    - **Mercury**: Communication, news
    - **Venus**: Value, relationships
    - **Mars**: Action, aggression
    - **Jupiter**: Expansion, optimism
    - **Saturn**: Structure, restriction
    """)
    
    st.markdown("### ⏱️ Detailed Timing")
    st.markdown("""
    **Timing Events Include:**
    - **Moon Phases**: New, Full, Quarters
    - **Moon Aspects**: With other planets
    - **Planetary Hours**: Ruler changes
    - **Intensity Levels**: Based on aspects
    
    **Moon Phases:**
    - **New Moon**: Trend initiation
    - **Full Moon**: Culmination, emotion
    - **Quarters**: Decision points
    
    **Intensity Scale:**
    - 🔥🔥🔥 High intensity
    - 🔥🔥 Medium intensity
    - 🔥 Low intensity
    """)
    
    st.markdown("### 🔗 Planetary Aspects")
    st.markdown("""
    **Major Aspects:**
    - **Conjunction** (0°): New beginnings
    - **Opposition** (180°): Turning points
    - **Trine** (120°): Harmonious flow
    - **Square** (90°): Challenges/action
    - **Sextile** (60°): Opportunities
    
    **Key Combinations:**
    - Mars-Saturn: Bearish pressure
    - Venus-Jupiter: Bullish support
    - Sun-Moon: Trend initiation
    """)
    
    st.markdown("### ⚠️ Risk Management")
    st.markdown("""
    - Use **stop losses** at next level
    - **Position size** based on zone strength
    - **Time windows** show best entry/exit
    - **Multiple confirmations** for major trades
    - **Date-specific** planetary influences
    - **Transit timing** for major moves
    """)
