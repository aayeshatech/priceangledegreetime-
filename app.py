import streamlit as st
import swisseph as swe
from datetime import datetime, timedelta
import time

# Initialize ephemeris path at the module level
swe.set_ephe_path(None)  # Use default ephemeris path

# Cache the planetary position calculations
@st.cache_data
def get_planet_positions(julian_day):
    """Calculate and cache planetary positions"""
    planets = {
        "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY,
        "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER,
        "Saturn": swe.SATURN, "Uranus": swe.URANUS, "Neptune": swe.NEPTUNE, "Pluto": swe.PLUTO
    }
    
    planet_data = {}
    for name, planet_id in planets.items():
        pos = swe.calc_ut(julian_day, planet_id)[0]
        planet_data[name] = {
            "longitude": pos[0],
            "latitude": pos[1],
            "distance": pos[2],
            "speed": pos[3]
        }
    return planet_data

def generate_financial_astronomy_report(symbol, current_price, tehran_time=None):
    """Generate a financial astronomy report for any trading symbol"""
    # Validate inputs
    if not isinstance(symbol, str) or not symbol:
        raise ValueError("Symbol must be a non-empty string")
    if not isinstance(current_price, (int, float)) or current_price <= 0:
        raise ValueError("Current price must be a positive number")
    
    # Set default time if not provided
    if tehran_time is None:
        tehran_time = datetime.now()
    
    # Convert Tehran time to UTC and IST
    utc_time = tehran_time - timedelta(hours=3, minutes=30)
    ist_time = tehran_time + timedelta(hours=2)
    
    # Calculate Julian Day
    julian_day = swe.julday(utc_time.year, utc_time.month, utc_time.day, 
                            utc_time.hour + utc_time.minute/60 + utc_time.second/3600)
    
    # Get cached planetary positions
    planet_data = get_planet_positions(julian_day)
    
    # Determine Moon's zodiac sign
    zodiac_signs = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    moon_longitude = planet_data["Moon"]["longitude"]
    moon_sign = zodiac_signs[int(moon_longitude // 30)]
    
    # Calculate key aspects
    aspects = []
    
    # Mars-Saturn opposition
    mars_saturn_angle = abs(planet_data["Mars"]["longitude"] - planet_data["Saturn"]["longitude"]) % 360
    mars_saturn_orb = min(mars_saturn_angle, 360 - mars_saturn_angle)
    if mars_saturn_orb < 5:
        aspects.append({
            "type": "Opposition",
            "planets": "Mars ☋ Saturn",
            "angle": mars_saturn_angle,
            "orb": mars_saturn_orb,
            "impact": f"Strong resistance at ${mars_saturn_angle * 19.05:.2f}"
        })
    
    # Venus-Jupiter conjunction
    venus_jupiter_angle = abs(planet_data["Venus"]["longitude"] - planet_data["Jupiter"]["longitude"]) % 360
    venus_jupiter_orb = min(venus_jupiter_angle, 360 - venus_jupiter_angle)
    if venus_jupiter_orb < 5:
        aspects.append({
            "type": "Conjunction",
            "planets": "Venus ☍ Jupiter",
            "angle": venus_jupiter_angle,
            "orb": venus_jupiter_orb,
            "impact": "Mild bullish support"
        })
    
    # Venus-Mars square
    venus_mars_angle = abs(planet_data["Venus"]["longitude"] - planet_data["Mars"]["longitude"]) % 360
    venus_mars_orb = min(abs(venus_mars_angle - 90), abs(venus_mars_angle - 270))
    if venus_mars_orb < 10:
        aspects.append({
            "type": "Square",
            "planets": "Venus □ Mars",
            "angle": venus_mars_angle,
            "orb": venus_mars_orb,
            "impact": "Volatility warning"
        })
    
    # Calculate resistance levels with dynamic scaling
    price_scale = max(1, current_price / 1000)  # Scale for high-priced assets
    venus_resistance = planet_data["Venus"]["longitude"] * 20.02 * price_scale
    mars_saturn_resistance = mars_saturn_angle * 19.05 * price_scale
    
    # Pre-calculate values for trading strategy
    is_mars_saturn_above = mars_saturn_resistance > current_price
    price_diff = abs(mars_saturn_resistance - current_price)
    
    # Trading strategy values with bounds
    target_price = max(0, mars_saturn_resistance - price_diff * 1.5 if is_mars_saturn_above else mars_saturn_resistance + price_diff * 1.5)
    stop_loss = max(0, mars_saturn_resistance + price_diff * 0.3 if is_mars_saturn_above else mars_saturn_resistance - price_diff * 0.3)
    entry_price = max(0, mars_saturn_resistance - price_diff * 0.2 if is_mars_saturn_above else mars_saturn_resistance + price_diff * 0.2)
    
    # Venus-Jupiter bounce target
    venus_jupiter_target = current_price + (venus_jupiter_orb * 10 * price_scale)
    
    # Price scenarios
    rejection_target = max(0, mars_saturn_resistance - price_diff * 1.5 if is_mars_saturn_above else mars_saturn_resistance + price_diff * 1.5)
    breakout_target = max(0, mars_saturn_resistance + price_diff * 2 if is_mars_saturn_above else mars_saturn_resistance - price_diff * 2)
    range_low = min(current_price, mars_saturn_resistance)
    range_high = max(current_price, mars_saturn_resistance)
    
    # Risk factor calculations
    squeeze_target = max(0, mars_saturn_resistance + price_diff * 2 if is_mars_saturn_above else mars_saturn_resistance - price_diff * 2)
    
    # Probability calculations
    rejection_prob = 85 if mars_saturn_orb < 1 else 70 if mars_saturn_orb < 3 else 50
    breakout_prob = 15 if mars_saturn_orb < 1 else 30 if mars_saturn_orb < 3 else 50
    
    # Generate report
    report = f"""
### Financial Astronomy Report for {symbol} Trading ({tehran_time.strftime('%Y-%m-%d')})
**Indian Standard Time (IST)** | **Current {symbol} Price: ${current_price}**
---
### ⏰ Time Conversion
- **Tehran Time**: {tehran_time.strftime('%H:%M:%S')}  
- **Indian Standard Time (IST)**: **{ist_time.strftime('%H:%M:%S')}**  
  *(IST is UTC+5:30, Tehran is UTC+3:30 → IST is 2 hours ahead)*
---
### 🌟 Planetary Positions (IST {ist_time.strftime('%H:%M:%S')})
| Planet      | Longitude (°) | Latitude (°) | Distance (AU) | Speed (°/day) | Financial Significance |
|-------------|---------------|--------------|---------------|---------------|------------------------|"""
    for name, data in planet_data.items():
        significance = ""
        if name == "Venus":
            significance = "Key resistance"
        elif name == "Mars":
            significance = "Bearish pressure"
        elif name == "Jupiter":
            significance = "Mild support"
        elif name == "Moon":
            significance = "Volatility trigger"
        elif name == "Saturn":
            significance = "Long-term uncertainty"
        
        report += f"""
| {name:<10} | {data['longitude']:>8.2f}°   | {data['latitude']:>8.2f}°   | {data['distance']:>13.3f}     | {data['speed']:>13.4f} | {significance} |"""
    
    # Resistance levels section
    report += f"""
---
### 💰 {symbol} Resistance Levels (Current Price: ${current_price})
| Method               | Calculation                     | Resistance Level | Distance to Current Price |
|----------------------|---------------------------------|------------------|----------------------------|
| Venus Longitude      | {planet_data['Venus']['longitude']:.2f}° × {20.02 * price_scale:.2f} | ${venus_resistance:<15.2f} | {venus_resistance - current_price:+.2f} ({'above' if venus_resistance > current_price else 'below'}) |
| Mars-Saturn Angle    | {mars_saturn_angle:.2f}° × {19.05 * price_scale:.2f} | ${mars_saturn_resistance:<15.2f} | {mars_saturn_resistance - current_price:+.2f} ({'above' if mars_saturn_resistance > current_price else 'below'}) |
| Current Price        | Market data                     | ${current_price:<15.2f} | Reference point            |
"""
    
    # Aspects section
    report += f"""
---
### 🔍 Key Planetary Aspects (IST)
| Aspect                | Planets Involved | Angle (°) | Orb (°) | {symbol} Impact at ${current_price} |
|-----------------------|------------------|-----------|---------|--------------------------------|"""
    for aspect in aspects:
        report += f"""
| {aspect['type']:<20} | {aspect['planets']:<16} | {aspect['angle']:>8.2f}°   | {aspect['orb']:>7.2f}°   | {aspect['impact']} |"""
    
    # Time windows section
    report += f"""
---
### ⏱️ Critical Time Windows (IST)
| Time (IST)   | Event                     | Expected {symbol} Movement | Current Price Context |
|--------------|---------------------------|----------------------------|------------------------|
| {ist_time.strftime('%H:%M')}-{(ist_time + timedelta(minutes=30)).strftime('%H:%M')} | Venus Cycle Peak         | Resistance test at ${venus_resistance:.2f} | ${abs(venus_resistance - current_price):.2f} {'above' if venus_resistance > current_price else 'below'} |
| {(ist_time + timedelta(minutes=30)).strftime('%H:%M')}-{(ist_time + timedelta(hours=1)).strftime('%H:%M')} | Mars-Saturn Opposition  | Rejection at ${mars_saturn_resistance:.2f} | ${price_diff:.2f} {'below' if is_mars_saturn_above else 'above'} |
| {(ist_time + timedelta(hours=1)).strftime('%H:%M')}-{(ist_time + timedelta(hours=2)).strftime('%H:%M')} | Moon-Uranus Tension      | High volatility        | Avoid new positions    |
| {(ist_time + timedelta(hours=2)).strftime('%H:%M')}-{(ist_time + timedelta(hours=3)).strftime('%H:%M')} | Venus-Jupiter Influence | Short-term bounce      | Potential recovery     |
"""
    
    # Trading strategy section
    report += f"""
---
### 📊 Trading Strategy for {symbol} (${current_price})
#### Primary Signal: Mars-Saturn Opposition
- **Resistance Level**: ${mars_saturn_resistance:.2f} (${price_diff:.2f} {'above' if is_mars_saturn_above else 'below'} current price)
- **Probability**: {rejection_prob}% chance of rejection
- **Action**: {'Sell' if is_mars_saturn_above else 'Buy'} {symbol} with target ${target_price:.2f}
- **Stop-Loss**: ${stop_loss:.2f}
- **Risk-Reward**: 1:{abs(1.5):.1f}
#### Secondary Signals
1. **Venus at ${venus_resistance:.2f}**:
   - Current price (${current_price}) is {abs(venus_resistance - current_price):.2f} {'above' if venus_resistance < current_price else 'below'} this level
   - {'No immediate impact' if abs(venus_resistance - current_price) > 100 * price_scale else 'Monitor for reaction'}
2. **Moon-Uranus Volatility** ({(ist_time + timedelta(hours=1)).strftime('%H:%M')}-{(ist_time + timedelta(hours=2)).strftime('%H:%M')} IST):
   - Reduce position size by 50%
   - Use wider stop-losses
3. **Venus-Jupiter Bounce** ({(ist_time + timedelta(hours=2)).strftime('%H:%M')}-{(ist_time + timedelta(hours=3)).strftime('%H:%M')} IST):
   - If {symbol} holds ${current_price - 10 * price_scale:.2f}, consider {'longs' if venus_jupiter_orb < 2 else 'shorts'} with target ${venus_jupiter_target:.2f}
"""
    
    # Lunar influence section
    report += f"""
---
### 🌙 Lunar Influence
- **Moon Position**: {planet_data['Moon']['longitude']:.2f}° ({moon_sign})
- **Effect**: Amplifies algorithmic trading
- **Recommendation**: Monitor volume spikes at ${mars_saturn_resistance - 3 * price_scale:.2f}-${mars_saturn_resistance + 3 * price_scale:.2f}
"""
    
    # Risk factors section
    report += f"""
---
### ⚠️ Critical Risk Factors
1. **Mars-Saturn Opposition** ({mars_saturn_angle:.2f}°):
   - Most precise aspect today ({mars_saturn_orb:.2f}° orb)
   - Historically causes 4-5% drops in precious metals
2. **Mercury Retrograde** ({planet_data['Mercury']['speed']:.4f}°/day):
   - Increases false breakout risk
   - Requires confirmation from RSI/volume
3. **Current Price Context**:
   - ${current_price} is {'dangerously close to' if price_diff < 20 * price_scale else 'within normal range of'} ${mars_saturn_resistance:.2f} resistance
   - Break {'above' if is_mars_saturn_above else 'below'} ${mars_saturn_resistance:.2f} could trigger {'short squeeze' if is_mars_saturn_above else 'liquidation cascade'} to ${squeeze_target:.2f}
"""
    
    # Price scenarios section
    report += f"""
---
### 📈 Price Action Scenarios
| Scenario       | Probability | Target Price | Action Required |
|----------------|-------------|--------------|-----------------|
| {'Rejection' if is_mars_saturn_above else 'Breakout'} | {rejection_prob}% | ${rejection_target:.2f} | {'Sell' if is_mars_saturn_above else 'Buy'} at ${entry_price:.2f} |
| {'Breakout' if is_mars_saturn_above else 'Rejection'} | {breakout_prob}% | ${breakout_target:.2f} | {'Buy' if is_mars_saturn_above else 'Sell'} {'above' if is_mars_saturn_above else 'below'} ${mars_saturn_resistance:.2f} |
| Sideways       | 30%         | ${range_low:.2f}-${range_high:.2f} | Range trading   |
"""
    
    # Key insight section
    report += f"""
---
### 💡 Key Insight for Today
The Mars-Saturn opposition at ${mars_saturn_resistance:.2f} is the dominant force today, overriding Venus's normally bullish influence. With {symbol} at ${current_price} (only ${price_diff:.2f} {'below' if is_mars_saturn_above else 'above'} resistance), traders should:
1. **Prepare for rejection** at ${mars_saturn_resistance - 3 * price_scale:.2f}-${mars_saturn_resistance + 3 * price_scale:.2f}
2. **{'Sell' if is_mars_saturn_above else 'Buy'} on approach** to resistance
3. **Avoid {'long' if is_mars_saturn_above else 'short'} positions** until after {(ist_time + timedelta(hours=2)).strftime('%H:%M')} IST
4. **Watch volume** - spike above 20K contracts confirms rejection
> **Final Recommendation**: {'Short' if is_mars_saturn_above else 'Long'} {symbol} at ${entry_price:.2f} with stop-loss ${stop_loss:.2f} and target ${target_price:.2f}. This offers {abs(1.5/0.3):.1f}:1 reward-risk ratio based on planetary resistance.
"""
    
    return report

# Streamlit app interface
st.set_page_config(layout="wide", page_title="Financial Astrology Report")

st.title("Financial Astrology Report Generator")
st.write("Enter a trading symbol and current price to generate a financial astrology report.")

# User inputs in columns for better layout
col1, col2 = st.columns(2)
with col1:
    symbol = st.text_input("Trading Symbol (e.g., Gold, Silver, BTC)", value="BTC")
with col2:
    current_price = st.number_input("Current Price ($)", min_value=0.01, value=64250.0, step=0.01)

tehran_time_str = st.text_input("Tehran Time (YYYY-MM-DD HH:MM:SS, optional)", value="2025-08-08 11:12:10")

# Parse Tehran time
try:
    tehran_time = datetime.strptime(tehran_time_str, "%Y-%m-%d %H:%M:%S") if tehran_time_str else None
except ValueError:
    st.error("Invalid date format. Use YYYY-MM-DD HH:MM:SS or leave blank for current time.")
    tehran_time = None

# Generate report on button click
if st.button("Generate Report"):
    try:
        # Show spinner during calculation
        with st.spinner("Calculating planetary positions and generating report..."):
            start_time = time.time()
            report = generate_financial_astronomy_report(symbol, current_price, tehran_time)
            elapsed_time = time.time() - start_time
            
        st.success(f"Report generated in {elapsed_time:.2f} seconds")
        st.markdown(report)
        
        # Add chart for resistance levels
        chart_data = {
            "type": "bar",
            "data": {
                "labels": ["Venus Resistance", "Mars-Saturn Resistance", "Current Price"],
                "datasets": [{
                    "label": f"{symbol} Price Levels",
                    "data": [
                        planet_data["Venus"]["longitude"] * 20.02 * max(1, current_price / 1000),
                        abs(planet_data["Mars"]["longitude"] - planet_data["Saturn"]["longitude"]) % 360 * 19.05 * max(1, current_price / 1000),
                        current_price
                    ],
                    "backgroundColor": ["#FF6384", "#36A2EB", "#FFCE56"],
                    "borderColor": ["#FF6384", "#36A2EB", "#FFCE56"],
                    "borderWidth": 1
                }]
            },
            "options": {
                "responsive": True,
                "scales": {
                    "y": {"beginAtZero": True, "title": {"display": True, "text": "Price ($)"}},
                    "x": {"title": {"display": True, "text": "Level"}}
                }
            }
        }
        
        st.markdown("### Resistance Levels Chart")
        st.markdown(f"```chartjs\n{chart_data}\n```")
        
    except Exception as e:
        st.error(f"Error generating report: {str(e)}")
        st.exception(e)
