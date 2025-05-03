import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense
from tensorflow.keras.optimizers import Adam
from openai import OpenAI
from loadenv import load_env
import os
load_env()



# Data Loading and Preprocessing
def load_machine_data(json_data):
    records = json_data["MILL-001"]
    data = []
    for rec in records:
        row = {"timestamp": rec["timestamp"]}
        row.update(rec["sensors"])
        data.append(row)
    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp').drop_duplicates('timestamp')
    return df.set_index("timestamp")


# Anomaly Detection Methods
def z_score_detection(df, threshold=3):
    z_scores = (df - df.mean()) / df.std()
    return (np.abs(z_scores) > threshold).any(axis=1).astype(int)


def isolation_forest_detection(df):
    iso = IsolationForest(contamination=0.05, random_state=42)
    preds = iso.fit_predict(df)
    return (preds == -1).astype(int)


def autoencoder_detection(df, epochs=30):
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df)
    
    ae = autoencoder_model(input_dim=X_scaled.shape[1])
    ae.fit(X_scaled, X_scaled, epochs=epochs, batch_size=8, verbose=0)

    recon = ae.predict(X_scaled)
    mse = np.mean(np.square(X_scaled - recon), axis=1)
    threshold = np.percentile(mse, 95)
    return (mse > threshold).astype(int)


def autoencoder_model(input_dim):
    input_layer = Input(shape=(input_dim,))
    encoded = Dense(8, activation="relu")(input_layer)
    bottleneck = Dense(3, activation="relu")(encoded)
    decoded = Dense(8, activation="relu")(bottleneck)
    output = Dense(input_dim, activation="linear")(decoded)
    autoencoder = Model(inputs=input_layer, outputs=output)
    autoencoder.compile(optimizer=Adam(0.001), loss='mse')
    return autoencoder


# Ensemble and Analysis
def ensemble_anomaly_detection(df):
    z = z_score_detection(df)
    i = isolation_forest_detection(df)
    a = autoencoder_detection(df)
    
    votes = z + i + a
    return (votes >= 2).astype(int)  # Majority vote


def detect_anomalies_near_issue(df, issue_time, window_minutes=15):
    start = pd.to_datetime(issue_time) - pd.Timedelta(minutes=window_minutes)
    end = pd.to_datetime(issue_time) + pd.Timedelta(minutes=window_minutes)
    window_df = df[(df.index >= start) & (df.index <= end)]
    
    if window_df.empty:
        print("No sensor data found near the issue time.")
        return pd.DataFrame()
        
    anomaly_flags = ensemble_anomaly_detection(window_df)
    window_df['anomaly'] = anomaly_flags
    return window_df[window_df['anomaly'] == 1]


def generate_ai_report(anomalies, issue_time, issue_desc, api_key):
    client = OpenAI(api_key=api_key)
    
    if anomalies.empty:
        return "No anomalies detected to analyze."
        
    prompt = (
        f"Issue Description: {issue_desc}\n"
        f"Timestamp: {issue_time}\n"
        f"Detected anomalies (first 5 rows):\n{anomalies.head().to_string()}\n"
        "Explain how these anomalies could have contributed to the issue."
    )

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300
    )
    
    return response.choices[0].message.content


# Main Execution
def main():
    # Input parameters
    issue_time = "2025-05-01T08:45:00Z"
    issue_desc = "Unexpected machine halt during operation."
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    
    # Load data
    with open("Data/Machine_Sensor_Data.json") as f:
        json_data = json.load(f)
    
    df = load_machine_data(json_data)
    
    # Detect anomalies
    anomalies = detect_anomalies_near_issue(df, issue_time)
    
    # Print results
    print(f"Anomalies detected near {issue_time} for issue: {issue_desc}")
    print(anomalies)
    
    # Generate and print AI report
    report = generate_ai_report(anomalies, issue_time, issue_desc, openai_api_key)
    print("\n--- AI-Generated Anomaly Report ---\n")
    print(report)


if __name__ == "__main__":
    main()