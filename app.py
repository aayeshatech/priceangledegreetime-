import streamlit as st
import swisseph as swe
from datetime import datetime, timedelta
import time
import pandas as pd
import plotly.graph_objects as go
import math

# Initialize ephemeris
try:
    swe.set_ephe_path(None)
except Exception as e:
    st.error(f"Error initializing Swiss Ephemeris: {e}")
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
    """Calculate realistic intraday price levels for each planet"""
    price_levels = {}
    
    # Define intraday percentage ranges based on planet characteristics
    planet_ranges = {
        "Sun": {"major": 2.0, "primary": 1.0, "minor": 0.3},
        "Moon": {"major": 3.0, "primary": 1.5, "minor": 0.5},
        "Mercury": {"major": 1.8, "primary": 0.8, "minor": 0.25},
        "Venus": {"major": 2.5, "primary": 1.2, "minor": 0.4},
        "Mars": {"major": 3.5, "primary": 1.8, "minor": 0.6},
        "Jupiter": {"major": 4.0, "primary": 2.0, "minor": 0.7},
        "Saturn": {"major": 2.8, "primary": 1.4, "minor": 0.45},
        "Uranus": {"major": 5.0, "primary": 2.5, "minor": 0.8},
        "Neptune": {"major": 3.2, "primary": 1.6, "minor": 0.5},
        "Pluto": {"major": 4.5, "primary": 2.2, "minor": 0.75}
    }
    
    for planet_name, data in planet_data.items():
        if planet_name in PLANETARY_CYCLES:
            ranges = planet_ranges.get(planet_name, {"major": 2.0, "primary": 1.0, "minor": 0.3})
            
            # Calculate planetary influence modifier
            degree_mod = (data["longitude"] % 360) / 360
            influence_multiplier = 0.7 + (0.6 * degree_mod)
            
            # Adjust ranges based on planetary influence
            major_pct = ranges["major"] * influence_multiplier
            primary_pct = ranges["primary"] * influence_multiplier  
            minor_pct = ranges["minor"] * influence_multiplier
            
            # Calculate actual price levels
            levels = {
                "Major_Resistance": current_price * (1 + major_pct/100),
                "Primary_Resistance": current_price * (1 + primary_pct/100),
                "Minor_Resistance": current_price * (1 + minor_pct/100),
                "Current_Level": current_price,
                "Minor_Support": current_price * (1 - minor_pct/100),
                "Primary_Support": current_price * (1 - primary_pct/100),
                "Major_Support": current_price * (1 - major_pct/100)
            }
            
            strength = 50 + (abs(data["speed"]) * 10) + ((360 - (data["longitude"] % 30)) / 30 * 50)
            
            price_levels[planet_name] = {
                "current_degree": data["longitude"],
                "speed": data["speed"],
                "sign": f"{data['sign']} {data['degree_in_sign']:.2f}°",
                "levels": levels,
                "influence": PLANETARY_CYCLES[planet_name]["influence"],
                "strength": min(strength, 100)
            }
    
    return price_levels

def calculate_todays_time_cycles(planet_data, base_time_ist):
    """Calculate today's critical planetary time cycles in IST"""
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
        if degree == 0: return "🌑 REDUCE SIZE - high volatility expected"
        elif degree == 90: return "🌓 REVERSAL TRADES - fade extremes"
        elif degree == 180: return "🌕 MAJOR REVERSAL - big moves"
        elif degree == 270: return "🌗 RANGE TRADING - consolidation"
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

def calculate_intraday_support_levels(current_price, planet_data, ist_time):
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
    
def identify_day_trading_zones(price_levels, current_price, intraday_levels):
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

def generate_daily_planetary_report(symbol, current_price, tehran_time):
    """Generate focused daily planetary cycles report"""
    try:
        # Time conversions
        ist_time = tehran_time + timedelta(hours=2)
        utc_time = tehran_time - timedelta(hours=3, minutes=30)
        
        # Get planetary data
        julian_day = swe.julday(utc_time.year, utc_time.month, utc_time.day, 
                               utc_time.hour + utc_time.minute/60 + utc_time.second/3600)
        
        planet_data = get_planetary_positions_today(julian_day)
        if not planet_data:
            st.error("Failed to get planetary data")
            return None, None, None, None, None, None, None
            
        price_levels = calculate_planetary_price_levels(planet_data, current_price, symbol)
        daily_cycles = calculate_todays_time_cycles(planet_data, ist_time)
        intraday_levels = calculate_intraday_support_levels(current_price, planet_data, ist_time)
        
        # Ensure all data structures are valid
        if not price_levels:
            price_levels = {}
        if not daily_cycles:
            daily_cycles = []
        if not intraday_levels:
            intraday_levels = []
        
        # Get trading zones and high-probability times
        sell_zones, buy_zones, high_prob_times = identify_day_trading_zones(price_levels, current_price, intraday_levels)
        
    except Exception as e:
        st.error(f"Error in data calculation: {e}")
        return None, None, None, None, None, None, None
    
    try:
        # Generate report
        report = f"""
# 🌟 Daily Planetary Cycles - Indian Intraday Trading
## {symbol} Trading - {tehran_time.strftime('%Y-%m-%d')}

### ⏰ Time Base (All times in IST - Indian Standard Time)
- **Tehran Time**: {tehran_time.strftime('%H:%M:%S')} 🇮🇷
- **Indian Standard Time**: **{ist_time.strftime('%H:%M:%S')}** 🇮🇳  
- **Current {symbol} Price**: **{current_price:,.0f}**

---

## 🎯 Today's Planetary Intraday Levels (Perfect for Day Trading)

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
| No data | - | - | - | - | - | - | - |"""

        # Intraday time-based planetary levels
        report += f"""

---

## ⏰ Intraday Time-Based Planetary Levels (IST)

| Time (IST) | Price Level | Planet Level | Trading Signal | Influence |
|------------|-------------|--------------|----------------|-----------|"""
        
        if intraday_levels:
            for level in intraday_levels[:15]:  # Show next 15 time-based levels
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

## 🔴 DAY RESISTANCE LEVELS - SELL ZONES

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

## 🟢 DAY SUPPORT LEVELS - BUY ZONES

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
        
        if high_prob_times:
            for time_window in high_prob_times[:12]:  # Next 12 high-probability windows
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

## ⏱️ Today's Critical Planetary Time Cycles (IST)

| Time (IST) | Planet | Event | Trading Action | Expected Move | Hours Away |
|------------|--------|-------|----------------|---------------|------------|"""
        
        if daily_cycles:
            for cycle in daily_cycles[:10]:
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
        if daily_cycles:
            try:
                next_event_text = f"{daily_cycles[0]['time_ist'].strftime('%H:%M IST')} - {daily_cycles[0]['planet']} @ {daily_cycles[0]['target_degree']:.0f}°"
            except:
                pass

        report += f"""

---

## 💡 Today's Key Insights

### 🎯 Dominant Influence: **{strongest_planet}**
- **Primary Action**: Focus on {strongest_planet.lower()} levels for best trades

### 📊 Trading Summary:
- **Sell Zones**: {len(sell_zones)} resistance levels identified
- **Buy Zones**: {len(buy_zones)} support levels identified  
- **High Prob Windows**: {len(high_prob_times)} time-based opportunities
- **Active Cycles**: {len(daily_cycles)} planetary events today

---

> **🚨 Next Major Event**: {next_event_text}
"""
        
        return report, price_levels, daily_cycles, intraday_levels, sell_zones, buy_zones, high_prob_times
        
    except Exception as e:
        st.error(f"Error generating report: {e}")
        return None, None, None, None, None, None, None

# Streamlit App
st.set_page_config(layout="wide", page_title="Daily Planetary Cycles")

st.title("🌟 Daily Planetary Cycles - Indian Intraday Trading")
st.markdown("*Realistic support/resistance levels for Nifty, Bank Nifty & Indian markets - All times in IST*")

# Input section
col1, col2, col3 = st.columns(3)

with col1:
    symbol = st.text_input("Symbol", value="NIFTY", help="Trading symbol (NIFTY, BANKNIFTY, etc.)")
    
with col2:
    current_price = st.number_input("Current Price", value=24594.0, step=0.1, help="Current market price")

with col3:
    default_time = datetime.now()
    tehran_time_input = st.text_input("Time", 
                                     value=default_time.strftime("%Y-%m-%d %H:%M:%S"),
                                     help="Format: YYYY-MM-DD HH:MM:SS")

# Parse time
try:
    tehran_time = datetime.strptime(tehran_time_input, "%Y-%m-%d %H:%M:%S")
except:
    tehran_time = datetime.now()
    st.error("Invalid time format, using current time")

# Generate report
if st.button("🚀 Generate Today's Report", type="primary"):
    try:
        with st.spinner("🌌 Calculating planetary cycles..."):
            start_time = time.time()
            report, price_levels, daily_cycles, intraday_levels, sell_zones, buy_zones, high_prob_times = generate_daily_planetary_report(
                symbol, current_price, tehran_time)
            elapsed_time = time.time() - start_time
            
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
        
    except Exception as e:
        st.error(f"❌ Error: {e}")

# Sidebar
with st.sidebar:
    st.markdown("### 🇮🇳 For Indian Traders")
    st.markdown("""
    **Perfect for NSE/BSE:**
    - 🕘 All times in **IST**
    - 📊 **Nifty/Bank Nifty** optimized
    - ⚡ **Scalping levels** 
    - 🎯 **Intraday range**: ±0.3% to ±5%
    
    **Zone Guide:**
    - 🔴 **SELL ZONES** = Resistance levels
    - 🟢 **BUY ZONES** = Support levels  
    - ⚡ **Prime targets** = Within ±1%
    """)
    
    st.markdown("### 🎯 Trading Zone Priorities")
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
    
    st.markdown("### 🎯 Example Trading Setup")
    st.markdown("""
    ```
    🚨 SELL ZONE ALERT:
    10:30 IST - Mars Resistance 
    Price: 24,680 (+0.35%)
    Action: SELL on approach
    
    🚨 BUY ZONE ALERT:  
    13:20 IST - Venus Support
    Price: 24,520 (-0.30%)
    Action: BUY on test
    ```
    """)
    
    st.markdown("### ⚠️ Risk Management")
    st.markdown("""
    - Use **stop losses** at next level
    - **Position size** based on zone strength
    - **Time windows** show best entry/exit
    - **Multiple confirmations** for major trades
    """)
