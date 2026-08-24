import os
import re
import json
import hashlib
import pandas as pd
import numpy as np

def clean_and_build_all_11_datasets():
    def fix_encoding(text: str) -> str:
        if not isinstance(text, str):
            return ""
        replacements = {
            'â€“': '—', 'â€”': '—', 'â€™': "'", 'â€œ': '"', 'â€': '"',
            '\u00e2\u20ac\u201c': '—', '\u00e2\u20ac\u2122': "'"
        }
        for bad, good in replacements.items():
            text = text.replace(bad, good)
        return re.sub(r'\s+', ' ', text).strip()

    def mask_pii(text: str) -> str:
        if not isinstance(text, str):
            return ""
        text = re.sub(r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b', '[REDACTED_PAN]', text)
        text = re.sub(r'\b\d{4}\s?\d{4}\s?\d{4}\b', '[REDACTED_AADHAAR]', text)
        text = re.sub(r'\b(?:\d[ -]*?){13,16}\b', '[REDACTED_CARD_NO]', text)
        text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[REDACTED_EMAIL]', text)
        text = re.sub(r'\b[6-9]\d{9}\b', '[REDACTED_PHONE]', text)
        return text

    processed_records = []
    seen_hashes = set()
    pii_redactions_count = 0
    duplicate_count = 0

    SYSTEM_PROMPT = (
        "You are an official HDFC Bank AI Assistant. Provide accurate, domain-specific, "
        "policy-grounded, and secure banking assistance using the provided authoritative context."
    )

    sources_summary = {}

    # Helper to register a record
    def add_record(rec_id, source, task_type, domain, inst, ctx, resp):
        nonlocal pii_redactions_count, duplicate_count
        inst_clean, ctx_clean, resp_clean = mask_pii(inst), mask_pii(ctx), mask_pii(resp)
        if inst_clean != inst or ctx_clean != ctx or resp_clean != resp:
            pii_redactions_count += 1

        chash = hashlib.sha256((inst_clean + ctx_clean + resp_clean).encode('utf-8')).hexdigest()
        if chash in seen_hashes:
            duplicate_count += 1
            return
        seen_hashes.add(chash)

        user_msg = f"Authoritative Context: {ctx_clean}\n\nQuestion: {inst_clean}" if ctx_clean else inst_clean
        
        processed_records.append({
            "record_id": rec_id,
            "source": source,
            "task_type": task_type,
            "domain": domain,
            "instruction": inst_clean,
            "context": ctx_clean,
            "response": resp_clean,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
                {"role": "assistant", "content": resp_clean}
            ],
            "hash": chash
        })
        sources_summary[source] = sources_summary.get(source, 0) + 1

    # 1. HDFC_Custom_LLM_7000rows_Dataset_Suite-v2.xlsx
    f1 = 'HDFC_Custom_LLM_7000rows_Dataset_Suite-v2.xlsx'
    if os.path.exists(f1):
        sft_df = pd.read_excel(f1, sheet_name='Instruction SFT Dataset')
        for idx, row in sft_df.iterrows():
            add_record(f"rec-sft-{row['Task ID']}", f1, "sft_grounded_generation", str(row['Domain']),
                       fix_encoding(str(row['Instruction / Input Prompt'])),
                       fix_encoding(str(row['Authoritative Context Snippet'])),
                       fix_encoding(str(row['Target Model Response (JSON)'])))

    # 2. HDFC_Faq.xlsx
    f2 = 'HDFC_Faq.xlsx'
    if os.path.exists(f2):
        faq_df = pd.read_excel(f2)
        for idx, row in faq_df.iterrows():
            q, a = fix_encoding(str(row['question'])), fix_encoding(str(row['answer']))
            if q and a and len(q) > 2 and len(a) > 2:
                add_record(f"rec-hdfcfaq-{idx+1:05d}", f2, "customer_faq_qa", "General Banking FAQ",
                           q, "HDFC Support Knowledge Base", a)

    # 3. BANKING77_Real_Banking_Dataset.xlsx
    f3 = 'BANKING77_Real_Banking_Dataset.xlsx'
    if os.path.exists(f3):
        b77_df = pd.read_excel(f3, sheet_name='All_Data')
        for idx, row in b77_df.iterrows():
            text, cat = fix_encoding(str(row['text'])), fix_encoding(str(row['category']))
            if text and cat:
                add_record(f"rec-b77-{row['id']:05d}", f3, "intent_classification", "Intent Taxonomy",
                           f"Classify the intent for this customer query: '{text}'", "BANKING77 Taxonomy", json.dumps({"intent_category": cat}))

    # 4. banking_knowledge_base_1000.xlsx
    f4 = 'banking_knowledge_base_1000.xlsx'
    if os.path.exists(f4):
        kb_df = pd.read_excel(f4)
        for idx, row in kb_df.iterrows():
            q, a, sec = fix_encoding(str(row['Question'])), fix_encoding(str(row['Answer'])), fix_encoding(str(row['Section']))
            if q and a:
                add_record(f"rec-kb-{idx+1:05d}", f4, "domain_concept_qa", sec, q, f"Domain: {sec}", a)

    # 5. bank_faq.xlsx
    f5 = 'bank_faq.xlsx'
    if os.path.exists(f5):
        bfaq_df = pd.read_excel(f5)
        for idx, row in bfaq_df.iterrows():
            q, a, cat = fix_encoding(str(row['question'])), fix_encoding(str(row['answer'])), fix_encoding(str(row['category']))
            if q and a:
                add_record(f"rec-bfaq-{row['faq_id']}", f5, "customer_faq_qa", cat, q, f"Category: {cat}", a)

    # 6. customer_queries.xlsx
    f6 = 'customer_queries.xlsx'
    if os.path.exists(f6):
        cq_df = pd.read_excel(f6)
        for idx, row in cq_df.iterrows():
            q, intent, cat = fix_encoding(str(row['query'])), fix_encoding(str(row['intent'])), fix_encoding(str(row['category']))
            if q and intent:
                add_record(f"rec-cq-{row['query_id']}", f6, "intent_classification", cat,
                           f"Identify the intent of this query: '{q}'", f"Channel: {row['channel']}", json.dumps({"intent": intent, "category": cat}))

    # 7. customers.xlsx
    f7 = 'customers.xlsx'
    if os.path.exists(f7):
        cust_df = pd.read_excel(f7)
        for idx, row in cust_df.iterrows():
            inst = f"Retrieve profile details for Customer ID {row['customer_id']}"
            ctx = f"Customer Profile: Name={row['customer_name']}, Age={row['age']}, Gender={row['gender']}, City={row['city']}, State={row['state']}, Occupation={row['occupation']}, Segment={row['customer_segment']}, KYC={row['kyc_status']}"
            resp = json.dumps({
                "customer_id": row['customer_id'],
                "customer_name": "[CUSTOMER_NAME]",
                "city": row['city'],
                "state": row['state'],
                "segment": row['customer_segment'],
                "kyc_status": row['kyc_status']
            })
            add_record(f"rec-cust-{row['customer_id']}", f7, "profile_extraction", "Customer Profile", inst, ctx, resp)

    # 8. accounts.xlsx
    f8 = 'accounts.xlsx'
    if os.path.exists(f8):
        acc_df = pd.read_excel(f8)
        for idx, row in acc_df.head(5000).iterrows():  # Sample top 5000 for balanced task weighting
            inst = f"What is the status and balance for Account ID {row['account_id']}?"
            ctx = f"Account Record: Type={row['account_type']}, City={row['branch_city']}, Status={row['account_status']}, Balance=₹{row['balance_inr']:,}, Nominee Registered={row['nominee_registered']}"
            resp = f"Account {row['account_id']} is a {row['account_status']} {row['account_type']} account at {row['branch_city']} branch with a current balance of ₹{row['balance_inr']:,}."
            add_record(f"rec-acc-{row['account_id']}", f8, "account_status_inquiry", "Account Management", inst, ctx, resp)

    # 9. credit_cards.xlsx
    f9 = 'credit_cards.xlsx'
    if os.path.exists(f9):
        cards_df = pd.read_excel(f9)
        for idx, row in cards_df.iterrows():
            inst = f"Check credit limit and utilization for Credit Card ID {row['card_id']}"
            ctx = f"Card Details: Type={row['card_type']}, Status={row['card_status']}, Limit=₹{row['credit_limit_inr']:,}, Current Utilization=₹{row['current_utilization_inr']:,} ({row['utilization_pct']}%), Reward Points={row['reward_points']}"
            resp = f"Card {row['card_id']} ({row['card_type']}) has a credit limit of ₹{row['credit_limit_inr']:,} with current utilization at {row['utilization_pct']}% (₹{row['current_utilization_inr']:,}). Reward points balance: {row['reward_points']}."
            add_record(f"rec-card-{row['card_id']}", f9, "card_servicing", "Credit Cards", inst, ctx, resp)

    # 10. loans.xlsx
    f10 = 'loans.xlsx'
    if os.path.exists(f10):
        loans_df = pd.read_excel(f10)
        for idx, row in loans_df.iterrows():
            inst = f"Provide EMI and loan summary for Loan ID {row['loan_id']}"
            ctx = f"Loan Summary: Type={row['loan_type']}, Amount=₹{row['loan_amount_inr']:,.2f}, Interest Rate={row['interest_rate_pct']}%, Tenure={row['tenure_months']} months, EMI=₹{row['monthly_emi_inr']:,.2f}, Status={row['loan_status']}"
            resp = f"Loan {row['loan_id']} ({row['loan_type']}) of amount ₹{row['loan_amount_inr']:,.2f} at {row['interest_rate_pct']}% interest rate has a monthly EMI of ₹{row['monthly_emi_inr']:,.2f}. Status: {row['loan_status']}."
            add_record(f"rec-loan-{row['loan_id']}", f10, "loan_summary", "Loans & Mortgages", inst, ctx, resp)

    # 11. transactions.xlsx
    f11 = 'transactions.xlsx'
    if os.path.exists(f11):
        txn_df = pd.read_excel(f11)
        # Sample 10,000 transaction records for balanced LLM training distribution
        for idx, row in txn_df.head(10000).iterrows():
            inst = f"Summarize transaction record {row['transaction_id']} and verify fraud status."
            ctx = f"Transaction Log: Type={row['transaction_type']}, Amount=₹{row['amount_inr']}, Channel={row['payment_channel']}, Merchant={row['merchant']}, City={row['transaction_city']}, Status={row['status']}, Fraud Flag={row['fraud_flag']}"
            resp = f"Transaction {row['transaction_id']} was a {row['transaction_type']} of ₹{row['amount_inr']} via {row['payment_channel']} at {row['merchant']} ({row['transaction_city']}). Status: {row['status']}. Fraud Alert: {row['fraud_flag']}."
            add_record(f"rec-txn-{row['transaction_id']}", f11, "transaction_audit", "Transactions & Fraud", inst, ctx, resp)

    # Shuffle & Split (80% Train / 10% Val / 10% Test)
    np.random.seed(42)
    indices = np.arange(len(processed_records))
    np.random.shuffle(indices)

    n_total = len(processed_records)
    n_train, n_val = int(0.80 * n_total), int(0.10 * n_total)

    train_recs = [processed_records[i] for i in indices[:n_train]]
    val_recs = [processed_records[i] for i in indices[n_train:n_train+n_val]]
    test_recs = [processed_records[i] for i in indices[n_train+n_val:]]

    def save_jsonl(recs, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            for r in recs:
                f.write(json.dumps(r, ensure_ascii=False) + '\n')

    save_jsonl(train_recs, 'hdfc_llm_train.jsonl')
    save_jsonl(val_recs, 'hdfc_llm_val.jsonl')
    save_jsonl(test_recs, 'hdfc_llm_test.jsonl')

    manifest = {
        "dataset_name": "HDFC_Custom_LLM_All_11_Datasets_Unified_Suite",
        "pipeline_version": "v2.0-complete",
        "total_records_processed": n_total,
        "duplicates_removed": duplicate_count,
        "pii_redactions_applied": pii_redactions_count,
        "splits": {
            "train_count": len(train_recs),
            "val_count": len(val_recs),
            "test_count": len(test_recs)
        },
        "sources_summary": sources_summary
    }

    with open('data_manifest.json', 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

    return manifest

manifest_all = clean_and_build_all_11_datasets()
print(json.dumps(manifest_all, indent=2))