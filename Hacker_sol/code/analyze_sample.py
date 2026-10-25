import pandas as pd
import os
import json

def analyze_and_save_sample():
    print("==================================================")
    print("    GENERATING SAMPLE DELETION AUDIT OUTPUT       ")
    print("==================================================")

    # Paths
    req_path = 'dataset/sample_deletion_requests.csv'
    users_path = 'dataset/user_identities.csv'
    audit_path = 'dataset/user_audit_log.csv'
    system_path = 'dataset/system_activity.csv'
    evidence_path = 'dataset/evidence_files.csv'
    
    output_path = 'dataset/sample_output.csv'

    # 1. Load Sample Requests
    if not os.path.exists(req_path):
        print(f"ERROR: {req_path} not found.")
        return

    requests_df = pd.read_csv(req_path)
    print(f"[INFO] Loaded {len(requests_df)} sample deletion request(s).")

    # 2. Load supporting datasets safely
    users_df = pd.read_csv(users_path) if os.path.exists(users_path) and os.path.getsize(users_path) > 0 else pd.DataFrame()
    audit_df = pd.read_csv(audit_path) if os.path.exists(audit_path) and os.path.getsize(audit_path) > 0 else pd.DataFrame()
    system_df = pd.read_csv(system_path) if os.path.exists(system_path) and os.path.getsize(system_path) > 0 else pd.DataFrame()
    evidence_df = pd.read_csv(evidence_path) if os.path.exists(evidence_path) and os.path.getsize(evidence_path) > 0 else pd.DataFrame()

    results = []

    # 3. Analyze each sample case
    for _, row in requests_df.iterrows():
        case_id = row.get('case_id')
        email = str(row.get('email', '')).strip().lower()
        request_text = str(row.get('request_text', ''))

        exposures = []

        # Check for exposure across datasets
        if not users_df.empty and 'email' in users_df.columns:
            if not users_df[users_df['email'].astype(str).str.lower() == email].empty:
                exposures.append("user_identities.csv")

        if not audit_df.empty and 'email' in audit_df.columns:
            if not audit_df[audit_df['email'].astype(str).str.lower() == email].empty:
                exposures.append("user_audit_log.csv")

        if not system_df.empty:
            for col in system_df.columns:
                if not system_df[system_df[col].astype(str).str.lower().str.contains(email, na=False)].empty:
                    exposures.append(f"system_activity.csv ({col})")

        if not evidence_df.empty:
            for col in evidence_df.columns:
                if not evidence_df[evidence_df[col].astype(str).str.lower().str.contains(email, na=False)].empty:
                    exposures.append(f"evidence_files.csv ({col})")

        # Determine Status and Steps
        if pd.isna(request_text) or request_text.strip() == "" or "no deletion" in request_text.lower():
            status = "NOT_APPLICABLE"
            steps = [{"step": "Analyze request_text", "result": "No valid deletion request found."}]
        elif len(exposures) > 0:
            status = "INCOMPLETE"
            steps = [{
                "step": f"Check exposure for email: {email}",
                "result": f"User data still exposed in: {', '.join(exposures)}"
            }]
        else:
            status = "COMPLETE"
            steps = [{
                "step": f"Check exposure for email: {email}",
                "result": "No residual records or identifiers found. Purge verified."
            }]

        results.append({
            'case_id': case_id,
            'status': status,
            'steps_json': json.dumps(steps)
        })

    # 4. Save results to sample_output.csv
    output_df = pd.DataFrame(results)
    output_df.to_csv(output_path, index=False)
    print(f"\n[SUCCESS] Analysis complete! Results successfully written to '{output_path}'.")

if __name__ == "__main__":
    analyze_and_save_sample()