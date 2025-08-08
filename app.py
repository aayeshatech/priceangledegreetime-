import streamlit as st
import swisseph as swe
from datetime import datetime, timedelta
import time
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math

# Initialize ephemeris path
try:
    swe.set_ephe_path(None)
except Exception as e:
    st.error(f"Error initializing Swiss Ephemeris: {e}")
    st.stop()

# Zodiac signs and their characteristics
ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

ZODIAC_TRAITS = {
    "Aries": "Aggressive, impulsive trading",
    "Taurus": "Stable, resistance to change",
    "Gemini": "Volatile, quick reversals", 
    "Cancer": "Emotional reactions, support levels",
    "Leo": "Strong trends, leadership",
    "Virgo": "Analytical, precise movements",
    "Libra": "Balance, consolidation",
    "Scorpio": "Deep corrections, transformations",
    "Sagittarius": "Optimistic expansion",
    "Capricorn": "Conservative, long-term trends",
    "Aquarius": "Unexpected moves, innovation",
    "Pisces": "Confusion, lack of direction"
}

@st.cache_data
def get_planet_positions(julian_day):
    """Calculate planetary positions with enhanced data"""
    planets = {
        "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY,
        "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER,
        "Saturn": swe.SATURN, "Uranus": swe.URANUS, "Neptune": swe.NEPTUNE, 
        "Pluto": swe.PLUTO, "North Node": swe.MEAN_NODE
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
                "sign": ZODIAC_SIGNS[int(pos[0] // 30)],
                "degree_in_sign": pos[0] % 30
            }
        except Exception as e:
            st.error(f"Error calculating position for {name}: {e}")
            planet_data[name] = {
                "longitude": 0.0, "latitude": 0.0, "distance": 0.0, "speed": 0.0,
                "sign": "Aries", "degree_in_sign": 0.0
            }
    return planet_data

def calculate_aspects(planet_data):
    """Calculate planetary aspects with precise orbs"""
    aspects = []
    planets = list(planet_data.keys())
    
    aspect_types = {
        "Conjunction": (0, 8, "☌"),
        "Sextile": (60, 6, "⚹"), 
        "Square": (90, 8, "□"),
        "Trine": (120, 8, "△"),
        "Opposition": (180, 8, "☍")
    }
    
    for i in range(len(planets)):
        for j in range(i + 1, len(planets)):
            planet1, planet2 = planets[i], planets[j]
            angle = abs(planet_data[planet1]["longitude"] - planet_data[planet2]["longitude"])
            if angle > 180:
                angle = 360 - angle
                
            for aspect_name, (target_angle, max_orb, symbol) in aspect_types.items():
                orb = abs(angle - target_angle)
                if orb <= max_orb:
                    aspects.append({
                        "type": aspect_name,
                        "symbol": symbol,
                        "planet1": planet1,
                        "planet2": planet2,
                        "angle": angle,
                        "orb": orb,
                        "strength": "Strong" if orb <= 2 else "Moderate" if orb <= 5 else "Weak",
                        "exact_time": calculate_exact_aspect_time(planet_data, planet1, planet2, target_angle)
                    })
    
    return sorted(aspects, key=lambda x: x["orb"])

def calculate_exact_aspect_time(planet_data, planet1, planet2, target_angle):
    """Calculate when aspect becomes exact"""
    current_angle = abs(planet_data[planet1]["longitude"] - planet_data[planet2]["longitude"])
    if current_angle > 180:
        current_angle = 360 - current_angle
    
    speed_diff = planet_data[planet1]["speed"] - planet_data[planet2]["speed"]
    if abs(speed_diff) < 0.001:
        return "Stationary"
    
    angle_diff = target_angle - current_angle
    days_to_exact = angle_diff / speed_diff
    
    if abs(days_to_exact) > 30:
        return f"{abs(days_to_exact):.0f} days ({'approaching' if days_to_exact > 0 else 'separating'})"
    else:
        hours_to_exact = days_to_exact * 24
        return f"{abs(hours_to_exact):.1f} hours ({'approaching' if hours_to_exact > 0 else 'separating'})"

def calculate_resistance_support_levels(symbol, current_price, planet_data):
    """Calculate dynamic support/resistance based on planetary positions"""
    levels = {}
    price_scale = max(1, current_price / 1000)
    
    # Primary planetary resistance formulas
    venus_level = planet_data["Venus"]["longitude"] * 25.0 * price_scale
    mars_level = planet_data["Mars"]["longitude"] * 18.5 * price_scale  
    jupiter_level = planet_data["Jupiter"]["longitude"] * 22.3 * price_scale
    saturn_level = planet_data["Saturn"]["longitude"] * 15.8 * price_scale
    
    # Aspect-based levels
    mars_saturn_angle = abs(planet_data["Mars"]["longitude"] - planet_data["Saturn"]["longitude"]) % 360
    venus_jupiter_angle = abs(planet_data["Venus"]["longitude"] - planet_data["Jupiter"]["longitude"]) % 360
    sun_moon_angle = abs(planet_data["Sun"]["longitude"] - planet_data["Moon"]["longitude"]) % 360
    
    levels = {
        "Venus Resistance": {
            "price": venus_level,
            "distance": venus_level - current_price,
            "strength": "Strong" if abs(venus_level - current_price) < 50 * price_scale else "Moderate",
            "type": "Resistance" if venus_level > current_price else "Support"
        },
        "Mars Level": {
            "price": mars_level,
            "distance": mars_level - current_price,
            "strength": "Strong" if abs(mars_level - current_price) < 30 * price_scale else "Moderate",
            "type": "Resistance" if mars_level > current_price else "Support"
        },
        "Jupiter Support": {
            "price": jupiter_level,
            "distance": jupiter_level - current_price,
            "strength": "Strong" if abs(jupiter_level - current_price) < 40 * price_scale else "Weak",
            "type": "Support" if jupiter_level < current_price else "Resistance"
        },
        "Saturn Barrier": {
            "price": saturn_level,
            "distance": saturn_level - current_price,
            "strength": "Very Strong" if abs(saturn_level - current_price) < 20 * price_scale else "Moderate",
            "type": "Resistance" if saturn_level > current_price else "Support"
        },
        "Mars-Saturn Angle": {
            "price": mars_saturn_angle * 19.05 * price_scale,
            "distance": (mars_saturn_angle * 19.05 * price_scale) - current_price,
            "strength": "Critical",
            "type": "Major Resistance"
        },
        "Venus-Jupiter Harmony": {
            "price": venus_jupiter_angle * 23.4 * price_scale,
            "distance": (venus_jupiter_angle * 23.4 * price_scale) - current_price,
            "strength": "Moderate",
            "type": "Support Zone"
        }
    }
    
    return levels

def calculate_time_windows(planet_data, base_time):
    """Calculate critical trading time windows"""
    windows = []
    
    # Fast-moving planet transits
    moon_speed = planet_data["Moon"]["speed"]  # ~13 degrees per day
    mercury_speed = planet_data["Mercury"]["speed"]  # ~1.2 degrees per day
    venus_speed = planet_data["Venus"]["speed"]  # ~1.6 degrees per day
    
    # Calculate when planets hit critical degrees
    critical_degrees = [0, 15, 30, 45, 60, 90, 120, 135, 150, 180, 210, 225, 240, 270, 300, 315, 330, 345]
    
    for planet_name, data in planet_data.items():
        if planet_name in ["Moon", "Mercury", "Venus", "Mars"]:
            current_degree = data["longitude"] % 360
            
            for critical_deg in critical_degrees:
                degrees_to_travel = (critical_deg - current_degree) % 360
                if degrees_to_travel > 180:
                    degrees_to_travel = degrees_to_travel - 360
                    
                if abs(degrees_to_travel) <= 5:  # Within 5 degrees
                    hours_to_transit = degrees_to_travel / (data["speed"] / 24) if data["speed"] != 0 else 999
                    
                    if abs(hours_to_transit) <= 48:  # Within 48 hours
                        transit_time = base_time + timedelta(hours=hours_to_transit)
                        
                        windows.append({
                            "planet": planet_name,
                            "event": f"{planet_name} @ {critical_deg}°",
                            "time": transit_time,
                            "hours_from_now": hours_to_transit,
                            "market_impact": get_transit_impact(planet_name, critical_deg),
                            "trading_advice": get_trading_advice(planet_name, critical_deg)
                        })
    
    return sorted(windows, key=lambda x: abs(x["hours_from_now"]))[:8]  # Top 8 upcoming events

def get_transit_impact(planet, degree):
    """Get market impact for planetary transits"""
    impacts = {
        ("Moon", 0): "New cycle begins - volatility spike",
        ("Moon", 90): "Quarter moon tension - price swings", 
        ("Moon", 180): "Full moon peak - trend reversals",
        ("Moon", 270): "Last quarter - profit taking",
        ("Mercury", 0): "Communication clarity - trend confirmation",
        ("Mercury", 90): "Information conflicts - fake breakouts",
        ("Venus", 0): "Value reassessment - support tests",
        ("Venus", 180): "Value extremes - resistance hits",
        ("Mars", 0): "Aggressive buying/selling",
        ("Mars", 90): "Sharp corrections - stop losses hit"
    }
    
    # Find closest match
    for (p, d), impact in impacts.items():
        if p == planet and abs(d - degree) <= 15:
            return impact
    
    return f"{planet} transit - moderate impact"

def get_trading_advice(planet, degree):
    """Get specific trading advice for transits"""
    advice_map = {
        ("Moon", 0): "Reduce position sizes, high volatility expected",
        ("Moon", 90): "Set wider stops, expect whipsaws",
        ("Moon", 180): "Watch for reversals, take profits",
        ("Mercury", 0): "Good for trend following",
        ("Mercury", 90): "Avoid new positions, confusion likely",
        ("Venus", 0): "Look for value entries",
        ("Mars", 0): "Momentum trades favored",
        ("Mars", 90): "Defensive positioning advised"
    }
    
    for (p, d), advice in advice_map.items():
        if p == planet and abs(d - degree) <= 15:
            return advice
    
    return "Monitor price action carefully"

def generate_comprehensive_report(symbol, current_price, tehran_time=None):
    """Generate comprehensive financial astrology report"""
    if tehran_time is None:
        tehran_time = datetime.now()
    
    # Time conversions
    utc_time = tehran_time - timedelta(hours=3, minutes=30)
    ist_time = tehran_time + timedelta(hours=2)
    julian_day = swe.julday(utc_time.year, utc_time.month, utc_time.day, 
                            utc_time.hour + utc_time.minute/60 + utc_time.second/3600)
    
    # Get planetary data
    planet_data = get_planet_positions(julian_day)
    aspects = calculate_aspects(planet_data)
    levels = calculate_resistance_support_levels(symbol, current_price, planet_data)
    time_windows = calculate_time_windows(planet_data, ist_time)
    
    # Generate report
    report = f"""
### Financial Astronomy Report for {symbol} Trading ({tehran_time.strftime('%Y-%m-%d')})
**Indian Standard Time (IST)** | **Current {symbol} Price: ${current_price:,.2f}**

---

### ⏰ Time Conversion
- **Tehran Time**: {tehran_time.strftime('%H:%M:%S')}  
- **Indian Standard Time (IST)**: **{ist_time.strftime('%H:%M:%S')}**  
- **UTC**: {utc_time.strftime('%H:%M:%S')}
- **Julian Day**: {julian_day:.6f}

---

### 🌟 Planetary Positions & Transits (IST {ist_time.strftime('%H:%M:%S')})
| Planet      | Longitude | Sign & Degree | Speed (°/day) | Distance (AU) | Financial Significance |
|-------------|-----------|---------------|---------------|---------------|------------------------|"""
    
    for name, data in planet_data.items():
        significance = {
            "Sun": "Overall market direction",
            "Moon": "Daily volatility & sentiment", 
            "Mercury": "News & communication impact",
            "Venus": "Value & support levels",
            "Mars": "Aggressive moves & resistance",
            "Jupiter": "Expansion & major trends",
            "Saturn": "Restrictions & long-term barriers",
            "Uranus": "Sudden reversals & innovation",
            "Neptune": "Deception & unclear trends", 
            "Pluto": "Major transformations",
            "North Node": "Destiny point & major cycles"
        }.get(name, "Secondary influence")
        
        report += f"""
| {name:<11} | {data['longitude']:>7.2f}° | {data['sign']} {data['degree_in_sign']:>5.2f}° | {data['speed']:>9.4f} | {data['distance']:>11.3f} | {significance} |"""

    # Resistance/Support Levels
    report += f"""

---

### 💰 {symbol} Support & Resistance Levels (Current: ${current_price:,.2f})
| Level Name | Price | Distance | Type | Strength | Trading Signal |
|------------|-------|----------|------|----------|----------------|"""
    
    for level_name, level_data in levels.items():
        distance_text = f"{level_data['distance']:+.2f}"
        signal = "STRONG SELL" if level_data['type'] == "Resistance" and abs(level_data['distance']) < 20 else \
                "STRONG BUY" if level_data['type'] == "Support" and abs(level_data['distance']) < 20 else \
                "MONITOR"
        
        report += f"""
| {level_name} | ${level_data['price']:,.2f} | {distance_text} | {level_data['type']} | {level_data['strength']} | {signal} |"""

    # Planetary Aspects
    report += f"""

---

### 🔍 Key Planetary Aspects & Influences
| Aspect | Planets | Current Angle | Orb | Strength | Market Impact | Exact Timing |
|--------|---------|---------------|-----|----------|---------------|--------------|"""
    
    for aspect in aspects[:6]:  # Show top 6 aspects
        impact = {
            "Conjunction": "Amplification of combined energies",
            "Sextile": "Mild positive influence", 
            "Square": "Tension & volatility",
            "Trine": "Harmonious flow & support",
            "Opposition": "Conflict & reversals"
        }.get(aspect["type"], "Mixed influence")
        
        report += f"""
| {aspect['type']} {aspect['symbol']} | {aspect['planet1']}-{aspect['planet2']} | {aspect['angle']:>6.2f}° | {aspect['orb']:>4.2f}° | {aspect['strength']} | {impact} | {aspect['exact_time']} |"""

    # Critical Time Windows  
    report += f"""

---

### ⏱️ Critical Time Windows & Planetary Transits
| Time (IST) | Event | Hours Away | Market Impact | Trading Advice |
|------------|-------|------------|---------------|----------------|"""
    
    for window in time_windows:
        time_str = window['time'].strftime('%H:%M')
        hours_away = f"{window['hours_from_now']:+.1f}h"
        
        report += f"""
| {time_str} | {window['event']} | {hours_away} | {window['market_impact']} | {window['trading_advice']} |"""

    # Moon Phase Analysis
    sun_moon_angle = abs(planet_data["Sun"]["longitude"] - planet_data["Moon"]["longitude"])
    moon_phase = "New Moon" if sun_moon_angle < 45 else \
                "Waxing Crescent" if sun_moon_angle < 90 else \
                "First Quarter" if sun_moon_angle < 135 else \
                "Waxing Gibbous" if sun_moon_angle < 180 else \
                "Full Moon" if sun_moon_angle < 225 else \
                "Waning Gibbous" if sun_moon_angle < 270 else \
                "Last Quarter" if sun_moon_angle < 315 else "Waning Crescent"

    report += f"""

---

### 🌙 Lunar Analysis & Market Sentiment
- **Current Moon Phase**: {moon_phase} ({sun_moon_angle:.1f}° separation)
- **Moon Sign**: {planet_data['Moon']['sign']} - {ZODIAC_TRAITS[planet_data['Moon']['sign']]}
- **Moon Speed**: {planet_data['Moon']['speed']:.2f}°/day ({'Fast' if planet_data['Moon']['speed'] > 13 else 'Slow'})
- **Lunar Impact**: {'High volatility expected' if sun_moon_angle < 45 or 135 < sun_moon_angle < 225 else 'Moderate volatility'}

---

### 📊 Trading Strategy Summary for {symbol} (${current_price:,.2f})

#### 🎯 Primary Signals:
"""
    
    # Find the strongest resistance/support levels
    closest_resistance = min([l for l in levels.values() if l['type'] == 'Resistance' and l['distance'] > 0], 
                           key=lambda x: x['distance'], default=None)
    closest_support = min([l for l in levels.values() if l['type'] == 'Support' and l['distance'] < 0], 
                         key=lambda x: abs(x['distance']), default=None)
    
    if closest_resistance:
        report += f"""
- **Next Resistance**: ${closest_resistance['price']:,.2f} ({closest_resistance['strength']} - {closest_resistance['distance']:+.2f} away)
- **Resistance Strategy**: Monitor for rejection, consider shorts if approach with high volume"""
    
    if closest_support:
        report += f"""
- **Next Support**: ${closest_support['price']:,.2f} ({closest_support['strength']} - {abs(closest_support['distance']):.2f} below)
- **Support Strategy**: Look for bounces, consider longs on successful test"""

    # Strongest aspects for trading
    strongest_aspect = aspects[0] if aspects else None
    if strongest_aspect:
        aspect_advice = {
            "Square": "High volatility - use tight stops and smaller positions",
            "Opposition": "Expect reversals - fade extremes", 
            "Conjunction": "Strong directional moves - trend following favored",
            "Trine": "Smooth trends - good for swing trading",
            "Sextile": "Mild positive bias - look for buying opportunities"
        }.get(strongest_aspect["type"], "Monitor price action")
        
        report += f"""

#### 🌟 Dominant Aspect: {strongest_aspect['type']} {strongest_aspect['symbol']} 
- **Planets**: {strongest_aspect['planet1']} - {strongest_aspect['planet2']}
- **Orb**: {strongest_aspect['orb']:.2f}° ({strongest_aspect['strength']})
- **Trading Impact**: {aspect_advice}
- **Timing**: {strongest_aspect['exact_time']}"""

    report += f"""

#### ⚠️ Risk Management:
- **Position Size**: Reduce by 25% during high volatility windows
- **Stop Loss**: Use wider stops during Moon-Mars aspects
- **Time Limits**: Avoid new positions 1 hour before major transits

#### 🎲 Probability Assessment:
- **Bullish Scenario**: 35% - Jupiter-Venus influences support bounce
- **Bearish Scenario**: 45% - Mars-Saturn creating resistance pressure  
- **Sideways**: 20% - Conflicting planetary forces create consolidation

---

### 💡 Key Insight for {symbol} Today

The cosmic landscape shows {aspects[0]['planet1']}-{aspects[0]['planet2']} {aspects[0]['type']} as the dominant influence, creating {'tension and volatility' if aspects[0]['type'] in ['Square', 'Opposition'] else 'supportive energy'} for {symbol}. 

**Current price of ${current_price:,.2f}** is positioned {'near critical resistance' if closest_resistance and closest_resistance['distance'] < 50 else 'in a neutral zone'}. 

**Key Times to Watch:**
{time_windows[0]['time'].strftime('- %H:%M IST')}: {time_windows[0]['event']} - {time_windows[0]['trading_advice']}
{time_windows[1]['time'].strftime('- %H:%M IST')}: {time_windows[1]['event']} - {time_windows[1]['trading_advice']}

> **Final Recommendation**: {'BEARISH BIAS' if aspects[0]['type'] in ['Square', 'Opposition'] else 'BULLISH BIAS'} - Trade with the dominant {aspects[0]['type']} energy. Use planetary levels for entries and exits.
"""
    
    return report, planet_data, aspects, levels, time_windows

def create_planetary_chart(planet_data, current_price, levels):
    """Create comprehensive planetary chart"""
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Planetary Positions (Degrees)', 'Support/Resistance Levels', 
                       'Planetary Speeds', 'Zodiac Distribution'),
        specs=[[{"type": "bar"}, {"type": "bar"}],
               [{"type": "scatter"}, {"type": "pie"}]]
    )
    
    # Planetary positions
    planets = list(planet_data.keys())
    longitudes = [planet_data[p]["longitude"] for p in planets]
    
    fig.add_trace(
        go.Bar(x=planets, y=longitudes, name="Longitude (°)", 
               marker_color="lightblue"),
        row=1, col=1
    )
    
    # Support/Resistance levels  
    level_names = list(levels.keys())
    level_prices = [levels[l]["price"] for l in level_names]
    colors = ['red' if levels[l]["type"] == "Resistance" else 'green' for l in level_names]
    
    fig.add_trace(
        go.Bar(x=level_names, y=level_prices, name="Price Levels",
               marker_color=colors),
        row=1, col=2
    )
    
    # Add current price line
    fig.add_hline(y=current_price, line_dash="dash", line_color="orange", 
                  annotation_text=f"Current Price: ${current_price}", row=1, col=2)
    
    # Planetary speeds
    speeds = [planet_data[p]["speed"] for p in planets]
    fig.add_trace(
        go.Scatter(x=planets, y=speeds, mode='markers+lines', name="Speed (°/day)",
                   marker=dict(size=10, color="purple")),
        row=2, col=1
    )
    
    # Zodiac distribution
    sign_counts = {}
    for planet in planet_data.values():
        sign = planet["sign"]
        sign_counts[sign] = sign_counts.get(sign, 0) + 1
    
    fig.add_trace(
        go.Pie(labels=list(sign_counts.keys()), values=list(sign_counts.values()),
               name="Zodiac Distribution"),
        row=2, col=2
    )
    
    fig.update_layout(height=800, showlegend=True, 
                      title_text="Comprehensive Planetary Analysis")
    return fig

# Streamlit Interface
st.set_page_config(layout="wide", page_title="Comprehensive Financial Astrology")

st.title("🌟 Comprehensive Financial Astrology Report Generator")
st.markdown("*Generate detailed planetary transit analysis with precise support/resistance levels for any trading symbol*")

# Input Section
col1, col2, col3 = st.columns(3)

with col1:
    symbol = st.text_input("Trading Symbol", value="GOLD", help="Enter any trading symbol (e.g., GOLD, BTC, EURUSD)")
    
with col2:
    current_price = st.number_input("Current Price ($)", min_value=0.01, value=2640.50, step=0.01,
                                   help="Enter the current market price")
    
with col3:
    tehran_time_str = st.text_input("Tehran Time (optional)", 
                                   value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                   help="Format: YYYY-MM-DD HH:MM:SS")

# Parse time
try:
    tehran_time = datetime.strptime(tehran_time_str, "%Y-%m-%d %H:%M:%S")
except ValueError:
    st.error("Invalid date format. Using current time.")
    tehran_time = datetime.now()

# Generate Report
if st.button("🚀 Generate Comprehensive Report", type="primary"):
    try:
        with st.spinner("🌌 Calculating planetary positions and market influences..."):
            start_time = time.time()
            report, planet_data, aspects, levels, time_windows = generate_comprehensive_report(
                symbol, current_price, tehran_time)
            elapsed_time = time.time() - start_time
            
        st.success(f"✅ Report generated in {elapsed_time:.2f} seconds")
        
        # Display report
        st.markdown(report)
        
        # Charts
        st.markdown("### 📊 Planetary Analysis Charts")
        fig = create_planetary_chart(planet_data, current_price, levels)
        st.plotly_chart(fig, use_container_width=True)
        
        # Data Tables
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🌍 Planetary Data")
            df_planets = pd.DataFrame(planet_data).T
            st.dataframe(df_planets, use_container_width=True)
            
        with col2:
            st.markdown("#### 🎯 Aspects Data") 
            if aspects:
                df_aspects = pd.DataFrame(aspects)
                st.dataframe(df_aspects, use_container_width=True)
            else:
                st.info("No major aspects currently active")
                
        # Export options
        st.markdown("### 📥 Export Options")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📄 Download Report as Text"):
                st.download_button(
                    label="Download Report",
                    data=report,
                    file_name=f"{symbol}_astrology_report_{tehran_time.strftime('%Y%m%d_%H%M')}.txt",
                    mime="text/plain"
                )
                
        with col2:
            if st.button("📊 Download Planetary Data"):
                csv_data = pd.DataFrame(planet_data).T.to_csv()
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name=f"{symbol}_planetary_data_{tehran_time.strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
                
    except Exception as e:
        st.error(f"❌ Error generating report: {str(e)}")
        st.exception(e)

# Sidebar with additional information
with st.sidebar:
    st.markdown("### 🌟 About Financial Astrology")
    st.markdown("""
    This tool combines ancient astrological wisdom with modern financial analysis:
    
    **Key Features:**
    - Real-time planetary positions
    - Dynamic support/resistance levels
    - Precise aspect calculations
    - Time-based trading windows
    - Moon phase analysis
    - Transit timing predictions
    
    **Planetary Influences:**
    - 🌞 **Sun**: Overall market direction
    - 🌙 **Moon**: Daily volatility & sentiment  
    - ☿ **Mercury**: News impact & communication
    - ♀ **Venus**: Value levels & support
    - ♂ **Mars**: Aggressive moves & resistance
    - ♃ **Jupiter**: Major trends & expansion
    - ♄ **Saturn**: Long-term barriers
    - ♅ **Uranus**: Sudden reversals
    - ♆ **Neptune**: Deception & uncertainty
    - ♇ **Pluto**: Major transformations
    """)
    
    st.markdown("### ⚠️ Disclaimer")
    st.markdown("""
    This tool is for educational and research purposes only. 
    Astrological analysis should not be the sole basis for trading decisions. 
    Always combine with technical analysis and risk management.
    """)
