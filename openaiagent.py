from openai import OpenAI
import base64
import numpy as np
from tensorflow.keras.models import load_model
from PIL import Image
import sys
sys.stdout.reconfigure(encoding='utf-8')

# === OpenAI API Setup ===
api_key = "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".strip()
client = OpenAI(api_key=api_key)
# === Load Trained Model ===
model = load_model("m32.h5")

# === Class Labels ===
class_labels = ['Cell', 'Cell-Multi', 'Cracking', 'Diode', 'Diode-Multi',
                'Hot-Spot', 'Hot-Spot-Multi', 'No-Anomaly', 'Offline-Module',
                'Shadowing', 'Soiling', 'Vegetation']

# === Function to Predict from Image ===
def predict_image(img: Image.Image):
    img = img.convert("RGB")
    img = img.resize((24, 40))  # Resize to match model input
    img_array = np.array(img)
    img_input = img_array.reshape(1, 40, 24, 3)

    prediction = model.predict(img_input)
    class_index = np.argmax(prediction[0])
    predicted_class = class_labels[class_index]
    return predicted_class

# === Detect Anomalies using GPT-4o Vision ===
'''def detect_anomalies(image_path: str):
    with open(image_path, "rgb") as f:
        b64_image = base64.b64encode(f.read()).decode("utf-8")

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "This is an infrared image of a solar panel. Identify any faults such as hotspots, cracks, or soiling. Be specific about the location and severity."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}}
                ]
            }
        ],
        max_tokens=300
    )
    return response.choices[0].message.content'''

# === Check Warranty Eligibility ===
def check_warranty_eligibility(detected_issue, panel_metadata,data):
    prompt = f"""
    The issue detected is: {detected_issue}
    Panel installation date: {panel_metadata['install_date']}
    Warranty terms: {panel_metadata['warranty_terms']}
    Clamp Meter Readings: {data['clamp_meter']}
    Inverter Data Logs: {data['data_log']}
    Based on this, is the issue eligible for warranty?
    """
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300
    )
    return response.choices[0].message.content

# === Recommend Actions ===
def recommend_action(detected_issue):
    prompt = f"""
    The solar panel issue is: {detected_issue}
    Suggest repair steps, urgency level, and whether the panel should be replaced or cleaned.
    """
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300
    )
    return response.choices[0].message.content

# === Generate Final Customer Report ===
def generate_customer_report(issue, warranty, actions):
    prompt = f"""
    Create a detailed report for the customer explaining the diagnosis (do not include their name or contact info):
    - Detected issue: {issue}
    - Warranty status: {warranty}
    - Recommended next steps: {actions}
    Format the report for use by a customer service representative.
    """
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500
    )
    return response.choices[0].message.content

# === Main Pipeline Function ===
def solar_panel_diagnosis_pipeline(image_path, metadata,data):
    img = Image.open(image_path)

    # Step 1: Use your model to classify the image
    predicted_class = predict_image(img)

    '''  # Step 2: Use GPT-4o vision to describe anomalies in detail
    visual_description = detect_anomalies(image_path)

    # Combine both descriptions
    combined_issue = f"{predicted_class} detected.\nDetailed analysis:\n{visual_description}"'''
    
    # Step 2: Datalog

    # Step 3: Warranty check
    warranty_status = check_warranty_eligibility(predicted_class, metadata,data)

    # Step 4: Recommendations
    recommendations = recommend_action(predicted_class)

    # Step 5: Final Report
    report = generate_customer_report(predicted_class, warranty_status, recommendations)

    return {
        "predicted_class": predicted_class,
        '''"visual_description": visual_description,'''
        "warranty": warranty_status,
        "recommendations": recommendations,
        "report": report
    }

# === Test Code ===
if __name__ == "__main__":
    metadata = {
        "install_date": "2022-01-15",
        "warranty_terms": "25-year coverage for material and workmanship defects. Hot-spots covered within first 10 years."
    }

    image_path = r"C:\Users\Harsh Chaudhary\Pictures\Camera Roll\IMG-20250509-WA0026.jpg"

    result = solar_panel_diagnosis_pipeline(image_path, metadata)

    print("\n=== Final Customer Report ===\n")
    print(result["report"])
