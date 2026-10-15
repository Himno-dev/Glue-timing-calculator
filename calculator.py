"""Prototype glue timing calculator for a marked product photo."""


import streamlit as st
from PIL import Image, ImageDraw


st.set_page_config(page_title="Glue Timing Calculator", page_icon="📏")
st.title("Glue Timing Calculator")
st.write("Define the item and machine, mark glue paths on its photo, and calculate trigger travel in inches.")

lead_edge = st.selectbox("Select the item's lead edge", ("Left", "Right", "Top", "Bottom"))
travel_direction = st.radio(
    "Select conveyor travel direction",
    ("← Left", "→ Right", "↑ Up", "↓ Down"),
    horizontal=True,
)

photo_file = st.camera_input("Take a picture") or st.file_uploader("Or upload a picture", type=["png", "jpg", "jpeg"])
piece_length = st.number_input("Item length in conveyor direction (in)", min_value=0.01, value=12.0)
speed = st.number_input("Machine speed (in/s)", min_value=0.01, value=10.0)
nominal_offset = st.number_input("Specified sensor-to-glue-head distance (in)", min_value=0.0, value=6.0)
measured_offset = st.number_input("Actual sensor-to-glue-head distance (in)", min_value=0.0, value=6.0)
mode = st.radio("Glue pattern", ("Lines", "Dots"), horizontal=True)
dot_size = st.number_input("Dot diameter (in)", min_value=0.01, value=0.1) if mode == "Dots" else 0.0

if photo_file:
    image = Image.open(photo_file).convert("RGB")
    st.image(image, caption="Item photo", use_container_width=True)
    st.caption("For a reliable scale, photograph the full item straight-on. The image width is calibrated to the item length.")
    count = st.number_input("Number of paths" if mode == "Lines" else "Number of dots", min_value=1, max_value=30, value=1, step=1)
    marks = []
    st.subheader("Mark glue locations")
    st.caption("Coordinates are percentages of photo width/height. X measures distance from the leading edge; Y selects a position across the item.")
    for i in range(int(count)):
        with st.expander(f"{mode[:-1] if mode == 'Lines' else 'Dot'} {i + 1}", expanded=True):
            a, b = st.columns(2)
            x1 = a.number_input("Start/center X (%)", 0.0, 100.0, 10.0, key=f"x1{i}")
            y1 = b.number_input("Start/center Y (%)", 0.0, 100.0, 50.0, key=f"y1{i}")
            if mode == "Lines":
                c, d = st.columns(2)
                x2 = c.number_input("End X (%)", 0.0, 100.0, 90.0, key=f"x2{i}")
                y2 = d.number_input("End Y (%)", 0.0, 100.0, 50.0, key=f"y2{i}")
            else:
                x2, y2 = x1, y1
            marks.append((x1, y1, x2, y2))

    preview = image.copy()
    pen = ImageDraw.Draw(preview)
    for x1, y1, x2, y2 in marks:
        p1 = (round(x1 * image.width / 100), round(y1 * image.height / 100))
        p2 = (round(x2 * image.width / 100), round(y2 * image.height / 100))
        if mode == "Lines":
            pen.line((p1, p2), fill="red", width=max(2, image.width // 250))
        else:
            r = max(3, round(dot_size * image.width / piece_length / 2))
            pen.ellipse((p1[0] - r, p1[1] - r, p1[0] + r, p1[1] + r), fill="red")
    st.image(preview, caption="Marked glue paths", use_container_width=True)

    if st.button("Calculate timing", type="primary"):
        # The travel direction selects which photo axis represents item length;
        # the selected lead edge determines which end of that axis is zero.
        horizontal_travel = travel_direction in ("← Left", "→ Right")
        lead_edge_is_start = (
            (horizontal_travel and lead_edge == "Left")
            or (not horizontal_travel and lead_edge == "Top")
        )
        offset_correction = measured_offset - nominal_offset
        st.subheader("Glue head settings")
        for i, (x1, y1, x2, y2) in enumerate(marks, 1):
            coord1, coord2 = (x1, x2) if horizontal_travel else (y1, y2)
            if not lead_edge_is_start:
                coord1, coord2 = 100 - coord1, 100 - coord2
            start = min(coord1, coord2) * piece_length / 100 + offset_correction
            finish = max(coord1, coord2) * piece_length / 100 + offset_correction
            if mode == "Dots":
                start -= dot_size / 2
                finish += dot_size / 2
            start = max(0.0, start)
            run = max(0.0, finish - start)
            st.markdown(f"**Path {i} — Start from:** {start:.3f} in  ")
            st.markdown(f"**Run till:** {run:.3f} in")
            st.caption(f"At {speed:.3f} in/s: trigger after {start / speed:.3f} s; fire for {run / speed:.3f} s.")
        st.warning("Confirm the sensor-offset sign, glue response delay, and conveyor orientation on a test item before production. This estimate assumes the photo width is aligned with travel and represents the full item length.")
else:
    st.info("Take or upload an item photo to mark glue locations.")
