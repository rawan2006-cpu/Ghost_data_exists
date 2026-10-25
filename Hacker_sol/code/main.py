import pandas as pd
import os
import json
import sys

class Logger(object):
    """Dual logger to print to console and write to log.txt simultaneously."""
    def __init__(self, filename='log.txt'):
        self.terminal = sys.stdout
        self.log = open(filename, 'w', encoding='utf-8')

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()

    def flush(self):
        self.terminal.flush()
        self.log.flush()

def run_compliance_evaluation_workflow():
    # Redirect standard output to log.txt as well as the console
    sys.stdout = Logger('log.txt')

    print("=== STARTING COMPLIANCE EVALUATION WORKFLOW ===")
    
    req_path = 'dataset/deletion_requests.csv'
    rules_path = 'dataset/deletion_rules.csv'
    output_path = 'output.csv'

    if not os.path.exists(req_path):
        print(f"ERROR: Primary dataset '{req_path}' not found.")
        return

    # 1. Read deletion requests and deletion rules
    requests_df = pd.read_csv(req_path)
    print(f"Loaded {len(requests_df)} deletion requests from {req_path}")
    
    rules_df = pd.DataFrame()
    if os.path.exists(rules_path) and os.path.getsize(rules_path) > 0:
        rules_df = pd.read_csv(rules_path)
        print(f"Loaded {len(rules_df)} deletion rules from {rules_path}")
    else:
        print("No deletion rules file found or file is empty. Using default actions.")

    # 2. Load auxiliary sources safely
    auxiliary_sources = {}
    aux_files = ["user_identities.csv", "user_audit_log.csv", "system_activity.csv", "evidence_files.csv"]
    for file_name in aux_files:
        file_path = os.path.join('dataset', file_name)
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            auxiliary_sources[file_name] = pd.read_csv(file_path)
            print(f"Loaded auxiliary source: {file_name} ({len(auxiliary_sources[file_name])} rows)")
        else:
            auxiliary_sources[file_name] = pd.DataFrame()
            print(f"Auxiliary source {file_name} is empty or missing. Initialized empty DataFrame.")

    evaluation_results = []

    # 3. Process each case
    for _, row in requests_df.iterrows():
        case_id = row.get('case_id')
        email = str(row.get('email', '')).strip().lower()
        request_text = str(row.get('request_text', ''))

        # Intent check
        invalid_keywords = ["no deletion", "keep my data", "cancel"]
        is_invalid_request = (
            pd.isna(request_text) or 
            request_text.strip() == "" or 
            any(kw in request_text.lower() for kw in invalid_keywords)
        )

        if is_invalid_request:
            status = "NOT_APPLICABLE"
            steps = [{
                "step_no": 1,
                "phase": "FINDING",
                "system_id": "account_service",
                "resource_id": f"account_{case_id}",
                "operation": "REPORT_INVALID_REQUEST",
                "state": "NOT_APPLICABLE",
                "evidence_id": "evidence_01"
            }]
            print(f"Case {case_id}: Evaluated as NOT_APPLICABLE (Invalid request intent).")
        else:
            exposed_sources = []
            matched_rule_action = "DELETE_RECORD"

            # Scan auxiliary tables and check rules
            for source_name, df in auxiliary_sources.items():
                if df.empty:
                    continue
                for col in df.columns:
                    matches = df[df[col].astype(str).str.lower().str.contains(email, na=False)]
                    if not matches.empty and email != 'nan':
                        exposed_sources.append(source_name)
                        
                        if not rules_df.empty:
                            rule_match = rules_df[rules_df.astype(str).apply(lambda x: x.str.contains(source_name.split('.')[0], case=False)).any(axis=1)]
                            if not rule_match.empty and 'action' in rule_match.columns:
                                matched_rule_action = str(rule_match.iloc[0]['action']).upper()
                        break

            exposed_sources = list(set(exposed_sources))

            if len(exposed_sources) > 0:
                status = "INCOMPLETE"
                target_state = "ABSENT" if "DELETE" in matched_rule_action else ("REDACTED" if "REDACT" in matched_rule_action else "ANONYMIZED")

                steps = [
                    {
                        "step_no": 1,
                        "phase": "FINDING",
                        "system_id": "account_service",
                        "resource_id": f"account_{case_id}",
                        "operation": "REPORT_REMAINING_RECORD",
                        "state": "PRESENT",
                        "evidence_id": "evidence_01"
                    },
                    {
                        "step_no": 2,
                        "phase": "REMEDIATION",
                        "system_id": "account_service",
                        "resource_id": f"account_{case_id}",
                        "operation": matched_rule_action if matched_rule_action in ["DELETE_RECORD", "REDACT_RECORD", "ANONYMIZE_RECORD"] else "DELETE_RECORD",
                        "state": target_state,
                        "evidence_id": "evidence_01"
                    },
                    {
                        "step_no": 3,
                        "phase": "VERIFICATION",
                        "system_id": "account_service",
                        "resource_id": f"account_{case_id}",
                        "operation": f"VERIFY_RECORD_{target_state}",
                        "state": target_state,
                        "evidence_id": "evidence_01"
                    }
                ]
                print(f"Case {case_id}: Evaluated as INCOMPLETE (Lingering records found in {exposed_sources}).")
            else:
                status = "COMPLETE"
                steps = [
                    {
                        "step_no": 1,
                        "phase": "FINDING",
                        "system_id": "account_service",
                        "resource_id": f"account_{case_id}",
                        "operation": "REPORT_NO_RECORD",
                        "state": "ABSENT",
                        "evidence_id": "evidence_01"
                    },
                    {
                        "step_no": 2,
                        "phase": "VERIFICATION",
                        "system_id": "account_service",
                        "resource_id": f"account_{case_id}",
                        "operation": "VERIFY_RECORD_ABSENT",
                        "state": "ABSENT",
                        "evidence_id": "evidence_01"
                    }
                ]
                print(f"Case {case_id}: Evaluated as COMPLETE (No residual records found).")

        evaluation_results.append({
            'case_id': case_id,
            'status': status,
            'steps_json': json.dumps(steps)
        })

    # 4. Save results to output.csv
    output_df = pd.DataFrame(evaluation_results)
    output_df.to_csv(output_path, index=False)
    print(f"SUCCESS: Evaluation completed successfully. Results written to '{output_path}' and logged to 'log.txt'.")
    print("=== WORKFLOW COMPLETED ===")

if __name__ == "__main__":
    run_compliance_evaluation_workflow()