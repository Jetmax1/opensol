import streamlit as st
from PIL import Image
import requests
import base64
import json
from openaiagent import solar_panel_diagnosis_pipeline 

# --- Streamlit Page Configuration ---
st.set_page_config(page_title="Unified Solar Panel Diagnostics", layout="wide")
st.title("🌞 Solar Panel Diagnostics Suite")

# --- Mode Selection ---
mode = st.radio(
    "Select Diagnostic Mode:",
    ('Infrared Warranty Diagnosis', 'Hotspot Detection')
)

# --- Infrared Warranty Diagnosis Mode ---
if mode == 'Infrared Warranty Diagnosis':
    with st.form("ir_form"):
        st.header("1. Upload Infrared Image")
        ir_img = st.file_uploader("Infrared Image (jpg, jpeg, png)", type=["jpg", "jpeg", "png"])

        st.header("2.Clamp Meter Readings/Inverter Data Logs")
        clamp_meter = st.text_area("Clamp Meter Readings", help="Paste or write clamp meter readings or inverter data logs here."  )
        data_log = st.text_area(
            "Inverter Data Logs", height=150,
            help="Paste or write inverter data logs here. This will help in diagnosing the panel's performance."
        )
        
        st.header("3. Panel Metadata")
        install_date = st.date_input("Installation Date")
        warranty_terms = st.text_area(
            "Warranty Terms", height=150,
            help="Paste or write warranty details here."
        )

        submitted_ir = st.form_submit_button("Run IR Diagnosis")

    if submitted_ir:
        if not ir_img:
            st.error("Please upload an infrared image to proceed.")
        else:
            st.success("Running IR-based analysis...")
            metadata = {
                "install_date": str(install_date),
                "warranty_terms": warranty_terms,
            }
            data ={
                "clamp_meter": clamp_meter,
                "data_log": data_log,
            }
            results = solar_panel_diagnosis_pipeline(ir_img, metadata,data)

            st.subheader("📋 Full IR Report")
            st.markdown(results.get("report", "No report available."))

            with st.expander("⚠️ Detected Anomalies"):
                st.markdown(results.get("anomalies", "No anomalies found."))

            with st.expander("✅ Warranty Status"):
                st.markdown(results.get("warranty", "Unable to determine warranty status."))

            with st.expander("🛠️ Recommendations"):
                st.markdown(results.get("recommendations", "No recommendations available."))

# --- Hotspot Detection Mode ---
else:
    st.header("🔍 Hotspot Detection")
    st.write("Upload an image or enter a URL to detect panel hotspots and faults.")

    uploaded_file = st.file_uploader("Upload an Image", type=["jpg", "jpeg", "png"])
    image_url = st.text_input("Or enter Image URL")

    if st.button("Process for Hotspots"):
        # Build payload
        if uploaded_file:
            image_bytes = uploaded_file.read()
            img_b64 = base64.b64encode(image_bytes).decode('utf-8')
            inputs = {"type": "base64", "value": img_b64}
        elif image_url:
            inputs = {"type": "url", "value": image_url}
        else:
            st.error("Please upload an image or provide a URL.")
            st.stop()

        payload = {
            "api_key": "4Gdqy3MPPMplaXVVr1yG",
            "inputs": {"image": inputs}
        }

        with st.spinner("Processing image for hotspots..."):
            response = requests.post(
                'https://detect.roboflow.com/infer/workflows/project-jxvu8/detect-count-and-visualize-3',
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload)
            )
            if response.status_code != 200:
                st.error("Failed to process image. HTTP code {}".format(response.status_code))
                st.stop()
            result = response.json()

        # Display processed image
        try:
            out_b64 = result["outputs"][0]["output_image"]["value"]
            out_bytes = base64.b64decode(out_b64)
            st.image(out_bytes, caption="Hotspot Detection Result", use_column_width=True)
        except Exception:
            st.warning("Could not display the processed image.")

        # Summarize detections
        st.subheader("🧾 Detection Summary")
        counts = {"PID": 0, "PID2": 0, "PV": 0, "hotspot": 0}
        try:
            preds = result["outputs"][0]["predictions"]["predictions"]
            for pred in preds:
                cls = pred.get("class")
                if cls in counts:
                    counts[cls] += 1
        except Exception:
            st.warning("No prediction data in response.")

        st.markdown(f"""
        - **PID**: {counts['PID']} detected — Potential-Induced Degradation affects efficiency.
        - **PID2**: {counts['PID2']} detected — Secondary degradation.
        - **PV**: {counts['PV']} detected — PV panel presence confirmed.
        - **Hotspot**: {counts['hotspot']} detected — Indicates overheating or damage.
        """)

        # Download JSON
        st.download_button(
            label="📥 Download JSON Result",
            data=json.dumps(result, indent=2),
            file_name="hotspot_result.json",
            mime="application/json"
        )
