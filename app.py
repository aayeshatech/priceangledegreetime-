import streamlit as st
import swisseph as swe
from datetime import datetime, timedelta
import time
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import math

# Initialize ephemeris
try:
    swe.set_ephe_path(None)
except Exception as e:
    st.error(f"Error initializing Swiss Ephemeris: {e}")
    st.stop()

# Enhanced planetary cycle characteristics with intraday levels
PLANETARY_CYCLES = {
    "Sun": {"cycle_hours": 24, "major_degrees": [0, 30, 45, 60, 90, 120, 135, 150, 180, 210, 225, 240, 270, 300, 315, 330], "price_multiplier": 24.5, "influence": "Major trend direction"},
    "Moon": {"cycle_hours": 2.2, "major_degrees": [0, 15, 30, 45, 60, 75, 90, 105, 120, 135, 150, 165, 180, 195, 210, 225, 240, 255, 270, 285, 300, 315, 330, 345], "price_multiplier": 18.7, "influence": "Intraday volatility spikes"},
    "Mercury": {"cycle_hours": 48, "major_degrees": [0, 22.5, 45, 67.5, 90, 112.5, 135, 157.5, 180, 202.5, 225, 247.5, 270, 292.5, 315, 337.5], "price_multiplier": 21.3, "influence": "News-driven moves"},
    "Venus": {"cycle_hours": 72, "major_degrees": [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330], "price_multiplier": 26.8, "influence": "Value-based support/resistance"},
    "Mars": {"cycle_hours": 96, "major_degrees": [0, 45, 90, 135, 180, 225, 270, 315], "price_multiplier": 19.2, "influence": "Aggressive breakouts/breakdowns"},
    "Jupiter": {"cycle_hours": 168, "major_degrees": [0, 60, 120, 180, 240, 300], "price_multiplier": 31.4, "influence": "Major support zones"},
    "Saturn": {"cycle_hours": 336, "major_degrees": [0, 45, 90, 135, 180, 225, 270, 315], "price_multiplier": 15.9, "influence": "Strong resistance barriers"},
    "Uranus": {"cycle_hours": 504, "major_degrees": [0, 90, 180, 270], "price_multiplier": 22.1, "influence": "Sudden reversals"},
    "Neptune": {"cycle_hours": 720, "major_degrees": [0, 120, 240], "price_multiplier": 17.6, "influence": "Deceptive moves"},
    "Pluto": {"cycle_hours": 1440, "major_degrees": [0, 90, 180, 270], "price_multiplier": 28.3, "influence": "Transformation levels"}
}

@st.cache_data
def get_planetary_positions_today(julian_day):
    """Get today's planetary positions"""
    planets = {
        "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY,
        "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER,
        "Saturn": swe.SATURN, "Uranus": swe.URANUS, "Neptune": swe.NEPTUNE, "Pluto": swe.PLUTO
    }
    
    planet_data = {}
    for name, planet_id in planets.items():
        try:
            pos = swe.calc_ut(julian_day, planet_id)[0]
            planet_data[name] = {
                "longitude": pos[0],
                "latitude": pos[1], 
                "distance": pos[2],
                "speed": pos[3],
                "sign": get_zodiac_sign(pos[0]),
                "degree_in_sign": pos[0] % 30
            }
        except Exception:
            planet_data[name] = {"longitude": 0, "latitude": 0, "distance": 1, "speed": 0.5, "sign": "Aries", "degree_in_sign": 0}
    
    return planet_data

def get_zodiac_sign(longitude):
    """Get zodiac sign from longitude"""
    signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    return signs[int(longitude // 30)]

def calculate_planetary_price_levels(planet_data, current_price, symbol):
    """Calculate specific price levels for each planet including intraday levels"""
    price_scale = max(1, current_price / 1000)  # Dynamic scaling
    price_levels = {}
    
    for planet_name, data in planet_data.items():
        if planet_name in PLANETARY_CYCLES:
            cycle_info = PLANETARY_CYCLES[planet_name]
            base_price = (data["longitude"] * cycle_info["price_multiplier"] * price_scale) % (current_price * 2)
            
            # Ensure base_price is within reasonable range of current price
            while base_price < current_price * 0.7:
                base_price += current_price * 0.1
            while base_price > current_price * 1.3:
                base_price -= current_price * 0.1
            
            # Calculate multiple levels for each planet including intraday micro-levels
            levels = {
                "Major_Resistance": base_price * 1.08,
                "Primary_Resistance": base_price * 1.03,
                "Minor_Resistance": base_price * 1.015,
                "Current_Level": base_price,
                "Minor_Support": base_price * 0.985,
                "Primary_Support": base_price * 0.97,
                "Major_Support": base_price * 0.92
            }
            
            price_levels[planet_name] = {
                "current_degree": data["longitude"],
                "speed": data["speed"],
                "sign": f"{data['sign']} {data['degree_in_sign']:.2f}°",
                "levels": levels,
                "influence": cycle_info["influence"],
                "cycle_hours": cycle_info["cycle_hours"],
                "strength": calculate_planetary_strength(data, current_price)
            }
    
    return price_levels

def calculate_planetary_strength(planet_data, current_price):
    """Calculate planetary strength based on speed and position"""
    speed_factor = min(abs(planet_data["speed"]) * 10, 100)
    degree_factor = 100 - (planet_data["longitude"] % 30) * 3.33  # Stronger at beginning of sign
    return (speed_factor + degree_factor) / 2

def calculate_todays_time_cycles(planet_data, base_time_ist):
    """Calculate today's critical planetary time cycles in IST with expanded time window"""
    daily_cycles = []
    
    for planet_name, data in planet_data.items():
        if planet_name in PLANETARY_CYCLES:
            cycle_info = PLANETARY_CYCLES[planet_name]
            current_degree = data["longitude"] % 360
            speed_per_hour = max(abs(data["speed"]) / 24, 0.001)  # Ensure minimum speed
            
            # Calculate time to next critical degrees (expanded to 48 hours for slow planets)
            max_hours = 48 if planet_name in ["Saturn", "Uranus", "Neptune", "Pluto"] else 24
            
            for target_degree in cycle_info["major_degrees"]:
                # Calculate forward movement
                degrees_to_travel = (target_degree - current_degree) % 360
                if degrees_to_travel > 180:
                    degrees_to_travel = degrees_to_travel - 360
                
                hours_to_target = degrees_to_travel / speed_per_hour
                
                # Also calculate backward movement for comprehensive coverage
                degrees_backward = (current_degree - target_degree) % 360
                if degrees_backward > 180:
                    degrees_backward = degrees_backward - 360
                hours_backward = abs(degrees_backward / speed_per_hour)
                
                # Include both forward and backward movements within time window
                for hours, direction in [(hours_to_target, "approaching"), (-hours_backward, "separating")]:
                    if 0 <= abs(hours) <= max_hours:
                        cycle_time = base_time_ist + timedelta(hours=hours)
                        
                        daily_cycles.append({
                            "planet": planet_name,
                            "target_degree": target_degree,
                            "current_degree": current_degree,
                            "time_ist": cycle_time,
                            "hours_away": hours,
                            "direction": direction,
                            "market_impact": get_cycle_impact(planet_name, target_degree),
                            "trading_action": get_trading_action(planet_name, target_degree),
                            "price_effect": get_price_effect(planet_name, target_degree),
                            "strength": calculate_event_strength(planet_name, abs(hours))
                        })
    
    # Add synthetic cycles if no real cycles found
    if not daily_cycles:
        # Create some default cycles based on current positions
        for planet_name, data in planet_data.items():
            if planet_name in ["Moon", "Mercury", "Venus"]:  # Fast-moving planets
                for i in range(1, 25):  # Every hour for 24 hours
                    cycle_time = base_time_ist + timedelta(hours=i)
                    daily_cycles.append({
                        "planet": planet_name,
                        "target_degree": (data["longitude"] + (data["speed"] * i / 24)) % 360,
                        "current_degree": data["longitude"],
                        "time_ist": cycle_time,
                        "hours_away": i,
                        "direction": "moving",
                        "market_impact": f"{planet_name} hourly influence",
                        "trading_action": "MONITOR market movement",
                        "price_effect": "±0.5% to ±1.5%",
                        "strength": max(50 - i, 10)
                    })
    
    return sorted(daily_cycles, key=lambda x: abs(x["hours_away"]))

def calculate_event_strength(planet, hours_away):
    """Calculate event strength based on planet importance and proximity"""
    planet_weights = {
        "Sun": 100, "Moon": 90, "Mercury": 70, "Venus": 80, "Mars": 85,
        "Jupiter": 75, "Saturn": 95, "Uranus": 60, "Neptune": 50, "Pluto": 65
    }
    
    base_strength = planet_weights.get(planet, 50)
    time_factor = max(100 - abs(hours_away) * 4, 10)  # Closer events are stronger
    
    return (base_strength + time_factor) / 2

def get_cycle_impact(planet, degree):
    """Get market impact for specific planetary degrees"""
    impacts = {
        ("Sun", 0): "🌅 Market session begins - strong directional bias",
        ("Sun", 30): "🌞 Early momentum - trend establishment", 
        ("Sun", 90): "🌞 Mid-session peak - trend confirmation/reversal", 
        ("Sun", 180): "🌇 Session high/low - profit taking begins",
        ("Sun", 270): "🌙 Late session - position adjustments",
        
        ("Moon", 0): "🌑 Lunar reset - high volatility spike",
        ("Moon", 15): "🌒 Early waxing - gentle upward bias",
        ("Moon", 30): "🌓 Increasing energy - momentum builds",
        ("Moon", 45): "🌔 Growing tension - breakout potential",
        ("Moon", 60): "🌕 Harmonic energy - smooth trending",
        ("Moon", 90): "🌓 Quarter tension - sharp reversals",
        ("Moon", 120): "🌕 Trine support - bullish bias",
        ("Moon", 150): "🌖 Stress angle - selling pressure",
        ("Moon", 180): "🌕 Opposition peak - major reversals",
        
        ("Venus", 0): "💎 Value cycle begins - reassessment phase",
        ("Venus", 30): "💰 Semi-sextile - mild support building",
        ("Venus", 60): "✨ Sextile harmony - buying opportunities",
        ("Venus", 90): "⚖️ Square tension - resistance at highs",
        ("Venus", 120): "💫 Trine flow - strong support holds",
        ("Venus", 150): "💔 Quincunx stress - uncertain values",
        ("Venus", 180): "⚖️ Opposition - peak resistance levels",
        
        ("Mars", 0): "⚔️ Aggressive cycle starts - breakout energy",
        ("Mars", 45): "💥 Semi-square - initial resistance",
        ("Mars", 90): "💥 Square force - sharp corrections",
        ("Mars", 135): "⚡ Sesquiquadrate - late-stage pressure",
        ("Mars", 180): "🛡️ Opposition - maximum resistance",
        
        ("Jupiter", 0): "🚀 Expansion begins - major trend start",
        ("Jupiter", 60): "📈 Sextile opportunity - good entries",
        ("Jupiter", 120): "🌟 Trine support - major buying zone",
        ("Jupiter", 180): "🎯 Opposition - trend exhaustion",
        
        ("Saturn", 0): "🏔️ Barrier erected - strong resistance begins",
        ("Saturn", 45): "⛔ Semi-square - early warning pressure",
        ("Saturn", 90): "🚫 Square block - major selling pressure",
        ("Saturn", 135): "💀 Sesquiquadrate - intense bearish force",
        ("Saturn", 180): "⚰️ Opposition wall - maximum resistance"
    }
    
    # Find closest match
    closest_match = None
    min_diff = float('inf')
    
    for (p, d), impact in impacts.items():
        if p == planet:
            diff = abs(d - degree)
            if diff < min_diff:
                min_diff = diff
                closest_match = impact
    
    return closest_match or f"{planet} @ {degree}° - moderate influence"

def get_trading_action(planet, degree):
    """Get specific trading actions for planetary cycles"""
    actions = {
        ("Sun", 0): "🔥 ENTER TREND - follow momentum strongly",
        ("Sun", 30): "📈 BUILD POSITION - add to winners",
        ("Sun", 90): "⚡ REASSESS - confirm trend continuation",
        ("Sun", 180): "💰 TAKE PROFITS - book 50% of gains",
        ("Sun", 270): "😴 REDUCE RISK - minimal new positions",
        
        ("Moon", 0): "📉 REDUCE SIZE - expect 2-4% volatility",
        ("Moon", 15): "🛒 GRADUAL BUY - small position entries",
        ("Moon", 30): "📊 MONITOR - watch volume confirmation", 
        ("Moon", 45): "⚠️ PREPARE - breakout/breakdown setup",
        ("Moon", 90): "🔄 REVERSAL TRADE - fade extremes",
        ("Moon", 120): "💪 ADD LONGS - strong support area",
        ("Moon", 180): "🎯 MAJOR REVERSAL - big position changes",
        
        ("Venus", 0): "🛒 VALUE BUY - look for discounted entries",
        ("Venus", 60): "✅ CONFIRM BUY - good risk/reward setups",
        ("Venus", 90): "⚠️ CAUTION - resistance testing zone",
        ("Venus", 120): "🚀 STRONG BUY - major support confirmed",
        ("Venus", 180): "🚨 SELL SPIKE - distribute at highs",
        
        ("Mars", 0): "🚀 MOMENTUM LONG - aggressive trend entries",
        ("Mars", 45): "🛡️ TIGHTEN STOPS - resistance building",
        ("Mars", 90): "📉 DEFENSIVE SHORT - breakdown trades",
        ("Mars", 180): "💀 MAJOR SHORT - strong resistance trade",
        
        ("Jupiter", 0): "📈 MAJOR LONG - big trend following",
        ("Jupiter", 60): "💫 OPPORTUNITY - excellent buy setups",
        ("Jupiter", 120): "🌟 MAXIMUM LONG - strongest support",
        
        ("Saturn", 0): "⛔ NO LONGS - resistance zone active",
        ("Saturn", 90): "📉 SHORT RALLY - major selling setup",
        ("Saturn", 180): "🚫 MAJOR SHORT - maximum resistance"
    }
    
    # Find closest match
    closest_match = None
    min_diff = float('inf')
    
    for (p, d), action in actions.items():
        if p == planet:
            diff = abs(d - degree)
            if diff < min_diff:
                min_diff = diff
                closest_match = action
    
    return closest_match or f"MONITOR {planet} influence"

def get_price_effect(planet, degree):
    """Get expected price movement effect"""
    effects = {
        ("Sun", 0): "+1% to +3%", ("Sun", 30): "+0.5% to +1.5%", ("Sun", 90): "±1% to ±3%", ("Sun", 180): "-0.5% to -2%",
        ("Moon", 0): "±2% to ±5%", ("Moon", 15): "+0.3% to +1%", ("Moon", 30): "+0.5% to +1.5%", ("Moon", 45): "±1% to ±2%",
        ("Moon", 60): "+0.5% to +2%", ("Moon", 90): "±2% to ±4%", ("Moon", 120): "+1% to +3%", ("Moon", 180): "±3% to ±6%",
        ("Venus", 0): "+0.5% to +1.5%", ("Venus", 60): "+1% to +2%", ("Venus", 90): "-0.5% to -1.5%", ("Venus", 120): "+1% to +3%", ("Venus", 180): "-1% to -2.5%",
        ("Mars", 0): "+2% to +5%", ("Mars", 45): "-0.5% to -2%", ("Mars", 90): "-2% to -4%", ("Mars", 180): "-3% to -6%",
        ("Jupiter", 0): "+3% to +7%", ("Jupiter", 60): "+1% to +3%", ("Jupiter", 120): "+2% to +5%", ("Jupiter", 180): "-1% to -3%",
        ("Saturn", 0): "-1% to -3%", ("Saturn", 45): "-1% to -2%", ("Saturn", 90): "-3% to -5%", ("Saturn", 180): "-4% to -7%"
    }
    
    # Find closest match
    closest_match = None
    min_diff = float('inf')
    
    for (p, d), effect in effects.items():
        if p == planet:
            diff = abs(d - degree)
            if diff < min_diff:
                min_diff = diff
                closest_match = effect
    
    return closest_match or "±0.5% to ±1.5%"

def calculate_intraday_support_levels(current_price, planet_data):
    """Calculate intraday micro support/resistance levels"""
    levels = []
    
    # Moon-based intraday levels (every 15 degrees = ~1.2 hours)
    moon_deg = planet_data["Moon"]["longitude"]
    moon_speed = planet_data["Moon"]["speed"]
    
    for i in range(0, 360, 15):  # Every 15 degrees
        hours_to_degree = ((i - moon_deg) % 360) / (moon_speed / 24) if moon_speed != 0 else 999
        if 0 <= hours_to_degree <= 12:  # Next 12 hours only
            level_price = current_price + (i - moon_deg) * 0.8
            levels.append({
                "time_hours": hours_to_degree,
                "degree": i,
                "price": level_price,
                "type": "Moon Support" if level_price < current_price else "Moon Resistance",
                "strength": "Intraday"
            })
    
    # Mercury-based news levels
    mercury_deg = planet_data["Mercury"]["longitude"]
    for angle in [0, 30, 45, 60, 90, 120, 135, 150, 180]:
        price_adj = (angle - mercury_deg) * 0.5
        levels.append({
            "time_hours": angle / 15,  # Approximate
            "degree": angle,
            "price": current_price + price_adj,
            "type": "News Level",
            "strength": "Moderate"
        })
    
    # Venus-based value levels  
    venus_deg = planet_data["Venus"]["longitude"]
    for angle in [0, 30, 60, 90, 120, 150, 180]:
        price_adj = (angle - venus_deg) * 1.2
        levels.append({
            "time_hours": angle / 10,  # Approximate
            "degree": angle,
            "price": current_price + price_adj,
            "type": "Value Zone",
            "strength": "Strong"
        })
    
    return sorted(levels, key=lambda x: x["time_hours"])[:15]  # Top 15 intraday levels

def generate_daily_planetary_report(symbol, current_price, tehran_time):
    """Generate focused daily planetary cycles report"""
    # Time conversions
    ist_time = tehran_time + timedelta(hours=2)
    utc_time = tehran_time - timedelta(hours=3, minutes=30)
    
    # Get planetary data
    julian_day = swe.julday(utc_time.year, utc_time.month, utc_time.day, 
                           utc_time.hour + utc_time.minute/60 + utc_time.second/3600)
    
    planet_data = get_planetary_positions_today(julian_day)
    price_levels = calculate_planetary_price_levels(planet_data, current_price, symbol)
    daily_cycles = calculate_todays_time_cycles(planet_data, ist_time)
    intraday_levels = calculate_intraday_support_levels(current_price, planet_data)
    
    # Generate report
    report = f"""
# 🌟 Daily Planetary Cycles & Price Levels Report
## {symbol} Trading - {tehran_time.strftime('%Y-%m-%d')}

### ⏰ Time Base
- **Tehran Time**: {tehran_time.strftime('%H:%M:%S')} 🇮🇷
- **Indian Standard Time**: **{ist_time.strftime('%H:%M:%S')}** 🇮🇳  
- **Current {symbol} Price**: **${current_price:,.2f}**

---

## 🎯 Today's Planetary Price Levels & Multi-Layer Support/Resistance

| Planet | Position | Major Resist | Minor Resist | Current | Minor Support | Major Support | Strength |
|--------|----------|--------------|--------------|---------|---------------|---------------|----------|"""
    
    for planet_name, data in price_levels.items():
        levels = data["levels"]
        strength = f"{data['strength']:.0f}%"
        
        report += f"""
| **{planet_name}** | {data['sign']} | ${levels['Major_Resistance']:,.0f} | ${levels['Minor_Resistance']:,.0f} | ${levels['Current_Level']:,.0f} | ${levels['Minor_Support']:,.0f} | ${levels['Major_Support']:,.0f} | {strength} |"""

    # Intraday micro levels
    report += f"""

---

## 📊 Intraday Micro Support/Resistance Levels (Next 12 Hours)

| Time (IST) | Price Level | Type | Distance | Strength | Trading Signal |
|------------|-------------|------|----------|----------|----------------|"""
    
    for level in intraday_levels:
        time_from_now = ist_time + timedelta(hours=level["time_hours"])
        distance = level["price"] - current_price
        signal = "🔴 SELL ZONE" if distance > 20 else "🟡 MONITOR" if abs(distance) <= 20 else "🟢 BUY ZONE"
        
        report += f"""
| {time_from_now.strftime('%H:%M')} | ${level['price']:,.0f} | {level['type']} | {distance:+.0f} | {level['strength']} | {signal} |"""

    # Today's critical time cycles
    if daily_cycles:
        report += f"""

---

## ⏱️ Today's Critical Planetary Time Cycles (IST)

| Time (IST) | Planet | Event | Market Impact | Trading Action | Expected Move | Hours Away | Strength |
|------------|--------|-------|---------------|----------------|---------------|------------|----------|"""
        
        for cycle in daily_cycles[:15]:  # Show top 15 cycles
            time_str = cycle["time_ist"].strftime("%H:%M")
            hours_str = f"{cycle['hours_away']:+.1f}h"
            strength_bar = "🔥🔥🔥" if cycle['strength'] > 80 else "🔥🔥" if cycle['strength'] > 60 else "🔥"
            
            report += f"""
| **{time_str}** | {cycle['planet']} | {cycle['planet']} @ {cycle['target_degree']:.0f}° | {cycle['market_impact']} | {cycle['trading_action']} | {cycle['price_effect']} | {hours_str} | {strength_bar} |"""
    else:
        report += f"""

---

## ⏱️ No Major Planetary Events Today
*Slow-moving planets dominate - expect range-bound trading*"""

    # Current planetary strength analysis
    report += f"""

---

## 💪 Current Planetary Strength & Influence Rankings

| Rank | Planet | Strength | Current Impact on {symbol} | Speed (°/day) | Next Critical | Action Priority |
|------|--------|----------|----------------------------|---------------|---------------|----------------|"""
    
    # Calculate planetary strength
    planetary_strength = []
    for planet_name, data in planet_data.items():
        if planet_name in PLANETARY_CYCLES:
            strength_score = calculate_planetary_strength(data, current_price)
            
            planetary_strength.append({
                "planet": planet_name,
                "strength_score": strength_score,
                "speed": data["speed"],
                "current_degree": data["longitude"] % 360
            })
    
    # Sort by strength
    planetary_strength.sort(key=lambda x: x["strength_score"], reverse=True)
    
    for i, planet_info in enumerate(planetary_strength):
        planet = planet_info["planet"]
        strength = "🔥 VERY HIGH" if planet_info["strength_score"] > 70 else \
                  "⚡ HIGH" if planet_info["strength_score"] > 50 else \
                  "📊 MODERATE" if planet_info["strength_score"] > 30 else "📉 LOW"
        
        # Find next critical degree
        current_deg = planet_info["current_degree"]
        critical_degrees = PLANETARY_CYCLES[planet]["major_degrees"]
        next_critical = min(critical_degrees, key=lambda x: abs(x - current_deg))
        
        impact = get_current_impact(planet, abs(next_critical - current_deg))
        priority = "🚨 URGENT" if i < 2 else "⚠️ IMPORTANT" if i < 4 else "📋 MONITOR"
        
        report += f"""
| {i+1} | **{planet}** | {strength} | {impact} | {planet_info['speed']:+.4f} | {next_critical:.0f}° | {priority} |"""

    # Key trading windows
    if daily_cycles:
        next_major_events = [cycle for cycle in daily_cycles if 0 <= cycle["hours_away"] <= 8][:6]
        
        if next_major_events:
            report += f"""

---

## 🚀 Key Trading Windows (Next 8 Hours)

| Exact Time (IST) | Planet Event | Action Required | Price Target | Risk Level | Confidence |
|------------------|--------------|-----------------|--------------|------------|------------|"""
            
            for event in next_major_events:
                time_str = event["time_ist"].strftime("%H:%M:%S")
                price_target = get_price_target(current_price, event["planet"], event["target_degree"])
                risk = get_risk_level(event["planet"], event["target_degree"])
                confidence = f"{event['strength']:.0f}%"
                
                report += f"""
| **{time_str}** | {event['planet']} @ {event['target_degree']:.0f}° | {event['trading_action']} | ${price_target:,.0f} | {risk} | {confidence} |"""

    # Summary and recommendations
    strongest_planet = planetary_strength[0]["planet"] if planetary_strength else "Sun"
    next_major_cycle = daily_cycles[0] if daily_cycles else None
    
    report += f"""

---

## 💡 Today's Key Insights & Final Recommendations

### 🎯 Dominant Planetary Influence: **{strongest_planet}**
- Currently the strongest influence on {symbol} price action
- **Current Position**: {planet_data[strongest_planet]['sign']} {planet_data[strongest_planet]['degree_in_sign']:.2f}°
- **Speed**: {planet_data[strongest_planet]['speed']:+.4f}°/day ({'Fast-moving' if abs(planet_data[strongest_planet]['speed']) > 1 else 'Slow-moving'})

### ⏰ Next Critical Time Window:"""
    
    if next_major_cycle:
        report += f"""
- **{next_major_cycle['time_ist'].strftime('%H:%M IST')}**: {next_major_cycle['planet']} reaches {next_major_cycle['target_degree']:.0f}°
- **Expected Impact**: {next_major_cycle['market_impact']}
- **Trading Strategy**: {next_major_cycle['trading_action']}
- **Price Effect**: {next_major_cycle['price_effect']}
- **Confidence Level**: {next_major_cycle['strength']:.0f}%"""
    else:
        report += f"""
- **No major planetary events in next 24 hours**
- **Market Condition**: Range-bound, slow planetary movement
- **Strategy**: Focus on intraday micro levels above"""
    
    # Key resistance/support for today
    current_above = [p for p, data in price_levels.items() if data["levels"]["Primary_Resistance"] > current_price]
    current_below = [p for p, data in price_levels.items() if data["levels"]["Primary_Support"] < current_price]
    
    if current_above:
        closest_resistance = min(current_above, key=lambda p: price_levels[p]["levels"]["Primary_Resistance"] - current_price)
        resistance_price = price_levels[closest_resistance]["levels"]["Primary_Resistance"]
        report += f"""

### 🚧 Next Major Resistance: **{closest_resistance} @ ${resistance_price:,.0f}**
- **Distance**: +${resistance_price - current_price:,.0f} ({((resistance_price/current_price - 1) * 100):+.1f}%)
- **Strategy**: Monitor for rejection, consider shorts on approach with volume
- **Intraday Levels**: Watch ${resistance_price * 0.995:,.0f} and ${resistance_price * 1.005:,.0f}"""
    
    if current_below:
        closest_support = max(current_below, key=lambda p: price_levels[p]["levels"]["Primary_Support"])
        support_price = price_levels[closest_support]["levels"]["Primary_Support"]
        report += f"""

### 🛡️ Next Major Support: **{closest_support} @ ${support_price:,.0f}**  
- **Distance**: ${support_price - current_price:,.0f} ({((support_price/current_price - 1) * 100):+.1f}%)
- **Strategy**: Look for bounces, consider longs on successful test
- **Intraday Levels**: Watch ${support_price * 0.995:,.0f} and ${support_price * 1.005:,.0f}"""

    report += f"""

### 🎲 Today's Probability Assessment:
- **Bullish Scenario (35%)**: {strongest_planet} supports upward momentum
- **Bearish Scenario (40%)**: Planetary resistance creates selling pressure  
- **Sideways (25%)**: Limited planetary activity = range trading

### 🛡️ Risk Management for Today:
1. **Position Size**: Reduce by 30% during high-impact planetary events
2. **Stop Losses**: Use wider stops ±2% during Moon/Mars events  
3. **Time Limits**: No new positions 15 minutes before major planetary transitions
4. **Volume Confirmation**: Require 1.5x average volume for breakout trades
5. **Intraday Scalping**: Use micro support/resistance levels for quick trades"""

    if next_major_cycle:
        report += f"""

---

> **🚨 URGENT ALERT**: Next major planetary event in **{next_major_cycle['hours_away']:.1f} hours** at **{next_major_cycle['time_ist'].strftime('%H:%M IST')}**  
> **Planet**: {next_major_cycle['planet']} @ {next_major_cycle['target_degree']:.0f}°  
> **Action Required**: {next_major_cycle['trading_action']}  
> **Expected Move**: {next_major_cycle['price_effect']}  
> **Confidence**: {next_major_cycle['strength']:.0f}%"""
    else:
        report += f"""

---

> **📊 MARKET STATUS**: Limited planetary activity today - Focus on intraday micro-levels  
> **Strategy**: Use Moon-based 15° cycles and Mercury news levels for scalping  
> **Next Major Event**: Check tomorrow's planetary calendar"""
    
    return report, price_levels, daily_cycles

def get_current_impact(planet, distance_to_critical):
    """Get current market impact based on distance to critical degrees"""
    if distance_to_critical <= 2:
        return f"🔥 MAXIMUM IMPACT - Exact {planet} influence active"
    elif distance_to_critical <= 5:
        return f"⚡ HIGH IMPACT - Strong {planet} influence building"
    elif distance_to_critical <= 10:
        return f"📊 MODERATE IMPACT - {planet} influence present"
    else:
        return f"📉 LOW IMPACT - {planet} influence minimal"

def get_price_target(current_price, planet, degree):
    """Calculate specific price targets for planetary events"""
    adjustments = {
        ("Sun", 0): 1.025, ("Sun", 30): 1.015, ("Sun", 90): 1.01, ("Sun", 180): 0.985,
        ("Moon", 0): 1.04, ("Moon", 15): 1.008, ("Moon", 30): 1.015, ("Moon", 45): 1.02, ("Moon", 90): 1.03, ("Moon", 180): 0.97,
        ("Venus", 0): 1.02, ("Venus", 60): 1.025, ("Venus", 90): 0.985, ("Venus", 120): 1.03, ("Venus", 180): 0.975,
        ("Mars", 0): 1.05, ("Mars", 45): 0.98, ("Mars", 90): 0.96, ("Mars", 180): 0.94,
        ("Jupiter", 0): 1.07, ("Jupiter", 60): 1.025, ("Jupiter", 120): 1.04, ("Jupiter", 180): 0.97,
        ("Saturn", 0): 0.96, ("Saturn", 45): 0.975, ("Saturn", 90): 0.94, ("Saturn", 180): 0.92
    }
    
    # Find closest match
    closest_key = None
    min_diff = float('inf')
    
    for (p, d) in adjustments.keys():
        if p == planet:
            diff = abs(d - degree)
            if diff < min_diff:
                min_diff = diff
                closest_key = (p, d)
    
    multiplier = adjustments.get(closest_key, 1.0)
    return current_price * multiplier

def get_risk_level(planet, degree):
    """Get risk level for planetary events"""
    high_risk = [("Mars", 90), ("Mars", 180), ("Saturn", 90), ("Saturn", 180), ("Moon", 0), ("Moon", 180)]
    medium_risk = [("Sun", 90), ("Venus", 90), ("Venus", 180), ("Mercury", 90)]
    
    for p, d in high_risk:
        if p == planet and abs(d - degree) <= 15:
            return "🔴 HIGH"
    
    for p, d in medium_risk:
        if p == planet and abs(d - degree) <= 15:
            return "🟡 MEDIUM"
    
    return "🟢 LOW"

def create_planetary_timeline_chart(daily_cycles, current_time):
    """Create timeline chart of today's planetary events"""
    if not daily_cycles:
        # Create placeholder chart
        fig = go.Figure()
        fig.add_annotation(
            x=0.5, y=0.5, text="No major planetary events today<br>Check intraday micro levels",
            showarrow=False, font=dict(size=16)
        )
        fig.update_layout(title="Today's Planetary Events Timeline (IST)", height=400)
        return fig
    
    fig = go.Figure()
    
    # Create timeline
    times = [cycle["time_ist"] for cycle in daily_cycles[:10]]
    planets = [cycle["planet"] for cycle in daily_cycles[:10]]
    strengths = [cycle["strength"] for cycle in daily_cycles[:10]]
    
    # Color mapping for planets
    planet_colors = {
        "Sun": "#FFD700", "Moon": "#C0C0C0", "Mercury": "#FFA500",
        "Venus": "#FF69B4", "Mars": "#FF4500", "Jupiter": "#4169E1",
        "Saturn": "#8B4513", "Uranus": "#40E0D0", "Neptune": "#0000FF", "Pluto": "#800080"
    }
    
    fig.add_trace(go.Scatter(
        x=times,
        y=planets,
        mode='markers+text',
        marker=dict(
            size=[max(15, strength/3) for strength in strengths],
            color=[planet_colors.get(planet, "#666666") for planet in planets],
            line=dict(width=2, color="white")
        ),
        text=[cycle["time_ist"].strftime("%H:%M") for cycle in daily_cycles[:10]],
        textposition="middle center",
        textfont=dict(size=9, color="white"),
        name="Planetary Events"
    ))
    
    # Add current time line
    fig.add_vline(x=current_time, line_dash="dash", line_color="red", 
                  annotation_text="Current Time")
    
    fig.update_layout(
        title="Today's Planetary Events Timeline (IST)",
        xaxis_title="Time (IST)",
        yaxis_title="Planet",
        height=500,
        showlegend=False
    )
    
    return fig

# Streamlit App
st.set_page_config(layout="wide", page_title="Daily Planetary Cycles")

st.title("🌟 Daily Planetary Cycles & Multi-Level Support/Resistance")
st.markdown("*Comprehensive daily report with planetary times, resistance levels, and intraday micro-levels*")

# Input section
col1, col2, col3 = st.columns(3)

with col1:
    symbol = st.text_input("Symbol", value="GOLD", help="Trading symbol")
    
with col2:
    current_price = st.number_input("Current Price", value=3423.0, step=0.1, 
                                   help="Current market price")

with col3:
    tehran_time_input = st.text_input("Tehran Time", 
                                     value="2025-08-08 17:07:10",
                                     help="Format: YYYY-MM-DD HH:MM:SS")

# Parse time
try:
    tehran_time = datetime.strptime(tehran_time_input, "%Y-%m-%d %H:%M:%S")
except:
    tehran_time = datetime.now()
    st.error("Invalid time format, using current time")

# Generate report
if st.button("🚀 Generate Today's Planetary Report", type="primary"):
    try:
        with st.spinner("🌌 Calculating planetary cycles and support levels..."):
            start_time = time.time()
            report, price_levels, daily_cycles = generate_daily_planetary_report(
                symbol, current_price, tehran_time)
            elapsed_time = time.time() - start_time
            
        st.success(f"✅ Report generated in {elapsed_time:.2f} seconds")
        
        # Display main report
        st.markdown(report)
        
        # Charts section
        col1, col2 = st.columns(2)
        
        with col1:
            # Timeline chart
            st.markdown("### 📊 Today's Planetary Events Timeline")
            ist_current = tehran_time + timedelta(hours=2)
            fig = create_planetary_timeline_chart(daily_cycles, ist_current)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Price levels chart
            st.markdown("### 💰 Multi-Level Support/Resistance Chart")
            
            fig2 = go.Figure()
            
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F']
            
            for i, (planet, data) in enumerate(price_levels.items()):
                levels = data["levels"]
                level_names = ["Major Support", "Primary Support", "Minor Support", "Current", "Minor Resist", "Primary Resist", "Major Resist"]
                level_values = [levels["Major_Support"], levels["Primary_Support"], levels["Minor_Support"], 
                               levels["Current_Level"], levels["Minor_Resistance"], levels["Primary_Resistance"], levels["Major_Resistance"]]
                
                fig2.add_trace(go.Scatter(
                    x=level_names,
                    y=level_values,
                    mode='lines+markers',
                    name=planet,
                    line=dict(color=colors[i % len(colors)], width=2),
                    marker=dict(size=8)
                ))
            
            # Add current price line
            fig2.add_hline(y=current_price, line_dash="dash", line_color="red", line_width=3,
                          annotation_text=f"Current Price: ${current_price:,.0f}")
            
            fig2.update_layout(
                title=f"{symbol} Multi-Layer Support/Resistance Levels",
                xaxis_title="Level Type",
                yaxis_title="Price ($)",
                height=500,
                showlegend=True
            )
            
            st.plotly_chart(fig2, use_container_width=True)
        
        # Data tables
        if daily_cycles:
            st.markdown("### ⚡ Quick Reference Tables")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 🕐 Next 8 Hours Events")
                next_events = [c for c in daily_cycles if 0 <= c["hours_away"] <= 8][:8]
                if next_events:
                    events_df = pd.DataFrame({
                        "Time (IST)": [e["time_ist"].strftime("%H:%M") for e in next_events],
                        "Planet": [e["planet"] for e in next_events],
                        "Degree": [f"{e['target_degree']:.0f}°" for e in next_events],
                        "Action": [e["trading_action"][:20] + "..." if len(e["trading_action"]) > 20 else e["trading_action"] for e in next_events],
                        "Move": [e["price_effect"] for e in next_events],
                        "Strength": [f"{e['strength']:.0f}%" for e in next_events]
                    })
                    st.dataframe(events_df, use_container_width=True)
                else:
                    st.info("No major events in next 8 hours")
            
            with col2:
                st.markdown("#### 🎯 Key Price Levels")
                levels_data = []
                for planet, data in price_levels.items():
                    levels_data.append({
                        "Planet": planet,
                        "Resistance": f"${data['levels']['Primary_Resistance']:,.0f}",
                        "Support": f"${data['levels']['Primary_Support']:,.0f}",
                        "Strength": f"{data['strength']:.0f}%"
                    })
                
                levels_df = pd.DataFrame(levels_data)
                st.dataframe(levels_df, use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ Error: {e}")
        st.exception(e)

# Enhanced sidebar
with st.sidebar:
    st.markdown("### 🌟 Enhanced Features")
    st.markdown("""
    **Multi-Layer Support/Resistance:**
    - 🔴 Major levels (±8-10%)
    - 🟡 Primary levels (±3-5%)  
    - 🟢 Minor levels (±1-2%)
    
    **Intraday Micro Levels:**
    - 🌙 Moon 15° cycles (~1.2h)
    - ☿ Mercury news levels
    - ♀ Venus value zones
    
    **Time-Based Precision:**
    - Exact IST timing for each event
    - Strength percentage for each signal
    - Multi-hour windows for planning
    
    **Risk Management:**
    - 🔴 HIGH risk events
    - 🟡 MEDIUM risk periods  
    - 🟢 LOW risk opportunities
    """)
    
    st.markdown("### 📊 Usage Tips")
    st.markdown("""
    - Use **Major levels** for position entries
    - Use **Minor levels** for scalping
    - **High strength events** (>80%) are most reliable
    - **Fast planets** (Moon/Mercury) = short-term
    - **Slow planets** (Saturn/Jupiter) = major moves
    """)
