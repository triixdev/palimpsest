"""Starter conflict cases (fictional, hand-written). Gold = what the LLM should be allowed to see:
A, B, both, or abstain (a person must decide). Grow this to 40+ before you quote numbers; n=20 is a smoke test."""
C = [
 ("What is the casual leave limit?", "Ref: P-1\nIssued 2021-01-05. Casual leave is 12 days a year.", "Ref: P-2\nIssued 2024-03-01. This policy supersedes P-1. Casual leave is 8 days a year.", "B"),
 ("How long is the notice period?", "Ref: H-4\nEffective 2025-07-01. The notice period is 30 days.", "Ref: H-1\nEffective 2022-02-01. The notice period is 60 days.", "A"),
 ("What is the late fee?", "Effective 2020-04-01. The late fee is 50 rupees per week.", "Effective 2026-04-01. The late fee is 100 rupees per week.", "B"),
 ("How many guests may stay?", "Issued 2023-09-01. Residents may host 2 guests overnight.", "Issued 2025-11-15. Residents may host 1 guest overnight.", "B"),
 ("Is remote work allowed?", "Issued 2026-02-01. Staff may work remotely 2 days a week.", "Issued 2022-02-01. Staff may work remotely 4 days a week.", "A"),
 ("What is the reimbursement cap for travel?", "Effective 2024-01-01. Travel reimbursement is capped at 5000 rupees.", "Effective 2024-09-01. In the travel policy, the cap is raised to 8000 rupees. Everything else in the travel policy remains.", "both"),
 ("Who approves purchases above 10000 rupees?", "Issued 2023-01-01. Purchases above 10000 rupees need the finance head and the director.", "Issued 2025-01-01. In the purchase policy, the approval limit for cash advances changes to 3000 rupees.", "both"),
 ("What are the lab hours?", "Issued 2024-05-01. The lab opens at 9 am and closes at 5 pm.", "Issued 2025-05-01. The lab hours for the chemistry wing only are extended to 7 pm.", "both"),
 ("What is the visitor policy for the library?", "Issued 2022-08-01. Visitors may use the library with a day pass.", "Issued 2024-08-01. Day passes now also cover the reading hall. The rest of the visitor rules stand.", "both"),
 ("What time do hostel gates close?", "Hostel gates close at 9 pm on weekdays.", "Hostel gates close at 10 pm on weekdays.", "abstain"),
 ("What is the exam re-evaluation fee?", "The re-evaluation fee is 500 rupees per paper.", "The re-evaluation fee is 750 rupees per paper.", "abstain"),
 ("How many attempts are allowed?", "Issued 2023-02-01. Students get 3 attempts.", "Issued 2023-02-01. Students get 2 attempts.", "abstain"),
 ("What is the data retention period?", "Effective 2022-01-01. Logs are kept for 90 days.", "Draft, not yet approved. Logs will be kept for 30 days.", "abstain"),
 ("What is the parking fee?", "Issued 2025-01-01. Parking costs 200 rupees a month.", "Issued 2021-01-01. Parking costs 100 rupees a month. This notice is repeated here for reference.", "A"),
 ("What is the dress code?", "Issued 2026-01-01. Formal wear is required on Mondays.", "Issued 2019-01-01. Formal wear is required every day.", "A"),
 ("What is the fine for a lost ID card?", "Ref: ID-1\nIssued 2020-01-01. The fine for a lost ID card is 100 rupees.", "Ref: ID-2\nIssued 2024-01-01. This policy supersedes ID-1. The fine for a lost ID card is 250 rupees.", "B"),
 ("How early must interns report?", "Issued 2025-03-01. Interns report at 9 am.", "Issued 2025-03-01. Interns report at 9 am on all working days.", "both"),
 ("What is the cafeteria refund rule?", "Issued 2024-06-01. Unused meal coupons are refunded in full.", "Issued 2026-06-01. Unused meal coupons are no longer refunded.", "B"),
 ("Can laptops be borrowed?", "Issued 2021-10-01. Laptops may be borrowed for 7 days.", "Issued 2026-10-01. Laptops may be borrowed for 3 days.", "B"),
 ("What is the sick leave allowance?", "Updated recently. Sick leave is 15 days.", "Sick leave is 10 days. Last reviewed some time ago.", "abstain"),
]
