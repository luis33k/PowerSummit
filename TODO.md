# TODO: Fix Memory Error in load_master_log

## Tasks
- [ ] Modify load_master_log in data_handler.py to use pd.concat instead of outer merge to prevent Cartesian product explosion.
- [ ] Optimize data types: Convert numeric columns to float32/int32 after loading sheets to reduce memory usage.
- [ ] Test the fix by running the app and checking for memory issues.
- [ ] Ensure no random sessions are created and no infinite loops occur.

## Notes
- The outer merge was causing row multiplication when multiple sheets had rows for the same date.
- pd.concat will stack DataFrames vertically, preserving separate rows.
- Data type optimization should help with large arrays.
