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
    
    # Sort by time and return
    return sorted(intraday_levels, key=lambda x: x["time"])

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
    # Time conversions
    ist_time = tehran_time + timedelta(hours=2)
    utc_time = tehran_time - timedelta(hours=3, minutes=30)
    
    # Get planetary data
    julian_day = swe.julday(utc_time.year, utc_time.month, utc_time.day, 
                           utc_time.hour + utc_time.minute/60 + utc_time.second/3600)
    
    planet_data = get_planetary_positions_today(julian_day)
    price_levels = calculate_planetary_price_levels(planet_data, current_price, symbol)
    daily_cycles = calculate_todays_time_cycles(planet_data, ist_time)
    intraday_levels = calculate_intraday_support_levels(current_price, planet_data, ist_time)
    
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
    
    for planet_name, data in price_levels.items():
        levels = data["levels"]
        
        report += f"""
| **{planet_name}** | {data['sign']} | {levels['Major_Resistance']:,.0f} | {levels['Primary_Resistance']:,.0f} | {levels['Current_Level']:,.0f} | {levels['Primary_Support']:,.0f} | {levels['Major_Support']:,.0f} | {data['strength']:.0f}% |"""

    # Intraday time-based planetary levels
    report += f"""

---

## ⏰ Intraday Time-Based Planetary Levels (IST)

| Time (IST) | Price Level | Planet Level | Trading Signal | Influence |
|------------|-------------|--------------|----------------|-----------|"""
    
    for level in intraday_levels[:15]:  # Show next 15 time-based levels
        time_str = level["time"].strftime("%H:%M")
        influence_str = f"{level['influence_pct']:+.2f}%"
        
        report += f"""
| **{time_str}** | {level['price']:,.0f} | {level['planet']} {level['level_type']} | {level['signal']} | {influence_str} |"""

    # Today's critical time cycles
    report += f"""

---

## ⏱️ Today's Critical Planetary Time Cycles (IST)

| Time (IST) | Planet | Event | Trading Action | Expected Move | Hours Away |
|------------|--------|-------|----------------|---------------|------------|"""
    
    for cycle in daily_cycles[:10]:
        time_str = cycle["time_ist"].strftime("%H:%M")
        hours_str = f"{cycle['hours_away']:+.1f}h"
        
        report += f"""
| **{time_str}** | {cycle['planet']} | @ {cycle['target_degree']:.0f}° | {cycle['trading_action']} | {cycle['price_effect']} | {hours_str} |"""

    # Immediate trading opportunities
    report += f"""

---

## 🎯 Immediate Trading Opportunities (Within 3% Range)

| Planet Level | Price | Distance | % Move | Action |
|--------------|-------|----------|--------|--------|"""
    
    opportunity_count = 0
    for planet_name, data in price_levels.items():
        levels = data["levels"]
        for level_name, level_price in levels.items():
            if level_name not in ["Current_Level"] and opportunity_count < 8:
                distance_pct = abs((level_price - current_price) / current_price) * 100
                if distance_pct <= 3.0:
                    distance = level_price - current_price
                    action = "🚀 BUY ZONE" if distance < 0 else "🛑 SELL ZONE"
                    if abs(distance_pct) <= 1.0:
                        action = "⚡ PRIME TARGET"
                    
                    level_display = level_name.replace("_", " ")
                    
                    report += f"""
| {planet_name} {level_display} | {level_price:,.0f} | {distance:+.0f} | {distance_pct:+.2f}% | {action} |"""
                    
                    opportunity_count += 1
    
    if opportunity_count == 0:
        report += f"""
| No levels within 3% | Current market | 0 | 0.00% | Monitor wider ranges |"""

    # Key insights
    strongest_planet = max(price_levels.items(), key=lambda x: x[1]['strength'])[0]
    
    report += f"""

---

## 💡 Today's Key Insights

### 🎯 Dominant Influence: **{strongest_planet}**
- **Strength**: {price_levels[strongest_planet]['strength']:.0f}%
- **Position**: {price_levels[strongest_planet]['sign']}
- **Primary Action**: Focus on {strongest_planet.lower()} levels for best trades

### 📊 Trading Summary:
- **Bullish Bias**: Look for support at lower planetary levels
- **Bearish Bias**: Watch for resistance at higher planetary levels  
- **Range Trading**: Use minor levels for scalping opportunities
- **Position Trading**: Use major levels for swing trades

---

> **🚨 Next Major Event**: {daily_cycles[0]['time_ist'].strftime('%H:%M IST')} - {daily_cycles[0]['planet']} @ {daily_cycles[0]['target_degree']:.0f}°  
> **Expected Move**: {daily_cycles[0]['price_effect']}  
> **Action**: {daily_cycles[0]['trading_action']}
"""
    
    return report, price_levels, daily_cycles, intraday_levels

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
            report, price_levels, daily_cycles, intraday_levels = generate_daily_planetary_report(
                symbol, current_price, tehran_time)
            elapsed_time = time.time() - start_time
            
        st.success(f"✅ Report generated in {elapsed_time:.2f} seconds")
        
        # Display main report
        st.markdown(report)
        
        # Simple chart
        st.markdown("### 📊 Support/Resistance Levels")
        
        chart_data = []
        for planet, data in price_levels.items():
            chart_data.append({
                "Planet": planet,
                "Support": data["levels"]["Primary_Support"],
                "Current": current_price,
                "Resistance": data["levels"]["Primary_Resistance"]
            })
        
        df = pd.DataFrame(chart_data)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(name='Support', x=df['Planet'], y=df['Support'], marker_color='green'))
        fig.add_trace(go.Bar(name='Resistance', x=df['Planet'], y=df['Resistance'], marker_color='red'))
        fig.add_hline(y=current_price, line_dash="dash", line_color="orange", 
                      annotation_text=f"Current: {current_price:,.0f}")
        
        fig.update_layout(title=f"{symbol} Support/Resistance Levels", height=400)
        st.plotly_chart(fig, use_container_width=True)
        
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
    
    **Level Guide:**
    - 🟢 **Support** = Buy zones
    - 🔴 **Resistance** = Sell zones  
    - ⚡ **Prime targets** = Within ±1%
    """)
    
    st.markdown("### ⏰ Intraday Time Levels")
    st.markdown("""
    **Planetary Time Cycles:**
    - 🌙 **Moon**: Every 1.5h - Scalping
    - ☿ **Mercury**: Every 3h - News levels
    - ♀ **Venus**: Every 4h - Value zones
    - ♂ **Mars**: Every 2h - Breakout levels
    - ♃ **Jupiter**: Every 6h - Major levels
    
    **Trading Signals:**
    - **PRIME SCALP** - Best scalping opportunity
    - **NEWS WATCH** - Monitor for news impact
    - **VALUE BUY/SELL** - Value-based trades
    - **MOMENTUM TRADE** - Breakout opportunities
    """)
    
    st.markdown("### 📊 Example Levels")
    st.markdown("""
    ```
    10:30 IST - 24,520 - Moon Support - PRIME SCALP
    11:45 IST - 24,680 - Mercury Level - NEWS WATCH  
    13:20 IST - 24,590 - Venus Zone - VALUE BUY
    14:15 IST - 24,745 - Mars Breakout - MOMENTUM
    ```
    """)
