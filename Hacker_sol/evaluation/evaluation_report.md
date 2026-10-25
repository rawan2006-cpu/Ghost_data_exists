
Data privacy detection and Compliance Evaluation report

The log.txt file: Giving complete historical audit log of 
                      -every file loaded
                      -how many rows were read
                      -How each case was classified
                      -When the output csv was successfully saved
                    By interceppting the output 
                Helping also for tracing if there is any conflict in the output.csv

First: The User requests deletion

   - Reading requests and rules for the deletion
   - Existence check (Error if the primary file is not found)
   - Dictionary mapping (iterates over the files and ensures that each of them is not empty)
   - Variable extraction and text capturing and intent filtering to see if the user is NOT_APPLICABLE

Second: Multi-Source dataset and column scanning
    
   - Skips the empty file if there is one (if df.empty:)
   - Looping through every column and checking if the user's email is anywhere
   - Apply deletion_rules.csv governance if rules exist

Third: Evaluate compliance status and generate strict phase-based steps

   Senario A:
     Record is clean ( COMPLETE )
     1. REPORT_NO_RECORD, ABSENT
     2. VERIFY_RECORD_ABSENT, ABSENT

   Senario B:
     Lingering data Found (Incomplete)

     1. Finding Phase
      REPORT_REMAINING_RECORD, PRESENT
     
     2. Remediation Phase
      DELETE_RECORD, ABSENT
     
     3. Verification Phase
      VERIFY_RECORD_ABSENT, ABSENT
