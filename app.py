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

# Planetary cycle characteristics
PLANETARY_CYCLES = {
    "Sun": {"cycle_hours": 24, "major_degrees": [0, 90, 180, 270], "price_multiplier": 24.5, "influence": "Major trend direction"},
    "Moon": {"cycle_hours": 2.2, "major_degrees": [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330], "price_multiplier": 18.7, "influence": "Intraday volatility spikes"},
    "Mercury": {"cycle_hours": 48, "major_degrees": [0, 45, 90, 135, 180, 225, 270, 315], "price_multiplier": 21.3, "influence": "News-driven moves"},
    "Venus": {"cycle_hours": 72, "major_degrees": [0, 60, 120, 180, 240, 300], "price_multiplier": 26.8, "influence": "Value-based support/resistance"},
    "Mars": {"cycle_hours": 96, "major_degrees": [0, 90, 180, 270], "price_multiplier": 19.2, "influence": "Aggressive breakouts/breakdowns"},
    "Jupiter": {"cycle_hours": 168, "major_degrees": [0, 120, 240], "price_multiplier": 31.4, "influence": "Major support zones"},
    "Saturn": {"cycle_hours": 336, "major_degrees": [0, 90, 180, 270], "price_multiplier": 15.9, "influence": "Strong resistance barriers"},
    "Uranus": {"cycle_hours": 504, "major_degrees": [0, 180], "price_multiplier": 22.1, "influence": "Sudden reversals"},
    "Neptune": {"cycle_hours": 720, "major_degrees": [0, 180], "price_multiplier": 17.6, "influence": "Deceptive moves"},
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
            planet_data[name] = {"longitude": 0, "latitude": 0, "distance": 1, "speed": 0, "sign": "Aries", "degree_in_sign": 0}
    
    return planet_data

def get_zodiac_sign(longitude):
    """Get zodiac sign from longitude"""
    signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    return signs[int(longitude // 30)]

def calculate_planetary_price_levels(planet_data, current_price, symbol):
    """Calculate specific price levels for each planet"""
    price_scale = max(1, current_price / 1000)  # Dynamic scaling
    price_levels = {}
    
    for planet_name, data in planet_data.items():
        if planet_name in PLANETARY_CYCLES:
            cycle_info = PLANETARY_CYCLES[planet_name]
            base_price = data["longitude"] * cycle_info["price_multiplier"] * price_scale
            
            # Calculate multiple levels for each planet
            levels = {
                "Primary": base_price,
                "Secondary": base_price * 1.05,  # 5% above
                "Support": base_price * 0.95,    # 5% below
                "Extended": base_price * 1.10    # 10% extension
            }
            
            price_levels[planet_name] = {
                "current_degree": data["longitude"],
                "speed": data["speed"],
                "sign": f"{data['sign']} {data['degree_in_sign']:.2f}°",
                "levels": levels,
                "influence": cycle_info["influence"],
                "cycle_hours": cycle_info["cycle_hours"]
            }
    
    return price_levels

def calculate_todays_time_cycles(planet_data, base_time_ist):
    """Calculate today's critical planetary time cycles in IST"""
    daily_cycles = []
    
    for planet_name, data in planet_data.items():
        if planet_name in PLANETARY_CYCLES:
            cycle_info = PLANETARY_CYCLES[planet_name]
            current_degree = data["longitude"] % 360
            speed_per_hour = data["speed"] / 24 if data["speed"] != 0 else 0.01
            
            # Calculate time to next critical degrees for today
            for target_degree in cycle_info["major_degrees"]:
                degrees_to_travel = (target_degree - current_degree) % 360
                if degrees_to_travel > 180:
                    degrees_to_travel = degrees_to_travel - 360
                
                # Only show cycles within next 24 hours
                if speed_per_hour != 0:
                    hours_to_target = degrees_to_travel / speed_per_hour
                    
                    if 0 <= hours_to_target <= 24:  # Today's cycles only
                        cycle_time = base_time_ist + timedelta(hours=hours_to_target)
                        
                        daily_cycles.append({
                            "planet": planet_name,
                            "target_degree": target_degree,
                            "current_degree": current_degree,
                            "time_ist": cycle_time,
                            "hours_away": hours_to_target,
                            "market_impact": get_cycle_impact(planet_name, target_degree),
                            "trading_action": get_trading_action(planet_name, target_degree),
                            "price_effect": get_price_effect(planet_name, target_degree)
                        })
    
    return sorted(daily_cycles, key=lambda x: x["hours_away"])

def get_cycle_impact(planet, degree):
    """Get market impact for specific planetary degrees"""
    impacts = {
        ("Sun", 0): "🌅 Market open energy - strong directional moves",
        ("Sun", 90): "🌞 Midday peak - trend confirmation or reversal", 
        ("Sun", 180): "🌇 Evening - profit taking begins",
        ("Sun", 270): "🌙 Night preparation - position adjustments",
        
        ("Moon", 0): "🌑 New lunar cycle - volatility spike expected",
        ("Moon", 90): "🌓 Quarter tension - sharp price swings",
        ("Moon", 180): "🌕 Full energy - major reversals possible",
        ("Moon", 270): "🌗 Waning energy - momentum fadeouts",
        
        ("Venus", 0): "💎 Value reassessment - support test",
        ("Venus", 60): "💰 Harmony aspect - mild bullish support",
        ("Venus", 120): "✨ Trine energy - strong support holds",
        ("Venus", 180): "⚖️ Opposition - resistance at highs",
        
        ("Mars", 0): "⚔️ Aggressive phase begins - breakout setup",
        ("Mars", 90): "💥 Square tension - sharp corrections",
        ("Mars", 180): "🛡️ Opposition force - strong resistance",
        ("Mars", 270): "⚡ Final push - exhaustion moves",
        
        ("Jupiter", 0): "🚀 Expansion phase - major trend begins",
        ("Jupiter", 120): "📈 Trine support - strong buying zone",
        ("Jupiter", 240): "🔄 Completion - trend maturity",
        
        ("Saturn", 0): "🏔️ Restriction begins - strong barriers",
        ("Saturn", 90): "⛔ Square pressure - selling climax",
        ("Saturn", 180): "🚫 Opposition wall - major resistance",
        ("Saturn", 270): "⚰️ Final test - capitulation bottom"
    }
    
    return impacts.get((planet, degree), f"{planet} {degree}° - moderate influence")

def get_trading_action(planet, degree):
    """Get specific trading actions for planetary cycles"""
    actions = {
        ("Sun", 0): "🔥 BUY momentum - trend following favored",
        ("Sun", 90): "⚡ MONITOR - confirm direction",
        ("Sun", 180): "💰 TAKE PROFITS - book gains",
        ("Sun", 270): "😴 REDUCE SIZE - limited activity",
        
        ("Moon", 0): "📉 REDUCE POSITIONS - high volatility",
        ("Moon", 90): "⚠️ TIGHT STOPS - expect whipsaws", 
        ("Moon", 180): "🔄 REVERSAL TRADES - fade extremes",
        ("Moon", 270): "📊 CONSOLIDATION - range trading",
        
        ("Venus", 0): "🛒 VALUE BUYING - look for entries",
        ("Venus", 180): "🚨 SELL RALLIES - resistance area",
        
        ("Mars", 0): "🚀 MOMENTUM LONG - aggressive entries",
        ("Mars", 90): "🛡️ DEFENSIVE - protect positions",
        ("Mars", 180): "📉 SHORT RALLIES - resistance trade",
        
        ("Jupiter", 0): "📈 MAJOR LONG - trend following",
        ("Jupiter", 120): "💪 ADD LONGS - strong support",
        
        ("Saturn", 0): "⛔ AVOID LONGS - resistance zone",
        ("Saturn", 90): "📉 SHORT SETUP - selling pressure",
        ("Saturn", 180): "🚫 MAJOR SHORT - strong resistance"
    }
    
    return actions.get((planet, degree), f"MONITOR {planet} influence")

def get_price_effect(planet, degree):
    """Get expected price movement effect"""
    effects = {
        ("Sun", 0): "+2% to +4%", ("Sun", 90): "±1% to ±3%", ("Sun", 180): "-1% to -2%",
        ("Moon", 0): "±3% to ±6%", ("Moon", 90): "±2% to ±5%", ("Moon", 180): "±4% to ±7%",
        ("Venus", 0): "+1% to +2%", ("Venus", 180): "-1% to -3%",
        ("Mars", 0): "+3% to +6%", ("Mars", 90): "-2% to -4%", ("Mars", 180): "-3% to -5%",
        ("Jupiter", 0): "+4% to +8%", ("Jupiter", 120): "+2% to +4%",
        ("Saturn", 0): "-2% to -5%", ("Saturn", 90): "-3% to -6%", ("Saturn", 180): "-4% to -8%"
    }
    
    return effects.get((planet, degree), "±1% to ±2%")

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
    
    # Generate report
    report = f"""
# 🌟 Daily Planetary Cycles & Price Levels Report
## {symbol} Trading - {tehran_time.strftime('%Y-%m-%d')}

### ⏰ Time Base
- **Tehran Time**: {tehran_time.strftime('%H:%M:%S')} 🇮🇷
- **Indian Standard Time**: **{ist_time.strftime('%H:%M:%S')}** 🇮🇳  
- **Current {symbol} Price**: **${current_price:,.2f}**

---

## 🎯 Today's Planetary Price Levels & Resistance Zones

| Planet | Current Position | Primary Level | Support | Resistance | Extended Target | Influence Type |
|--------|------------------|---------------|---------|------------|-----------------|----------------|"""
    
    for planet_name, data in price_levels.items():
        primary = data["levels"]["Primary"]
        support = data["levels"]["Support"] 
        secondary = data["levels"]["Secondary"]
        extended = data["levels"]["Extended"]
        
        # Determine if levels are support or resistance based on current price
        resistance_level = primary if primary > current_price else secondary
        support_level = support if support < current_price else primary
        
        report += f"""
| **{planet_name}** | {data['sign']} | ${primary:,.0f} | ${support_level:,.0f} | ${resistance_level:,.0f} | ${extended:,.0f} | {data['influence']} |"""

    # Today's critical time cycles
    report += f"""

---

## ⏱️ Today's Critical Planetary Time Cycles (IST)

| Time (IST) | Planet | Event | Market Impact | Trading Action | Expected Move | Hours Away |
|------------|--------|-------|---------------|----------------|---------------|------------|"""
    
    for cycle in daily_cycles[:12]:  # Show next 12 cycles
        time_str = cycle["time_ist"].strftime("%H:%M")
        hours_str = f"{cycle['hours_away']:+.1f}h"
        
        report += f"""
| **{time_str}** | {cycle['planet']} | {cycle['planet']} @ {cycle['target_degree']}° | {cycle['market_impact']} | {cycle['trading_action']} | {cycle['price_effect']} | {hours_str} |"""

    # Current planetary strength analysis
    report += f"""

---

## 💪 Current Planetary Strength & Influence Rankings

| Rank | Planet | Strength | Current Impact on {symbol} | Speed (°/day) | Distance from Critical | Action Priority |
|------|--------|----------|----------------------------|---------------|----------------------|----------------|"""
    
    # Calculate planetary strength based on speed and proximity to critical degrees
    planetary_strength = []
    for planet_name, data in planet_data.items():
        if planet_name in PLANETARY_CYCLES:
            current_deg = data["longitude"] % 360
            critical_degrees = PLANETARY_CYCLES[planet_name]["major_degrees"]
            
            # Find closest critical degree
            min_distance = min([abs(current_deg - cd) for cd in critical_degrees] + 
                             [abs(current_deg - (cd + 360)) for cd in critical_degrees if cd < current_deg])
            
            # Calculate strength (closer to critical degrees = stronger)
            strength_score = 10 - min_distance if min_distance <= 10 else 1
            strength_score *= abs(data["speed"])  # Faster planets have more immediate impact
            
            planetary_strength.append({
                "planet": planet_name,
                "strength_score": strength_score,
                "speed": data["speed"],
                "distance_to_critical": min_distance,
                "current_degree": current_deg
            })
    
    # Sort by strength
    planetary_strength.sort(key=lambda x: x["strength_score"], reverse=True)
    
    for i, planet_info in enumerate(planetary_strength):
        planet = planet_info["planet"]
        strength = "🔥 VERY HIGH" if planet_info["strength_score"] > 50 else \
                  "⚡ HIGH" if planet_info["strength_score"] > 20 else \
                  "📊 MODERATE" if planet_info["strength_score"] > 5 else "📉 LOW"
        
        impact = get_current_impact(planet, planet_info["distance_to_critical"])
        priority = "🚨 URGENT" if i < 2 else "⚠️ IMPORTANT" if i < 4 else "📋 MONITOR"
        
        report += f"""
| {i+1} | **{planet}** | {strength} | {impact} | {planet_info['speed']:+.4f} | {planet_info['distance_to_critical']:.1f}° | {priority} |"""

    # Key trading times for today
    next_major_events = [cycle for cycle in daily_cycles if cycle["hours_away"] <= 8][:5]
    
    report += f"""

---

## 🚀 Key Trading Times for Today (Next 8 Hours)

| Exact Time (IST) | Planet Event | Action Required | Price Target | Risk Level |
|------------------|--------------|-----------------|--------------|------------|"""
    
    for event in next_major_events:
        time_str = event["time_ist"].strftime("%H:%M:%S")
        price_target = get_price_target(current_price, event["planet"], event["target_degree"])
        risk = "🔴 HIGH" if event["planet"] in ["Mars", "Saturn"] else "🟡 MEDIUM" if event["planet"] in ["Moon", "Mercury"] else "🟢 LOW"
        
        report += f"""
| **{time_str}** | {event['planet']} @ {event['target_degree']}° | {event['trading_action']} | ${price_target:,.0f} | {risk} |"""

    # Summary and recommendations
    strongest_planet = planetary_strength[0]["planet"]
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
- **{next_major_cycle['time_ist'].strftime('%H:%M IST')}**: {next_major_cycle['planet']} reaches {next_major_cycle['target_degree']}°
- **Expected Impact**: {next_major_cycle['market_impact']}
- **Trading Strategy**: {next_major_cycle['trading_action']}
- **Price Effect**: {next_major_cycle['price_effect']}"""
    
    # Key resistance/support for today
    current_above = [p for p, data in price_levels.items() if data["levels"]["Primary"] > current_price]
    current_below = [p for p, data in price_levels.items() if data["levels"]["Primary"] < current_price]
    
    if current_above:
        closest_resistance = min(current_above, key=lambda p: price_levels[p]["levels"]["Primary"] - current_price)
        resistance_price = price_levels[closest_resistance]["levels"]["Primary"]
        report += f"""

### 🚧 Next Major Resistance: **{closest_resistance} @ ${resistance_price:,.0f}**
- **Distance**: +${resistance_price - current_price:,.0f} ({((resistance_price/current_price - 1) * 100):+.1f}%)
- **Strategy**: Monitor for rejection, consider shorts on approach with volume"""
    
    if current_below:
        closest_support = max(current_below, key=lambda p: price_levels[p]["levels"]["Primary"])
        support_price = price_levels[closest_support]["levels"]["Primary"]
        report += f"""

### 🛡️ Next Major Support: **{closest_support} @ ${support_price:,.0f}**  
- **Distance**: ${support_price - current_price:,.0f} ({((support_price/current_price - 1) * 100):+.1f}%)
- **Strategy**: Look for bounces, consider longs on successful test"""

    report += f"""

### 🎲 Today's Probability Assessment:
- **Bullish Scenario (35%)**: {strongest_planet} supports upward momentum
- **Bearish Scenario (40%)**: Planetary resistance creates selling pressure
- **Sideways (25%)**: Conflicting planetary forces create consolidation

### 🛡️ Risk Management for Today:
1. **Position Size**: Reduce by 30% during high-impact planetary events
2. **Stop Losses**: Use wider stops ±2% during Moon events  
3. **Time Limits**: No new positions 30 minutes before major planetary transitions
4. **Volume Confirmation**: Require 2x average volume for breakout trades

---

> **🚨 URGENT ALERT**: Next major planetary event in **{daily_cycles[0]['hours_away']:.1f} hours** at **{daily_cycles[0]['time_ist'].strftime('%H:%M IST')}**  
> **Action Required**: {daily_cycles[0]['trading_action']}  
> **Expected Move**: {daily_cycles[0]['price_effect']}
"""
    
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
        ("Sun", 0): 1.03, ("Sun", 90): 1.01, ("Sun", 180): 0.98,
        ("Moon", 0): 1.05, ("Moon", 90): 1.03, ("Moon", 180): 0.97,
        ("Venus", 0): 1.02, ("Venus", 180): 0.98,
        ("Mars", 0): 1.06, ("Mars", 90): 0.96, ("Mars", 180): 0.94,
        ("Jupiter", 0): 1.08, ("Jupiter", 120): 1.04,
        ("Saturn", 0): 0.95, ("Saturn", 90): 0.94, ("Saturn", 180): 0.92
    }
    
    multiplier = adjustments.get((planet, degree), 1.0)
    return current_price * multiplier

def create_planetary_timeline_chart(daily_cycles, current_time):
    """Create timeline chart of today's planetary events"""
    fig = go.Figure()
    
    # Create timeline
    times = [cycle["time_ist"] for cycle in daily_cycles[:10]]
    planets = [cycle["planet"] for cycle in daily_cycles[:10]]
    impacts = [len(cycle["market_impact"]) for cycle in daily_cycles[:10]]  # Use length as proxy for impact strength
    
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
            size=[20 + impact/10 for impact in impacts],
            color=[planet_colors.get(planet, "#666666") for planet in planets],
            line=dict(width=2, color="white")
        ),
        text=[cycle["time_ist"].strftime("%H:%M") for cycle in daily_cycles[:10]],
        textposition="middle center",
        textfont=dict(size=10, color="white"),
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

st.title("🌟 Daily Planetary Cycles & Price Levels")
st.markdown("*Focused daily report with exact planetary times and resistance levels*")

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
        with st.spinner("🌌 Calculating today's planetary cycles..."):
            start_time = time.time()
            report, price_levels, daily_cycles = generate_daily_planetary_report(
                symbol, current_price, tehran_time)
            elapsed_time = time.time() - start_time
            
        st.success(f"✅ Report generated in {elapsed_time:.2f} seconds")
        
        # Display main report
        st.markdown(report)
        
        # Timeline chart
        st.markdown("### 📊 Today's Planetary Events Timeline")
        ist_current = tehran_time + timedelta(hours=2)
        fig = create_planetary_timeline_chart(daily_cycles, ist_current)
        st.plotly_chart(fig, use_container_width=True)
        
        # Price levels chart
        st.markdown("### 💰 Planetary Price Levels Chart")
        
        fig2 = go.Figure()
        
        for planet, data in price_levels.items():
            levels = data["levels"]
            fig2.add_trace(go.Bar(
                name=f"{planet}",
                x=["Support", "Primary", "Resistance", "Extended"],
                y=[levels["Support"], levels["Primary"], levels["Secondary"], levels["Extended"]],
                text=[f"${v:,.0f}" for v in [levels["Support"], levels["Primary"], levels["Secondary"], levels["Extended"]]],
                textposition='auto'
            ))
        
        # Add current price line
        fig2.add_hline(y=current_price, line_dash="dash", line_color="red",
                      annotation_text=f"Current Price: ${current_price:,.0f}")
        
        fig2.update_layout(
            title=f"{symbol} Planetary Price Levels",
            xaxis_title="Level Type",
            yaxis_title="Price ($)",
            height=600
        )
        
        st.plotly_chart(fig2, use_container_width=True)
        
        # Quick action table
        st.markdown("### ⚡ Quick Action Summary")
        next_5_events = daily_cycles[:5]
        
        action_df = pd.DataFrame({
            "Time (IST)": [event["time_ist"].strftime("%H:%M:%S") for event in next_5_events],
            "Planet": [event["planet"] for event in next_5_events],
            "Event": [f"{event['planet']} @ {event['target_degree']}°" for event in next_5_events],
            "Action": [event["trading_action"] for event in next_5_events],
            "Expected Move": [event["price_effect"] for event in next_5_events],
            "Hours Away": [f"{event['hours_away']:+.1f}h" for event in next_5_events]
        })
        
        st.dataframe(action_df, use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ Error: {e}")
        st.exception(e)

# Sidebar info
with st.sidebar:
    st.markdown("### 🌟 Planetary Influence Guide")
    st.markdown("""
    **Time-Based Trading:**
    - 🌞 **Sun**: 24h major trend cycles
    - 🌙 **Moon**: 2.2h volatility cycles  
    - ☿ **Mercury**: 48h news-driven moves
    - ♀ **Venus**: 72h value-based levels
    - ♂ **Mars**: 96h aggressive breakouts
    - ♃ **Jupiter**: 168h major trends
    - ♄ **Saturn**: 336h resistance barriers
    
    **Critical Degrees:**
    - 0° = New cycle starts
    - 90° = Maximum tension
    - 180° = Opposition/reversal
    - 270° = Completion phase
    """)
