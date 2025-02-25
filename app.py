import streamlit as st
import math
import matplotlib.pyplot as plt

# Custom CSS for dark theme and styling
st.set_page_config(page_title="Panel Cut List", layout="wide")
st.markdown("""
    <style>
    .stApp {
        background-color: #1a1a1a;
        color: #FFFFFF;
    }
    .stTextInput > div > div > input, .stNumberInput > div > div > input, .stSelectbox > div > div > select {
        background-color: #333333;
        color: #FFFFFF;
        border: 1px solid #4a90e2;
    }
    .stButton > button {
        background-color: #4a90e2;
        color: #FFFFFF;
        border: none;
        padding: 8px 16px;
    }
    .stButton > button:hover, .stButton > button:active, .stButton > button:focus {
        background-color: #357ABD;
        color: #D3D3D3 !important;
    }
    .output-text {
        font-family: "Courier New", Courier, monospace;
        font-size: 18px;
        white-space: pre-wrap;
        overflow-y: visible;
    }
    hr.divider {
        border: 1px solid #4a90e2;
        margin: 20px 0;
    }
    .section-spacing {
        margin-top: 20px;
    }
    .shape-note {
        color: #FF0000;
        font-size: 16px;
        margin-top: 5px;
    }
    </style>
""", unsafe_allow_html=True)

def to_feet_inches(inches):
    """Convert inches to feet and inches string."""
    feet = int(inches // 12)
    remaining_inches = round(inches % 12, 1)
    return f"{feet} ft {remaining_inches} in"

def calculate_intersection_angle(working_slope, joining_slope):
    """Calculate the horizontal cut angle based on working slope and joining_slope."""
    run = 12
    rise_working = working_slope
    rise_joining = joining_slope
    
    if rise_joining == 0:
        return 0
    slope_diff = rise_joining - rise_working
    adjusted_run = run - (slope_diff / rise_joining) * run
    
    denominator = math.sqrt(run**2 + rise_working**2 + adjusted_run**2)
    angle = math.degrees(math.acos(adjusted_run / denominator))
    return angle

def calculate_panel_lengths(current_length, panel_width, working_slope, top_condition, top_joining_slope, bottom_condition, bottom_joining_slope):
    working_angle = math.degrees(math.atan(working_slope / 12))
    top_joining_angle = calculate_intersection_angle(working_slope, top_joining_slope) if top_condition != "Ridge" else 0
    bottom_joining_angle = calculate_intersection_angle(working_slope, bottom_joining_slope) if bottom_condition != "Eave" else 0

    top_offset = panel_width * math.tan(math.radians(top_joining_angle)) if top_joining_angle != 0 else 0
    bottom_offset = panel_width * math.tan(math.radians(bottom_joining_angle)) if bottom_joining_angle != 0 else 0

    length_change = 0
    base_length = current_length

    if bottom_condition == "Eave" and top_condition == "Ridge":
        length_change = 0
    elif bottom_condition == "Valley Moving Up" and top_condition == "Ridge":
        length_change = -bottom_offset
    elif bottom_condition == "Valley Moving Down" and top_condition == "Ridge":
        length_change = bottom_offset
    elif bottom_condition == "Eave" and top_condition == "Hip Moving Up":
        length_change = top_offset
    elif bottom_condition == "Eave" and top_condition == "Hip Moving Down":
        length_change = -top_offset
    elif bottom_condition == "Valley Moving Up" and top_condition == "Hip Moving Down":
        length_change = -(bottom_offset + top_offset)
    elif bottom_condition == "Valley Moving Down" and top_condition == "Hip Moving Up":
        length_change = bottom_offset + top_offset
    elif bottom_condition == "Valley Moving Up" and top_condition == "Hip Moving Up":
        length_change = top_offset - bottom_offset
    elif bottom_condition == "Valley Moving Down" and top_condition == "Hip Moving Down":
        length_change = -(top_offset - bottom_offset)

    panel_lengths = []
    current = base_length
    for _ in range(10):
        panel_lengths.append(round(current, 1))
        current += length_change

    bottom_angle = 0
    top_angle = 0
    if bottom_condition == "Valley Moving Up":
        bottom_angle = bottom_joining_angle
    elif bottom_condition == "Valley Moving Down":
        bottom_angle = -bottom_joining_angle
    if top_condition == "Hip Moving Up":
        top_angle = top_joining_angle
    elif top_condition == "Hip Moving Down":
        top_angle = -top_joining_angle

    bottom_angle_display = abs(bottom_angle) if bottom_angle != 0 else 0
    top_angle_display = abs(top_angle) if top_angle != 0 else 0

    same_direction = (bottom_condition == "Valley Moving Up" and top_condition == "Hip Moving Up") or \
                     (bottom_condition == "Valley Moving Down" and top_condition == "Hip Moving Down")
    slope_adjustment = panel_width / math.cos(math.radians(working_angle)) if same_direction else 0

    # Build output string
    output = "<div class='output-text'>"
    output += f"Step Length: {round(length_change, 1):6.1f} in ({to_feet_inches(length_change)})<br><br>"
    output += f"Top Angle: {round(top_angle_display, 1):6.1f}°<br><br>"
    output += f"Bottom Angle: {round(bottom_angle_display, 1):6.1f}°<br><br>"
    output += "<hr class='divider'>"
    output += "Panel Lengths:<br><br>"
    for i, length in enumerate(panel_lengths, 1):
        line = f"{i:2}: {length:6.1f} in ({to_feet_inches(length)})"
        if same_direction:
            cut_length = round(length + slope_adjustment, 1)
            line += f" [RUN {cut_length:6.1f} in]"
        output += line + "<br><br>"
    
    if same_direction:
        if top_joining_slope != bottom_joining_slope:
            output += f"Reminder: Panel Cut Lengths shown in brackets adjust for slope geometry due to differing top and bottom slopes.<br><br>"
        else:
            adjusted_length = round(current_length + slope_adjustment, 1)
            output += f"<span style='color: #FFFF00'>Reminder: Actual panel length used is input length + slope adjustment: {adjusted_length:6.1f} in ({to_feet_inches(adjusted_length)})</span><br>"
    output += "</div>"

    return output, top_angle, bottom_angle, panel_width

def draw_panel_shape(top_angle, bottom_angle, panel_width, direction="LTR"):
    """Draw a parallelogram representing the panel shape, with direction toggle."""
    # Use a small figure size with moderate DPI for sharpness and thicker lines
    fig, ax = plt.subplots(figsize=(1.5, 0.9), dpi=200)  # Small size, moderate DPI for clarity, thicker lines
    
    # Fixed parameters
    fixed_length = 48  # 48 inches
    
    if direction == "LTR":
        # Start from left, fixed height of 48 inches
        bottom_left = (0, 0)
        top_left = (0, fixed_length)
        
        # Calculate endpoints for bottom and top lines using angles
        bottom_dx = panel_width
        bottom_angle_rad = math.radians(bottom_angle)
        bottom_dy = bottom_dx * math.tan(bottom_angle_rad)
        bottom_right = (bottom_dx, bottom_dy)
        
        top_dx = panel_width
        top_angle_rad = math.radians(top_angle)
        top_dy = fixed_length + (top_dx * math.tan(top_angle_rad))
        top_right = (top_dx, top_dy)
        
        # Draw fill with black edges
        x = [bottom_left[0], bottom_right[0], top_right[0], top_left[0]]
        y = [bottom_left[1], bottom_right[1], top_right[1], top_left[1]]
        ax.fill(x, y, "lightblue", edgecolor="black", linewidth=2)  # Thicker lines
        
        # Draw opposite line (right side) in red
        ax.plot([bottom_right[0], top_right[0]], [bottom_right[1], top_right[1]], color="red", linewidth=2)  # Thicker red line
    else:
        # Start from right, fixed height of 48 inches, mirrored
        bottom_right = (panel_width, 0)
        top_right = (panel_width, fixed_length)
        
        bottom_dx = -panel_width  # Move left
        bottom_angle_rad = math.radians(-bottom_angle)  # Mirror angle
        bottom_dy = bottom_dx * math.tan(bottom_angle_rad)
        bottom_left = (0, bottom_dy)
        
        top_dx = -panel_width
        top_angle_rad = math.radians(-top_angle)  # Mirror angle
        top_dy = fixed_length + (top_dx * math.tan(top_angle_rad))
        top_left = (0, top_dy)
        
        # Draw fill with black edges
        x = [bottom_left[0], bottom_right[0], top_right[0], top_left[0]]
        y = [bottom_left[1], bottom_right[1], top_right[1], top_left[1]]
        ax.fill(x, y, "lightblue", edgecolor="black", linewidth=2)
        
        # Draw opposite line (left side) in red
        ax.plot([bottom_left[0], top_left[0]], [bottom_left[1], top_left[1]], color="red", linewidth=2)
    
    # Remove axes and tighten margins
    ax.set_axis_off()
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)  # Maximize use of space, no margins
    
    # Set limits to fit shape exactly
    ax.set_xlim(min(x) - 5, max(x) + 5)
    ax.set_ylim(min(y) - 5, max(y) + 5)
    ax.set_aspect("equal")
    return fig

# Streamlit app
st.title("Panel Cut List")

st.write("### Inputs")

# Direction dropdown with title
direction = st.selectbox("Install Direction", [">>>>>", "<<<<<"], index=0)
direction_value = "LTR" if direction == ">>>>>" else "RTL"

# Inputs
start_length = st.number_input("Start Length (in)", value=0.0, step=0.1)
panel_width = st.number_input("Panel Width (in)", value=16.0, step=0.1)
working_slope = st.number_input("Working Slope", value=6.0, step=0.1)

# Top Condition with blue "Intersecting Slope"
top_condition = st.selectbox("Top Condition", ["Hip Moving Up", "Hip Moving Down", "Ridge"], index=2)
if top_condition != "Ridge":
    st.write("<span style='color: #4a90e2;'>Intersecting Slope</span>", unsafe_allow_html=True)
    top_joining_slope = st.number_input("Top Intersecting Slope", value=working_slope, step=0.1, key="top_slope", label_visibility="hidden", help="Slope intersecting the top condition")
else:
    top_joining_slope = working_slope

# Bottom Condition with blue "Intersecting Slope"
bottom_condition = st.selectbox("Bottom Condition", ["Valley Moving Up", "Valley Moving Down", "Eave"], index=2)
if bottom_condition != "Eave":
    st.write("<span style='color: #4a90e2;'>Intersecting Slope</span>", unsafe_allow_html=True)
    bottom_joining_slope = st.number_input("Bottom Intersecting Slope", value=working_slope, step=0.1, key="bottom_slope", label_visibility="hidden", help="Slope intersecting the bottom condition")
else:
    bottom_joining_slope = working_slope

if st.button("Calculate"):
    st.markdown("<hr class='divider'>", unsafe_allow_html=True)  # Divider after button
    output, top_angle, bottom_angle, panel_width = calculate_panel_lengths(
        start_length, panel_width, working_slope, top_condition, top_joining_slope, bottom_condition, bottom_joining_slope
    )
    st.markdown("<h3 class='section-spacing'>Panel Measurements</h3>", unsafe_allow_html=True)
    st.markdown(output, unsafe_allow_html=True)
    
    # Draw the panel shape below output with note
    st.markdown("### Panel Shape")
    st.markdown("<div class='shape-note'>The leading edge (screw side) is shown in red</div>", unsafe_allow_html=True)
    fig = draw_panel_shape(top_angle, bottom_angle, panel_width, direction_value)
    st.pyplot(fig)